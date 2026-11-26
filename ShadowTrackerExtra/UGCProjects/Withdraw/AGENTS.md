# Withdraw AGENTS

已开发的完整撤离类（搜打撤）项目：基地 + 4 张地图（共 5 个模式）、多模式匹配、物品/背包 V2、耐久、护盾、建造、医疗、任务、商业化。

- 工程配置：`Withdraw.ugcproj`（版本 `1.39.13.16226`，`UpdateVersion=10`）
- 启动：`StartMapName=/Withdraw/UGCmap`，`GameModePath=/Withdraw/Asset/Blueprint/UGCGameMode.UGCGameMode_C`
- 模式：`[MultiModeSetting_0..4]` = 基地(1001)、Map1(1002)、Map2(1003)、Map3(1004)、Map4(1005)；Map4 需从 Map3 撤离后解锁
- 打包目标：`LinuxServer+WindowsNoEditor+Android_ETC2+IOS+OpenHarmony_ETC2`

## Script 结构

| 目录 | 文件数 | 职责 |
|---|---:|---|
| `Blueprint/` | 265 | 蓝图绑定脚本：GameMode/GameState/PlayerController/PlayerPawn/PlayerState、组件、模块、Prefab（Buff/Item/Loot/Monster/Projectile/Skill/Weapon）、UI |
| `Package/` | 109 | 按业务域分包：AttributeSystem、Building、Collect、CountDown、Encumbrance、GameMode、GamePlayRecord、ItemSystem、LevelSystem、MakeUp、MapProgression、Player、Shield、SkillSystem、Task、Teleport |
| `UI/` | 74 | 各界面控制脚本（Main、Backpack、Shop、Task、Challenge、Durability…） |
| `Config/` | 54 | 静态配置：AutoTestSuite、Command、GM、Package 配置 |
| `Tool/` | 26 | 写入/业务封装（耐久、武器、掉落、小地图、教学…） |
| `Core/` | 22 | EventCore、GameDataCore、PlayerDataCore、TipCore、UIManager、ClientCache、CommandSystem、DebugKit、AutoTestKit |
| `Setting/` | 9 | 注册表/索引（多为生成物）与全局配置 |
| `Const/` | 5 | 常量/枚举（含生成物） |
| `Manager/` | 4 | 运行时数据：ArmsDealer、Durability、Loot、PlayerCondition |
| `Query/` | 7 | 只读查询 |
| `Service/` | 6 | 业务编排：ArmsDealer、Durability、ItemPack、Loot、Shop、Test |
| `Event/` | 2 | `EventType.lua`、`Event_DataChange.lua` |
| `LifeCycle/` | 1 | `LifeCycle.lua` 生命周期总入口 |
| `Mail/`、`GamePlay/`、`GamePartCustom/`、`Utility/`、`UMGTemplate/` |  | 邮件、玩法效果、背包 V2 定制、工具、UMG 模板 |

## 启动与初始化顺序

```text
UGCGameMode:ReceiveBeginPlay
  → LifeCycle.BeginPlay()                注册 GameState/PC/Pawn 生命周期监听
  → LifeCycle.OnGameStateInit
      → Core_Registry.BeginPlay()        Core 模块（UIManager/GameDataCore/PlayerDataCore…）
      → Util_ConfigLoader.BeginPlay()
      → Svc_ArmsDealer.BindCommodityDelegate()
      → Svc_Durability.Init()            双端 Override + 服务端 Fire Hook
      → Tool_InfiniteAmmo/Tool_WeaponFireMode/WeaponHandling.Init()
      → Package_Registry.BeginPlay()     16 个业务 Package
      → GameService_CountDown.BeginPlay()
      → Registry_GameMode.LoadCurrentMode(gameState)
  → LifeCycle.OnPCInit → 延迟 1.5s → OnPCInit_Handle
      → 服务端发 Server_OnPlayerControllerInit / Server_OnPlayerDataLoaded
      → 客户端打开 GM/状态/射击 UI，初始化小地图
  → LifeCycle.OnPawnInit → 延迟 2.5s → OnPawn_Server_Init_Handle
      → 耐久/无限弹药/射击模式/后坐力接入，发 Server_OnPlayerInstanceInit
```

## 分层规范

```text
UI / Blueprint
  → Service（业务用例，服务端为主）
      → Tool / Utility（写入、底层封装）
          → Manager（运行时数据）
              → Query（只读）
                  → Config（静态配置，可直接读）
EventSystem：独立的事件派发中心，EventHandler 统一调 Service
LifeCycle：最先执行，协调各层初始化
```

硬规则：

- **Query 只读**，禁止写。
- **UI 不直接碰 Manager**：UI 走 Query / Service / Tool。
- **Service 不直接写 Manager**：写走 Tool，读走 Query。
- **Config 可被各层直接读取**。
- **单向依赖**：下层不反向调用上层。

