# 载具

> 载具生成、进出、座位、血量/油量、载具武器与生命周期。对应 `UGCVehicleSystem`（V1）、`UGCVehicleSystemV2`（实验性）、`UGCVehicleSeatSystem`、`UGCVehicleCommonSystem`。

## 何时读

- 需要在运行时按蓝图路径生成载具，或销毁/重生载具。
- 要让玩家或 AI 进入、离开、换座位。
- 需要改载具血量、油量、轮胎血量或免伤/免油耗。
- 要操作车载武器、驾驶输入、手刹、加速、喇叭。
- 要区分 V1 与 V2 的座位编号和返回值，避免混用。

## API 一览

| System | 文件 | 状态 | 关键函数 | 生效范围 |
|---|---|---|---|---|
| UGCVehicleSystem | `UGCAPI/UGCVehicleSystem.lua` | 规范 | `SpawnVehicleNew`、`EnterVehicle`/`ExitVehicle`、`DestroySelf`、`Respawn`、`GetVehicleWeapon` | 生成/销毁/重生、`CharacterEnterVehicle`/`CharacterLeaveVehicle` 仅服务器；`EnterVehicle`/`ExitVehicle` 与查询双端；驾驶输入仅客户端 |
| UGCVehicleSystemV2 | `UGCAPI/UGCVehicleSystemV2.lua` | 实验性 | `SpawnVehicle`、`DestroyVehicle`、`EnterVehicle`/`LeaveVehicle`、`GetSeatDataByIndex`、`ChangePassengerSeat` | 生成/销毁/重生/座位数据仅服务器；进出与换座双端 |
| UGCVehicleSeatSystem | `UGCAPI/UGCVehicleSeatSystem.lua` | 规范 | `ChangePassengerSeat`、`ForceChangePassengerSeat`、`GetDriver`、`GetPassengers`、`GetAvailableSeatIndexes` | 查询双端；换座/武器配置以服务器为主 |
| UGCVehicleCommonSystem | `UGCAPI/UGCVehicleCommonSystem.lua` | 规范 | `SetVehicleHP`、`SetVehicleHPMax`、`SetVehicleFuelPercent`、`GetVehicleFuel`、`SetWheelHP` | 设置仅服务器；查询双端 |

- `UGCVehicleSystem` 共 45 个函数，其中唯一废弃项是 `SpawnVehicle`，替代为 `SpawnVehicleNew`。
- `UGCVehicleSystemV2` 24 个函数、`UGCVehicleSeatSystem` 14 个、`UGCVehicleCommonSystem` 12 个。

## 核心概念

### V1 与 V2 的选择

| 维度 | UGCVehicleSystem（V1） | UGCVehicleSystemV2（V2） |
|---|---|---|
| 状态 | 规范 | 实验性 |
| 生成 | `SpawnVehicleNew(VehicleBlueprintPath, Location, Rotation, SnapFloor, IsForce)` | `SpawnVehicle(VehiclePath, Location, Rotation, SnapFloor, IsForce)` |
| 座位编号 | 从 1 开始，配合 `ESTExtraVehicleSeatType` | 从 0 开始，`0` 为驾驶位，`-1` 表示任意空位 |
| 座位信息 | `GetOccupierBySeatIndex`、`GetVehicleSeatType` | `GetSeatDataByIndex` 返回 `UGCVehicleSeatData`（座位索引、乘客、是否司机位、能否探头、当前武器） |
| 进出 | `EnterVehicle(Pawn, Vehicle, SeatType, IsForce)` 双端 | `EnterVehicle(Player, Vehicle, SeatIndex, IsForce)`，客户端只能操作自己的角色 |
| 重生 | `Respawn` 无返回值 | `Respawn` 返回新载具，旧载具销毁；失败返回 nil 且不销毁旧车 |
| 类型查询 | `GetVehicleType` 返回 `ESTExtraVehicleType` | `GetVehicleType` 返回 `ESTExtraVehicleBaseType` |
| 武器 | `GetVehicleWeapon(SeatIndex, WeaponID)`、`GetAllVehicleWeaponList`、Start/Stop | 仅 `StartFireVehicleWeapon(Vehicle)` |

新代码优先 V2；需要按座位类型进入、读具体车型、逐把操作车载武器时仍要用 V1 或座位系统补足。两者可以并存，但不要用 V2 的 0 基座位号去调 V1 的 1 基接口。

