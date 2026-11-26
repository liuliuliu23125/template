# LuaHelper AGENTS

UGC 编辑器的 **Lua/蓝图类型库**。目录下 9068 个 `.lua` 文件**全部以 `---@meta` 开头**（`Source/` 6412、`Engine/` 2010、`Content/` 646），是给 EmmyLua/VSCode 做补全与类型检查的存根，不是运行时代码。

## 为什么重要

- 所有创作接口的权威签名都在这里；工程 `.emmyrc.json` 的 `workspace.library` 指向 `../../Content/LuaHelper/Source`。
- 工程 `workspace.code-workspace` 也把 `Content/LuaHelper` 加为工作区目录。
- 写 Lua 前在这里查函数、参数、返回、服务端/客户端生效范围，比猜 API 可靠。

## 目录

| 路径 | 文件数 | 内容 |
|---|---:|---|
| `Source/Lua/ugc/UGCAPI/` | 77 | **创作者 API 总入口**：`UGC*System`、`UGC*Utility`，共约 13.4k 行 |
| `Source/Lua/ugc/UGCGame/` | 111 | UGC 框架类：GamePart、BackpackV2、Activity、AirAttack、TaskManager 等 |
| `Source/Lua/ugc/UGCCommoditySystem/` | 1 | 商业化 UI 类 |
| `Source/Lua/ugc/UGCSystemInternal/` | 2 | 系统设置/包装器内部类型 |
| `Source/Lua/ugc/RAF/` | 8 | RAF MVVM：`UGCView`、`UGCViewModel`、`CollectionBinder` 等 |
| `Source/Lua/common/` | 19 | `utils`、`Async`、`Delegate`、`PromiseFuture`、`ue_object` 等通用类型 |
| `Source/UGCGame/` | 193 | UGC 玩法类 API：GameMode、Character、Backpack、Vehicle、Task、PVE、Weapons、HUD、Minimap |
| `Source/Gameplay/` | 141 | 玩法框架：CustomActor、CustomComponent、PhysicsActors、公共接口、Tools |
| `Source/Basic/` | 128 | 基础框架：Buff、Skill、Camera、Framework、UECommon、Public、MultiDS |
| `Source/Client/` | 37 | UMG 控件扩展：`NewButton`、`DynaCanvasPanel`、`MaskBox`、`ParallaxWidget` 等 |
| `Source/ShadowTrackerExtra/` | 5695 | 游戏本体的类 API（内部实现层，数量最大） |
| `Engine/Source/` | 2009（+`Engine/NoExportTypes.lua`） | UE4 引擎类/枚举/结构存根 |
| `Content/` | 646 | 蓝图类存根：`BP_*_C`（载具、角色、控制器、UGCGame 预览资产等） |

> `Engine/Source` 与 `Source/` 同级，位于 `LuaHelper/Engine/Source`。

## 命名约定

| 形式 | 含义 |
|---|---|
| `UGCXxxSystem` | 创作者接口库（静态函数集合），优先使用 |
| `UGCXxxUtility` | 工具库（无状态函数） |
| `AUGCXxx` / `A*` | Actor 类 |
| `UUGCXxx` / `U*` | UObject/Component 类 |
| `EXxx` | 枚举 |
| `FXxx` | 结构体 |
| `BP_Xxx_C` | 蓝图生成类；Lua 绑定文件用同名 `_C` 作为 `---@class` 父类 |
| `---@field X type <ReadWrite>` | 可读写属性；无标记通常只读 |

## 读取 API 的三步

1. **定位系统**：按功能查 `Docs/api-index.md`，或
   `grep -rln "关键词" Source/Lua/ugc/UGCAPI/`。
2. **看状态与范围**：类注释 `【规范】/【实验性】/【废弃】`；函数注释 `---生效范围：服务器 / 客户端 / 服务器&客户端`。
3. **看替代与示例**：`@deprecated` 给出替代；再到 `../../UGCProjects/Template_*` 或 `Withdraw/Script/` 搜真实用法。

> 领域文档表格里的 `UGCAPI/...` 基准为 `Source/Lua/ugc/`；`Source/AGENTS.md` 中的链接可直接打开。

