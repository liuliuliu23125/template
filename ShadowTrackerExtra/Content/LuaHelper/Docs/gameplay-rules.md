# 玩法规则与流程

> 一局玩法的生命周期、玩家身份链、伤害/复活/结算、定时器、GameplayTag、异步任务与多模式匹配。主要系统：`UGCGameSystem`、`UGCGameplayTaskSystem`、`UGCGameplayTagSystem`、`UGCTimeSystem`、`UGCMultiMode`、`UGCRankSystem`、`UGCGameSettingSystem`。

## 何时读

- 要在一局内按 UID / PlayerKey / Controller / Pawn / PlayerState 互相查找玩家。
- 要接入 GameMode/GameState 初始化、玩家进入/离开、淘汰、复活、观战、结算与 DS 关闭。
- 要造成伤害、生成 Actor、发 TLog、开定时器、读写 GameplayTag。
- 要用 `UGCGameplayTaskSystem` 做传送、冲刺、切武器、自动瞄准等异步玩法任务。
- 要做关卡流、多模式匹配、段位分或设备/画质适配。

## API 一览

| System | 文件 | 状态 | 关键函数 | 生效范围 |
|---|---|---|---|---|
| UGCGameSystem | UGCAPI/UGCGameSystem.lua | 规范；10 个函数废弃 | `GetAllPlayerController` / `GetPlayerPawnByUID` / `ApplyDamage` / `SetTimer` / `GameOver` | 按函数区分，查找类多为双端 |
| UGCGameSettingSystem | UGCAPI/UGCGameSettingSystem.lua | 规范 | `GetDeviceLevel` / `GetRenderQualitySetting` / `AllowSoftwareOcclusion` | 客户端 |
| UGCGameplayTaskSystem | UGCAPI/UGCGameplayTaskSystem.lua | 规范 | `*NewTask` / `EndTask` | 按任务区分服务器/客户端 |
| UGCGameplayTagSystem | UGCAPI/UGCGameplayTagSystem.lua | 规范 | `RequestGameplayTag` / `MatchesTag` / `HasTag` | 服务器&客户端 |
| UGCTimeSystem | UGCAPI/UGCTimeSystem.lua | 规范 | `Now` / `GetDate` / `GetTimestamp` / `GetWeekDay` | 服务器&客户端 |
| UGCMultiMode | UGCAPI/UGCMultiMode.lua | 规范 | `GetModeID` / `GetModeSetting` / `RequestMatch` | 客户端为主，部分服务器 |
| UGCRankSystem | UGCAPI/UGCRankSystem.lua | 规范 | `GetUGCRank` / `AddRankProgress` / `GetUGCGameSeasonId` | 服务器 |
| UGCLevelFlowSystem | UGCAPI/UGCLevelFlowSystem.lua | 规范 | `EnableLevelFlow` / `GoToNextLevelForAllPlayers` / `GameSettle` | 服务器为主；`GetCurrentLevelStage` 双端 |

## 核心概念

### 一局流程

| 阶段 | 入口/回调 | 要点 |
|---|---|---|
| 初始化 | GameMode/GameState 的 `ReceiveBeginPlay` | `UGCGameSystem.GameMode` 仅服务器；`GameState` 双端；`IsServer()` 依赖 GameState，初始化前判断不可靠 |
| 玩家进入 | `AUGCGameModeBase:UGC_PlayerPreLoadingEvent` → `UGC_PlayerLoginEvent` | PreLoading 时 PC 尚未创建；Login 时 PC 与玩家数据已就绪 |
| Pawn 复活 | `UGC_PlayerRespawnEvent`；全局消息 `UGC.PlayerPawn.PawnRespawn` | 复活时触发；工程常在此重绑 HUD/组件，首次出生是否触发以实际事件为准 |
| 淘汰 | `UGC_PlayerKilledEvent`；消息 `UGC.PlayerPawn.PawnDefeat`、`UGC.MobPawn.PostBeKilled` | 玩家淘汰事件给 Killer/Victim Controller 与 DamageType；`PostBeKilled` 是怪物死亡（Rogue 用于加经验） |
| 离开 | `UGC_PlayerExitEvent` | PC、Pawn、PlayerState 即将销毁，此时做清理 |
| 结算/关闭 | `SetTournamentInfo` / 段位接口 → `GameOver` | `SendPlayerSettlement` 已废弃，退出/关闭 DS 时自动发送；客户端返回大厅用 `ReturnToLobby`，DS 关闭后客户端断链用 `DisconnectClient` |
| 观战 | `EnterSpectating` / `ChangeOBPlayer` / `IsObserver` | `EnterSpectating`、`ChangeOBPlayer` 仅服务器；`IsObserver` 双端；可观战列表用 `ChangeAllowOBPlayerKeys` |
| 人机 | `UGC_SpawnedAIEvent` / `GetAllAIController` | 人机的 Controller 是 `AIController`，仍可参与 PlayerKey 查找 |

