#!/usr/bin/env python3
import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

TASK_HEAD_RE = re.compile(r"^#{2,4}\s+(T\d+(?:-R\d+)?)\b(.*)$", re.M)
TASK_ROW_RE = re.compile(r"^\|\s*(T\d+(?:-R\d+)?)\s*\|(.+)\|\s*$", re.M)
STATUS_RE = re.compile(r"状态[:：]\s*([^\n|]+)")
SOURCE_RE = re.compile(r"来源[:：]\s*([^\n|]+)")
FP_RE = re.compile(r"^fp-[A-Za-z0-9_-]+$")


def editor_root():
    return Path(__file__).resolve().parents[2]


def parse_index(path):
    rows = []
    header = None
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]
        if header is None:
            if "模块名" in cells and "spec 目录" in cells:
                header = {name: index for index, name in enumerate(cells)}
            continue
        if all(set(cell) <= set("-: ") for cell in cells):
            continue
        row = {
            name: cells[index] if index < len(cells) else ""
            for name, index in header.items()
        }
        if row.get("模块名"):
            rows.append(row)
    return rows


def resolve_spec_dir(root, spec_root, value):
    path = Path(value)
    if path.is_absolute():
        return path
    if value.startswith("spec/") or value.startswith("spec\\"):
        return root / path
    return spec_root / path


def parse_plan(text):
    tasks = []
    headings = list(TASK_HEAD_RE.finditer(text))
    for index, match in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        block = text[match.start():end]
        status = STATUS_RE.search(block)
        source = SOURCE_RE.search(block)
        tasks.append(
            {
                "id": match.group(1),
                "title": match.group(2).strip(),
                "status": status.group(1).strip() if status else "",
                "source": source.group(1).strip() if source else "",
                "block": block,
            }
        )
    for match in TASK_ROW_RE.finditer(text):
        task_id = match.group(1)
        if any(task["id"] == task_id for task in tasks):
            continue
        row = match.group(0)
        status = STATUS_RE.search(row)
        source = SOURCE_RE.search(row)
        tasks.append(
            {
                "id": task_id,
                "title": row.strip(),
                "status": status.group(1).strip() if status else "",
                "source": source.group(1).strip() if source else "",
                "block": row,
            }
        )
    return tasks


def parse_sync(text):
    header = None
    rows = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]
        if header is None:
            if "FP" in cells and "实现状态" in cells:
                header = {name: index for index, name in enumerate(cells)}
            continue
        if all(set(cell) <= set("-: ") for cell in cells):
            continue
        row = {
            name: cells[index] if index < len(cells) else ""
            for name, index in header.items()
        }
        if row.get("FP"):
            rows.append(row)
    return rows


