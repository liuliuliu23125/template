#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import sys
from collections import Counter, OrderedDict
from datetime import datetime
from pathlib import Path

CLASS_RE = re.compile(r'^---@class\s+(\w+)_C\s*:\s*(\w+)', re.M)
FIELD_RE = re.compile(r'^---@field\s+(\w+)\s+(\S+)', re.M)
MARKER = '--Edit Below--'

COMPONENT_PREFIX = ('U',)
COMPONENT_TYPES = {
    'USceneComponent', 'UStaticMeshComponent', 'USkeletalMeshComponent',
    'UParticleSystemComponent', 'USphereComponent', 'UBoxComponent',
    'UCapsuleComponent', 'UCameraComponent', 'USpringArmComponent',
    'UWidgetComponent', 'UAudioComponent', 'UChildActorComponent',
}

NON_CONFIG = {
    'Slot', 'Padding', 'RenderOpacity', 'Visibility', 'ToolTipText', 'Cursor',
    'WidgetStyle', 'ColorAndOpacity', 'Brush', 'DesiredSize', 'IsFocusable',
    'IsEnabled', 'bIsFocusable', 'bIsEnabled', 'Tags',
}

NOT_PLACEABLE_PARENTS = re.compile(
    r'(UserWidget|Widget|UIBP|Layout|Skill|Buff|Effect|ItemHandle|Projectile|'
    r'Consumable|Weapon|Armor|Helmet|Attachment|Handle)$'
)
PLACEABLE_SUFFIX = re.compile(
    r'(Actor|Pawn|Spawner|Teleport|Chest|Area|Point|Manager|Gate|Trigger|Mob|Boss|NPC)$'
)


def normalize_parent(parent):
    return parent[:-2] if parent.endswith('_C') else parent


def resolve_chain(cls, by_class, placed_names):
    chain = []
    cur = cls
    for _ in range(8):
        b = by_class.get(cur)
        if not b:
            break
        parent = normalize_parent(b['parent'])
        chain.append(parent)
        cur = parent
    return chain


def is_placeable(cls, parent, by_class, placed_names):
    if cls in placed_names:
        return True
    for name in [cls] + resolve_chain(cls, by_class, placed_names):
        if NOT_PLACEABLE_PARENTS.search(name):
            return False
    return any(PLACEABLE_SUFFIX.search(n)
               for n in [cls, normalize_parent(parent)] + resolve_chain(cls, by_class, placed_names))


def read_text(path):
    return Path(path).read_text(encoding='utf-8', errors='ignore')


def is_component(name, type_name):
    if name in NON_CONFIG:
        return True
    return type_name in COMPONENT_TYPES


def is_enum_or_struct(type_name):
    return type_name.startswith('TEnumAsByte') or type_name.startswith('F')


def field_kind(name, type_name):
    if name in NON_CONFIG:
        return 'meta'
    if type_name in COMPONENT_TYPES:
        return 'component'
    if type_name.endswith('_C'):
        return 'actor_ref'
    if is_enum_or_struct(type_name):
        return 'enum_struct'
    return 'config'


def parse_binding(path):
    text = read_text(path)
    head, body = text.split(MARKER, 1) if MARKER in text else (text, '')
    m = CLASS_RE.search(head)
    if not m:
        return None
    fields = FIELD_RE.findall(head)
    return {
        'class': m.group(1),
        'parent': m.group(2),
        'fields': [(n, t, field_kind(n, t)) for n, t in fields],
        'bound': MARKER in text,
        'body': body,
    }


def scan_bindings(root, label):
    base = Path(root)
    out = []
    if not base.is_dir():
        return out
    for p in sorted(base.rglob('*.lua')):
        parsed = parse_binding(p)
        if not parsed:
            continue
        out.append({**parsed, 'script': p.relative_to(base).as_posix(), 'label': label})
    return out


CODE_CLASS_RE = re.compile(
    r'LoadClass\(\s*(?:\w+\.GetUGCResourcesFullPath\()?\s*["\']Asset/(?:Blueprint/)?([A-Za-z0-9_/]+?)(?:\.\w+)?["\']')