工程常用全局消息（`UGCGenericMessageSystem.Messages`）：`UGC.Game.GameStart`、`UGC.Game.GameEnd`、`UGC.LevelFlow.LevelBegin`、`UGC.Player.PlayerEnter`、`UGC.PlayerPawn.PawnRespawn`、`UGC.PlayerPawn.PawnDefeat`。

### 玩家身份链与通用查找

`UID`（账号） ↔ `PlayerKey`（局内唯一，含人机） ↔ `{PlayerController, PlayerPawn, PlayerState}`。

| 目标 | 函数 | 限制 |
|---|---|---|
| UID → PlayerKey | `GetPlayerKeyByUID` | 双端；无效返回 -1 |
| PlayerKey → UID | `GetUIDByPlayerKey` | 存根标注返回 `string`，且经 Pawn 反查，敌人 Pawn 死亡时可能不全 |
| PlayerKey → PC/Pawn/State | `GetPlayerControllerByPlayerKey` / `GetPlayerPawnByPlayerKey` / `GetPlayerStateByPlayerKey` | Pawn 接口不会拿到尸体；State 在客户端仅队友 |
| PC/Pawn/State → PlayerKey | `GetPlayerKeyByPlayerController` / `GetPlayerKeyByPlayerPawn` / `GetPlayerKeyByPlayerState` | 双端；无效返回 -1 |
| UID → PC | `GetPlayerControllerByUID` | 仅服务器 |
| UID → Pawn/State | `GetPlayerPawnByUID` / `GetPlayerStateByUID` | Pawn 双端可拿敌人；State 客户端仅队友 |
| 全量列表 | `GetAllPlayerController` / `GetAllPlayerPawn` / `GetAllPlayerState` / `GetAllPlayerKey` / `GetAllUID` | 客户端 PC 仅自己；State 仅队友；Pawn 全量；Key/UID 经 Pawn 反查，敌人无 Pawn 时不全 |
| 本地玩家 | `GetLocalPlayerController` / `GetLocalPlayerPawn` / `GetLocalPlayerState` / `GetLocalPlayerKey` | 仅客户端 |
| 人机 | `GetAIControllerByPlayerKey` / `GetAllAIController` | 服务器 |

> 这里只讲跨对象查找；Pawn/Controller/State 自身能力见 `character.md`。`GetAllPlayer*` 的 `NotIgnorePureSpectator` 用于是否包含全局观战者。

### 伤害

| 接口 | 适用 | 返回 |
|---|---|---|
| `ApplyDamage(DamagedActor, BaseDamage, EventInstigator, DamageCauser, DamageTypeTags)` | 通用点伤害 | 实际伤害 |
| `ApplyPointDamage(..., HitFromDirection, HitInfo, ...)` | 带命中信息的射击/抛体 | 实际伤害 |
| `ApplyAvatarPositionDamage(..., AvatarDamagePosition, ...)` | 指定部位 | 实际伤害 |
| `ApplyRadialDamage(...)` / `ApplyRadialDamageWhiteList(...)` | 爆炸范围，内圈满伤、外圈衰减 | 是否造成伤害 |
| `AddUGCCustomDamageNumber` | 客户端自定义伤害数字 | 无 |

伤害接口均仅服务器；`DamageTypeTags` 为 `FGameplayTag[]`；爆炸接口额外带 `DamagePreventionChannel` 与 `ItemID`。自定义伤害数字先用 `MakeCustomDamageNumberParams()` 取参数。

### 生成、复活与补人

