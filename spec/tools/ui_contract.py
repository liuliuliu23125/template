#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import sys
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

CLASS_RE = re.compile(r'^---@class\s+(\w+)_C\s*:\s*(\w+)', re.M)
FIELD_RE = re.compile(r'^---@field\s+(\w+)\s+(\w+)', re.M)
MARKER = '--Edit Below--'

BASE_PROPS = {
    'Slot', 'Padding', 'RenderOpacity', 'Visibility', 'ToolTipText', 'Cursor',
    'WidgetStyle', 'ColorAndOpacity', 'Brush', 'DesiredSize', 'IsFocusable',
    'IsEnabled', 'bIsFocusable', 'bIsEnabled',
}

WIDGET_SUFFIX = re.compile(
    r'(Box|Panel|Btn|Button|Image|Text|Bar|Slot|Widget|Icon|Label|Bg|Border|'
    r'Switcher|Scroll|Grid|Overlay|Canvas|SizeBox|Root|Title|Name|Desc)$'
)


def read_text(path):
    return Path(path).read_text(encoding='utf-8', errors='ignore')


def read_bytes(path):
    return Path(path).read_bytes()


def parse_binding(path):
    text = read_text(path)
    head, body = text.split(MARKER, 1) if MARKER in text else (text, '')
    m = CLASS_RE.search(head)
    if not m:
        return None
    fields = [(n, t) for n, t in FIELD_RE.findall(head)]
    return {
        'class': m.group(1),
        'parent': m.group(2),
        'fields': fields,
        'bound': MARKER in text,
        'head_lines': head.count('\n'),
        'body': body,
    }


def is_widget_field(name, type_name):
    if name in BASE_PROPS:
        return False
    return type_name.startswith('U')


def scan_scripts(roots):
    result = []
    seen = set()
    for root, prefix in roots:
        base = Path(root)
        if not base.is_dir():
            continue
        for p in sorted(base.rglob('*.lua')):
            key = str(p.resolve()).lower()
            if key in seen:
                continue
            seen.add(key)
            parsed = parse_binding(p)
            if not parsed:
                continue
            rel = p.relative_to(base).as_posix()
            result.append({
                'script': rel,
                'source_root': str(base),
                'label': prefix,
                'class': parsed['class'],
                'parent': parsed['parent'],
                'fields': parsed['fields'],
                'bound': parsed['bound'],
                'body': parsed['body'],
                'size': p.stat().st_size,
            })
    return result


def build_asset_index(asset_roots):
    index = {}
    for root in asset_roots:
        base = Path(root)
        if not base.is_dir():
            continue
        for p in base.rglob('*.uasset'):
            index.setdefault(p.stem, []).append(p)
    return index


def find_asset(class_name, asset_index):
    hits = asset_index.get(class_name)
    return hits or []


def widget_names_in_asset(path, cache):
    key = str(Path(path).resolve())
    if key in cache:
        return cache[key]
    data = read_bytes(path)
    cache[key] = data
    return data


def classify_scripts(scripts, asset_index, only_widgets=True):
    entries = []
    for s in scripts:
        if only_widgets and 'UserWidget' not in s['parent']:
            continue
        widgets = [(n, t) for n, t in s['fields'] if is_widget_field(n, t)]
        assets = find_asset(s['class'], asset_index)
        entries.append({**s, 'widgets': widgets, 'assets': [str(a) for a in assets]})
    return entries


def check_entry(entry, asset_cache, strict=False):
    declared = {n for n, _ in entry['widgets']}
    body = entry['body']
    used = set(re.findall(r'self\.(\w+)', body))
    defined = set(re.findall(r'self[.:](\w+)\s*=\s*function', body))
    funcref = set(re.findall(r'self\.(\w+)\s*[,)]', body))
    guarded = set(re.findall(r'self\.(\w+)\s*(?:==|~=|and\b|or\b|then)', body))
    dict_names = set()
    for block in re.findall(r'\{([^{}]*)\}', body):
        dict_names |= set(re.findall(r'"(\w+)"', block))

    stale = sorted(
        n for n in used - declared - defined - funcref - dict_names
        if n not in guarded and n not in BASE_PROPS
        and not n.startswith('_') and (strict or WIDGET_SUFFIX.search(n))
    )

    nested = {n for n, t in entry['widgets'] if t.endswith('_C')}
    missing_in_asset = []
    if entry['assets']:
        data = widget_names_in_asset(entry['assets'][0], asset_cache)
        missing_in_asset = sorted(
            n for n in declared if n.encode() not in data and n not in nested)

    return {
        'class': entry['class'],
        'script': entry['script'],
        'label': entry['label'],
        'asset': entry['assets'][0] if entry['assets'] else None,
        'widget_count': len(declared),
        'stale_refs': stale,
        'missing_in_asset': missing_in_asset,
    }


def resolve_asset_roots(project_roots, store_roots, extra):
    if extra:
        roots = list(extra)
    else:
        roots = []
        for root, _ in project_roots:
            base = Path(root)
            if base.name.lower() == 'script' and (base.parent / 'Asset').is_dir():
                roots.append(str(base.parent / 'Asset'))
    roots.extend(r for r, _ in store_roots)
    return roots