CLASS_PATH_RE = re.compile(
    r'GetUGCResourcesFullPath\(\s*["\'](Asset/Blueprint/[A-Za-z0-9_/]+?)(?:\.\w+)?["\']')
TAG_USE_RE = re.compile(r'GetAllActorsWithTag\s*\([^,]+,\s*([^)]+)\)')
TAG_DEF_RE = re.compile(r'TagKey\s*=\s*\{([^}]+)\}', re.S)
ENUM_LOADER_RE = re.compile(r'DT_\w+\s*=\s*["\']([^"\']+)["\']')


_ASSET_CACHE = {}


def asset_exists(name, dirs):
    key = (name, tuple(dirs))
    if key in _ASSET_CACHE:
        return _ASSET_CACHE[key]
    found = False
    for d in dirs:
        base = Path(d)
        if not base.is_dir():
            continue
        if next(base.rglob(name + '.uasset'), None) is not None:
            found = True
            break
    _ASSET_CACHE[key] = found
    return found


def map_pattern(map_prefix):
    if map_prefix:
        prefix = map_prefix if map_prefix.endswith('/') else map_prefix + '/'
        return re.compile(re.escape(prefix).encode() + rb'([A-Za-z0-9_/]+)')
    return re.compile(rb'/[A-Za-z0-9_]+/Asset/Blueprint/([A-Za-z0-9_/]+)')


def scan_maps(map_dir, map_prefix=None):
    base = Path(map_dir)
    placed = Counter()
    maps = {}
    if not base.is_dir():
        return placed, maps
    pattern = map_pattern(map_prefix)
    for p in sorted(base.glob('*.umap')):
        data = p.read_bytes()
        refs = {m.group(1).decode() for m in pattern.finditer(data)}
        maps[p.name] = refs
        for r in refs:
            placed[r.split('/')[-1]] += 1
    return placed, maps


def scan_tag_defs(roots):
    tags = {}
    for root in roots:
        base = Path(root)
        if not base.is_dir():
            continue
        for p in base.rglob('*.lua'):
            text = read_text(p)
            m = TAG_DEF_RE.search(text)
            if not m:
                continue
            for line in m.group(1).splitlines():
                km = re.match(r'\s*(\w+)\s*=\s*"([^"]+)"', line)
                if km:
                    tags[km.group(1)] = {
                        'value': km.group(2),
                        'script': p.as_posix(),
                    }
    return tags


def source_sha256(roots):
    digest = hashlib.sha256()
    count = 0
    for root, label in roots:
        base = Path(root)
        if not base.is_dir():
            continue
        for path in sorted(base.rglob('*.lua')):
            digest.update(label.encode('utf-8'))
            digest.update(path.relative_to(base).as_posix().encode('utf-8'))
            digest.update(path.read_bytes())
            count += 1
    return digest.hexdigest(), count


def confirm_baseline(requested, yes):
    if not requested:
        return False
    if yes:
        return True
    if sys.stdin.isatty():
        try:
            answer = input('写入基线会固化当前问题，确认？[y/N] ').strip().lower()
            return answer in ('y', 'yes')
        except EOFError:
            print('拒绝写入基线：读取确认输入失败，需显式 --yes。', file=sys.stderr)
            return False
    print('拒绝写入基线：非交互环境必须显式 --yes。', file=sys.stderr)
    return False


def render_command(tool, args):
    lines = [f'python -I spec/tools/{tool} \\']
    for root, label in args.project:
        lines.append(f'  --project "{root}" {label} \\')
    if args.map_dir:
        lines.append(f'  --map-dir "{args.map_dir}" \\')
    if args.map_prefix:
        lines.append(f'  --map-prefix "{args.map_prefix}" \\')
    for root in args.asset_dir:
        lines.append(f'  --asset-dir "{root}" \\')
    lines.append(f'  --out "{args.out}"')
    return lines


