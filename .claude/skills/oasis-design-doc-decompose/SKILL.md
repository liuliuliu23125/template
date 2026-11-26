---
name: oasis-design-doc-decompose
description: 把策划写的系统向需求文档（腾讯文档 docs.qq.com）拆解成绿洲启元 UGC 工程可执行的分步任务清单。Use when 用户给出腾讯文档链接，要求「拆解需求」「列任务」「出实现步骤」，或要求按现有工程惯例实现某个系统模块。触发硬前提：必须给出腾讯文档链接；没有链接一律不启动，先索要链接。模块名从文档标题自动取；目标 UGC 工程必须明确（用户指定，未指定时 Phase A 末尾确认一次）。QA 用例不在本流程内。Do not use for 纯代码 bug 修复、单文件小改动、或非本项目的文档整理。
agent_created: true
---

# 绿洲启元需求文档拆解工作流

> 只适用于 `rail_apps/OasisEraEditor(2001776)`。路径均以编辑器根目录（含 `version.txt` 与 `ShadowTrackerExtra/`）为基准；内容硬编码了本项目的工程结构、验证命令与运行期规则，上提全局没有意义。
> 编辑器根 `AGENTS.md` 有一行指向本文件，保证 skill 自动发现失效时也能被读到。

## 工程目录约定

| 名称 | 路径 | 说明 |
|---|---|---|
| `<EDITOR_ROOT>` | 当前安装根 | 含 `version.txt`、`ShadowTrackerExtra/`、`ShadowTrackerExtraUGCEditor.exe` |
| `<PROJECT>` | `<EDITOR_ROOT>/ShadowTrackerExtra/UGCProjects/<工程名>` | 业务代码唯一落点 |
| 业务代码 | `<PROJECT>/Script/` | 只改这里；`Content/LuaHelper/` 是只读类型库 |
| spec | `<EDITOR_ROOT>/spec/` | 拆解产物；不放进任何 UGC 工程 |
| 日志 | `<EDITOR_ROOT>/ShadowTrackerExtra/Saved/Logs/` | 主日志 + `<工程名>/Clientlog/LuaLog`、`DSlog/FullLog` |
| 静态检查 | `<EDITOR_ROOT>/ShadowTrackerExtra/Plugins/UGCEditor/Resources/LuaCheck/x64/luacheck.exe` | 工程侧配置 `ShadowTrackerExtra/SpeedupSync/luacheck/check.json` |

`<PROJECT>` 由用户指定。未指定时 Phase A 先做理解，在 `01-understand.md` 标「目标工程：待确认」，Phase B 前必须确认一次。不要默认 Withdraw，也不要直接改 `Template_*`（模板只读参考）。

## 0. 第一性原理（改动前先读）

**风险按代价排序**：需求理解错（发现最晚、返工最贵）> 方案选错 > 实现质量差。
→ **gate 要对准风险密度，不是均匀分布。** 需求理解那一两百字是性价比最高的 gate；「现状调研对不对」是事实问题，机器可校验，不值得占人的注意力。

**落盘判据**：只持久化「重新获取成本高」或「需要人写入」的东西。

| 内容 | 落盘？ | 原因 |
| --- | --- | --- |
| 腾讯文档原文 | **不落** | 浏览器随时能开，且文档是活的会过期；未登录时内容还可能不完整，落下来反而变成假基线 |
| 需求指纹 | 落 | 重建要通读一遍文档 |
| 关键视觉素材 | 落 | 界面验收基准 + 画板变更基线（见 `references/visual-assets.md` §4） |
| 现状调研结论 | 落 | 重建要读几百个 Lua / 资产 |
| 决策 + 任务清单 | 落 | 人要确认 |
| 任务状态 | 落 | 人要打勾，是 gate 载体 |
| 变更日志 | 落 | 过了就不可重建 |
| 实现记录 + 证据 | 落 | 人要验收 |
| QA 用例 | 不落 | **不属本流程**；需要时另起独立动作 |