- 生成 Actor：`UGCGameSystem.SpawnActor` 已废弃，改用 `UGCActorComponentUtility.SpawnActor`；也可用 `UGCGameplayTaskSystem.General.SpawnActor.NewTask`。
- 客户端特效：`SpawnEmitterAtLocation` / `SpawnEmitterAttached` / `SpawnDecalAtLocation` 仅客户端且不网络复制。
- 复活：`UGCGameSystem.RespawnPlayer` / `RespawnAllPlayers` 已废弃，改用 `UGCPlayerPawnSystem.RespawnPlayer(PlayerKey, RespawnDelayTime, IsDestoryAlivePawn, DestroyDelayTime)`（实验性）。
- 补人：`OpenPlayerJoin` 开启后，用 `ApplyPlayerJoin(Count, TeamID)` 或 `ApplyPlayerJoinLimitCount(TeamPlayerCounts)` 申请；`StopPlayerJoin` 清空申请；成功/停止分别监听 `ApplyPlayerJoinSucceededDelegate` / `ApplyPlayerJoinStoppedDelegate`。

### 定时器、GameplayTag、异步任务

- 定时器：`SetTimer(Object, CallbackFunction, Time, IsLooping)` 返回 `(FTimerHandle, ULuaSingleDelegate)`，用 `ClearTimer(Object, TimerHandle)` 清除；双端可用。纯 Lua 计时器见 `toolbox.md` 的 `UGCTimerUtility`。
- 时间：`UGCTimeSystem.Now()` 取服务器 UTC 秒；`GetDate` / `GetTimestamp` 互转，`GetWeekDay` 返回 1–7（周一到周日）；`GetStartOfCurrentDay` / `GetStartOfCurrentWeek` / `GetStartOfCurrentMonth` / `GetStartOfCurrentYear` 取周期起点。时区参数范围 `[-12, 14]`，不传默认 UTC+8。时间系统不负责定时器。
- GameplayTag：`RequestGameplayTag(TagString)` 取 Tag，`IsValidTag` 校验，`MatchesTag(a, b, bExactMatch)` 匹配，容器用 `CreateGameplayTagContainer` / `CreateGameplayTagContainerFromTag` / `AddGameplayTagToContainer` / `HasTag`。内置状态树在 `UGCGameplayTagSystem.Tags.PawnState`（如 `PawnState.Dead`、`PawnState.Dying`）。
- 异步任务：`UGCGameplayTaskSystem.<域>.<任务>.NewTask(...)` 创建即启动，返回 `UGCGameplayTaskInstance`，用 `EndTask()` 结束。域包括 `General`、`Player`、`PlayerPawn`、`GenericCharacter`、`Weapon`、`PersistEffect`。多数任务的 `TaskOwner` 必须是 `PlayerController`、`PersistEffect`、`PersistBaseComponent` 或 `ActivityBaseActor`。

### TLog 与结算

| 接口 | 用途 | 范围/校验 |
|---|---|---|
| `SendTLog(Key, Value)` | 普通埋点 | 服务器；`Value` 多字段建议下划线分隔 |
| `SendGreyTLog(ID, PlayerKey)` | 灰度埋点 | 服务器 |
| `SendGameTlog(Index, UID, CustomData)` | 结构化 TLog | 服务器；`Index` 限 `[800800, 804800]`，部分区间字段必填，本地限频 100 次/分钟，nil UID 被拦截 |
| `SendLiveStreamingTLog(LogType, Id, Value)` | 直播日志 | 服务器；LogType 1 赛事 / 2 人生 |
| `UploadOfficialModuleData(playerUid, moduleName, data)` | 官方面板数据 | 服务器；`national_arena` 固定 4 个 number 字段，`camp` 可任意结构 |
| `CollectPlayerAntiAFKData(UID, DataKey, DataValue)` | 反挂机数据 | 服务器；随结算上报 |
| `AUGCGameModeBase:ServerSendTlog(key, value, PlayerKey)` | GameMode 侧发送 | 服务器 |

结算的推荐顺序是：写排名/赛事信息（`SetTournamentInfo`）、加段位分（`UGCRankSystem.AddRankProgress`）、按需 `ShowUGCRankAndAchievementUI`（客户端），最后 `GameOver()` 发送全量结算并关闭 DS。`AddRankProgress` 后 `GetUGCRank` 会返回新段位分，`GetUGCGameSeasonId` 取当前玩法段位赛赛季 ID。DS 关闭前可用 `GetDSRemainingTime` / `SetDSCloseNotify` 做关闭提醒。

