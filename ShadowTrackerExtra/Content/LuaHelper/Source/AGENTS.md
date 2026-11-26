# LuaHelper/Source AGENTS

`LuaHelper/Source` 是编辑器 Lua 类型库的主体（6412 个 `.lua`，全部 `---@meta`）。它按「接口层 / 框架层 / 游戏实现层 / 引擎层」分了 6 个目录。**这里只用来看签名和类型，不写业务代码。**

## 先选目录

| 你要找 | 目录 | 文件数 |
|---|---|---:|
| 创作者可直接调用的 `UGC*System` / `UGC*Utility` | `Lua/ugc/UGCAPI/` | 77 |
| UGC 框架类（GamePart、BackpackV2、UI MVVM、任务管理） | `Lua/ugc/` | 199 |
| Lua 通用类型与工具（Async、Delegate、utils、ue_object） | `Lua/common/` | 19 |
| UGC 玩法类（GameMode、Character、Vehicle、PVE、Weapons） | `UGCGame/` | 193 |
| 自定义 Actor / 组件 / 物理 Actor 框架 | `Gameplay/` | 141 |
| 基础框架（Buff、Skill、Camera、Framework、Public） | `Basic/` | 128 |
| UMG 控件扩展 | `Client/UMG/` | 37 |
| 游戏本体类（角色、载具、武器、动画、UI 等内部 API） | `ShadowTrackerExtra/` | 5695 |

## 各层说明

### Lua/ugc/UGCAPI — 创作者 API（最重要）

- 77 个文件，约 13.4k 行；每个文件一个 `UGC*System` 或 `UGC*Utility`。
- 函数注释固定格式：
  `---【规范】说明` → `---生效范围：服务器&客户端` → `---@param` / `---@return`。
- 状态关键字：`【规范】`、`【实验性】`、`【废弃】`；废弃函数带 `@deprecated` 与替代项。
- 例：`UGCGameSystem.GetAllPlayerPawn()`、`UGCBackpackSystemV2.*`、`UGCPersistEffectSystem.*`。

### Lua/ugc — UGC 框架

| 子目录 | 内容 |
|---|---|
| `UGCGame/GamePart/` | GamePart 实现：Activity、AirAttack、BackpackV2、CircleManager、CommodityOperationManager、EMPZone、NewbieGuide、PlayerListManager、PlayerProfileManager、RankingListManager、SideScrolling、TaskManager、TeamRecruit、TopDown、VirtualItemManager |
| `UGCGame/ObjectLibrary/` | 对象库 |
| `RAF/Framework/MVVM/` | `UGCView`、`UGCViewModel`、`UGCItemView`、`CollectionBinder`、`MVVMProperty/Command` |
| `UGCCommoditySystem/UI/` | 二次确认弹窗 |
| `UGCSystemInternal/` | `UGCSystemSettings`、`UGCSystemWrapper` |

### UGCGame — UGC 玩法类

| 子目录 | 文件数 | 内容 |
|---|---:|---|
| `GameMode/` | 6 | `UGCGameModeBase`、`UGCGameStateBase`、TDM、TopDown 配置 |
| `Character/CharacterPreset/` | 10 | 角色预设、控制、自定义移动（Flying/Locomotion） |
| `Backpack/` | 21 | 背包 V2 句柄、拾取包装、物品容器接口 |
| `PVEGame/` | 11 | PVE 组件/条件/GameModeActor/玩家状态/任务 |
| `Task/` | 14 | 攻击、评价、物品、系统任务 |
| `Weapons/` | 13 | 武器自定义组件、功能模块、抛体 |
| `Vehicle/` | 6 | UGC 载具 |
| `AI/`、`SeekTarget/` | 2 | 假控制器、索敌 |
| `HUD/`、`Minimap/`、`WidgetUI/` | 9 | HUD、伤害数字、小地图、控件 UI |
| `GamePart/`、`GameSystem/`、`KillFlow/`、`Motion/`、`PostProcess/`、`TeamRecruit/`、`Utilities/`、`TemplateActor/` |  | 其余玩法框架 |

### Gameplay — 玩法框架

