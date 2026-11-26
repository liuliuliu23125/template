# 场景与环境

> 关卡流、天气、导航、环境查询、物理重叠，以及信号圈 / 空投 / 轰炸区 / EMP / 地图标记等战场区域能力。对应 `UGCLevelFlowSystem`、`UGCWeatherSystem`、`UGCNavigationSystem`、`UGCSceneQueryUtility`、`UGCPhysicsUtility`、`UGCCircleManagerSystem`、`UGCAirDropManagerSystem`、`UGCMapMarkManagerSystem`、`UGCAirAttackSystem`、`UGCEMPZoneSystem`。

## 何时读

- 做多关卡闯关、副本推进、按队伍结算。
- 需要切换天气、昼夜或调整天气播放进度。
- 运行时生成导航图、找地面可达点、判断导航是否构建完成。
- 做技能命中、拾取可见性、屋顶遮挡、生成点合法性等射线/范围检测。
- 需要触发区重叠回调，或对物理物施加力/冲量。
- 控制信号圈、空投、轰炸区、电磁干扰区，或在大小地图上打标记。

## API 一览

| System | 文件 | 状态 | 关键函数 | 生效范围 |
|---|---|---|---|---|
| UGCLevelFlowSystem | `UGCAPI/UGCLevelFlowSystem.lua` | 规范 | `EnableLevelFlow`、`GoToNextLevelForAllPlayers`、`LevelSettle`、`GameSettle`、`GetCurrentLevelStage` | 服务器；`GetCurrentLevelStage` 双端 |
| UGCWeatherSystem | `UGCAPI/UGCWeatherSystem.lua` | 规范 | `LoadWeatherSequence`、`SeekWeatherSequence`、`PauseWeatherSequence`、`GetCurrentWeatherTime` | 加载/卸载仅服务器；查询与播放控制双端 |
| UGCNavigationSystem | `UGCAPI/UGCNavigationSystem.lua` | 规范 | `BuildNavmesh`、`AsyncBuildNavmesh`、`ProjectPointToNavigation`、`GetRandomReachablePointInRadius`、`IsNavigationBeingBuilt` | 服务器 |
| UGCSceneQueryUtility | `UGCAPI/UGCSceneQueryUtility.lua` | 规范 | `QueryByLine*`、`QueryBySphere*`、`QueryByBox*`、`QueryByCapsule*`、`QueryOverlapActorsBySphere*`、`QueryBlocksByChannel` | 存根未标注，按调用端使用 |
| UGCPhysicsUtility | `UGCAPI/UGCPhysicsUtility.lua` | 实验性 | `AddBeginOverlapDelegate`、`GetOverlappingActors`、`ApplyImpulse`、`SetSimulatePhysics` | 双端 |
| UGCCircleManagerSystem | `UGCAPI/UGCCircleManagerSystem.lua` | 规范 | `StartCircle`、`StopCircle`、`PauseCircle`、`GetBlueCircleCenter`、`GetCurrentCircleIndex` | 圈中心/半径双端；启停与配置仅服务器 |
| UGCAirDropManagerSystem | `UGCAPI/UGCAirDropManagerSystem.lua` | 规范 | `GenerateAirDrop`、`DestroyAirDrop`、`GetAirDropItemList`、`GetAllAirDropInstanceIDs` | 服务器 |
| UGCMapMarkManagerSystem | `UGCAPI/UGCMapMarkManagerSystem.lua` | 规范 | `AddCustomMark`、`AddLocalCustomMark`、`AddPlayerMark`、`UpdateMarkLocation`、`MakeMapMarkGraph` | 创建分端：`AddCustomMark`/`AddPlayerMark` 服务器，`AddLocal*` 客户端；更新/删除双端；画图仅客户端 |
| UGCAirAttackSystem | `UGCAPI/UGCAirAttackSystem.lua` | 规范 | `GenerateBombingArea`、`StopBombingArea`、`ModifyBombingAreaConfig`、`GetAirAttackManager` | 服务器；`GetAirAttackManager` 双端 |
| UGCEMPZoneSystem | `UGCAPI/UGCEMPZoneSystem.lua` | 规范 | `GenerateElectromagneticArea`、`DestroyElectromagneticArea`、`ModifyConfigElectromagneticArea`、`GetEMPZoneManager` | 服务器；`GetEMPZoneManager` 双端 |