### 生成与生命周期

| 阶段 | API | 说明 |
|---|---|---|
| 生成 | `SpawnVehicleNew` / V2 `SpawnVehicle` | 服务器；按蓝图路径生成，`SnapFloor` 贴地，`IsForce` 无视碰撞 |
| 传送 | `UGCVehicleSystem.TeleportVehicleTo` | 服务器；生成后不要立刻传送，等落地停稳 |
| 行驶 | `GetForwardSpeed` / V2 `GetVelocity`、`IsStoped`、`IsEngineStarted` | 双端读 |
| 受伤 | `SetVehicleHP`、`GetVehicleHealthState` | 健康状态 `VHS_Good` / `VHS_Smoking` / `VHS_Burning` / `VHS_Destroyed` |
| 摧毁 | `DestroySelf` / V2 `DestroyVehicle` | 服务器 |
| 重生 | `Respawn` | 服务器；注意 V1/V2 返回值差异 |

- 生成后立即改位置会失败，尤其是 `Spawn` 后马上 `TeleportVehicleTo`；需要精确落点时直接按目标点生成。
- V2 `Respawn` 会创建新载具并销毁旧载具，旧引用不可再用。

### 座位模型

- `UGCVehicleSeatSystem`：`GetSeatNum`、`GetAvailableSeatNum`、`GetPassenger`、`IsSeatIndexAvailable`、`GetCharacterSeatIndex`、`GetDriver`、`GetPassengers`、`GetAvailableSeatIndexes`、`CanLeanOut`。
- 换座：目标空位用 `ChangePassengerSeat`（双端）；目标有人用 `ForceChangePassengerSeat`（服务器）。
- V2 换座：`ChangePassengerSeat(Player, SeatIndex)`，客户端只能指定空位，服务器可指定有人座位并交换。
- V1 进座用 `ESTExtraVehicleSeatType`：`ESeatType_DriversSeat`、`ESeatType_PassengersSeat`、`ESeatType_FreeFiringLeftSeat`、`ESeatType_FreeFiringRightSeat`、`ESeatType_GunnerSeat` 等，定义在 `../Source/ShadowTrackerExtra/Vehicle/VehicleSeatComponent.lua`。

### 血量、油量与伤害

- `UGCVehicleCommonSystem.SetVehicleHPMax` 只改上限，不会自动改当前血量；改当前血量用 `SetVehicleHP`。
- 油量：`SetVehicleFuelPercent`（服务器，按百分比）、`GetVehicleFuel`、`GetVehicleFuelMax`、`GetVehicleFuelConsumeFactor`、`IsDontConsumeFuel`。
- 轮胎：`GetWheelHP`（双端）、`SetWheelHP`（服务器）；V1 另有 `IsWheelDamageable` / `SetWheelDamageable`（服务器）。
- 免伤：`UGCVehicleCommonSystem.IsDontDamage`（双端）；V2 用 `CanDamage` / `SetCanDamage`（服务器）。

### 爆炸

- UGCAPI 没有独立的“引爆载具”函数。业务上通常把血量打到 0，再按 `ESTExtraVehicleHealthState.VHS_Destroyed` 处理，或直接 `DestroySelf` / `DestroyVehicle`。
- 底层载具基类 `../Source/ShadowTrackerExtra/Vehicle/STExtraVehicleBase.lua` 提供：
  - `ASTExtraVehicleBase.UGC_OnVehicleExplosionDelegate`（字段注释标 `生效范围S 载具爆炸事件`）。
  - `ASTExtraVehicleBase:VehicleSelfExplode(bShouldCauseExplodeDamage)`。
- `../Source/ShadowTrackerExtra/Vehicle/VehicleDamageComponent.lua` 的 `UVehicleDamageComponent` 含 `ExplosionBaseDamage`、`ExplosionRadiusInner`、`ExplosionRadiusOuter`、`ExplosionDamageFalloff`、`bServerDoVehicleExplosion` 等爆炸参数。
- 这些属于游戏本体内层层，不是 `UGCAPI` 创作者接口；跨版本可用性需自行验证。

### 载具武器

