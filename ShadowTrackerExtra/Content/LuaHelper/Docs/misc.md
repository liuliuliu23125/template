# 其他：枪械、武器、实体、脚本模块、假人

> 杂项能力集合：`UGCGunSystem` 调枪械数值与开火，`UGCWeaponManagerSystem` 管玩家武器槽与切枪，`UGCEntityTypeSystem` 按实体类型查询 Actor，`UGCScriptModuleManager` 注册脚本模块，`UGCFakePlayerSystem` 生成假人，`UGCMiscFunctionSystem` 提供航线/空投入口。

## 何时读

- 需要改子弹伤害、射速、弹匣、后坐力、换弹时间或开关镜/自动瞄准。
- 需要按槽位取武器、切枪、读当前武器或弹药，或给武器加/卸配件。
- 需要按“实体类型”或 GameplayTag 做范围检测、类型判断。
- 需要把一套逻辑封装成可注册的服务器/客户端/玩家脚本模块。
- 需要在服务器生成假人玩家陪练或占位。
- 需要开局航线，或迁移旧的空投调用。

## API 一览

| System | 文件 | 状态 | 关键函数 | 生效范围 |
|---|---|---|---|---|
| UGCGunSystem | UGCAPI/UGCGunSystem.lua | 规范（42） | StartFire / StopFire / Reload / OpenScope / EnableInfiniteBullets / SetMaxBulletNumInOneClip / SetBulletBaseDamage / SetShootIntervalTime / AddGunAttachment / CreateAndAddGunAttachment / RemoveGunAttachmentBySocketType | 开火/换弹/开镜为客户端；数值设置与配件为服务器；读取双端 |
| UGCWeaponManagerSystem | UGCAPI/UGCWeaponManagerSystem.lua | 规范（11） | GetWeaponManagerComponent / GetWeaponBySlot / GetCurrentWeapon / GetLastUsedWeapon / GetCurrentWeaponSlot / SwitchWeaponBySlot / CurrentWeaponAttachToBack / GetWeaponItemID / GetCurrentUsingAmmoID / SetWeaponSlotVisible | 服务器&客户端；`SetWeaponSlotVisible` 为客户端 |
| UGCEntityTypeSystem | UGCAPI/UGCEntityTypeSystem.lua | 规范（24） | IsActorOfEntityType / GetActorEntityType / GetAllEntityTypeNames / OverlapBoxByEntityType / OverlapSphereByEntityType / OverlapCapsuleByEntityType / IsActorOfEntityTypeByTag / SetConfigDataAssetPath / ForceReloadConfig | 服务器&客户端 |
| UGCScriptModuleManager | UGCAPI/UGCScriptModuleManager.lua | 规范（6） | RegisterServerScriptModule / RegisterPlayerScriptModule / RegisterClientScriptModule / GetScriptModule / GetPlayerScriptModule / GetLocalPlayerScriptModule | 按接口区分服务器 / 客户端 / 双端 |
| UGCFakePlayerSystem | UGCAPI/UGCFakePlayerSystem.lua | 规范（3） | SpawnFakePlayer / GetRandomAIPlayerKey / DestroyFakePlayer | 服务器 |
| UGCMiscFunctionSystem | UGCAPI/UGCMiscFunctionSystem.lua | 规范 1 / 废弃 2 | StartAirRoute / StartAirDrop（废弃）/ StartNormalAirDrop（废弃） | 服务器 |

## 核心概念

### 枪械与武器是两层

| 层 | 对象 | 职责 |
|---|---|---|
| 武器管理 | `UWeaponManagerComponent` | 槽位、当前武器、上一把武器、切枪、收枪、弹药 ID、武器可见性 |
| 枪械本体 | `STExtraShootWeapon` | 弹匣、射速、射程、伤害、冲量、后坐力、扩散、换弹时间、开火 |
| 配件 | `ItemDefineID` / `ItemID` | 按 `EWeaponAttachmentSocketType` 槽位增删查 |

`ESurviveWeaponPropSlot` 常用槽位：`SWPS_MainShootWeapon1`、`SWPS_MainShootWeapon2`、`SWPS_SubShootWeapon`、`SWPS_MeleeWeapon`、`SWPS_HandProp`、`SWPS_TempSpecialWeapon`、`SWPS_VehicleWeapon`、`SWPS_GunBag`。

