#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path

CALL_RE = re.compile(r'(?<![\w.])([A-Za-z_]\w*)\.([A-Za-z_]\w*)\s*\(')
SCOPE_NAMES = {1: "server", 2: "client", 3: "both"}
VARIADIC_CALLS = {"UnrealNetwork.CallUnrealRPC", "UGCGameSystem.SetTimer"}
BLOCK_WORDS = {"function", "if", "for", "while", "do", "repeat"}


def editor_root():
    return Path(__file__).resolve().parents[2]


def blank_preserving_lines(match):
    return "".join("\n" if char == "\n" else " " for char in match.group(0))


def sanitize_lua(text):
    text = re.sub(r"--\[\[.*?\]\]", blank_preserving_lines, text, flags=re.S)
    text = re.sub(r"\[\[.*?\]\]", blank_preserving_lines, text, flags=re.S)
    text = re.sub(r"--[^\n]*", "", text)

    def mask_string(match):
        value = match.group(0)
        return value[0] + " " * max(0, len(value) - 2) + value[-1]

    return re.sub(r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')', mask_string, text)


def count_args(text, start):
    depth = 0
    commas = 0
    has_value = False
    blocks = []
    index = start
    while index < len(text):
        char = text[index]
        if char.isalpha() or char == "_":
            end = index + 1
            while end < len(text) and (text[end].isalnum() or text[end] == "_"):
                end += 1
            word = text[index:end]
            if word in BLOCK_WORDS:
                if word == "do" and blocks and blocks[-1] in ("for", "while"):
                    pass
                else:
                    blocks.append(word)
            elif word == "end":
                if blocks:
                    blocks.pop()
            elif word == "until":
                if blocks and blocks[-1] == "repeat":
                    blocks.pop()
            index = end
            continue
        if char in "([{":
            depth += 1
        elif char in ")]}":
            if depth == 0:
                break
            depth -= 1
        elif char == "," and depth == 0 and not blocks:
            commas += 1
        elif not char.isspace():
            has_value = True
        index += 1
    return 0 if not has_value else commas + 1


def call_context(path, mode):
    if mode in ("server", "client", "both"):
        return mode
    if mode == "off":
        return None
    parts = {part.lower() for part in Path(path).parts}
    if "ui" in parts or "client" in parts:
        return "client"
    if "service" in parts or "server" in parts:
        return "server"
    return "both"


def add_finding(findings, path, line, call, kind, severity, detail):
    findings.append(
        {
            "file": str(path),
            "line": line,
            "call": call,
            "kind": kind,
            "severity": severity,
            "detail": detail,
        }
    )


def scan_file(path, signatures, known_libs, local_stems, scope_mode, strict):
    text = sanitize_lua(path.read_text(encoding="utf-8", errors="ignore"))
    local_names = set(re.findall(r"\blocal\s+([A-Za-z_]\w*)", text))
    findings = []
    calls = 0
    for match in CALL_RE.finditer(text):
        lib, func = match.group(1), match.group(2)
        if lib not in known_libs or lib in local_names:
            continue
        calls += 1
        key = f"{lib}.{func}"
        line = text.count("\n", 0, match.start()) + 1
        args = count_args(text, match.end())
        signature = signatures.get(key)
        if signature is None:
            if lib in local_stems:
                continue
            add_finding(
                findings,
                path,
                line,
                key,
                "unknown_api",
                "error",
                "签名缓存中不存在该 API",
            )
            continue
        params = int(signature.get("params", 0) or 0)
        if key in VARIADIC_CALLS:
            params = args
        if args > params:
            add_finding(
                findings,
                path,
                line,
                key,
                "param_too_many",
                "error",
                f"调用参数 {args} 个，签名最多 {params} 个",
            )
        elif args < params:
            add_finding(
                findings,
                path,
                line,
                key,
                "param_too_few",
                "error" if strict else "warning",
                f"调用参数 {args} 个，签名参数 {params} 个（可能使用默认值）",
            )
        if signature.get("deprecated"):
            replacement = signature.get("replacement") or ""
            add_finding(
                findings,
                path,
                line,
                key,
                "deprecated",
                "error" if strict else "warning",
                f"已废弃；替代：{replacement or '未提供'}",
            )
        api_scope = int(signature.get("scope", 0) or 0)
        context = call_context(path, scope_mode)
        if context in ("server", "client"):
            if api_scope == 1 and context == "client":
                add_finding(
                    findings,
                    path,
                    line,
                    key,
                    "scope_mismatch",
                    "error" if strict else "warning",
                    "API 仅服务器可用，当前路径判定为客户端",
                )
            elif api_scope == 2 and context == "server":
                add_finding(
                    findings,
                    path,
                    line,
                    key,
                    "scope_mismatch",
                    "error" if strict else "warning",
                    "API 仅客户端可用，当前路径判定为服务器",
                )
    return calls, findings