### 关卡流与多模式

- 流式关卡：`LoadStreamLevel(LevelName, bMakeVisibleAfterLoad, bShouldBlockOnLoad, LatentInfo)`、`UnloadStreamLevel`、`FlushLevelStreaming`、`GetCurrentLevel`。前两者双端，`bShouldBlockOnLoad` 只影响 DS。
- 关卡流程：`UGCLevelFlowSystem.EnableLevelFlow(MgrPath)` 启用；`GoToNextLevelForAllPlayers` / `GoToNextLevelForOnePlayer`、`LevelAddScore` / `GameAddScore`、`LevelSettle` / `GameSettle`、`GetCurrentLevelStage` / `GetTotalLevelCount`。细节与随机关卡限制见 `scene.md`。
- 多模式：`UGCMultiMode.GetModeID()` 取当前模式（无则 0），`GetModeSetting(ModeID)` 取 `ModeSetting`（队伍数、`TeamPlayers`、匹配分数段、聊天开关等）；客户端用 `RequestMatch(SubModeID, ResCallBack, Obj, IsTeamUnfill)` / `RequestCancelMatch` / `RequestReadyMatch`，并监听 `NotifyMatchResponseDelegate` / `NotifyMatchSucceededDelegate`。`SetPlayerFill` 为服务器接口。
- 工程配置：多模式在 `.ugcproj` 的 `[MultiModeSetting_N]` 中定义，不要复制多套 Script；Withdraw 配了 `[MultiModeSetting_0..4]`（基地 + 4 张地图），路由见 `Query_GameMode`。
- 设备/画质：`UGCGameSettingSystem.GetDeviceLevel()`（0 低/1 中/2 高）、`GetRenderQualitySetting`、`GetRenderStyleSetting`；2D 类玩法建议 `AllowSoftwareOcclusion(false)`。

## 典型用法

1. **Withdraw 生命周期**：`UGCGameState:ReceiveBeginPlay` 调 `LifeCycle.BeginPlay()`，再发 `Lifecycle_GameState_Init`；`LifeCycle` 监听 GameState/PC/Pawn 三类初始化，用 `SetTimer` 延迟 1.5s / 2.5s 执行重逻辑；`UGCGameMode.lua` 目前只有 `ReceiveBeginPlay` 和注释掉的 `EnableLevelFlow` 模板。参考 `../../../UGCProjects/Withdraw/Script/Blueprint/UGCGameState.lua`、`../../../UGCProjects/Withdraw/Script/LifeCycle/LifeCycle.lua`、`../../../UGCProjects/Withdraw/Script/Blueprint/UGCGameMode.lua`。

2. **Withdraw PlayerController**：客户端用 `RequestGameplayTag` + `UGCInputSystem.BindInputMapping` 绑定交互键，`RemoveBindingToObject` 在结束时解绑，并用 `InjectInputMapping` 手动触发。参考 `../../../UGCProjects/Withdraw/Script/Blueprint/UGCPlayerController.lua`。

3. **RogueShooting 关卡流程**：GameMode 先取 `UGCMultiMode.GetModeID()`，再按模式查表并 `EnableLevelFlow`：

```lua
local ModeID = UGCMultiMode.GetModeID()
local MgrPath = UGCGameData.GetGameModeActorMgrConfig(ModeID)
UGCLevelFlowSystem.EnableLevelFlow(UGCGameSystem.GetUGCResourcesFullPath(MgrPath))
```

   关内结算用 `GetAllPlayerControllerInCurrentLevel` / `GetCurrentLevelStage`，倒地玩家先扶起、死亡玩家用 `UGCPlayerPawnSystem.RespawnPlayer` 拉起。参考 `../../../UGCProjects/Template_RogueShooting/Script/Blueprint/UGCGameMode.lua`、`../../../UGCProjects/Template_RogueShooting/Script/Blueprint/GameModeActor/SingleMode/SingleMode_1/SingleMode_1_Settle.lua`、`../../../UGCProjects/Template_RogueShooting/Script/Blueprint/GameModeActor/SingleMode/SingleModeSettlement.lua`。