**落指纹，不落原文**：检测「策划改了什么」必须有基线，但基线只需几十行功能点列表，不是几千行全文。

**注意力是稀缺资源**：一个模块 10-20 个任务，全 gate 会让人在第 5 个开始无脑通过，gate 就失效了 → 任务分级（§4）。

---

## 1. 对全局用户级 `AGENTS.md` 的例外（Override）

全局用户级指令文件（如用户主目录下的 `.zcode/AGENTS.md`）仍全局生效，以下**仅在本 skill 执行期间**不适用：

| 被覆盖条款 | 原因 |
| --- | --- |
| 「不主动新建 README / 设计文档」 | 本 skill 的交付物就是 `spec/` 下的 md，属用户显式要求 |
| 「任务跟踪文件写入 `tasks/todo.md`」 | `spec/<模块>/03-plan.md` 就是计划载体，另建 todo 会变成两份对不上的计划 |
| 「Spec 完整生成后 gate 一次」 | 改为「理解 → 方案」两次决策 gate + L1 任务级验收 gate，粒度更细 |
| 「Spec 分段确认：现状 → 功能点 → 风险决策，每段等确认」 | 现状段（`02-context.md`）**不 gate**——事实问题机器可校验，占人的注意力不划算。顺序改为「理解需求（gate）→ 查现状（不 gate）→ 决策（gate）」 |

**不覆盖的**：自研代码零注释照常执行。非显然的「为什么」写进 `03-plan.md` 或最近的 `AGENTS.md`/`Docs/`，不写进代码；机械注释一律不写。**例外**：蓝图绑定文件的 `---@class`、`---@field`、`--Edit Below--` 等编辑器生成标记必须原样保留；已有文件里的历史注释不主动删，只保证新写代码无注释。

### Spec 三铁律如何落到本 skill

| 铁律 | 落点 |
| --- | --- |
| **No Spec, No Code** | Spec = `01-understand.md` + `03-plan.md`。两者过 gate 前，Phase C 不动代码 |
| **Spec is Truth** | 代码与 `03-plan.md` 冲突时改代码。要改计划走 §6 变更流程，不许悄悄改 |
| **Reverse Sync** | 见下方分流 |

**Reverse Sync 分流**——「偏差」有两种，处理相反，混了会出事：

| 偏差来源 | 判定 | 处理 |
| --- | --- | --- |
| **实现偏差**：计划写错、API 不存在、方案行不通 | 与原文无关 | agent 自主改 `03-plan.md` 再改代码，在 `04-impl/NN` 记一行偏差说明 |
| **需求变更**：策划改了原文 | 与原文相关 | 走 §6 的 C2，**不动代码**，出报告等 gate |

**分类判据**：改动是否触及 `01-understand.md` 的功能点清单——**触及 = 需求变更，走 C2**；不触及才是实现偏差。分类结论 + 证据写进 `04-impl/NN`（「原计划 X 行不通，因为 Y 文件 Z 行」），不许口头一说就过。

口诀：**改的是「我们怎么做」→ 自主修；改的是「做成什么」→ 等人拍板。**

**严格执行、不覆盖**：Research 必须有出处（文件路径 + 模块.函数名）、执行自由度曲线、Verification 铁律（要证据不要"应该没问题"）、Simplicity First、Minimal Impact。

---

## 2. 工作目录

```
<EDITOR_ROOT>/spec/
  INDEX.md              # 文档注册表：腾讯文档地址 → 定位已有 spec
  <模块名>/             # = 文档标题，首次建目录时定名，之后不随标题改
    01-understand.md    # 需求理解复述 + 文档歧义清单      [决策 gate]
    02-context.md       # 现状依据：事实 + 出处（不 gate，供人查证）
    03-plan.md          # 决策 + 任务清单（含 L0/L1 分级）  [决策 gate]
    04-impl/NN-<名>.md  # 实现记录 + 验证证据
    05-qa.md            # 预留；QA 不属本流程，本 skill 不生成、不 gate
    06-sync.md          # 功能点 KV + 变更日志             [C2 变更时 gate]
    assets/             # 关键视觉素材（画板/截图），验收与变更基线
    logs\               # luacheck 输出、PIE 日志摘录
```