- 武器由座位配置决定：`GetVehicleWeapon(Vehicle, SeatIndex, WeaponID)`，座位与武器 ID 都从 1 开始；`GetAllVehicleWeaponList` 返回全部武器。
- V1 开火/停火仅客户端，且仅驾驶位车载武器生效：`StartFireVehicleWeapon(Vehicle, VehicleWeapon, Character)`，`Character` 传 nil 视为 Driver；`StopFireVehicleWeapon` 同理。
- V2 只有 `StartFireVehicleWeapon(Vehicle)`（客户端，仅驾驶位），没有对应的 Stop。
- 座位武器库：`AddVehicleWeaponFromSupportKit`、`RemoveVehicleWeapon`、`SetPassengerVehicleWeapon` 均为服务器；前两者要求座位原本配置了武器且武器未在使用中，`SetPassengerVehicleWeapon` 要求乘客正在该座位上。
- 武器类：`AVehicleShootWeapon`（`../Source/ShadowTrackerExtra/Vehicle/VehicleModify/VehicleWeapon/VehicleShootWeapon.lua`），UGC 包装为 `AUGCVehicleShootWeapon`（`../Source/UGCGame/Weapons/UGCVehicleShootWeapon.lua`）。

### 载具蓝图与模板类

- 原生车型存根：`../Content/Arts_PlayerBluePrints/Vehicle/`，21 个一级车型目录、37 个蓝图类存根，含 Buggy、Dacia、UAZ01、Motorcycle、PG117、AquaRail、ArmedVehicle 下的 4 个武装型号等。
- UGC 模板载具：`../Content/UGC/UGCGame/Vehicle/VehicleTemplate/`，共 29 个类：`GroundVehicles` 23、`WaterVehicles` 2、`WeaponsVehicles` 4。类名形如 `UGC_Buggy_C:BP_VH_Buggy_C`、`UGC_Buggy_Armed_C:ArmedBuggy_C`、`UGC_PG117_C:VH_PG117_C`。
- `SpawnVehicleNew` / V2 `SpawnVehicle` 的路径格式示例（来自 API 注释）：`/Game/Arts_PlayerBluePrints/Vehicle/VH_Buggy/BP_VH_Buggy.BP_VH_Buggy_C`。实际工程资产路径需以工程内蓝图为准。

### 辅助类型

| 文件 | 内容 |
|---|---|
| `../Source/UGCGame/Vehicle/UGCVehicleFunctionLibrary.lua` | `UUGCVehicleFunctionLibrary:EnterVehicle(PC, Vehicle, SeatIndex, IsForce)`、`LeaveVehicle(PC, IsForce)` |
| `../Source/UGCGame/Vehicle/UGCVehicleComponent.lua` | `UUGCVehicleComponent`、`UUGCWheeledVehicleComponent`、`UUGCFloatingVehicleComponent` 及引擎/转向/轮胎/差速器/武器/座位 DataAsset |
| `../Source/UGCGame/Vehicle/UGCVehicleSeatComponent.lua` | `UUGCVehicleSeatComponent` |
| `../Source/UGCGame/Vehicle/UGCVehicleRefresher.lua` | `AUGCVehicleRefresher` |
| `../Source/Gameplay/Public/RacingTrack/RacingTrack.lua` | `ARacingTrack:PreStartRace` / `StartRace`、`RaceTotalTime` |
| `../Source/Gameplay/Public/RacingTrack/RacingCheckPoint.lua` | `ARacingCheckPoint`、`FCheckPointArea`、`FPlayerCheckPointRecordUpdate` |

## 典型用法

| 需求 | 推荐 API | 参考 |
|---|---|---|
| 按路径生成载具 | `UGCVehicleSystem.SpawnVehicleNew` 或 V2 `SpawnVehicle` | API 注释中的 Buggy 路径示例 |
| 玩家上下车 | V2 `EnterVehicle` / `LeaveVehicle` | 客户端只操作自己 |
| AI 驾驶 | 蓝图 `STExtraVehicleAIController` + `Possess` | `../../../UGCProjects/Template_RacingCar/Script/Blueprint/AutoDrive/BP_RCVehicleAIController.lua` |
| 竞速生成车辆 | `ScriptGameplayStatics.SpawnActor` + `GameState.CarList` | `../../../UGCProjects/Template_RacingCar/Script/Blueprint/UGCPlayerController.lua`、`.../AutoDrive/BP_RCVehicleAIManager.lua` |
| 改血量/油量 | `UGCVehicleCommonSystem` | 无模板直接示例 |
| 座位查询/换座 | `UGCVehicleSeatSystem` 或 V2 座位数据 | 无模板直接示例 |
| 车载武器 | `GetVehicleWeapon` + `StartFireVehicleWeapon` | 无模板直接示例 |

