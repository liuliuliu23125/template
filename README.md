# Oasis UGC Agent 工作流模板

> 给「绿洲启元 UGC 编辑器」安装目录使用的 Agent 指令与工作流模板。
> 只包含 `AGENTS.md` 指令链、需求拆解 skill、spec 检查工具，不含编辑器二进制、打包资产和任何玩法工程内容。

## 这是什么

一套可以复制进任意绿洲启元编辑器安装目录的「Agent 协作骨架」：

- 每一级目录有一份 `AGENTS.md`，告诉 Agent 这个目录是什么、什么能改、下一步该读哪份文档。
- 一个需求拆解 skill，把腾讯文档拆成有 gate、有指纹、可追溯的 `spec/<模块>/` 任务。
- 一组离线检查工具，覆盖 UI 控件、场景 Actor、API 签名、spec 结构，以及 PIE 自动运行。

## 不是什么

- 不是编辑器安装包：`Engine/`、`Content/Paks/`、`Binaries/` 等一个都没有。
- 不是可运行工程：没有 `uasset` / `umap` / `navmesh`，`ShadowTrackerExtra/UGCProjects/Withdraw/` 只有一份 AGENTS 示例。
- 不是文档全集：AGENTS 里引用的 `Docs/*.md` 未随模板提供，需要从自己的安装补齐或另行维护。
- 不是生成物仓库：`spec/ui-contracts/`、`spec/scene-contracts/`、`spec/api-contracts/`、`spec/pie-runs/` 均由工具在本地生成，不入库。

## 设计思路

### 1. 指令分层，不重复事实

```text
全局偏好（~/.zcode/AGENTS.md 或等价的用户级文件）
  → 编辑器根 AGENTS.md          总入口：目录树、启动链路、硬约束、文档索引
    → 模块 AGENTS.md            只回答本模块「是什么、能不能改、去哪查」
      → 工程 / 插件 AGENTS.md   只写该工程/插件的分层与项目级约束
```

每层只做两件事：**索引入口**和**硬约束**。事实、参数、踩坑细节下沉到最近的 `Docs/` 或工具 README，避免同一事实在多份 AGENTS 里各说一遍、随后不同步。

### 2. 工作流与编辑器内容分离

`spec/` 放在编辑器根、不属于任何 UGC 工程：需求拆解、契约库、检查报告都在这里，工程更新不会清掉它。编辑器侧只保留 `AGENTS.md` 作为路标。

### 3. 只落指纹，不落原文

腾讯文档原文随时能重读且会变化，持久化它只会得到过期基线。模板的做法是：

- reader 输出（`document.md/txt`、原图）只进系统临时目录；
- `spec/<模块>/06-sync.md` 只存功能点指纹与哈希；
- 只有影响验收的关键视觉素材复制到 `spec/<模块>/assets/fp-xxx-*.png`。

### 4. 可验证优先于口头约定

能机器判定的规则都配了脚本；脚本只阻断**新增**问题，历史遗留进基线，避免一上来就红灯导致没人看：

| 工具 | 回答的问题 | 阻断条件 |
|---|---|---|
| `spec/tools/spec_check.py` | spec 目录结构、任务来源、FP 交叉引用是否完整 | 结构错误 |
| `spec/tools/ui_contract.py` | 代码是否引用了未声明的控件；声明控件是否在资产里 | 新增未声明引用 |
| `spec/tools/scene_contract.py` | `LoadClass` 引用与 Tag 字面量是否存在；Actor 摆放层 | 新增问题 |
| `spec/tools/api_contract.py` | API 是否存在、参数个数、scope、废弃映射 | 未知 API / 参数过多 |
| `spec/tools/pie_runner.py` | 能否自动启停 PIE、跑 AutoTestKit、抓日志/截图 | 测试失败或运行期 Lua 错误 |

### 5. 模板只保留结构

所有 `AGENTS.md` 保持与编辑器一致的相对路径。目录本身（`Engine/`、`ShadowTrackerExtra/` 等）由你的安装提供；本仓库只提供挂在对应位置上的说明文件。因此克隆后把内容覆盖到编辑器根即可，不需要改路径。

### 6. 需求拆解用 gate 控风险，而不是均匀确认

skill 按「返工代价」排序风险：**需求理解错 > 方案选错 > 实现质量差**。因此只在两处设重 gate（`01-understand.md`、`03-plan.md`），L0 机械任务不打扰人，L1 判断型任务逐个验收；文档变更按 C0/C1/C2 分级，已经实现的功能变更必须新开 `T03-R1` 修订任务，不改历史任务。

## 目录说明

### 工作流核心（缺一不可）

| 路径 | 作用 |
|---|---|
| `AGENTS.md` | 编辑器总入口：目录树、启动链路、硬约束、文档索引、快速定位 |
| `global/AGENTS.md` | 用户级全局偏好（中文交流、代码不写注释、文档维护、角色与执行方式）。复制到 `~/.zcode/AGENTS.md` 或客户端对应的全局指令位置 |
| `.claude/skills/oasis-design-doc-decompose/` | 腾讯文档 → 分步任务的完整 skill：Phase A 理解、Phase B 方案、Phase C 实现、C2 变更同步、gate 规则、读取脚本 |
| `spec/INDEX.md` | 文档注册表模板：腾讯文档链接 → spec 目录 → 进度。首次拆解必须登记，否则变更同步查不到 |
| `spec/tools/` | 5 个检查/自动化工具及各自 README（见上表） |