> `UGCAPI/UGCAirAttackSystem.lua` 内声明的类名是 `UGCAirAttachSystem`（拼写与文件名不同），搜代码时以类名为准。

## 核心概念

### 关卡流与子关卡

| 环节 | API | 说明 |
|---|---|---|
| 启用 | `UGCLevelFlowSystem.EnableLevelFlow(InMgrPath)` | 注册 `GameModeActorMgr` 路径，服务器 |
| 推进 | `GoToNextLevelForAllPlayers` / `GoToNextLevelForOnePlayer` | 需满足通关条件；前者要求全队/全员 |
| 结算 | `LevelSettle(TeamID, IsFinish)` / `GameSettle(IsFinish)` | 服务器 |
| 查询 | `GetCurrentLevelStage(PC)`、`GetTotalLevelCount()`、`GetAllPlayerControllerInCurrentLevel()` | `GetTotalLevelCount` 不支持随机切关 |

- 子关卡的加载/卸载不走 `UGCLevelFlowSystem`，而用 `UGCGameSystem.LoadStreamLevel(LevelName, bMakeVisibleAfterLoad, bShouldBlockOnLoad, LatentInfo)` 与 `UGCGameSystem.UnloadStreamLevel(LevelName, LatentInfo)`，双端可用，详见 `gameplay-rules.md`。
- Withdraw 在流关卡 `IsLevelLoaded() && IsLevelVisible()` 后才异步构建导航，避免在未加载的几何体上烘图。

### 天气序列

- `WeatherSequence` 实参类型是 `UWeatherSequence`（`UDataAsset`），字段含 `WeatherSequenceConfig`、`TimelineEventConfig`、`Priority`、`Type`、`bUseCirculation`、`DefaultPlaybackPosition` 等，定义在 `../Source/ShadowTrackerExtra/Weather/WeatherSequence.lua`。
- 所有接口都以 `PlayerController` 为粒度：加载/卸载仅服务器，`Seek/Pause/Resume` 与查询双端。
- `GetCurrentWeatherTime` 返回 0–24，`GetCurrentWeatherPlayPercentage` 返回 0–1。

### 环境查询族系

| 形状 | 单目标 | 多目标 | 指定 ObjectTypes |
|---|---|---|---|
| 射线 | `QueryByLineSingle` | `QueryByLineMulti` | `QueryByLineMultiForObjects` |
| 球体 | `QueryBySphereSingle` | `QueryBySphereMulti` | `QueryBySphereMultiForObjects` |
| 盒子 | `QueryByBoxSingle` | `QueryByBoxMulti` | `QueryByBoxMultiForObjects` |
| 胶囊 | `QueryByCapsuleSingle` | `QueryByCapsuleMulti` | — |
| 重叠 | `QueryOverlapActorsBySphere`、`QueryOverlapActorsBySphereWithFinder` | — | — |

- `ESceneQueryType` 提供 `Teleport`、`PlayerPawn`、`Bullet`、`PlayerApplyDamage`、`BotApplyDamage`、`STEMesh`、`PropMesh`、`Footstep`、`WheelCollision`、`AutoAim`、`Projectile`、`SpreadingBlockerOverlap` 等 18 种查询语义，完整列表见文件头部。
- `QueryByLineWithChannel` 的参数顺序特殊：`OutHit` 在第一位，随后才是 `ContextObject`、`Start`、`End`、`IgnoreActors`、`TraceChannel`。
- `FindPositionToHoldCapsule` 从目标点按八方向迭代，找一个能容纳胶囊的位置。

### 物理重叠与受力

- `UGCPhysicsUtility` 全部为 `【实验性】`，双端可用。
- 事件绑定：`AddBeginOverlapDelegate` / `AddEndOverlapDelegate`，移除用同名 `Remove*`；双方组件都要开启重叠事件。
- 查询：`GetOverlappingActors(Actor, ActorClassFilter)` 返回当前接触的 Actor。
- 开关：`SetOverlapEventsEnabled`、`SetActorCollisionEnabled`、`SetSimulatePhysics`；编辑器新建组件默认关闭重叠事件。
- 物理：`ApplyForce`、`ApplyImpulse`、`ApplyImpulseAtLocation`、`ApplyAngularImpulse`，以及 `Get/SetLinearVelocity`、`Get/SetAngularVelocity`、`Get/SetMass`。