def cmd_index(args):
    bindings = []
    for root, label in args.project:
        bindings += scan_bindings(root, label)

    placed, maps = scan_maps(args.map_dir, args.map_prefix) if args.map_dir else (Counter(), {})
    tags = scan_tag_defs([r for r, _ in args.project])

    placed_names = set()
    for refs in maps.values():
        placed_names |= {r.split('/')[-1] for r in refs}

    by_class = OrderedDict()
    for b in sorted(bindings, key=lambda x: (x['label'], x['class'])):
        by_class.setdefault(b['class'], b)

    entries = []
    for cls, b in by_class.items():
        if not is_placeable(cls, b['parent'], by_class, placed_names):
            continue
        cfg = [(n, t) for n, t, k in b['fields'] if k in ('config', 'enum_struct')]
        comps = [(n, t) for n, t, k in b['fields'] if k == 'component']
        refs = [(n, t) for n, t, k in b['fields'] if k == 'actor_ref']
        entries.append({
            'class': cls,
            'parent': b['parent'],
            'script': b['script'],
            'label': b['label'],
            'placed_count': placed.get(cls, 0),
            'placed_in': sorted(m for m, refs_ in maps.items()
                                if any(r.endswith('/' + cls) for r in refs_)),
            'config': cfg,
            'components': comps,
            'actor_refs': refs,
        })

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    payload = {
        'actor_count': len(entries),
        'placed_count': sum(1 for e in entries if e['placed_count']),
        'map_count': len(maps),
        'tags': tags,
        'entries': entries,
    }
    (out / 'index.json').write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    cards = [e for e in entries if e['placed_count']]
    cards.sort(key=lambda e: (-e['placed_count'], e['class']))

    lines = [
        '# 场景契约库',
        '',
        '> 由 `spec/tools/scene_contract.py index` 生成，勿手改。',
        f'> Actor 类 {len(entries)} 个，其中已被摆放 {len(cards)} 个；地图 {len(maps)} 张。',
        '',
        '## 用途',
        '',
        '场景没有 UI 那样的自动声明清单：`---@field` 只描述「这个类可调什么」，',
        '不描述「图上有几个」。所以本库分两层：',
        '',
        '- **属性层**（脚本静态可读）：每个 Actor 的配置字段、组件、引用',
        '- **摆放层**（扫描 `.umap` 得到）：哪些类真的被摆到图上、摆在哪几张图',
        '',
        '两层都对不上时说明该类只作为模板定义存在，或者被代码动态生成。',
        '',
        '## 索引',
        '',
        '| 来源 | Actor 类 | 已摆放 | 明细 |',
        '|---|---:|---:|---|',
    ]
    by_label = OrderedDict()
    for e in entries:
        by_label.setdefault(e['label'], []).append(e)
    for label, items in by_label.items():
        fname = f'{label}.md'
        lines.append(f'| {label} | {len(items)} | '
                     f'{sum(1 for i in items if i["placed_count"])} | [{fname}]({fname}) |')

    lines += [
        '',
        '## 运行时约定',
        '',
        '场景内容只能在运行时枚举，且返回值是 **Lua userdata 不是 table**',
        '（`type()=="userdata"`，`#`/`ipairs` 靠 metatable 模拟）。调用下游前先转纯表。',
        '',
        '```lua',
        'UGCActorComponentUtility.GetAllActorsOfClass(worldContext, ActorClass)',
        'UGCActorComponentUtility.GetAllActorsWithTag(worldContext, Tag)',
        '```',
        '',
        '## Actor Tag',
        '',
    ]
    if tags:
        lines.append('| 常量 | 值 | 定义位置 |')
        lines.append('|---|---|---|')
        for k, v in tags.items():
            lines.append(f'| `TagKey.{k}` | `{v["value"]}` | `{v["script"]}` |')
    else:
        lines.append('未发现 `TagKey` 定义。')

    lines += (
        ['', '## 命令', '', '```bash']
        + render_command('scene_contract.py index', args)
        + ['']
        + render_command('scene_contract.py check', args)
        + ['```', '', '机器可读版本见 `index.json`。']
    )
    (out / 'INDEX.md').write_text('\n'.join(lines), encoding='utf-8')

    for label, items in by_label.items():
        detail = [
            f'# {label} Actor 明细',
            '',
            '> 由 `spec/tools/scene_contract.py index` 生成，勿手改。',
            '',
        ]
        for e in items:
            detail.append(f'## `{e["class"]}`')
            detail.append('')
            detail.append(f'- 父类 `{e["parent"]}`')
            detail.append(f'- 脚本 `{e["script"]}`')
            if e['placed_count']:
                detail.append(f'- 已摆放 **{e["placed_count"]}** 处，地图：'
                              f'{", ".join(e["placed_in"])}')
            else:
                detail.append('- **未在扫描的地图中找到**（模板定义 / 代码动态生成）')
            if e['config']:
                detail.append('')
                detail.append('| 配置字段 | 类型 |')
                detail.append('|---|---|')
                for n, t in e['config']:
                    detail.append(f'| `{n}` | `{t}` |')
            if e['actor_refs']:
                detail.append('')
                detail.append('| Actor 引用 | 类型 |')
                detail.append('|---|---|')
                for n, t in e['actor_refs']:
                    detail.append(f'| `{n}` | `{t}` |')
            if e['components']:
                detail.append('')
                detail.append(f'组件 {len(e["components"])} 个：'
                              + ', '.join(f'`{n}`' for n, _ in e['components']))
            detail.append('')
        (out / f'{label}.md').write_text('\n'.join(detail), encoding='utf-8')

    print(f'index: {len(entries)} 个 Actor 类 (已摆放 {len(cards)}) -> {out}')
    return 0