`spec/` 在编辑器根、不在任何 UGC 工程内，也不随工程分支切换而丢失。它被 `.gitignore` 默认忽略；确需留档或更新已跟踪的契约库时，用 `git add -f`。

**位置是更新安全的**：`rail_files/rail_game_build_info.dat` 的 `clean_paths` 会清理 `ShadowTrackerExtra/Content` 和多个 `Template_*`，但不含根目录的 `spec/`、`.claude/`。不要把拆解产物放进 `Content/` 或 `Template_*`——更新会直接清掉。

**只落指纹**：reader 的 `document.md/txt` 和原始图片放系统临时目录（如 `%TEMP%/oasis-doc-reader/<token>`）；Phase A 只把功能点/指纹写进 `01-understand.md`/`06-sync.md`，关键视觉素材复制到 `assets/fp-xxx-*.png`，随后删除临时目录。`meta.json` 的哈希/字数只用于证明读取完整，不进 `spec/`。

---

## 3. Gate 机制

**Gate = agent 停下、等人改状态位、下一轮才继续。** 无论执行层是否真的拦截命令，gate 都必须落在文件状态上。

| 类型 | 触发 | 人做什么 | 次数 |
| --- | --- | --- | --- |
| **决策 gate**（重） | `01-understand.md`、`03-plan.md` 产出后 | 判断方向对不对 | 2 次/需求 |
| **验收 gate**（轻） | 每个 **L1** 任务完成 | 看改动清单 + 证据 | 只数 L1，通常 4-8 次 |
| **自检 gate**（不打断） | 每个任务内部，agent 自己跑 luacheck / 契约检查 / 日志检查 | —— | 每任务 1 次 |

每个需要 gate 的文件末尾固定：

```markdown
## 验收
- 状态: 待确认
- 改动文件: 3 个，+120 / -8
- 验证证据: 见 spec/<模块>/logs/luacheck-03.txt，allErrNum=0；PIE 日志无 LuaException
```

**结构自检**：gate 前运行 `python -I spec/tools/spec_check.py`。它只校验 `INDEX.md`、`01/03/06`、`04-impl` 的结构与交叉引用，不替代内容 gate；结构错误不能算过 gate。

agent 规则：

1. 产出 → 写 `状态: 待确认` → **立即停止**，输出「已完成 XX，请验收」。**一轮只推进到下一个 gate**——同轮内还有余力也不许继续，这是硬约束不是建议。
2. 下一轮先读 `03-plan.md`，找第一个 `待确认`/`未开始` 的任务。
3. 读到未确认的前置 → **停止并提示**，不要自作主张往下推。
4. L1 一轮一个；L0 可一批连续做，做完一起报。
5. 人改成 `状态: 已确认 by <人> @ <日期>` 后，下一轮才继续。

---

## 4. 任务分级（可持续的关键）

在 `03-plan.md` 阶段就标级，**人在这个 gate 里同时决定「哪些任务要盯」**。

| 级别 | 判据 | gate |
| --- | --- | --- |
| **L0 机械型** | 有明确参照物；改动 < 100 行；不动框架基类、公共注册与生命周期入口；只有一条明显正确的实现路径 | **不 gate**，批量做 |
| **L1 判断型** | 新业务逻辑、新/改网络消息或属性复制、动框架基类/生命周期、有多条路径要选、有性能或兼容风险 | **每个一个验收 gate** |

标不出 L0/L1 的，按 L1 处理。

---

## 5. 阶段流程

### 复杂度分档（继承全局「按需复杂度」）

| 档 | 判据 | 压缩什么 |
| --- | --- | --- |
| **S 轻量** | 功能点 ≤ 4，且不新增 DataTable/DA/配置、不改网络消息、不跨模块 | `02-context.md` 按需写、任务可合并到 3-5 个 |
| **F 完整** | 其余（含任一 L1 特征） | 四阶段全走 |