def impl_references(spec_dir, task_id):
    impl_dir = spec_dir / "04-impl"
    if not impl_dir.is_dir():
        return []
    hits = []
    for path in sorted(impl_dir.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if task_id in path.name or task_id in text:
            hits.append(str(path))
    return hits


def check_spec(spec_root):
    errors = []
    warnings = []
    index_path = spec_root / "INDEX.md"
    if not index_path.is_file():
        return ["spec/INDEX.md 不存在"], warnings, {}
    root = spec_root.parent
    rows = parse_index(index_path)
    summary = {"entries": len(rows)}
    for row in rows:
        name = row.get("模块名", "")
        progress = row.get("进度", "")
        if any(marker in progress for marker in ("已废弃", "已被取代")):
            continue
        value = row.get("spec 目录", "")
        if not value:
            errors.append(f"{name}: INDEX 未填写 spec 目录")
            continue
        spec_dir = resolve_spec_dir(root, spec_root, value)
        if not spec_dir.is_dir():
            errors.append(f"{name}: spec 目录不存在 {spec_dir}")
            continue
        for required in ("01-understand.md", "06-sync.md"):
            if not (spec_dir / required).is_file():
                errors.append(f"{name}: 缺少 {required}")
        need_plan = progress.strip() not in ("读取完成", "拆解未开始", "未开始")
        plan_path = spec_dir / "03-plan.md"
        if need_plan and not plan_path.is_file():
            errors.append(f"{name}: 缺少 03-plan.md（进度={progress or '空'}）")
        if not plan_path.is_file():
            continue
        plan_text = plan_path.read_text(encoding="utf-8", errors="ignore")
        tasks = parse_plan(plan_text)
        if not tasks:
            errors.append(f"{name}: 03-plan.md 未解析到任务（需要 ### Txx 或 | Txx | 行）")
        sync_path = spec_dir / "06-sync.md"
        sync_rows = []
        if sync_path.is_file():
            sync_rows = parse_sync(sync_path.read_text(encoding="utf-8", errors="ignore"))
            if not sync_rows:
                errors.append(f"{name}: 06-sync.md 未解析到 FP 表")
        fp_ids = {row.get("FP", "") for row in sync_rows}
        implemented = []
        for task in tasks:
            task_id = task["id"]
            status = task["status"]
            if not task["source"]:
                warnings.append(f"{name}: {task_id} 缺少 来源: fp-xxx")
            else:
                for fp in re.split(r"[,，\s]+", task["source"]):
                    if FP_RE.match(fp) and fp_ids and fp not in fp_ids:
                        errors.append(f"{name}: {task_id} 来源 {fp} 不在 06-sync.md")
            if any(marker in status for marker in ("已确认", "已完成", "已实现")):
                implemented.append(task_id)
                hits = impl_references(spec_dir, task_id)
                if not hits:
                    errors.append(f"{name}: {task_id} 状态={status}，但 04-impl 无记录")
        for sync_row in sync_rows:
            if "已实现" in sync_row.get("实现状态", "") and not implemented:
                warnings.append(f"{name}: 06-sync 有已实现 FP，但 plan 无已确认/已完成任务")
        summary[name] = {
            "spec_dir": str(spec_dir),
            "tasks": len(tasks),
            "implemented": implemented,
            "fps": len(sync_rows),
        }
    return errors, warnings, summary


def run_self_test():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        spec = root / "spec"
        demo = spec / "demo"
        (demo / "04-impl").mkdir(parents=True)
        (spec / "INDEX.md").write_text(
            "| 模块名 | 腾讯文档地址 | 别名地址 | spec 目录 | 首次拆解 | 上次同步 | 进度 |\n"
            "|---|---|---|---|---|---|---|\n"
            f"| Demo | https://docs.qq.com/doc/demo | | spec/demo | 2026-01-01 | 2026-01-01 | 已实现 |\n",
            encoding="utf-8",
        )
        (demo / "01-understand.md").write_text("# Demo\n", encoding="utf-8")
        (demo / "03-plan.md").write_text(
            "### T01 示例\n\n- 状态: 已确认\n- 来源: fp-demo\n",
            encoding="utf-8",
        )
        (demo / "06-sync.md").write_text(
            "| FP | 功能点 | 内容摘要 | 哈希 | 文档状态 | 实现状态 | 关联任务 | 素材来源 |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| fp-demo | 示例 | 内容 | hash | 活跃 | 已实现 | T01 | |\n",
            encoding="utf-8",
        )
        (demo / "04-impl" / "01-demo.md").write_text("T01 实现完成\n", encoding="utf-8")
        errors, warnings, summary = check_spec(spec)
        valid = not errors
        (demo / "04-impl" / "01-demo.md").unlink()
        broken_errors, _, _ = check_spec(spec)
        invalid = bool(broken_errors)
        (demo / "03-plan.md").unlink()
        (spec / "INDEX.md").write_text(
            "| 模块名 | 腾讯文档地址 | 别名地址 | spec 目录 | 首次拆解 | 上次同步 | 进度 |\n"
            "|---|---|---|---|---|---|---|\n"
            f"| Demo | https://docs.qq.com/doc/demo | | spec/demo | 2026-01-01 | 2026-01-01 | T01-T03 未开始 |\n",
            encoding="utf-8",
        )
        plan_errors, _, _ = check_spec(spec)
        plan_required = any("03-plan.md" in error for error in plan_errors)
        passed = valid and invalid and plan_required
        print(
            json.dumps(
                {
                    "result": "passed" if passed else "failed",
                    "valid_case_errors": errors,
                    "invalid_case_errors": broken_errors,
                    "plan_required_errors": plan_errors,
                    "summary": summary,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser(prog="spec_check")
    parser.add_argument("--spec-dir", default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return run_self_test()
    spec_root = Path(args.spec_dir) if args.spec_dir else editor_root() / "spec"
    errors, warnings, summary = check_spec(spec_root)
    out = Path(args.out) if args.out else spec_root / "CHECK-REPORT.md"
    lines = [
        "# Spec 状态检查",
        "",
        f"- spec: `{spec_root.as_posix()}`",
        f"- 活跃条目: {summary.get('entries', 0)}",
        f"- 错误: {len(errors)}",
        f"- 警告: {len(warnings)}",
        "",
    ]
    if errors:
        lines.extend(["## 错误（阻断）", ""])
        lines.extend(f"- {error}" for error in errors)
        lines.append("")
    if warnings:
        lines.extend(["## 警告", ""])
        lines.extend(f"- {warning}" for warning in warnings)
        lines.append("")
    if not errors and not warnings:
        lines.extend(["无问题。", ""])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"errors": len(errors), "warnings": len(warnings), "summary": summary},
                     ensure_ascii=False, indent=2))
    print(f"report: {out}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