- `Public/`（122）：核心接口与组件，如 `BackpackComponent`、`BackpackItemInterface`、`GameModeBaseComponent`、`GeneratorActor*`、`GroupSpotSceneComponent`、`ConfigInterface`、`DataSource/`、`RacingTrack/`、`SubSystem/`。
- `CustomActor/`：`MoveablePlatformBaseActor`。
- `CustomComponent/`：`MoveComponent`、`MoveablePlatformComponent`。
- `PhysicsActors/`：物理 Actor 基类与组件/接口。
- `Tools/`：工具。

### Basic — 基础框架

| 子目录 | 文件数 | 内容 |
|---|---:|---|
| `Public/` | 96 | 属性修改、物品基类、背包、快照、Pak 预热、UAE 网络/表管理、UI 中间层、BigWorld、子弹幕、曲线、EffectModifiers、GenericAbility、TagLogLua |
| `Buff/` | 10 | `STBaseBuff*`：Buff 实例、管理器、条件、事件、状态 |
| `Skill/` | 1 | `UAEBaseSkillCondition` |
| `Camera/` | 4 | 相机占有、弹簧臂 |
| `Framework/` | 10 | TickTask、OnlyActorComponent、NavLink |
| `UECommon/` | 5 | UE 公共封装 |
| `MultiDS/` | 2 | 多 DS |

### Client/UMG — 控件扩展

`NewButton`、`NewCheckBox`、`DynaCanvasPanel/HorizontalBox/VerticalBox`、`MaskBox`、`ParallaxWidget`、`PerspectiveWidget`、`TransformWidget`、`ImageEx/ImageHQ`、`CustomGridWidget`、`UIParticleEmitterHQ`、`RealtimeLog` 等 37 个。

### ShadowTrackerExtra — 游戏本体（内部层）

5695 个文件，按系统分目录。数量前 15：

| 目录 | 文件数 | 目录 | 文件数 |
|---|---:|---|---:|
| `Private/` | 1198 | `UI/` | 195 |
| `CustomComponent/` | 709 | `Buff/` | 174 |
| `CustomActor/` | 507 | `BackPack/` | 150 |
| `Character/` | 426 | `AnimNotify/` | 90 |
| `Vehicle/` | 337 | `CustomClosure/` | 88 |
| `Skill/` | 337 | `GameMode/` | 76 |
| `Weapons/` | 218 | `Player/` | 75 |
| `Animation/` | 217 | | |

其余：`LobbyCharacter`、`Utility`、`LogicEffect`、`Interface`、`LobbyBase`、`General`、`Security`、`BigWorld`、`Task`、`SubSystem`、`Replay`、`Props`、`ADS`、`GenericInteractiveSystem`、`DataAssets`、`Airdrop`、`Voice`、`AutoTest` 等。

> 这一层是游戏本体的类 API，多数不是创作者直接调的；查 UGC 功能时优先 `Lua/ugc/UGCAPI`。确需底层能力时再在此搜类名。

### Engine/Source — UE4 类型存根

2009 个文件，按 `Runtime/<Module>/` 组织（CoreUObject、Engine、AIModule、UMG、Slate、Landscape…），对应 `UClass/UStruct/UEnum`。查 UE 引擎侧类型时用。

## 存根格式

```lua
---@meta

---【规范】游戏通用接口库
---@class UGCGameSystem
UGCGameSystem = {}

---【规范】获取所有玩家角色
---生效范围：服务器&客户端
---@return ASTExtraPlayerCharacter[]
function UGCGameSystem.GetAllPlayerPawn() end
```

- `---@class Xxx: 父类` 表示继承；`---@field` 表示属性，`<ReadWrite>` 可写。
- 函数体一律为空；不要据此推断实现。
- 文件编码多为 UTF-8 BOM，检索时注意。

## 检索命令

```bash
cd ShadowTrackerExtra/Content/LuaHelper

grep -rn "函数名关键词" Source/Lua/ugc/UGCAPI/
grep -rn "@deprecated" Source/Lua/ugc/UGCAPI/
grep -rln "GetPlayerPawnByPlayerKey" Source/ | head
grep -rn "生效范围：服务器" Source/Lua/ugc/UGCAPI/UGCGameSystem.lua | head
```

## 约束

- 只读。更新会覆盖，改了不生效。
- 文档细节放 `../Docs/`，本文件只做索引。
- 业务实现与示例去 `../../../UGCProjects/`，不要在这里找。