两档都**必须建 `06-sync.md` KV**——下次再来的定位全靠它，省了会重拆。细节见 `references/granularity.md` §1。分档在 Phase A 结束时定，写进 `01-understand.md`。

### Phase A — 需求理解 → `01-understand.md`

**硬前提：必须有腾讯文档链接。** 没有链接就回「需要腾讯文档链接才能开始拆解」并停止，禁止翻工程目录同名文档替代、禁止先拆一部分等链接再补。

优先用已登录浏览器打开腾讯文档直接阅读；没有浏览器时按下方「读取手段」降级。**先取标题定模块名**（规则见 §7），再产出五块，**第四块最有价值**：

1. **一句话目标**
2. **功能点清单**：每条对应文档一处，**且必须覆盖视觉素材**（画板 / 截图 / 表格）。腾讯文档的关键信息常常不在文字里，只读文字拆等于默认画板不存在。分类提取与截图方法见 `references/visual-assets.md`
3. **明确不含什么** —— 防范围蔓延，也防 agent 自作主张加戏
4. **文档歧义 / 缺失清单** —— 策划没写清、前后矛盾、压根没提的地方。**人最容易忽略**，列出来 gate 时一并问掉
5. **需求指纹**：把功能点写成 `06-sync.md` 的初始表，记下文档链接和读取时间；同时在 `spec/INDEX.md` 登记一行（链接为主键、spec 目录、进度）。两者是后续变更同步的定位依据，缺一则 §6 查不到该模块

同时记录：模块名、**目标 UGC 工程（待确认则显式标注）**、复杂度档 S/F。

**当前环境可用的读取手段（按优先级）**：

1. **Playwright 读取脚本（首选）**：`python .claude/skills/oasis-design-doc-decompose/scripts/read_tencent_doc.py <url> --out <临时目录>`。用系统 Chrome 全选复制，直接取剪贴板全文，并从复制 HTML 中提取图片和表格，输出 `document.md`、`document.txt`、`images/`、`meta.json`（标题/字数/大纲/图片数/表格数/content_sha256）。**文字读文本，图片读原图，默认不截图；`--out` 必须是系统临时目录，不能是 `spec/`。**
2. **私有/受限文档**：同一脚本加 `--login`，打开 Chrome 登录一次；profile 默认在 `%LOCALAPPDATA%\TencentDocReader\profile`，后续无头运行复用。
3. **截图兜底**：复制被禁用、剪贴板为空或需要看排版时，用 `--mode screenshot`；输出 `page-NNN.png`，由视觉模型读图。只在文本路径失败时使用。
4. **WebFetch**：快速拿标题和判断登录墙；腾讯文档常只返回首屏，不能当全文。
5. **curl 抓 HTML + 解析 SSR `<text>` 节点**：公共预览页的部分正文，只用于兜底。
6. **用户导出/粘贴**：登录墙后或脚本失败时的兜底。

首次使用若缺依赖：`pip install -r .claude/skills/oasis-design-doc-decompose/scripts/requirements.txt`；无系统 Chrome 时再跑 `python -m playwright install chromium`。

脚本目前针对 `/doc/` 文档；`/sheet/`、`/slide/` 的 DOM 不同，需要另适配，不要假装读全。

当前环境没有浏览器文本/图片读取能力时，视觉素材必须由用户提供；拿不到就按下面的规则报告，不得用文字猜测界面。

**读取能力缺失必须报告**：

- 未登录腾讯文档时页面会出现「登录腾讯文档」「只能查看」「正在同步内容...」等提示。此时读到的只是部分内容，**不得当作完整文档拆解**；要么加 `--login` 重读，要么请用户导出/粘贴全文。
- 读取脚本失败（复制被禁用、登录墙、非 `/doc/` 链接、找不到滚动容器）时，记录失败原因和已读范围；可回退 `--mode screenshot`，仍失败就请用户导出/粘贴。
- 图片提取失败或未读取视觉素材时，在 `01-understand.md` 写明「本轮未读取视觉素材，功能点仅基于文字」，并列出哪些素材没读到。**禁止假装读过。**