### 战场区域

| 能力 | 控制端 | 关键约束 |
|---|---|---|
| 信号圈 | 服务器 | 蓝圈为当前伤害圈、白圈为下一安全圈；启停/暂停/配置仅服务器，中心与半径可双端读 |
| 空投 | 服务器 | `GenerateAirDrop(ID, DroppingLocation, DroppingSpeed)` 返回实例 ID；`DestroyAirDrop` 延迟约 0.1s 销毁 |
| 轰炸区 | 服务器 | `GenerateBombingArea` 会用射线把中心修正到地面；`ModifyBombingAreaConfig` 按参数名改配置 |
| EMP | 服务器 | 生成/销毁/改配置仅服务器，`GetEMPZoneManager` 可双端取管理器绑事件 |

- 空投另有旧接口 `UGCMiscFunctionSystem.StartAirDrop`，已标注 `【废弃】请使用 UGCAirDropManagerSystem`。`Template_Ty_Forest` 仍调用旧接口。

### 地图标记

- 静态/自定义标记：服务器 `AddCustomMark(WidgetClassPath, RangeType, RangeRad, OwnerPlayerState)`，客户端 `AddLocalCustomMark(WidgetClassPath, RangeRad)`。
- 跟随玩家的动态标记：服务器 `AddPlayerMark`，客户端 `AddLocalPlayerMark`；Widget 需分别继承 `MapUIMarkBaseWidget` / `UGCMapUIMarkDynamicWidget`。
- 标记生命周期由返回的 `MarkID` 串起来：`UpdateMarkLocation` / `UpdateMarkRotation` / `GetMarkLocation` / `GetMarkRotation` / `GetMarkOwner` / `RemoveMark` 都要求调用者与 `InstanceID` 匹配，通常在同一端完成创建和后续操作。
- 必须至少调用一次 `UpdateMarkLocation`，`GetMarkLocation` / `GetMarkRotation` 才有效。
- `MakeMapMarkGraph`、`ClearMapMarkGraph`、`ChangeMapByMapID`、`DrawGuidePathToTarget` 仅客户端；`MakeMapMarkGraph` 按点数画圆/直线/多边形，`AddMarkFlag` 决定小地图、全图或两者。

## 典型用法

| 需求 | 推荐 API | 参考模板 |
|---|---|---|
| 多关卡闯关 | `EnableLevelFlow` → `GoToNextLevelForAllPlayers` / `LevelSettle` | `../../../UGCProjects/Template_RogueShooting/Script/Blueprint/UGCGameMode.lua`、`.../Blueprint/PortalDoor/PortalDoor.lua` |
| 队伍/单人结算与阶段查询 | `LevelSettle`、`GameSettle`、`GetCurrentLevelStage` | `../../../UGCProjects/Template_RogueShooting/Script/Blueprint/UGCGameState.lua`、`.../GameModeActor/SingleMode/SingleModeSettlement.lua` |
| 流关卡后构建导航 | `AsyncBuildNavmesh`、`GetNavigationGenerationFinishedDelegate`、`IsNavigationBeingBuilt` | `../../../UGCProjects/Withdraw/Script/Package/GameMode/System/System_GameMode.lua` |
| 生成点/掉落点找可达位置 | `QueryByLineWithChannel`、`ProjectPointToNavigation`、`GetRandomReachablePointInRadius` | `../../../UGCProjects/Withdraw/Script/Tool/Tool_SpawnNavigation.lua` |
| 屋顶遮挡/视线检测 | `QueryByLineWithChannel` | `../../../UGCProjects/Withdraw/Script/Tool/Tool_RoofVisibility.lua` |
| 范围伤害/技能区域 | `QueryOverlapActorsBySphereWithFinder`、`QueryByBoxMultiForObjects` | `../../../UGCProjects/Template_RogueShooting/Script/Blueprint/Prefabs/Regions/Skill1Poison1.lua`、`.../Prefabs/Regions/hero1skill1regions.lua` |
| 信号圈开关 | `StartCircle` / `TogglePoisonCircle` | `../../../UGCProjects/Template_PlaygroundHub/Script/Blueprint/UGCPlayerController.lua`、`../../../UGCProjects/Template_Ty_Forest/Script/GameMode/Action_TogglePoisonCircle.lua` |
| 小地图任务标记 | `AddLocalCustomMark` → `UpdateMarkLocation` → `RemoveMark` | `../../../UGCProjects/Template_TaskAndStory/Script/Blueprint/NPC/Talk/TalkNPC.lua`、`.../Blueprint/UGCPlayerController.lua` |