4. **PlaygroundHub 演示**：GameMode 监听 `GameStart` / `GameEnd` / `PawnRespawn` / `PawnDefeat`，用 `GetPlayerControllerByPlayerKey` 找 PC 并重绑 HUD；旧代码仍用已废弃的 `GetRespawnComponent`，新项目应改 `UGCPlayerPawnSystem`。参考 `../../../UGCProjects/Template_PlaygroundHub/Script/Blueprint/UGCGameMode.lua`。

5. **多模式匹配**：大厅 `LobbyModel:RequestMatch` 调 `UGCMultiMode.RequestMatch`，UI 用 `GetModeSetting(...).TeamPlayers` 显示人数；游戏内按 `GetModeID()` 分流。参考 `../../../UGCProjects/Template_RogueShooting/Script/Blueprint/Arts_UI/Lobby/LobbyModel.lua`、`../../../UGCProjects/Withdraw/Script/Package/GameMode/Query/Query_GameMode.lua`。

6. **BR/团竞模板**：FourMaps 用 `Action_GameEndCheck` 统计存活队伍并广播结算；CTCompetition2 用 GameState 状态机切 Prepare/Battle/Result 并对 `GetAllPlayerPawn` 批量设无敌。参考 `../../../UGCProjects/Template_FourMaps/Script/gamemode/Action_GameEndCheck.lua`、`../../../UGCProjects/Template_CTCompetition2/Script/Blueprint/UGCGameState.lua`。

## 约束与坑

- 客户端拿不到敌人 PlayerState，`GetAllPlayerState` / `GetPlayerStateByPlayerKey` 只保证队友；`GetAllPlayerController` 只保证自己。要拿敌人 Pawn 用 `GetAllPlayerPawn` / `GetPlayerPawnByUID`。
- `GetUIDByPlayerKey` 通过 Pawn 反查，敌人 Pawn 已死时 UID 可能缺失；存根里 UID 类型同时出现 `number` 与 `string`，跨接口使用前先 `tonumber` 或与实际值对齐。
- `IsServer()` 依赖 GameState 初始化；GameState 就绪前不要用它做分支。`UGCGameSystem.GameMode` 仅服务器可读。
- 伤害、复活、观战、补人、TLog 均为服务器接口；客户端调用不会生效。`ApplyDamage` 的 `DamageTypeTags` 可传 `nil`（模板即如此）。
- 废弃映射：`SpawnActor → UGCActorComponentUtility.SpawnActor`；`RespawnPlayer` / `RespawnAllPlayers` / `GetRespawnComponent` / `SetPlayerRespawnInfo → UGCPlayerPawnSystem`；`MakeWeakObjectPtr` / `GetObjectFromWeakObjectPtr` / `IsWeakObjectPtrValid → UGCObjectUtility`；`IsOuterlineDEV → GetDSEnvType`；`SendPlayerSettlement → GameOver`。
- `SendPlayerSettlement` 现在调用无效果，正常退出或请求退出 DS 时自动发送；不要靠它做结算触发。
- `SetTimer` 必须持有返回的 Handle 并 `ClearTimer`，否则对象销毁后回调可能落空；循环定时器尤其要清。
- `UGCGameplayTaskInstance` 创建即启动，结束要 `EndTask()`；任务 Owner 不合法会创建失败。
- `UGCMultiMode.RequestMatch` 等匹配请求仅客户端；`SetPlayerFill` 仅服务器。FourMaps/CTCompetition2 当前脚本未使用 `UGCMultiMode`，它们分别靠 `gamemode/Action_*` 与 GameState 状态机自行结算。
- `SendGameTlog` 会在本地先校验并限频，`Index` 越界、UID 为 nil、必填字段缺失都会直接 return，不会发包。
- `UGCLevelFlowSystem.GetTotalLevelCount` 在随机关卡下无法获取总关卡数，需要自定义逻辑。

## 相关

- 分类总表：`api-index.md`
- 角色/玩家细节：`character.md`
- 关卡流、场景查询：`scene.md`
- 全局消息/队伍：`social.md`
- 定时器工具、异步工具：`toolbox.md`
- 其他：`misc.md`
- API 总入口：`../AGENTS.md`
- 工程指南：`../../../UGCProjects/Docs/project-guide.md`