→ **决策 gate**。

### Phase B — 方案 → `02-context.md` + `03-plan.md`

**先读，再查。不要凭空调研。**

`02-context.md`（事实库，不 gate，供人查证）：

1. **走 AGENTS.md 链**：从 `<EDITOR_ROOT>/AGENTS.md` 起 → `ShadowTrackerExtra/AGENTS.md` → `UGCProjects/AGENTS.md` → 目标工程 AGENTS.md（如 `Withdraw/AGENTS.md`）→ `Content/LuaHelper/AGENTS.md` 及对应领域文档。框架约定已写好，直接继承
2. **用代码核实**：AGENTS.md 是索引不是事实。按它指出的模块/API 读真实 Lua 与 `LuaHelper` 存根确认仍成立，每条写 `文件路径 + 模块.函数名`。API 必须核对 `---生效范围：服务器 / 客户端 / 服务器&客户端` 和废弃映射
3. **找一个参照物**：挑最接近的现成系统，写完整调用链——入口绑定（`Script/Blueprint/UGCGameMode.lua` / `UGCPlayerController.lua` 等）→ `require` → 注册/生命周期 → 数据绑定 → 打开/关闭 → 回收。UI 按目标工程门面：Withdraw 走 `Global_UISystem`（底层 `UGCUIManagerSystem`），不要直接 `AddToViewport`。新功能照抄这套
4. **核对"已提供的资产"**：去工程里**真的找到**（`.uasset` 是二进制，用编辑器 Content Browser / 资产清单确认），列路径、蓝图/UMG 挂载、命名。资产路径用工程相对路径并走 `UGCGameSystem.GetUGCResourcesFullPath`，不要写绝对路径或 `/Game/`。找不到当场报缺，不要假设存在；无法检查内部结构时明确写「未核实」
5. **核对官方功能是否已启用**：涉及物品/技能/背包/商城/任务等，先查 `Docs/gamepart.md`；GamePart 在 `DA_GameModeGeneral` 启用，运行时用 `IsGamePartLoaded` / `GetAllLoadedGameParts` 确认，不能从 `.ugcproj` 判断。GamePart 异步加载，`ReceiveBeginPlay` 时可能未完成，需监听加载完成或延迟

`03-plan.md`（决策，要 gate）：

6. **工程形态决策**：新建工程 / 并入现有工程的多模式（`[MultiModeSetting_N]`）/ 扩展现有模式，三选一 + 理由。一个工程一个入口，不复制多套 `Script/`；`Template_*` 只读，且多数在更新 `clean_paths` 里
7. **配置决策**（必须死结论，不准"可能需要"）：复用现有 DataTable/DA/Lua Config / 扩表 / 新建，三选一 + 一句理由。写明路径、主键、字段、导表来源（编辑器导入 / 维护者 CSV）、谁读。**生成物（注册表/常量/索引）不手改**；重生成标为人工/工具链依赖
8. **网络决策**：复用还是新增，明确 `UGCGenericMessageSystem` 远程消息 / `UGCAttributeSystem` 属性复制 / 工程内事件总线 三者的选择；列消息名、字段、权威端、失败与错误提示怎么落地。工程内部事件不能替代跨端同步
9. **风险点**：运行期硬规则（封禁 API、UObject 有效性、容器 1 基、C++ 默认参数、Shipping `totable`、重连丢 RPC、`IsServer` 依赖 GameState 初始化、客户端拿不到全量 PlayerState）、目标工程硬规则（UI 门面、事件总线、玩家数据存储、分层单向依赖，如 Withdraw 的 `Global_UISystem`/`UGCEventSystem`/`PlayerDataCore`）、`require` 与 `UGCRequire` 的选择（要发布到资源商店的模块用后者）、性能预算、模板/扩展包不可改
10. **任务清单**：按 `references/granularity.md` 拆，标 L0/L1 + **五要素**（含 `来源: fp-xxx`，这是 §6 变更同步的枢纽）；验收方式要写明适用的 L2 检查（UI/场景/API/配置表）
11. **人工前置项**：新增/修改 UMG、DataTable/DA 的 RowStruct/列/行、场景 Actor 摆放、`.ugcproj` 配置，都由人在编辑器完成。任务清单里标 `前置: 人工`，未完成前保持 `未开始`，不得进入 Phase C；Agent 只写这些内容之下的 Lua 行为