```lua
UGCLevelFlowSystem.EnableLevelFlow(
    UGCGameSystem.GetUGCResourcesFullPath(UGCGameData.GetGameModeActorMgrConfig(ModeID)))
UGCLevelFlowSystem.GoToNextLevelForAllPlayers()
```

```lua
if UGCNavigationSystem.IsNavigationBeingBuilt(spawner) then return nil, "NavBuilding" end
local ok, seed = UGCNavigationSystem.ProjectPointToNavigation(spawner, ground, extent)
local found, point = UGCNavigationSystem.GetRandomReachablePointInRadius(spawner, seed, range)
```

```lua
local id = UGCMapMarkManagerSystem.AddLocalCustomMark(WidgetPath, 1000000)
UGCMapMarkManagerSystem.UpdateMarkLocation(id, self:K2_GetActorLocation())
UGCMapMarkManagerSystem.RemoveMark(id)
```

## 约束与坑

- `UGCLevelFlowSystem` 除 `GetCurrentLevelStage` 外都是服务器接口；客户端只读阶段，不要尝试推进关卡或结算。
- `GetTotalLevelCount` 在随机切换关卡时不准确，需要玩法侧自行记录。
- 导航接口全部服务器；`BuildNavmesh` 同步构建会阻塞服务器，优先 `AsyncBuildNavmesh`。只改局部时可 `AddDynamicNavAffect` + `AsyncIncrementalBuild`。
- 导航构建完成回调是 Delegate；Withdraw 同时用 `IsNavigationBeingBuilt` 兜底，因为同步完成或回调丢失都可能发生。
- `UGCSceneQueryUtility` 存根没有 `---生效范围` 标注，不能想当然当服务器接口用；模板在双端都有调用，按实际调用点判断。
- `QueryByLineWithChannel` 第一个参数是输出用的 `FHitResult` 表，传参顺序写错会静默失败。
- `UGCPhysicsUtility` 是实验性接口；重叠事件要求双方组件都开启，UGC 编辑器新建组件默认关闭。
- `UGCCircleManagerSystem.TogglePoisonCircle` 不接受参数，调用一次即翻转状态；`Template_Ty_Forest` 多传的 `true` 不会生效，需要确定开关时用 `StartCircle` / `StopCircle`。
- `Template_FourMaps` 的信号圈走旧蓝图库 `UGCBlueprintFunctionLibrary.TogglePoisonCircle`，不是 `UGCCircleManagerSystem`。
- 空投优先 `UGCAirDropManagerSystem`；`UGCMiscFunctionSystem.StartAirDrop` / `StartNormalAirDrop` 已废弃。
- 地图标记的更新/删除必须与创建端和 `InstanceID` 匹配；跨端操作无效。未 `UpdateMarkLocation` 前 `GetMarkLocation` 无意义。
- 轰炸区中心会自动做地面修正，不要先自己算地形高度；EMP 和轰炸区模板均未直接使用。

## 相关

- `api-index.md`
- `gameplay-rules.md`（`UGCGameSystem.LoadStreamLevel` / `UnloadStreamLevel`）
- `../Source/Lua/ugc/UGCAPI/` 下各 System 文件
- 辅助类型：`../Source/UGCGame/Minimap/UGCMinimapManager.lua`（地图标记显隐等委托）、`../Source/UGCGame/PostProcess/UGCPostProcessUtils.lua`（滤镜工具）
- 模板：`../../../UGCProjects/Template_RogueShooting/`、`../../../UGCProjects/Withdraw/`、`../../../UGCProjects/Template_Ty_Forest/`、`../../../UGCProjects/Template_PlaygroundHub/`
- 工程指南：`../../../UGCProjects/Docs/project-guide.md`