`EWeaponAttachmentSocketType` 常用槽位：`GunPoint`（枪口）、`Grip`（握把）、`Magazine`（弹匣）、`Gunstock`（枪托）、`OpticalSight`（瞄准镜）、`AngledOpticalSight`（侧瞄）、`MasterGun`（枪本）、`Ammo`（弹药）、`Pendant`（挂件），另有 `Refit_*` 与 `KillCountingScreen_*` 等改装位。

### 实体类型

`UGCEntityTypeSystem` 提供两套并行接口：

| 形式 | 判断/查询 | 范围检测 |
|---|---|---|
| 实体类型名字符串 | `IsActorOfEntityType` / `GetActorEntityType` / `GetActorEntityTypes` | `OverlapBoxByEntityType` / `OverlapSphereByEntityType` / `OverlapCapsuleByEntityType` |
| GameplayTag | `IsActorOfEntityTypeByTag` / `IsActorOfEntityTypeByTags` / `GetActorEntityTypeAsGameplayTag` | `Overlap*ByEntityTypeTag` / `Overlap*ByEntityTypeTags` |

另有按类路径的判断：`IsActorOfClassType`、`IsActorOfAnyClassTypes`。配置默认走内置 DataAsset；自定义时 `SetConfigDataAssetPath` 后调用 `ForceReloadConfig`。名字与 Tag 可互转：`ConvertEntityTypeNameToGameplayTag` / `ConvertGameplayTagToEntityTypeName`。

### 脚本模块

`UGCScriptModuleConfig` 含 `Name`、`Path`、`bEnableUpdate`。模块生命周期：`Initialize` → `PostInitialize` → `Update` → `PreFinalize` → `Finalize`，对应四个委托 `OnInitialized`、`OnPostInitialized`、`OnPreFinalized`、`OnFinalized`。玩家模块 `UGCPlayerScriptModule` 额外带 `PlayerKey`。

| 动作 | 服务器 | 客户端 |
|---|---|---|
| 注册 | `RegisterServerScriptModule`（全局）、`RegisterPlayerScriptModule` | `RegisterClientScriptModule`（全局）、`RegisterPlayerScriptModule` |
| 获取 | `GetScriptModule`（全局）、`GetPlayerScriptModule(PlayerKey, Name)` | `GetScriptModule`、`GetLocalPlayerScriptModule(Name)` |

### 假人与杂项

`SpawnFakePlayer(AIPlayerKey, TeamID, InFakePlayerClass)` 需要 GameMode 的 DataManager/AIProbe 数据中配置 AIController；`AIPlayerKey` 用 `GetRandomAIPlayerKey` 生成；`DestroyFakePlayer` 销毁。全部仅服务器。

`UGCMiscFunctionSystem.StartAirRoute` 开始航线飞行（服务器）。`StartAirDrop` 与 `StartNormalAirDrop` 已废弃，改用 `UGCAirDropManagerSystem`。

## 典型用法

### 1. 开火与无限子弹

参考 `../../../UGCProjects/Template_PlaygroundHub/Script/Blueprint/Prefabs/Buffs/Buff_InfBullet_Template.lua`：

```lua
local Weapon = UGCWeaponManagerSystem.GetWeaponBySlot(
    OwnerActor, ESurviveWeaponPropSlot.SWPS_MainShootWeapon1)
if Weapon then
    UGCGunSystem.EnableClipInfiniteBullets(Weapon, true)
    UGCGunSystem.EnableInfiniteBullets(Weapon, true)
end
```

客户端按住开火参考 `../../../UGCProjects/Withdraw/Script/Blueprint/BP_RightJoystick.lua`（`GetCurrentWeapon` + `StartFire`/`StopFire`）。

### 2. 切枪与武器组件

参考 `../../../UGCProjects/Withdraw/Script/Tool/Tool_Durability_Warning.lua`（`SwitchWeaponBySlot(pawn, slot, true)`）与 `../../../UGCProjects/Template_PlaygroundHub/Script/Blueprint/TriggerBox/BP_GunSingleExample.lua`（`GetWeaponManagerComponent` 后读组件数据）。