> 在 `UGCProjects/` 下 `grep UGCVehicleSystem`、`UGCVehicleSystemV2`、`UGCVehicleCommonSystem`、`UGCVehicleSeatSystem` 均无匹配：模板未直接使用这四套载具 API。`Template_RacingCar` 的载具来自蓝图类与 `ScriptGameplayStatics.SpawnActor`，不是 `UGCVehicleSystem`。

```lua
local vehicle = UGCVehicleSystem.SpawnVehicleNew(
    "/Game/Arts_PlayerBluePrints/Vehicle/VH_Buggy/BP_VH_Buggy.BP_VH_Buggy_C",
    location, rotation, true, false)
UGCVehicleCommonSystem.SetVehicleHP(vehicle, 1000)
```

```lua
local vehicle = UGCVehicleSystemV2.SpawnVehicle(vehiclePath, location, rotation, true, false)
local seat = UGCVehicleSystemV2.GetSeatDataByIndex(vehicle, 0)
UGCVehicleSystemV2.EnterVehicle(player, vehicle, -1, false)
```

```lua
local weapon = UGCVehicleSystem.GetVehicleWeapon(vehicle, 1, 1)
UGCVehicleSystem.StartFireVehicleWeapon(vehicle, weapon, nil)
UGCVehicleSystem.StopFireVehicleWeapon(vehicle, weapon)
```

## 约束与坑

- V2 标注为 `【实验性】`，接口可能变化；V1 是 `【规范】`，但 `SpawnVehicle` 已废弃，生成只能用 `SpawnVehicleNew`。
- V1 座位号从 1 开始，V2 从 0 开始；V2 `-1` 表示任意空位。混用会进错座或返回 nil。
- V2 的 `EnterVehicle` / `LeaveVehicle` 在客户端只能操作自己的角色，`IsForce` 仅服务器调用有效，客户端返回值无意义。
- V2 `ChangePassengerSeat` 客户端只能指定空位；服务器才能和有人的座位交换。
- V1 `EnterVehicle` / `ExitVehicle` 双端可用且只支持普通玩家角色；`CharacterEnterVehicle` / `CharacterLeaveVehicle` 仅服务器。
- 生成后不要立刻改位置或传送，等落地停稳；精确落点应在生成时给。
- `SetVehicleHPMax` 不改当前血量；`SetVehicleHP`、`SetVehicleFuelPercent`、`SetWheelHP`、`DestroySelf`、`Respawn` 都是服务器接口。
- V2 `Respawn` 返回新车并销毁旧车；V1 `Respawn` 无返回值。成功后旧引用必须替换。
- 车载武器开火是客户端接口且仅驾驶位；V2 只有 Start 没有 Stop。
- `PlayMusic` 双端但武装载具不支持；`MusicIndex` 范围 [1,8]，`StopMusic` 仅服务器。
- V1 `CanDriverUsingHorn` 在服务器，`StartHorn` / `StopHorn` 在客户端；判断与执行不在同一端。
- 驾驶输入 `MoveForward`、`StartBrake`、`StartBoosting`、`StartHorn` 等都要在驾驶员客户端每帧/按下抬起时调用，服务器调用无效。
- UGCAPI 未封装爆炸；`VehicleSelfExplode`、`UGC_OnVehicleExplosionDelegate` 属于 `ShadowTrackerExtra` 内层，不是稳定创作者接口。

## 相关

- `api-index.md`
- `scene.md`（场景查询、导航、地图标记）
- `character.md`（玩家与 AI Pawn）
- `../Source/Lua/ugc/UGCAPI/UGCVehicleSystem.lua`、`UGCVehicleSystemV2.lua`、`UGCVehicleSeatSystem.lua`、`UGCVehicleCommonSystem.lua`
- `../Content/Arts_PlayerBluePrints/Vehicle/`、`../Content/UGC/UGCGame/Vehicle/VehicleTemplate/`
- `../Source/ShadowTrackerExtra/Vehicle/STExtraVehicleBase.lua`、`VehicleDamageComponent.lua`、`VehicleSeatComponent.lua`
- 模板：`../../../UGCProjects/Template_RacingCar/`
- 工程指南：`../../../UGCProjects/Docs/project-guide.md`
