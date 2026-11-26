# UGCProjects AGENTS

所有可编辑玩法工程的根目录。日常开发只在这里写 Lua 和资产。两类工程：

- `Withdraw/`：已开发的完整撤离类项目（基地 + 4 张地图，共 5 个模式）。
- `Template_*`：官方模板，作为参考实现与新建工程的起点。

## 工程结构（标准）

```text
<Project>/
├── <Project>.ugcproj              工程配置（唯一入口，编辑器读写）
├── Script/                        业务 Lua（真正运行的代码）
│   ├── Blueprint/                 与蓝图同名的绑定脚本（--Edit Below--）
│   ├── gamemode/                  触发器 Action/Condition 脚本
│   ├── Common/                    枚举/结构补全
│   ├── GameAttribute/             属性类型
│   └── ...                        分层目录（见下）
├── Asset/                         可编辑 uasset：Blueprint、UI、Data、Material、Particles…
├── ExtendResource/                官方扩展包（Withdraw 有；模板通常没有）
│   └── <Package>/OfficialPackage/{Script,Asset}
├── Navmesh/                       导航数据
├── *.umap / *.uasset              地图与资产
├── Thumbnail.png                  工程缩略图
├── WhiteList.ini                  资源白名单
├── DeleteFiles.txt                删除清单（生成）
├── ReferenceAssetList.txt         引用资产清单（生成）
├── UGCLuaBindFiles.txt            Lua 绑定/上传清单（生成）
├── luahelper.json                 LuaHelper/EmmyLua 补全配置
├── .emmyrc.json                   EmmyLua 诊断配置（部分工程）
└── workspace.code-workspace       VSCode 工作区（指向 LuaHelper）
```

## `.ugcproj` 关键字段

| 字段 | 含义 |
|---|---|
| `ProjectName` / `ProjectDisplayName` | 工程名 |
| `StartMapName` | 启动地图，如 `/Withdraw/UGCmap` |
| `GameModePath` | 默认 GameMode 蓝图类，如 `/Withdraw/Asset/Blueprint/UGCGameMode.UGCGameMode_C` |
| `bIsBigWorld` | 是否大世界 |
| `Version` / `UpdateVersion` | 工程版本 |
| `[FeatureFlags]` | 物品/技能/粒子编辑器 V1/V2 开关 |
| `[MatchSetting]` / `[MultiModeSetting_N]` | 匹配、队伍、聊天、多模式 |
| `[JobOption]` / `[UGCUploadOption]` | 打包目标平台、SkipBake、PakOnly |
| `[SwitchesInMaps]` | 地图级渲染/流送开关 |
| `[Input]` | 保留输入动作 |

改工程配置优先用编辑器 UI；手改 `.ugcproj` 后需要重新打开工程。

## Script 分层（推荐）

模板与 Withdraw 的共性：

| 目录 | 作用 |
|---|---|
| `Blueprint/` | 绑定蓝图：`---@class Xxx_C:父类` + `--Edit Below--`；实现 `ReceiveBeginPlay/Tick/EndPlay` |
| `gamemode/` | 触发器脚本：`Action_*.lua` / `Condition_*.lua`，由 GameModeActor 配置调用 |
| `Common/` | `ue_enum_custom.lua`、`ue_struct_custom.lua` 等类型补全 |
| `Config/` | 静态配置表/常量配置 |
| `Const/` | 枚举、ID 常量（常由配表生成） |
| `Core/` | 事件、数据、UI 管理等核心框架 |
| `Manager/` | 运行时数据持有者 |
| `Query/` | 只读查询 |
| `Service/` | 业务用例编排（服务端为主） |
| `Tool/` | 业务写入/封装 |
| `UI/` | 界面控制脚本 |
| `Package/` | 按业务域打包的模块（Withdraw 模式） |
| `LifeCycle/` | 生命周期入口 |

新建工程可只保留 `Blueprint/` + `gamemode/` + `Common/`，随复杂度再引入分层。

## 选工程

| 需求 | 起点 |
|---|---|
| 从零开始 | `Template_SysNullMap`（空工程 + 可操作角色） |
| 经典 BR 地图 | `Template_Ty_Forest`、`Template_FourMaps`、`Template_Sys*Map` |
| 团竞 | `Template_CTCompetition`、`Template_ArmsTeamCompetition`、`Template_OTCompetition` |
| 技能 PVP | `Template_SkillCompetition` |
| PVE / 刷怪 | `Template_Athena`、`Template_RogueShooting` |
| 俯视角 / 2.5D / 横版 | `Template_TopDown`、`Template_TopDownSurvivor`、`Template_2dot5`、`Template_Transverse` |
| 载具竞速 | `Template_RacingCar` |
| 任务剧情 | `Template_TaskAndStory` |
| 棋牌 / 音游 | `Template_planechess`、`Template_MusicParty` |
| 功能大全 | `Template_PlaygroundHub`（211 个脚本，覆盖最多 API） |
| 完整项目 | `Withdraw` |

完整清单与每个模板的说明见 `Docs/templates.md`。

## 硬约束

- **模板只读参考**：正式开发先复制模板为新工程；直接改 `Template_*` 会污染后续新建工程。
- **不要手改编辑器生成文件**：`UGCLuaBindFiles.txt`、`DeleteFiles.txt`、`ReferenceAssetList.txt`、`Thumbnail.png` 由编辑器生成。
- **一个工程一个入口**：`StartMapName` + `GameModePath` 决定启动链路；多模式用 `[MultiModeSetting_N]`，不要复制多套 Script。
- **资产路径用工程相对路径**：`UGCGameSystem.GetUGCResourcesFullPath("Asset/...")`，不要写绝对路径。
- **跨工程复用先抽 `ExtendResource/<Package>/OfficialPackage/`**，再在工程内引用。