```lua
local Comp = UGCWeaponManagerSystem.GetWeaponManagerComponent(Pawn)
local Slot = UGCWeaponManagerSystem.GetCurrentWeaponSlot(Pawn)
UGCWeaponManagerSystem.SwitchWeaponBySlot(Pawn, Slot, true)
```

### 3. 配件

模板中未见直接调用，按存根使用（服务端）：

```lua
UGCGunSystem.CreateAndAddGunAttachment(Gun, ItemID)
local Ids = UGCGunSystem.GetWeaponAllAttachmentIDList(Gun)
UGCGunSystem.RemoveGunAttachmentBySocketType(
    Gun, EWeaponAttachmentSocketType.OpticalSight)
```

`GetAvailableWeaponAttachment` 要求武器已加载，不能在武器初始化阶段调用。

### 4. 实体范围检测

参考 `../../../UGCProjects/Withdraw/Script/Blueprint/BP_RightJoystick.lua`：

```lua
local Actors = UGCEntityTypeSystem.OverlapSphereByEntityType(
    self, "EntityType.Monster", PlayerLocation, 500)
```

### 5. 假人

```lua
local Key = UGCFakePlayerSystem.GetRandomAIPlayerKey()
UGCFakePlayerSystem.SpawnFakePlayer(Key, 1, FakePlayerControllerClass)
UGCFakePlayerSystem.DestroyFakePlayer(Key)
```

### 6. 航线与空投

参考 `../../../UGCProjects/Template_Ty_Forest/Script/GameMode/Action_StartAirDrop.lua`（旧空投调用）；新代码改用 `UGCAirDropManagerSystem`。航线直接 `UGCMiscFunctionSystem.StartAirRoute(WorldContext)`。

## 约束与坑

- `UGCGunSystem.StartFire` / `StopFire` / `Reload` / `OpenScope` 仅客户端；`Set*` 数值仅服务器；`Get*` 读取双端。客户端改数值不会生效。
- 配件相关接口均为服务端，`AddGunAttachment` 接收 `ItemDefineID`，`CreateAndAddGunAttachment` 接收 `ItemID`。
- `UGCWeaponManagerSystem` 同时支持普通玩家与人机玩家；`GetWeaponManagerComponent` 返回的是组件，不是武器。
- `UGCFakePlayerSystem` 仅服务器；假人控制器类必须与 GameMode 的 AIProbe/AIController 配置匹配。
- `UGCScriptModuleManager` 的模块配置项 `bEnableUpdate` 在存根中只标注为 `[Property]`，未说明具体语义；`Update` 是否被驱动以实现为准。
- 实体类型配置默认路径可用；改路径后必须 `ForceReloadConfig`，否则仍读旧配置。
- `UGCMiscFunctionSystem.StartAirDrop` / `StartNormalAirDrop` 已废弃，替代为 `UGCAirDropManagerSystem`。
- `UGCScriptModuleManager`、`UGCFakePlayerSystem` 在 `UGCProjects` 模板中未被直接调用；`UGCMiscFunctionSystem` 仅 `Template_Ty_Forest` 有一处旧空投调用；`UGCEntityTypeSystem` 仅在 `Withdraw` 出现一处。
- 存根只有签名，假人寻路/AI 行为与枪械实际数值由引擎配置决定。

## 相关

- [api-index.md](api-index.md)：全系统速查。
- [character.md](character.md)：玩家角色与控制器。
- [monster.md](monster.md)：怪物生成与 AI。
- [toolbox.md](toolbox.md)：Actor/组件与对象工具。
- `../Source/Lua/ugc/UGCAPI/UGCGunSystem.lua`、`UGCWeaponManagerSystem.lua`、`UGCEntityTypeSystem.lua`、`UGCScriptModuleManager.lua`、`UGCFakePlayerSystem.lua`、`UGCMiscFunctionSystem.lua`
- `../Source/ShadowTrackerExtra/Weapons/WeaponManagerComponent.lua`、`../Source/ShadowTrackerExtra/Player/PlayerTypeDefine.lua`