调研若可并行，仅在 Phase B 分头扫（UI / 配置 / 网络 / 资产），之后全部串行。

→ **决策 gate**（一次，看 `03-plan.md`）。

### Phase C — 实现 → `04-impl/NN-*.md`

**每个 L1 任务开工前做一次原文变更检查**（§6）。发现 C2 立刻停下报给人，不要边改需求边写代码。

每份记录含：改动文件清单（路径 + 增删行数）；**验证证据**；偏离任务描述的地方——**有偏离先写下来等确认，不要自己改方案**（Reverse Sync）。

**自检 gate（静态检查，agent 可执行）**：

```bash
"<EDITOR_ROOT>/ShadowTrackerExtra/Plugins/UGCEditor/Resources/LuaCheck/x64/luacheck.exe" -cmd 0 \
  -config "<EDITOR_ROOT>/ShadowTrackerExtra/SpeedupSync/luacheck/check.json" \
  -inputDir "<EDITOR_ROOT>/ShadowTrackerExtra/UGCProjects/<工程名>/Script" \
  -outputDir "<EDITOR_ROOT>/spec/<模块名>/logs/luacheck-NN.txt" \
  -logflag 0 -suffixCheck 0
```

- 退出码 0 且输出 `allErrNum=0` 为通过；退出码 1 为有错。
- 首次在目标工程跑先记基线：不属于本次改动的既有错误单独列出，不混入本次验收。
- 错误行形如 `[os.execute], <文件>, [Ln 3, Col 3]`，逐条修，不要带着错误交差。
- 该检查只覆盖封禁 API / 语法等静态项，**不能替代运行验证**。

**契约检查（L2，按改动类型追加）**：

| 改动类型 | 命令 | 通过标准 |
|---|---|---|
| UI / UMG | `python -I spec/tools/ui_contract.py check --project "ShadowTrackerExtra/UGCProjects/<工程名>/Script" <工程名> --store "ShadowTrackerExtra/UGCStoreAssets" Store --out spec/ui-contracts` | 无新增未声明控件引用；资产缺失逐条人工确认 |
| 场景 / 地图 | `python -I spec/tools/scene_contract.py check --project "ShadowTrackerExtra/UGCProjects/<工程名>/Script" <工程名> --map-dir "ShadowTrackerExtra/UGCProjects/<工程名>" --asset-dir "ShadowTrackerExtra/UGCProjects/<工程名>/Asset" --out spec/scene-contracts` | 无新增问题 |
| API 调用 | `python -I spec/tools/api_contract.py --project "ShadowTrackerExtra/UGCProjects/<工程名>/Script" --out spec/api-contracts` | 无错误；警告逐条判断 |
| 配置表 / DA | 无专用契约脚本：人工核对 RowStruct/列/行与 `GetTableData*` 调用（后者由 `api_contract.py` 覆盖签名），运行期用日志/读表验证 | 人工核对记录 + 运行证据 |
| spec 结构 | `python -I spec/tools/spec_check.py` | 退出码 0 |

- UI/场景首次接入某个工程时，先 `--write-baseline --yes` 固化历史问题，之后只阻断新增。
- 只改了 Lua 且不涉及 UI/场景/API 时，可只跑 `luacheck` + `spec_check`；改动了对应层就必须跑对应检查。
- 检查命令与参数说明见 `spec/tools/` 下各 README。

**运行验证（有证据才算完成）**：

