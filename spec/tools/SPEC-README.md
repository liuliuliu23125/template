# Spec 状态检查

> `spec_check.py` 把 `spec/INDEX.md`、`01-understand.md`、`03-plan.md`、`06-sync.md`、`04-impl/` 的结构纳入脚本判定；不评审内容质量。

## 约定

- `spec/INDEX.md`：表格用 `模块名`、`spec 目录`、`进度` 三列。前两列用于定位；`进度` 含 `已废弃`/`已被取代` 时跳过该条，缺 `进度` 按「需要 03-plan」处理。
- `01-understand.md`、`06-sync.md`：每个活跃条目必须有。
- `03-plan.md`：进度不是恰为 `读取完成`/`拆解未开始`/`未开始` 时必须有（`T01-T03 未开始` 仍需计划）。
- 任务：`### T01 标题` 或表格行 `| T01 | ... |`（支持 `T01-R1` 修订号）；块内写 `- 状态: 已确认` 等。
- 来源：任务缺 `来源: fp-xxx` 只记警告；填了 `fp-xxx` 但不在 `06-sync.md` 的 FP 表 → 错误。
- 状态为 `已确认`/`已完成`/`已实现` 的任务，`04-impl/` 必须有文件在文件名或正文引用该任务号。
- `06-sync.md` 必须有 `FP` + `实现状态` 表，且至少一行数据。

## 用法

```bash
python -I spec/tools/spec_check.py
python -I spec/tools/spec_check.py --spec-dir spec --out spec/CHECK-REPORT.md
python -I spec/tools/spec_check.py --self-test
```

- 退出码：0=无错误；1=有错误（警告不阻断）。
- 报告默认写 `spec/CHECK-REPORT.md`，属运行产物，不入库。
- `--self-test` 会在临时目录构造“有效/缺 04-impl”两个用例，验证检查器能区分。

## 不做的事

- 不判断任务描述是否正确、功能点是否覆盖文档、验收证据是否充分。
- 不替代 `01-understand.md` / `03-plan.md` 的人工 gate。
- 不生成或补写缺失文件。