## 交付物所有权

代码改动的边界由「文件类型」决定，不由「需求归属」决定。Agent 只能写表中标 ✅ 的部分。

| 交付物 | 谁写 | Agent 读 | Agent 写 | 验证手段 |
|---|---|---|---|---|
| 纯 Lua 模块（无 `--Edit Below--`） | Agent | ✅ | ✅ 全文 | luacheck → 可执行断言 |
| `--Edit Below--` 之下 | Agent | ✅ | ✅ | luacheck → 可执行断言 |
| `--Edit Below--` 之上（`---@class` / `---@field`） | 编辑器 | ✅ | ❌ 会被静默覆盖 | 编辑器重存蓝图后会被覆盖，改前确认 |
| UMG（`Asset/UI/*.uasset`） | 人 | ⚠️ 控件名/类型可读，布局数值不可读 | ❌ | 控件契约检查 + 人工视觉 |
| 场景（`.umap`） | 人 | ⚠️ 类名可读，Transform/实例数不可读 | ❌ | 场景契约检查 + 人工视觉 |
| DataTable（`Asset/Data/Table/*.uasset`） | 人（编辑器表格管理器） | ✅ 离线解析 schema + 运行时 `UGCGameSystem.GetTableData*` | ❌ | Daemon 行/列 + 人工核对 |
| `.ugcproj` | 人（编辑器 UI） | ✅ | ❌ 手改后需重开 | 编辑器 |

推论：**新增业务逻辑不受阻，新增 UMG / 场景 / 表结构必须等人先行**。拆解阶段就要标出这类前置。

## 配置与表格

- **表格由人在编辑器「表格管理器」中维护**，运行时通过 `UGCGameSystem.GetTableData / GetTableDataByRowName / GetTableCount`（双端可用）读取。表格管理器自带 CSV 导入导出，策划自行处理。
- **表格源**：`.ugcproj` 的 `DataTableRootDir` 不指向工程内目录时，说明该工程没有可版本控制的表格源。
- **Agent 不得"顺手加一行配置"**：表格内容与结构都归人。需要新表 / 新字段 = 前置阻塞项，先由人建 RowStruct 与列。
- 表格二进制可离线解析（UE `FProperty` 命名 `Name_Index_Hash`），用于取字段名与行键；这是 Agent 认识表格的唯一通道。

## UI 契约

UMG 是 cooked 二进制：**控件名、控件类型、控件树结构标记可读；布局数值不可读也不可写**。Agent 无法改界面外观，但必须知道有哪些控件。

- **契约库**：`spec/ui-contracts/INDEX.md`（含工程与商店模板；数量以库头为准）。接到 UI 需求先查库，命中则复用现有界面，未命中才设计新界面。
- **控件名以契约库为准**，禁止引用库中不存在的控件。
- **前置**：新界面需人先在编辑器建 UMG 并保存，绑定文件生成后 Agent 才能写逻辑。控件命名和类型由人在这一步定死，之后改控件名会让 Agent 代码静默失效。
- **校验**：`python -I spec/tools/ui_contract.py check ...`，有新增未声明引用时退出码 1。成本约 1 秒，属验证 L2 层。
- 工具说明见 `spec/tools/README.md`。

## 场景契约

场景没有 UI 那样的自动声明清单：`.umap` 摆了哪些 Actor 只能运行时枚举，
但 Actor 的**配置字段**在绑定脚本里可静态读。所以契约分两层，缺一层不成立。

- **契约库**：`spec/scene-contracts/INDEX.md`（数量以库头为准）。两层交叉：属性层（`---@field` 配置字段）+ 摆放层（扫 `.umap` 得到真实摆放）。
- **场景 = 人摆位置 + Agent 写行为**。Agent 不可改 Transform、地形、建筑布置。
- **动态生成必须走代码**：随机撤离点、动态刷怪、宝箱刷新用 `UGCActorComponentUtility.SpawnActor`（双端可用），编辑器摆死做不到。
- **枚举约定**：`GetAllActorsOfClass / GetAllActorsWithTag` 返回 **Lua userdata 不是 table**，调用下游前先 `ipairs` 转纯表。
- **Tag 走 `Util_EnumManager.TagKey`**，不要写字面量；遗留项见 `spec/scene-contracts/CHECK-REPORT.md`。
- **校验**：`python -I spec/tools/scene_contract.py check ...`，有新增问题时退出码 1。属验证 L2 层。
- 工具说明见 `spec/tools/SCENE-README.md`。

## 文档

| 文档 | 何时读 |
|---|---|
| `Docs/project-guide.md` | 工程生命周期、蓝图绑定、服务端/客户端、调试、打包 |
| `Docs/network-replication.md` | 属性复制、RPC、断线重连、弱网 |
| `Docs/debugging.md` | 日志位置、PIE 日志面板、环境错误、HotReload、失败对照 |
| `Docs/performance.md` | 预算、Profile、对象池、网络裁剪、防外挂 |
| `Docs/runtime-rules.md` | 封禁接口、UObject 有效性、结构体/容器、静态检查 |
| `Docs/release-checklist.md` | 真机、上传、提审、匹配、补人 |
| `Docs/release-notes-1.39.md` | 1.39 编码相关增量 |
| `Docs/wiki-map.md` | 官方 wiki 的机制/流程/配方索引 |
| `Docs/templates.md` | 模板选择与每个模板的能力 |
| `Withdraw/AGENTS.md` | 修改撤离项目 |
| `../Content/LuaHelper/AGENTS.md` | 查 API |