- 在编辑器打开 `<PROJECT>/<工程名>.ugcproj` 跑 PIE，取 `Saved/Logs/<工程名>/Clientlog/LuaLog`、`DSlog/FullLog` 与主日志；确认无 `LuaException`，关键路径有预期日志。
- 日志函数按端选：`ugcprint` 在真机只进 DS 日志，客户端可见日志用 `print`；PIE 下两者都能看到。
- 若目标工程有 `Script/Core/AutoTestKit/` + `Script/Config/AutoTestSuite/`（如 Withdraw），跑相关 Suite 并记录结果。
- **agent 无法启动/操作编辑器时**，只能写「PIE 未执行，待人工验证」，不能声称完成；这是 L1 验收 gate 的阻塞项，不是免责声明。

代码规范按全局：**自研 Lua 零注释**；绑定文件的 `---@class`/`---@field`/`--Edit Below--` 原样保留，业务代码只写 `--Edit Below--` 之下，已有历史注释不主动删。非显然的「为什么」写进 `03-plan.md` 或最近 `AGENTS.md`/`Docs/`。

**功能改完 = 文档改完**：同步最近的 `AGENTS.md`（从被改文件目录向上找第一份），细节下沉 `Docs/`，不新建 README；新增文档按 `.gitignore` 规则 `git add -f <path>`。

→ L1 每任务一个 **验收 gate**；L0 批量报。

### 流程终点与边界（用例不在本流程内）

**本流程止于 Phase C。** 拆解与实现由本 skill 负责；测试用例是**独立动作**，需要时另起，不接在流程尾部、也不由本 skill gate。

**需求完成的判据**：所有 **L1 任务**的验收 gate 已确认、`luacheck` 证据齐全（`logs/luacheck-NN.txt` 无错误）、对应 L2 契约检查无新增问题（UI/场景/API）、运行证据或明确的人工验证记录齐全、`04-impl/` 记录完整。

---

## 6. 原文变更同步

策划会改文档，这是常态。**完整规则见 `references/change-sync.md`**，本节只列主干。

### 两层 KV

| 层 | 位置 | key | value |
| --- | --- | --- | --- |
| 文档注册表 | `spec/INDEX.md` | 腾讯文档 token（主键） | 模块名、spec 目录、同步时间、进度 |
| 功能点 KV | `<模块>/06-sync.md` | FP slug | 哈希 + 文档状态 + 实现状态 + 关联任务 |

功能点 KV 的**两侧状态分开记**：文档状态（策划改没改）/ 实现状态（我们做没做，agent 在任务过 gate 时更新）。

### 判定顺序

1. **先查 KV**：命中 = 同一个需求走增量对齐；未命中 = 新需求走完整流程。**有链接时不要多问**
2. **用户「特别明确」表态时优先于 KV**（「差不多吧」「应该是」不算）。冲突时**改 KV 不改用户**——KV 是记录，用户说的是事实

**哈希是快筛不是判决**：哈希相同 → 跳过该行详细比对；哈希不同 → 逐行做语义比对，判定「措辞变了 / 真的变了」并写明依据。**不许哈希一变就判 C2。** 摘要按 `实体 / 行为 / 数量 / 边界值` 的 schema 提炼，减少措辞噪声（详见 reference）。

**本节只管「原文变更」。** 实现层面的偏差（计划写错、方案行不通）走 Reverse Sync（§1），不进分级。

### 变更分级：看实现状态，不看改动大小

| 级 | 判定 | 处理 | gate |
| --- | --- | --- | --- |
| **C0** | 不影响代码行为（错字、排版、配图、润色） | 更新哈希 | 否 |
| **C1** | 只影响「未开始」的任务 | 改任务描述 | 否，下轮带一句 |
| **C2** | 影响「进行中 / 已实现」的任务 | **不动代码**，新增修订任务 | **是，强制** |

改动大但没开工 = C1（便宜）；改动小但代码已写完 = C2（贵）。