def main():
    parser = argparse.ArgumentParser(prog="api_contract")
    parser.add_argument("--project", action="append", required=True,
                        help="待检查的 Lua 目录，可重复")
    parser.add_argument("--cache", default=None,
                        help="ApiMetadataCache.json；默认取编辑器 Saved/UGCResourceDaemon")
    parser.add_argument("--out", default="spec/api-contracts")
    parser.add_argument("--scope", choices=("auto", "off", "server", "client", "both"),
                        default="auto")
    parser.add_argument("--strict", action="store_true",
                        help="把参数不足/废弃/scope 警告升级为错误")
    args = parser.parse_args()

    root = editor_root()
    cache_path = Path(args.cache) if args.cache else (
        root / "ShadowTrackerExtra/Saved/UGCResourceDaemon/ApiMetadataCache.json"
    )
    if not cache_path.is_file():
        print(f"api cache not found: {cache_path}", file=sys.stderr)
        return 2
    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    signatures = cache.get("signatures") or {}
    known_libs = {key.split(".", 1)[0] for key in signatures}

    all_findings = []
    total_calls = 0
    files = 0
    local_stems = set()
    for project in args.project:
        base = Path(project)
        if not base.is_dir():
            print(f"project not found: {base}", file=sys.stderr)
            return 2
        local_stems.update(path.stem for path in base.rglob("*.lua"))
    for project in args.project:
        base = Path(project)
        for path in sorted(base.rglob("*.lua")):
            files += 1
            calls, findings = scan_file(
                path, signatures, known_libs, local_stems, args.scope, args.strict
            )
            total_calls += calls
            all_findings.extend(findings)

    errors = [finding for finding in all_findings if finding["severity"] == "error"]
    warnings = [finding for finding in all_findings if finding["severity"] == "warning"]
    warnings.sort(key=lambda finding: 0 if finding["kind"] == "deprecated" else 1)
    by_kind = {}
    for finding in all_findings:
        by_kind[finding["kind"]] = by_kind.get(finding["kind"], 0) + 1

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / "CHECK-REPORT.md"
    json_path = out / "report.json"

    lines = [
        "# API 契约检查",
        "",
        f"- 检查文件: {files}",
        f"- 已知 API 调用: {total_calls}",
        f"- 错误: {len(errors)}",
        f"- 警告: {len(warnings)}",
        f"- 分类: {json.dumps(by_kind, ensure_ascii=False)}",
        f"- 签名缓存: `{cache_path.as_posix()}` ({cache.get('version', 'unknown')})",
        "",
    ]
    if not all_findings:
        lines.extend(["无问题。", ""])
    for severity, title in (("error", "错误（阻断）"), ("warning", "警告（不阻断）")):
        items = [finding for finding in all_findings if finding["severity"] == severity]
        if not items:
            continue
        lines.extend([f"## {title}", ""])
        for finding in items[:200]:
            lines.append(
                f"- `{finding['file']}:{finding['line']}` **{finding['kind']}** "
                f"`{finding['call']}`：{finding['detail']}"
            )
        if len(items) > 200:
            lines.append(f"- …… 其余 {len(items) - 200} 条见 report.json")
        lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "files": files,
                "known_calls": total_calls,
                "errors": len(errors),
                "warnings": len(warnings),
                "by_kind": by_kind,
                "findings": all_findings,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        f"check: {files} files | calls {total_calls} | "
        f"errors {len(errors)} | warnings {len(warnings)}"
    )
    print(f"report: {report_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
