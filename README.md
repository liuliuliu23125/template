# Oasis UGC Agent 工作流模板

> 把 `AGENTS.md` 指令链、`Docs/`、需求拆解 skill 和 spec 检查/PIE 工具复制进绿洲启元编辑器安装目录，让 Agent 按「读文档 → 拆任务 → 实现 → 自动验证 → 人工验收」运行。
> 模板只含说明、配置与脚本，不含编辑器二进制、工程资产和玩法代码。

## 1. 使用方式（先看这里）

### 1.1 前置准备

| 项 | 要求 |
|---|---|
| 编辑器 | 已安装绿洲启元 UGC 编辑器，安装根含 `version.txt` 和 `ShadowTrackerExtra/` |
| Python | 3.x；所有脚本建议 `python -I` 运行，避免当前目录同名模块劫持导入 |
| 目标工程 | 含 `Script/`、`Asset/`、`.umap`；首次打开工程后生成 `Saved/UGCResourceDaemon/ApiMetadataCache.json` |
| 需求来源 | 腾讯文档链接；没有链接时拆解 skill 不会启动 |
| Lua 检查 | 编辑器自带的 `luacheck.exe`，配置见 `ShadowTrackerExtra/SpeedupSync/luacheck/check.json` |
| PIE 自动化 | 编辑器已启动、MCP Server 运行；端口读 `Saved/Config/WindowsUGCEditor/UGCSettings.ini` 的 `[AskQMCPServer]` |
| 腾讯文档读取 | Python 3 + Playwright + 系统 Chrome；`pip install -r .claude/skills/oasis-design-doc-decompose/scripts/requirements.txt`，缺浏览器时 `python -m playwright install chromium` |

首次 PIE 可能弹人脸识别，必须账号本人扫码；脚本会检测到、截图并以退出码 3 停下，处理后再 `--resume`。

### 1.2 内容前置（必须由人先准备）

Agent 只能写 Lua 行为，不能替代编辑器里的人工内容。下列内容没准备好，对应任务就是**阻塞项**，Phase C 不能开工：

| 内容 | 人先做什么 | Agent 只能做什么 |
|---|---|---|
| **UMG 界面** | 在编辑器创建/保存界面，控件名、类型和绑定字段由编辑器生成 | 写 `--Edit Below--` 之下的逻辑；不改布局、不改控件 |
| **配置表 / DA / Lua Config** | 定 RowStruct、列、行与导表；新表或新字段由人建 | 读表、写读取逻辑；不“顺手加一行配置” |
| **场景摆放** | 摆 Actor、Transform、地形、刷怪点、撤离点 | 写行为；需要动态生成时用 `UGCActorComponentUtility.SpawnActor` |
| **蓝图绑定头部** | 编辑器生成 `---@class` / `---@field` / `--Edit Below--` | 只写标记之下；改头部会被编辑器覆盖 |
| **`.ugcproj` / 工程配置** | 用编辑器 UI 修改 | 只读；手改后需要重开工程 |

Phase B 必须把这些写进 `03-plan.md`，标成 `前置: 人工`；人完成前，相关任务保持 `未开始`。

### 1.3 放进编辑器

1. 克隆或解压模板，把**内容**（不是外层目录）复制到编辑器安装根，与 `version.txt` 同级。
2. `global/AGENTS.md` 复制到用户级指令位置（如 `~/.zcode/AGENTS.md`）；若客户端用 `CLAUDE.md` 加载，另建一份内容为 `@AGENTS.md` 的指针文件。已有全局指令时合并，不要覆盖。
3. 用你的工程替换 `ShadowTrackerExtra/UGCProjects/Withdraw/` 示例：可只保留 `AGENTS.md`、`.emmyrc.json`、`Script/luahelper.json`、`workspace.code-workspace`，按你的工程改路径；示例文档可留作参考。
4. 从编辑器根运行所有命令；不要改 `Engine/`、`Content/Paks/`、`Binaries/` 和包内资产。

### 1.4 跑一次完整工作流

前提是拿到腾讯文档链接。在对话里直接给链接，skill 会按 Phase A/B/C 推进，之后文档变更走变更同步；每一步都在文件状态上留痕。工作流如下：

| 阶段 | 产出 | Gate |
|---|---|---|
| **Phase A 需求理解** | `spec/<模块>/01-understand.md`；`06-sync.md` 初始功能点表；在 `spec/INDEX.md` 登记一行 | **决策 gate**：人确认理解与范围 |
| **Phase B 方案** | `02-context.md`（现状事实，不 gate）；`03-plan.md`（L0/L1 任务、每任务带 `来源: fp-xxx`，人工前置项标 `前置: 人工`） | **决策 gate**：人确认方案与任务 |
| **Phase C 实现** | 每个任务写 `04-impl/NN-*.md`，附改动与验证证据 | L0 可批量；**L1 每个任务一个验收 gate** |
| **变更同步** | 策划改文档时按 C0/C1/C2 处理；已实现功能变更新开 `T03-R1` | C2 强制 gate |

需求里涉及的新 UMG、配置表/字段、场景摆放，在 Phase A/B 就要标成人工前置；人没准备好之前，任务停在前置，不进入 Phase C。

重要约定：

- Agent 产出后写 `状态: 待确认` 并停下；人改成 `已确认` 后下一轮才继续。Agent 不自己验收自己。
- 腾讯文档原文只进系统临时目录，`spec/` 只留功能点指纹、关键截图和实现记录；临时目录在 Phase A 结束后删除。
- 判断依据是文件，不是对话：任务状态、gate 结论、验证输出都要落到 `spec/<模块>/`。