## 关键入口文件

| 文件 | 说明 |
|---|---|
| `Blueprint/UGCGameMode.lua` | 局内 GameMode 绑定 |
| `Blueprint/UGCGameState.lua` | GameState 绑定，负责大量管理器/工具层的 require 与初始化 |
| `Blueprint/UGCPlayerController.lua` | 玩家控制器绑定，聚合玩家组件与 UI |
| `Blueprint/UGCPlayerPawn.lua`、`UGCPlayerState.lua` | 角色/玩家状态绑定 |
| `LifeCycle/LifeCycle.lua` | 生命周期总入口 |
| `Core/EventCore/UGCEventSystem.lua` | 项目事件总线（AddListener/SendEvent） |
| `Core/UIManager/Global_UISystem.lua` | 项目 UI 门面 |
| `Core/UIManager/Mgr_UIManager.lua` | UI 管理器 |
| `Package/ItemSystem/Registry_ItemSystem.lua` | 物品系统门面（实体背包/虚拟物品路由） |
| `Blueprint/UGCPlayerController.lua` 中的 `BP_Player*Component` | 玩家能力组件 |

## 生成物（勿手改）

以下文件为已知生成物；同目录文件头标注「自动生成」的同样适用，均勿手改：

- `Setting/Core_Registry.lua`
- `Setting/Package_Registry.lua`
- `Setting/Package_Meta_Index.lua`
- `Setting/Project_Globals.lua`
- `Setting/AutoTestSuiteIndex.lua`
- `Setting/CommandConfigIndex.lua`
- `Const/Generate/Const_Item.lua`

新增 Package 的步骤：

1. 建 `Script/Package/<Name>/`，提供 `Registry_<Name>.lua`、`Package_Meta.lua`（如需）。
2. 由维护者重新生成注册表（生成物不手改；本仓库不含生成器）。
3. 新逻辑按分层放入 `Manager/Query/Tool/Service/UI`。

## ExtendResource（官方资源商店包）

| 包 | 大小 | 内容 |
|---|---:|---|
| `Mail/` | 13M | 邮件 |
| `ShopV2/` | 21M | 商店 V2 |
| `Activity/` | 5.7M | 活动 |
| `TaskTemplate/` | 11M | 任务模板 |
| `pass/` | 9.7M | 通行证 |
| `GlobalPlayerList/`、`SignInEvent/`、`TeammateList/`、`GiftPack/` |  | 全局玩家列表、签到、队友列表、礼包 |

每个包含 `ResourceMeta.json`、`*.ugcstoreasset`、`OfficialPackage/{Script,Asset}`。升级/替换会整体覆盖，**定制优先放在工程 `Script/` 二次封装**。

> 本工程的 `Docs/` 已整体移除（历史设计文档过时）。架构与分层以本章「Script 结构」「启动与初始化顺序」「分层规范」三节为准，其余以 `Script/` 代码为唯一事实来源。

## 测试与调试

- 单元测试：`Core/AutoTestKit/` + `Config/AutoTestSuite/Suite_*.lua`；入口 `Global_AutoTestKit`。
- 自动跑 Suite：`python -I spec/tools/pie_runner.py run --suite <名字>`，见 `spec/tools/PIE-README.md`。
- GM/命令：`Core/CommandSystem/`、`Config/Command/`、`Config/GM/Config_GMResources.lua`。
- 日志：`ugcprint` → `Saved/Logs/ShadowTrackerExtra.log` 与 `Saved/Logs/Withdraw/`。
- 项目内调试面板：`UI/GM/UMG_AutoTestControl.lua`、`Script/Core/DebugKit/`。

## 硬约束

1. **遵守分层**：UI→Service/Tool/Query；Query 只读；Service 写走 Tool。
2. **不要手改生成物**（见上）。
3. **不要直接改 `ExtendResource/*/OfficialPackage/`**：升级会覆盖。
4. **事件统一走 `EventType` + `UGCEventSystem`**，不要新增全局字符串事件。
5. **玩家数据走 `PlayerDataCore`/`System_PlayerDataCore`**，不要各写一套存档。
6. **物品读写走 `Registry_ItemSystem`**，区分实体背包与引擎 VirtualItemManager。
7. **UI 打开/关闭走 `Global_UISystem`**，不要直接 `AddToViewport`（例外：临时调试）。
8. **新模块先建 Package**（`Registry_` + `Package_Meta`），再更新索引（生成物不手改）。
9. **`Blueprint/` 下绑定文件与蓝图同名**；含 `--Edit Below--` 时用户代码保持在其下，无标记的纯 Lua 类文件按普通模块组织。
10. **改动前先看本文件「分层规范」与硬约束**；改完同步本文件。