def coverage_stats(entries):
    total = sum(len(e['widgets']) for e in entries)
    checked = sum(
        1 for e in entries for name, _ in e['widgets'] if WIDGET_SUFFIX.search(name)
    )
    return {
        'widgets_total': total,
        'suffix_checked': checked,
        'suffix_unchecked': total - checked,
        'suffix_checked_pct': round(checked * 100 / total, 2) if total else 0.0,
    }


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
    for root, label in args.store:
        lines.append(f'  --store "{root}" {label} \\')
    for root in args.asset_dir:
        lines.append(f'  --asset-dir "{root}" \\')
    lines.append(f'  --out "{args.out}"')
    return lines


def cmd_index(args):
    scripts = scan_scripts(args.project + args.store)
    asset_roots = resolve_asset_roots(args.project, args.store, args.asset_dir)
    asset_index = build_asset_index(asset_roots)
    entries = classify_scripts(scripts, asset_index, only_widgets=True)
    entries.sort(key=lambda e: (e['label'], e['class']))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    coverage = coverage_stats(entries)
    payload = {
        'count': len(entries),
        'widgets_total': coverage['widgets_total'],
        'coverage': coverage,
        'asset_roots': asset_roots,
        'entries': [
            {
                'class': e['class'],
                'parent': e['parent'],
                'script': e['script'],
                'label': e['label'],
                'asset': e['assets'][0] if e['assets'] else None,
                'widgets': [{'name': n, 'type': t} for n, t in e['widgets']],
            }
            for e in entries
        ],
    }
    (out / 'index.json').write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    by_label = OrderedDict()
    for e in entries:
        by_label.setdefault(e['label'], []).append(e)

    lines = [
        '# UI 契约库',
        '',
        '> 由 `spec/tools/ui_contract.py index` 生成，勿手改。',
        f'> 界面 {len(entries)} 个，控件声明 {payload["widgets_total"]} 个。',
        f'> 控件名后缀规则覆盖 {coverage["suffix_checked"]}/{coverage["widgets_total"]}'
        f'（{coverage["suffix_checked_pct"]}%），未覆盖 {coverage["suffix_unchecked"]} 个。',
        '',
        '## 用途',
        '',
        'Agent 接到 UI 需求时先查本库：命中则复用现有界面（复制资产 + 绑定），',
        '未命中才设计新界面。控件名以本库为准，禁止引用库中不存在的控件。',
        '',
        '## 索引',
        '',
        '| 来源 | 界面数 | 控件数 | 明细 |',
        '|---|---:|---:|---|',
    ]
    for label, items in by_label.items():
        fname = f'{label}.md'
        cnt = sum(len(e['widgets']) for e in items)
        lines.append(f'| {label} | {len(items)} | {cnt} | [{fname}]({fname}) |')

    lines += (
        ['', '## 查询方式', '', '```bash', '# 全量重建']
        + render_command('ui_contract.py index', args)
        + ['', '# 控件名契约检查（有未声明引用时退出码 1）']
        + render_command('ui_contract.py check', args)
        + ['```', '', '机器可读版本见 `index.json`。']
    )
    (out / 'INDEX.md').write_text('\n'.join(lines), encoding='utf-8')

    for label, items in by_label.items():
        detail = [
            f'# {label} 界面明细',
            '',
            '> 由 `spec/tools/ui_contract.py index` 生成，勿手改。',
            '',
        ]
        for e in items:
            detail.append(f'## `{e["class"]}`')
            detail.append('')
            detail.append(f'- 父类 `{e["parent"]}`')
            detail.append(f'- 脚本 `{e["script"]}`')
            if e['assets']:
                detail.append(f'- 资产 `{Path(e["assets"][0]).as_posix()}`')
            else:
                detail.append('- 资产 **未找到同名文件**')
            if e['widgets']:
                detail.append('')
                detail.append('| 控件 | 类型 |')
                detail.append('|---|---|')
                for n, t in e['widgets']:
                    detail.append(f'| `{n}` | `{t}` |')
            detail.append('')
        (out / f'{label}.md').write_text('\n'.join(detail), encoding='utf-8')

    print(f'index: {len(entries)} 个界面, {payload["widgets_total"]} 个控件 -> {out}')
    return 0