## 2. 怎么靠文档自动推进

文档不是背景材料，而是自动化的输入和状态机：

1. **`AGENTS.md` 链** → Agent 进入目录先读最近的一份，拿到「什么能改、去哪查、怎么验证」。
2. **`Docs/`** → 具体事实（网络、运行期规则、性能、API、调试）；AGENTS 只做索引，不重复内容。
3. **`.claude/skills/oasis-design-doc-decompose/`** → 把腾讯文档拆成带 gate、带指纹、带来源链接的任务。
4. **`spec/<模块>/`** → 任务状态与实现证据；下一轮会话从这里继续，不靠记忆。
5. **`spec/INDEX.md`** → 文档 token → spec 目录；下次改同一份文档时先查这里，命中就走增量。

## 3. 自动验证与验收

所有命令从编辑器根运行；`<工程>` 替换成你的工程目录名。

### 3.1 每次改动都要跑的检查

```bash
# spec 结构、任务来源、FP 交叉引用；gate 前必跑
python -I spec/tools/spec_check.py

# API 签名/参数个数/scope/废弃（需要 ApiMetadataCache.json）
python -I spec/tools/api_contract.py --project "ShadowTrackerExtra/UGCProjects/<工程>/Script" --out spec/api-contracts

# UI 控件名契约；新增/修改 UMG 后先 index，再 check
python -I spec/tools/ui_contract.py index \
  --project "ShadowTrackerExtra/UGCProjects/<工程>/Script" <工程> \
  --store "ShadowTrackerExtra/UGCStoreAssets" Store \
  --out spec/ui-contracts
python -I spec/tools/ui_contract.py check \
  --project "ShadowTrackerExtra/UGCProjects/<工程>/Script" <工程> \
  --store "ShadowTrackerExtra/UGCStoreAssets" Store \
  --out spec/ui-contracts

# 场景 Actor 契约；人改过地图摆放后先 index，再 check（参数相同，只换子命令）
python -I spec/tools/scene_contract.py check \
  --project "ShadowTrackerExtra/UGCProjects/<工程>/Script" <工程> \
  --map-dir "ShadowTrackerExtra/UGCProjects/<工程>" \
  --asset-dir "ShadowTrackerExtra/UGCProjects/<工程>/Asset" \
  --out spec/scene-contracts
```

需要刷新契约库时，把对应的 `check` 换成 `index`。

检查只看**新增**问题：历史遗留用 `--write-baseline --yes` 固化一次（仅 UI/场景支持基线），之后只阻断新问题。UI 的“资产中缺失”只报告不阻断；API 的参数不足/废弃/scope 默认只是警告，加 `--strict` 才升级为错误。

### 3.2 运行期验证（PIE + AutoTestKit）

```bash
python -I spec/tools/pie_runner.py run --no-tests          # 冒烟：启动、截图、停止
python -I spec/tools/pie_runner.py run --suite <Suite>     # 跑指定测试套件
python -I spec/tools/pie_runner.py run --resume --suite <Suite>  # 人脸识别/对话框处理后继续
python -I spec/tools/pie_runner.py status
```

| 退出码 | 含义 |
|---|---|
| 0 | 启动/停止成功；测试通过，或无测试的 `smoke_passed` |
| 1 | 运行时错误 |
| 2 | MCP 不可用（编辑器未启动、端口不一致、Server Stopped） |
| 3 | 人脸识别或阻塞对话框，处理后 `run --resume` |
| 4 | 测试不通过，或启停期间日志命中阻断错误 |
| 5 | 启动/等待超时 |

产物在 `spec/pie-runs/<时间戳>/`：`report.json`、`screenshot.png`、阻塞时的 `blocked.png`。`report.json` 里有测试摘要、日志扫描、退出依据。

### 3.3 验收标准

一个任务可以进入 `已完成`，至少要同时满足：

| 层 | 通过标准 |
|---|---|
| 结构 | `spec_check.py` 退出码 0；任务有 `来源: fp-xxx`，状态为 `已确认` |
| 静态 | 用编辑器自带 `luacheck.exe` 检查，记录 `allErrNum=0`；输出存 `spec/<模块>/logs/` |
| 契约 | UI/场景无**新增**问题；API 无错误（警告逐条判断） |
| 运行期 | `pie_runner.py` 退出码 0，测试全过，日志无运行期 Lua 错误 |
| 证据 | `04-impl/NN-*.md` 写明命令、输出路径、截图/日志位置；人看到后才改 `已完成` |

## 4. 模板包含什么

```text
AGENTS.md                         编辑器总入口
global/AGENTS.md                  用户级全局偏好
.claude/skills/...                腾讯文档需求拆解工作流
spec/INDEX.md                     文档注册表
spec/tools/                       5 个检查/自动化工具 + README
Docs/                             安装、启动、更新
ShadowTrackerExtra/
├── AGENTS.md                     模块边界
├── Content/.../AGENTS.md、Docs/  API 类型库与专题文档
├── Plugins/.../AGENTS.md、Docs/  编辑器/MCP/DSL 文档与技能
└── UGCProjects/
    ├── AGENTS.md                 工程规范
    ├── Docs/                     跨工程指南
    └── Withdraw/                 工程示例：AGENTS、模块 README、Lua/IDE 配置模板
```

以下内容**不在模板里**，需要你的安装或本地生成：编辑器二进制与 Paks、工程 `uasset`/`umap`/Lua 代码与资产、`LuaHelper/Source` 存根、第三方依赖；`spec` 下的契约库、检查报告和 PIE 运行记录由工具在本地生成。`Docs/` 里指向这些文件的相对链接需要在实际安装中存在。