## 已废弃映射

| 旧接口 | 替代 |
|---|---|
| `UGCSkillManagerSystem` | `UGCPersistEffectSystem` |
| `UGCBuffSystem` | `UGCPersistEffectSystem` |
| `UGCMobPawnSystem` | `UGCGenericCharacterSystem` |
| `UGCPawnAttrSystem` | `UGCAttributeSystem` |
| `UGCPawnSystem` | `UGCPlayerPawnSystem` |
| `UGCWidgetManagerSystem` 的 36 个函数 | `UGCWidgetUtility` |
| `UGCVehicleSystem.SpawnVehicle` | `UGCVehicleSystem.SpawnVehicleNew` |

## 分类文档

| 分类 | 文档 | 主要系统 |
|---|---|---|
| 角色 | `Docs/character.md` | PlayerPawn/PlayerController/PlayerState |
| 怪物 | `Docs/monster.md` | GenericCharacter/SimpleCharacter |
| 技能 | `Docs/skill.md` | PersistEffect/Attribute/Projectile |
| 属性与伤害 | `Docs/attributes-damage.md` | 属性管理器/修改器/全局伤害/治疗公式 |
| 物品与背包 | `Docs/item-backpack.md` | ItemV2/BackpackV2/Drop |
| 商业化与功能模板 | `Docs/commerce-template.md` | GamePart/Commodity/Mail/Activity |
| GamePart 启用 | `Docs/gamepart.md` | `DA_GameModeGeneral`、加载时机、虚拟物品 |
| 技能/Buff 编辑器 | `Docs/skill-buff-editor.md` | 状态图、Task/Event/Condition、状态互斥 |
| 物品/背包编辑器 | `Docs/item-backpack-editor.md` | 物品模板、Handle、实例化数据、背包流程 |
| 怪物与 AI | `Docs/monster-ai.md` | 怪物模板、行为树、导航、刷怪 |
| 载具编辑器 | `Docs/vehicle-editor.md` | 载具模板、座位、武器、常见问题 |
| 场景与环境 | `Docs/scene.md` | LevelFlow/Weather/Navigation/SceneQuery/Circle/AirDrop |
| 载具 | `Docs/vehicle.md` | Vehicle/VehicleV2/Seat/Common |
| 社交 | `Docs/social.md` | Team/Camp/Voice/Message |
| 玩法规则 | `Docs/gameplay-rules.md` | GameSystem/GameplayTask/Tag/Time/MultiMode |
| UI | `Docs/ui.md` | UIManager/WidgetUtility/WidgetManager/CommonUI |
| 工具库 | `Docs/toolbox.md` | Math/Object/Actor/Timer/Async/Tween/Delegate |
| 基础功能 | `Docs/basic.md` | Global/Camera/Sound/Input/Debug |
| 其他 | `Docs/misc.md` | Gun/WeaponManager/EntityType/FakePlayer/ScriptModule |
| 全量速查 | `Docs/api-index.md` | 77 个 API 库的分类表 + 模板引用数 |

## 工程级专题

| 文档 | 何时读 |
|---|---|
| `../../UGCProjects/Docs/network-replication.md` | 属性复制、RPC、重连、弱网 |
| `../../UGCProjects/Docs/debugging.md` | 日志、环境错误、PIE/上传失败、HotReload |
| `../../UGCProjects/Docs/performance.md` | 性能预算、Profile、网络裁剪 |
| `../../UGCProjects/Docs/runtime-rules.md` | 封禁接口、UObject/结构体/容器规则 |
| `../../UGCProjects/Docs/release-checklist.md` | 真机、上传、提审、匹配/补人 |
| `../../UGCProjects/Docs/wiki-map.md` | 官方 wiki 机制页索引 |

## 约束

- 不要修改 `LuaHelper/` 下任何文件：编辑器更新会覆盖，且不影响运行逻辑。
- 不要据此判断实现细节：存根只有签名；真实实现是引擎 C++，业务代码在各工程 `Script/`。
- 不要依赖固定行号；函数会随版本增删，用名称检索。
- 需要查“某个模板怎么用”时，转到 `../../UGCProjects/`，不要在这里找示例实现。