def cmd_check(args):
    scripts = scan_scripts(args.project + args.store)
    asset_roots = resolve_asset_roots(args.project, args.store, args.asset_dir)
    asset_index = build_asset_index(asset_roots)
    entries = classify_scripts(scripts, asset_index, only_widgets=True)

    asset_cache = {}
    results = [check_entry(e, asset_cache, args.strict) for e in entries]
    coverage = coverage_stats(entries)

    stale = [r for r in results if r['stale_refs']]
    missing = [r for r in results if r['missing_in_asset']]
    clean = len(results) - len({r['class'] for r in stale} | {r['class'] for r in missing})

    lines = [
        '# UI 控件契约检查',
        '',
        f'- 界面总数: {len(results)}',
        f'- 通过: {clean}',
        f'- 代码引用未声明控件: {len(stale)}',
        f'- 声明控件在资产中缺失: {len(missing)}',
        f'- 控件名后缀规则覆盖: {coverage["suffix_checked"]}/{coverage["widgets_total"]}'
        f'（{coverage["suffix_checked_pct"]}%）',
        f'- 未覆盖控件名: {coverage["suffix_unchecked"]}',
        '',
    ]
    if stale:
        lines.append('## 代码引用未声明控件（必须修）')
        lines.append('')
        for r in stale:
            lines.append(f'### `{r["class"]}`')
            lines.append('')
            lines.append(f'脚本 `{r["script"]}`')
            lines.append('')
            for n in r['stale_refs']:
                lines.append(f'- `self.{n}` 不在上半部 `---@field` 中')
            lines.append('')
    if missing:
        lines.append('## 声明控件在资产中缺失（需人工确认）')
        lines.append('')
        lines.append('> 常见原因：控件在父类中声明、资产版本与脚本不同步、嵌套子控件。')
        lines.append('')
        for r in missing:
            lines.append(f'### `{r["class"]}`')
            lines.append('')
            if r['asset']:
                lines.append(f'资产 `{Path(r["asset"]).as_posix()}`')
            lines.append('')
            for n in r['missing_in_asset']:
                lines.append(f'- `{n}`')
            lines.append('')

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    report = out / 'CHECK-REPORT.md'

    baseline_file = out / 'BASELINE.json'
    current = sorted(
        [f'stale|{r["class"]}|{n}' for r in stale for n in r['stale_refs']]
        + [f'missing|{r["class"]}|{n}' for r in missing for n in r['missing_in_asset']])
    source_hash, source_files = source_sha256(args.project + args.store)
    known_baseline = set()
    baseline_hash = None
    if baseline_file.is_file():
        try:
            baseline_data = json.loads(baseline_file.read_text(encoding='utf-8'))
            known_baseline = set(baseline_data.get('entries', []))
            baseline_hash = baseline_data.get('source_sha256')
        except (ValueError, OSError):
            known_baseline = set()

    cur_set = set(current)
    new_entries = sorted(cur_set - known_baseline)
    fixed = sorted(known_baseline - cur_set)

    new_stale = [e for e in new_entries if e.startswith('stale|')]
    new_missing = [e for e in new_entries if e.startswith('missing|')]

    lines.insert(8, f'- 新增未声明引用（阻断）: {len(new_stale)}')
    lines.insert(9, f'- 新增资产缺失（需人工确认，不阻断）: {len(new_missing)}')
    if known_baseline:
        lines.insert(10, f'- 基线内已知问题: {len(cur_set & known_baseline)}')
        if fixed:
            lines.insert(11, f'- 基线中已修复（可更新基线）: {len(fixed)}')

    if new_entries:
        lines.append('')
        lines.append('## 新增问题')
        lines.append('')
        for e in new_stale:
            _, cls, name = e.split('|', 2)
            lines.append(f'- **未声明控件（阻断）** `{cls}` → `self.{name}`')
        for e in new_missing:
            _, cls, name = e.split('|', 2)
            lines.append(f'- **资产中缺失（不阻断）** `{cls}` → `{name}`')

    if fixed:
        lines.append('')
        lines.append('## 基线中已修复')
        lines.append('')
        for e in fixed:
            lines.append(f'- {e}')

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

    print(f'check: {len(results)} 界面 | 通过 {clean} | 未声明引用 {len(stale)} | '
          f'资产缺失 {len(missing)} | 新增 {len(new_entries)}')
    print(f'report: {report}')
    return 1 if new_stale or write_pending else 0


def main():
    ap = argparse.ArgumentParser(prog='ui_contract')
    sub = ap.add_subparsers(dest='cmd', required=True)

    def add_roots(p):
        p.add_argument('--project', action='append', nargs=2, metavar=('DIR', 'LABEL'), default=[])
        p.add_argument('--store', action='append', nargs=2, metavar=('DIR', 'LABEL'), default=[])
        p.add_argument('--asset-dir', action='append', default=[],
                       help='资产根目录；留空则从 <project>/Script 推导 <project>/Asset')
        p.add_argument('--out', required=True)

    pi = sub.add_parser('index', help='生成 UI 契约库')
    add_roots(pi)
    pi.set_defaults(func=cmd_index)

    pc = sub.add_parser('check', help='校验控件名契约')
    add_roots(pc)
    pc.add_argument('--write-baseline', action='store_true',
                    help='把当前问题写入 BASELINE.json')
    pc.add_argument('--yes', action='store_true',
                    help='非交互确认写入基线')
    pc.add_argument('--strict', action='store_true',
                    help='检查所有 self.X 引用，不再只按控件后缀过滤')
    pc.set_defaults(func=cmd_check)

    args = ap.parse_args()
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())