def cmd_check(args):
    bindings = []
    for root, label in args.project:
        bindings += scan_bindings(root, label)
    known = {b['class'] for b in bindings}

    placed, maps = scan_maps(args.map_dir, args.map_prefix) if args.map_dir else (Counter(), {})
    tags = scan_tag_defs([r for r, _ in args.project])
    tag_values = {v['value'] for v in tags.values()}

    classes_in_maps = set()
    for refs in maps.values():
        classes_in_maps |= {r.split('/')[-1] for r in refs}

    code_refs = []
    tag_uses = []
    table_paths = []
    for root, label in args.project:
        base = Path(root)
        if not base.is_dir():
            continue
        for p in base.rglob('*.lua'):
            text = read_text(p)
            rel = p.as_posix()
            for m in CODE_CLASS_RE.finditer(text):
                code_refs.append((rel, m.group(1), m.group(0)))

            for m in TAG_USE_RE.finditer(text):
                tag_uses.append((rel, m.group(1).strip()))
            for m in ENUM_LOADER_RE.finditer(text):
                table_paths.append((m.group(1), rel))

    problems = []

    seen_refs = set()
    for rel, ref, raw in code_refs:
        if (rel, ref) in seen_refs:
            continue
        seen_refs.add((rel, ref))
        name = ref.split('/')[-1]
        if name in classes_in_maps or name in known:
            continue
        if asset_exists(name, args.asset_dir or []):
            continue
        problems.append({
            'kind': '代码引用的蓝图类未找到',
            'detail': f'`{name}`（{rel}）',
            'hint': raw[:90],
        })

    for rel, expr in tag_uses:
        if expr.startswith('"') or expr.startswith("'"):
            value = expr.strip('"\'')
            if value not in tag_values:
                problems.append({'kind': 'Tag 字面量未在 TagKey 中定义',
                                 'detail': f'`{value}`（{rel}）', 'hint': '建议改用 Util_EnumManager.TagKey'})
        elif 'TagKey.' not in expr and not expr.isidentifier():
            pass

    lines = [
        '# 场景配置检查',
        '',
        f'- 绑定 Actor 类: {len(known)}',
        f'- 地图摆放类: {len(classes_in_maps)}',
        f'- 代码引用的蓝图类: {len(code_refs)}',
        f'- Tag 使用点: {len(tag_uses)}',
        f'- 问题: {len(problems)}',
        '',
    ]
    if problems:
        lines.append('## 问题')
        lines.append('')
        for p in problems:
            lines.append(f'- **{p["kind"]}**：{p["detail"]}')
            if p.get('hint'):
                lines.append(f'  - 出处 `{p["hint"]}`')
        lines.append('')
    else:
        lines.append('无问题。')
        lines.append('')

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    report = out / 'CHECK-REPORT.md'

    baseline_file = out / 'BASELINE.json'
    current = sorted(f'{p["kind"]}|{p["detail"]}' for p in problems)
    source_hash, source_files = source_sha256(args.project)
    known_baseline = set()
    baseline_hash = None
    if baseline_file.is_file():
        try:
            baseline_data = json.loads(baseline_file.read_text(encoding='utf-8'))
            known_baseline = set(baseline_data.get('entries', []))
            baseline_hash = baseline_data.get('source_sha256')
        except (ValueError, OSError):
            known_baseline = set()

    new_problems = [p for p in problems if f'{p["kind"]}|{p["detail"]}' not in known_baseline]
    fixed = sorted(known_baseline - set(current))

    lines.insert(5, f'- 新增问题（会阻断）: {len(new_problems)}')
    if known_baseline:
        lines.insert(6, f'- 基线内已知问题: {len(problems) - len(new_problems)}')
        if fixed:
            lines.insert(7, f'- 基线中已修复（可更新基线）: {len(fixed)}')

    if new_problems:
        lines.append('')
        lines.append('## 新增问题（阻断）')
        lines.append('')
        for p in new_problems:
            lines.append(f'- **{p["kind"]}**：{p["detail"]}')
            if p.get('hint'):
                lines.append(f'  - 出处 `{p["hint"]}`')

    if fixed:
        lines.append('')
        lines.append('## 基线中已修复')
        lines.append('')
        for f in fixed:
            lines.append(f'- {f}')

    lines.append('')
    lines.append(f'- 当前源哈希: `{source_hash}`（{source_files} 个 Lua 文件）')
    if baseline_hash and baseline_hash != source_hash:
        lines.append('- 基线源哈希已变化：基线可能过期。')
    if baseline_file.is_file() and not baseline_hash:
        lines.append('- 基线缺少源哈希（旧格式），建议用 `--write-baseline --yes` 重建。')

    write_confirmed = confirm_baseline(args.write_baseline, args.yes)
    write_pending = bool(args.write_baseline and not write_confirmed)
    if write_confirmed:
        baseline_file.write_text(json.dumps(
            {
                'entries': current,
                'generated_at': datetime.now().isoformat(timespec='seconds'),
                'source_sha256': source_hash,
                'source_files': source_files,
                'updated': 'manual',
            },
            ensure_ascii=False, indent=2), encoding='utf-8')
        lines.append('')
        lines.append('> 基线已写入 `BASELINE.json`。')
    elif write_pending:
        lines.append('')
        lines.append('> 未写入基线：需要 `--yes` 或交互确认。')

    report.write_text('\n'.join(lines), encoding='utf-8')
    print(f'check: {len(known)} 类 | 地图 {len(classes_in_maps)} 类 | '
          f'问题 {len(problems)} | 新增 {len(new_problems)}')
    print(f'report: {report}')
    return 1 if new_problems or write_pending else 0


def main():
    ap = argparse.ArgumentParser(prog='scene_contract')
    sub = ap.add_subparsers(dest='cmd', required=True)

    def add_common(p):
        p.add_argument('--project', action='append', nargs=2,
                       metavar=('DIR', 'LABEL'), default=[])
        p.add_argument('--map-dir', default=None)
        p.add_argument('--map-prefix', default=None,
                       help='蓝图资产包前缀，如 /MyProject/Asset/Blueprint/；留空则匹配任意 /<Project>/Asset/Blueprint/')
        p.add_argument('--asset-dir', action='append', default=[])
        p.add_argument('--out', required=True)

    pi = sub.add_parser('index', help='生成场景契约库')
    add_common(pi)
    pi.set_defaults(func=cmd_index)

    pc = sub.add_parser('check', help='校验场景配置')
    add_common(pc)
    pc.add_argument('--write-baseline', action='store_true',
                    help='把当前问题写入 BASELINE.json')
    pc.add_argument('--yes', action='store_true',
                    help='非交互确认写入基线')
    pc.set_defaults(func=cmd_check)

    args = ap.parse_args()
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())