### 域边界（只放 AGENTS.md，不放内容）

| 路径 | 说明 |
|---|---|
| `ShadowTrackerExtra/AGENTS.md` | 游戏模块总览：哪些目录可改、日志与缓存位置 |
| `ShadowTrackerExtra/Content/AGENTS.md`、`Content/LuaHelper/AGENTS.md`、`Content/LuaHelper/Source/AGENTS.md` | 类型存根库的定位与只读约束 |
| `ShadowTrackerExtra/Plugins/AGENTS.md`、`Plugins/UGCEditor/AGENTS.md`、`Plugins/UniExtend/AGENTS.md` | 编辑器插件能力边界：MCP、Python 工具集、Lua 调试、DSL |
| `ShadowTrackerExtra/UGCProjects/AGENTS.md` | 工程选择、目录规范、交付物所有权、UI/场景契约用法 |
| `ShadowTrackerExtra/UGCProjects/Withdraw/AGENTS.md` | 一个完整工程的 AGENTS 示例：分层、初始化顺序、生成物、硬约束。替换成你自己的工程即可 |
| `Engine/`、`TCLS/`、`WeGameLauncher/`、`rail_files/`、`tiny_cache/`、`安卓/`、`FeaturePacks/` | 只读/发布侧目录的边界说明，防止 Agent 误写 |

### 未包含、需要自行补齐

- `Docs/*.md`：`AGENTS.md` 中引用的项目文档，如 `UGCProjects/Docs/runtime-rules.md`、`Content/LuaHelper/Docs/api-index.md`。模板保留链接，内容由你的安装/团队维护。
- 任何 `uasset` / `umap` / `pak` / 可执行文件。
- 工具生成物：`spec/ui-contracts/`、`spec/scene-contracts/`、`spec/api-contracts/`、`spec/pie-runs/`、`spec/CHECK-REPORT.md`。

## 使用方式

1. 把仓库内容复制到编辑器安装根目录（该目录应包含 `version.txt` 与 `ShadowTrackerExtra/`）。
2. 把 `global/AGENTS.md` 放到用户级指令位置；若客户端用 `CLAUDE.md` 加载，可另建一份内容为 `@AGENTS.md` 的指针文件。
3. 用你的工程替换 `ShadowTrackerExtra/UGCProjects/Withdraw/AGENTS.md` 示例，或保留为参考。
4. 首次拆解腾讯文档时，在 `spec/INDEX.md` 登记一行，再按 skill 的 Phase A/B/C 推进。
5. 每批改动后按需运行 `spec/tools/` 下对应检查；UI/场景检查首次接入某个工程时，用 `--write-baseline --yes` 固化历史问题。

### 工具前置

| 工具 | 前置 |
|---|---|
| `spec_check.py` | 无，纯 Python |
| `ui_contract.py` | 目标工程 `Script/` 与 `Asset/`（可自动推导） |
| `scene_contract.py` | 目标工程 `Script/`、`Asset/`、`.umap` 所在目录 |
| `api_contract.py` | 编辑器生成的 `Saved/UGCResourceDaemon/ApiMetadataCache.json` |
| `pie_runner.py` | 编辑器已启动、MCP Server 运行（端口读 `UGCSettings.ini` 的 `[AskQMCPServer]`）；首次 PIE 可能需人工人脸识别 |
| skill 的 reader 脚本 | Python 3 + Playwright + 系统 Chrome，按 `scripts/requirements.txt` 安装 |

所有 Python 脚本建议用 `python -I` 运行，避免当前目录的 `json.py` 之类文件劫持导入。

## 维护约定

- 改功能 = 改文档：同步离被改文件最近的 `AGENTS.md`；细节写 `Docs/`，工具用法写 `spec/tools/*-README.md`。
- 同一事实只存一份，其余位置用相对路径链接。
- 新增目录需要 Agent 认知时，在该目录放 `AGENTS.md`，并挂到上一级的索引里。
- 不把生成物、运行日志、个人路径写进模板；本仓库公开前已移除本机用户名路径。

## 最小目录树

```text
.
├── AGENTS.md
├── README.md
├── global/AGENTS.md
├── .claude/skills/oasis-design-doc-decompose/
├── spec/INDEX.md
├── spec/tools/
├── Engine/AGENTS.md
├── FeaturePacks/AGENTS.md
├── TCLS/AGENTS.md
├── WeGameLauncher/AGENTS.md
├── rail_files/AGENTS.md
├── tiny_cache/AGENTS.md
├── 安卓/AGENTS.md
└── ShadowTrackerExtra/
    ├── AGENTS.md
    ├── Content/AGENTS.md
    ├── Content/LuaHelper/AGENTS.md
    ├── Content/LuaHelper/Source/AGENTS.md
    ├── Plugins/AGENTS.md
    ├── Plugins/UGCEditor/AGENTS.md
    ├── Plugins/UniExtend/AGENTS.md
    └── UGCProjects/
        ├── AGENTS.md
        └── Withdraw/AGENTS.md
```