**哈希只覆盖文字**：画板 / 截图改了而文字没改时检测不到，用 `06-sync.md` 的素材列（视觉指纹）补，见 `references/visual-assets.md` §3。

C2 时 agent 给三个选项和成本：返工 / 保留现状（在 `03-plan.md` 标注已知偏差）/ 砍功能。

### 已实现的功能变了 → 新增修订任务

**禁止回头改原任务 T03，改开 `T03-R1`。** 理由：改原任务等于篡改历史；返工量变成可见的独立单元（= 需求变更的真实成本）；追溯链完整；和 git 追加语义一致。

实现状态为「未开始」的变更 → 直接改任务描述即可，没落地就没有历史要保留。

**任务必须标 `来源: fp-xxx`** —— 没有这条链接，比对出变更也不知道影响了谁，整个机制转不起来。

---

## 7. 调用方式

```markdown
拆解这份需求：https://docs.qq.com/doc/XXXX
```

**只给链接，就够了。** 模块名从文档标题自动取；目标工程未指定时 Phase A 末尾确认一次。

### 模块名 = 腾讯文档标题

浏览器打开文档后取标题（页面 `<title>`、文档首行 H1，或编辑器标题栏，去掉「 - 腾讯文档」这类后缀），清洗后作为模块名：

- 去掉 Windows 目录非法字符 `\ / : * ? " < > |` 和首尾空格
- 保留中文，不强行转拼音
- 超长截断到 30 字

**目录名一旦建好就不再改。** 策划改了标题时只更新 `INDEX.md` 的模块名列，spec 目录路径不动——定位始终靠链接 token，不靠名字。否则改名会导致「按标题找不到旧 spec」，然后又重拆一遍。

标题取不到（页面没加载完、登录失效）才向用户要模块名，这是唯一需要问的情况。

用户在 prompt 里显式给了模块名时，用用户给的——和 §6 一致，人的明确表态优先。

### 硬前提：必须有腾讯文档链接

没链接就不启动本流程，回一句「需要腾讯文档链接才能开始拆解」并停止，**然后等链接**。禁止：翻工程目录同名文档替代；先拆一部分等链接再补；拿 INDEX.md 里的名字硬匹配然后开工（猜错会静默跑偏，发现时任务已拆完）。

唯一例外：只给了模块名没给链接时，可提示「`INDEX.md` 里 XX 模块上次用的是 <地址>，是这份吗？」，得到明确肯定后才继续。这把「agent 猜测」变成「人确认」，成本一句话，防整轮返工。

反过来，**有链接时不要多问**：查 KV，命中就走增量对齐，别再追问「这是不是上次那个」。只有用户主动表态才覆盖 KV 结论（§6）。

---

## 8. 反面审查

方案 gate 前、或某轮拆解看着不对时，做一次**只读不改**的挑刺，逐条检查：

- 功能点是否覆盖了画板 / 截图 / 表格，还是只读了文字？
- 方案依据是真实 Lua / LuaHelper 签名，还是只抄了 AGENTS.md 的索引？
- 是否核对了 API 的生效范围与废弃映射？
- 每个任务能否独立验证，验收证据是否可复现？
- 是否触碰运行期硬规则、网络权威、性能预算或不可改目录？
- 输入输出（配置、消息、存档）在断线重连、缺配置、空数据时是否成立？

人说「审一下 / 挑刺 / 找问题」时触发。

---

## 9. 参考文件

| 文件 | 管什么 |
| --- | --- |
| `references/granularity.md` | 复杂度分档、配置决策树、任务颗粒度与五要素 |
| `references/visual-assets.md` | 腾讯文档视觉素材提取与截图、画板变更检测（`06-sync.md` 的视觉指纹） |
| `references/change-sync.md` | 原文变更的三种冲突情形、哈希比对细则、C0/C1/C2 处理 |
| `scripts/read_tencent_doc.py` | 腾讯文档 `/doc/` 全文读取（剪贴板文本 + 图片/表格提取；截图兜底；`--login` 支持私有文档） |
