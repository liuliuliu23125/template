# 社交：队伍 / 阵营 / 语音 / 消息

> 局内组队与大厅组队、队伍→阵营映射、语音房间与频道、系统聊天与双端远程消息。对应 `UGCTeamSystem`、`UGCCampSystem`、`UGCVoiceManagerSystem`、`UGCMessageSystem`、`UGCGenericMessageSystem`。

## 何时读

- 开局按规则分队、换队、查同队成员或队长。
- 需要区分「队伍」（结算/复制/UI）和「阵营」（敌对关系/刷怪归属）。
- 接入局内语音房间、队伍频道、按键说话或自由发言。
- 发系统消息、开私聊，或让客户端与服务器互发自定义消息。
- 处理玩家进入/退出/掉线/重连、队员变更等事件。

## API 一览

| System | 文件 | 状态 | 关键函数 | 生效范围 |
|---|---|---|---|---|
| UGCTeamSystem | `UGCAPI/UGCTeamSystem.lua` | 规范（4 个废弃） | `ChangePlayerTeamID`、`GetPlayerKeysByTeamID`、`GetPlayerStatesByTeamID`、`GetTeamIDByPlayerKey`、`GetAllTeammatePlayerState`、`InviteInGamePlayer`、`RespondInvite` | 混合，见函数注释；查询分服务端/双端 |
| UGCCampSystem | `UGCAPI/UGCCampSystem.lua` | 规范 | `AddCamp`、`SetCampForTeam`、`SetCampForActor`、`SetCampRelation`、`GetCampRelationWithActor`、`SetCampDefaultSpawnMethod` | 设置类仅服务器；查询多为双端 |
| UGCVoiceManagerSystem | `UGCAPI/UGCVoiceSystem.lua` | 规范 | `JoinVoiceRoom`、`QuitVoiceRoom`、`SetMicMode`、`SetMicChannel`、`SetSpeakerChannel`、`SetVoiceRoomPlayerMuteState`、`GetNormalizedMicVolume` | 基本全部客户端；`GetPlayerMemberID` 服务器 |
| UGCMessageSystem | `UGCAPI/UGCMessageSystem.lua` | 规范 | `JoinCampMessageChannel`、`SendSystemMessageToPlayer`、`SendSystemMessageToAll`、`OpenPrivateChat` | 前三个服务器；`OpenPrivateChat` 客户端 |
| UGCGenericMessageSystem | `UGCAPI/UGCGenericMessageSystem.lua` | 规范 | `GetRemoteMessageHandle`、`ListenGlobalMessage`、`RegisterUserDefinedMessage`、`SendServerMessage`、`SendClientMessage`、`SendAllClientMessage` | 监听双端；发送按方向 |

> 文件名是 `UGCVoiceSystem.lua`，但存根里定义的类名是 **`UGCVoiceManagerSystem`**；调用时用后者。

## 核心概念

### 身份链

`UID`（平台账号）↔ `PlayerKey`（局内玩家，DS 连上后才稳定初始化）↔ `PlayerController` / `PlayerState` / `Pawn`。跨端传参优先 `PlayerKey`；`UGCTeamSystem` 大量接口注释提醒：客户端连上 DS 前取到的 `PlayerKey` 列表可能不准。

### 队伍（TeamID）

`TeamID` 是局内分组，驱动同队复制、结算与队友 UI。两套队伍概念：

| 概念 | 典型接口 | 范围 |
|---|---|---|
| 局内玩法队伍 | `ChangePlayerTeamID`、`GetPlayerKeysByTeamID`、`GetPlayerStatesByTeamID`、`LeaveTeam`、`KickMember` | 改队服务器；退出/踢人客户端 |
| 大厅队伍 | `InviteToJoinLobbyTeam`、`RequestToJoinLobbyTeam`、`QuitLobbyTeam`、`KickFromLobbyTeam`、`TransferLobbyTeamLeader` | 全部客户端 |
| 大厅队伍查询 | `GetLobbyTeammateUIDsByUID`、`GetLobbyTeammatePlayerKeysByPlayerKey` | 服务器 |
| 动态大厅队伍 | `GetDynamicLobbyTeammateUIDsByUID` | 客户端，含局内动态加入者 |

大厅邀请闭环：`InviteToJoinLobbyTeam` → 被邀请端 `NotifyInviteToJoinLobbyTeamDelegate` → `RespondToInvitingToJoinLobbyTeam`；请求闭环：`RequestToJoinLobbyTeam` → 队长端 `NotifyRequestToJoinLobbyTeamDelegate` → `RespondToRequestingToJoinLobbyTeam`。局内邀请：`InviteInGamePlayer`（同 DS）/ `InviteLobbyFriend` → `OnInviteReceivedDelegate` → `RespondInvite`。

### 阵营（CampID）

`CampID` 是战斗关系维度，由 `AddCamp(name)` 创建，`CampName` 与 `CampID` 都是唯一标识。队伍与 Actor 都可挂阵营：`SetCampForTeam`、`SetCampForActor`；关系用 `SetDefaultCampRelation` / `SetCampRelation` / `GetCampRelation`，Actor 间判定用 `GetCampRelationWithActor`。出生点用 `SetCampDefaultSpawnMethod`。

PvP 常见做法是 TeamID 与 CampID 一一映射：拆弹的 `BurstMode.CampTeamIDTable`（Police=2/Terrorist=1）、躲猫猫的 `PeekabooMode.Camps`（Hunter=1/Cat=2）。

### 语音

| 维度 | 值 | 接口 |
|---|---|---|
| 说话模式 | `EVoiceMode.Always`（自由发言）/ `EVoiceMode.Push`（按键） | `SetMicMode` |
| 麦克风频道 | `EVoiceChannel.All` / `Team` / `LobbyTeam` | `SetMicChannel` |
| 扬声器频道 | `EVoiceChannel.All` / `Team` | `SetSpeakerChannel` |
| 语音房间 | 自定义 `RoomKey`（由业务自行拼接） | `JoinVoiceRoom` / `QuitVoiceRoom` / `GetVoiceRoomKey` |
| 区域语音 | 全局语音半径（cm）与全局房间 index | `SetGlobalVoiceRadius` / `JoinGlobalVoiceRoom` |
| 音量 | 麦克风 dB 归一化到 0–100 | `GetNormalizedMicVolume` |

### 消息两条线

| 线 | 用途 | 代表接口 |
|---|---|---|
| `UGCMessageSystem` | 系统消息、阵营聊天室、私聊 UI | `SendSystemMessageToPlayer/All`、`JoinCampMessageChannel`、`OpenPrivateChat` |
| `UGCGenericMessageSystem` | 内置 GMP 事件、自定义全局/对象消息、双端远程消息 | `Messages.UGC.*`、`Listen*Message`、`GetRemoteMessageHandle` |

内置事件按域分组：`Player`（进入/退出/掉线/重连）、`PlayerPawn`（出生/伤害/治疗/击败/重生）、`MobPawn`、`MobSpawner`、`Weapon`、`Attribute`、`LevelFlow`、`Task`、`PersistEffect`、`Team.TeammateLogin`、`AirDrop`、`TowerWave`、`GamePart.GamePartLoaded`、`Game.GameStart/GameEnd`、`Client.MainUI.InitMainUI`。

远程消息方向：

| 调用 | 方向 | 生效范围 |
|---|---|---|
| `Handle:SendServer(...)` | 客户端 → 服务器 | 客户端 |
| `Handle:SendClient(PlayerKey, ...)` | 服务器 → 单个客户端 | 服务器 |
| `Handle:SendAllClient(...)` | 服务器 → 所有客户端 | 服务器 |
| `Handle:Listen(fn, owner)` | 收本端消息 | 服务器&客户端 |

另一组静态写法（直接传 Message 名）：`SendServerMessage`、`SendClientMessage`、`SendAllClientMessage`、`ListenRemoteMessage`。

## 典型用法

### 分队与队伍快照

服务端改队后立刻重建队伍视图。参考 `../../../UGCProjects/Template_CTCompetition2/Script/Blueprint/UGCGameMode.lua`（红蓝换队、人数上限、换队后重生）与 `../../../UGCProjects/Template_CTCompetition2/Script/Blueprint/UGCGameState.lua`（按 TeamID 聚合 PlayerKey/UID 并 `RepLazyProperty`）。

```lua
local TeamID = UGCTeamSystem.GetTeamIDByPlayerKey(PlayerKey)
local Keys = UGCTeamSystem.GetPlayerKeysByTeamID(TeamID, true)
local UIDs = UGCTeamSystem.GetUIDsByTeamID(TeamID)
UGCTeamSystem.ChangePlayerTeamID(PlayerKey, 2)
```

多人闯关需要把玩家并到同队以放行结算复制：参考 `../../../UGCProjects/Template_RogueShooting/Script/Blueprint/TeamAllocator.lua`。

### 分队后同步阵营

参考 `../../../UGCProjects/Template_SkillCompetition/Script/Blueprint/UGCGameMode.lua`（Blue→0、Red→1）与 `../../../UGCProjects/Template_TopDownSurvivor/Script/Blueprint/UGCGameMode.lua`（玩家进入时按 TeamID 设阵营）。

```lua
UGCCampSystem.SetCampForTeam(ETeamType.Blue, 0)
UGCCampSystem.SetCampForTeam(ETeamType.Red, 1)
```

按阵营/队伍批量操作：参考 `../../../UGCProjects/Template_PeekabooZ/Script/GameMode/Action_RedistributeTeams.lua`（随机分猎人/猫并统计人数）与 `../../../UGCProjects/Template_demolition/Script/Manager/BurstMode.lua`（阵营→队伍 ID 表）。

### 队长与队友 UI

取队长/队友：客户端用 `GetTeamLeaderPlayerKeyInGame`、`GetAllTeammatePlayerState(bExcludeSelf, bReturnAsLuaTable)`、`GetTeammatePlayerStateByPlayerKey`；服务端用 `GetIsLeaderOrNotByPlayerKey`、`GetTeamLeaderKeyByTeamID`。参考 `../../../UGCProjects/Template_RogueShooting/Script/Blueprint/UGCPlayerController.lua` 与 `../../../UGCProjects/Withdraw/ExtendResource/TeammateList/OfficialPackage/Script/SocialChat/Arts_UI/UIBP/WBP_SocialChat_TeammateList.lua`。

### 语音房间

按「对局 ID + TeamID」拼 `RoomKey`，换队时先退再进。参考 `../../../UGCProjects/Template_CTCompetition/Script/Blueprint/ClassicTeamDeathMatchPlayerController.lua`；单人房间示例见 `../../../UGCProjects/Template_planechess/Script/Blueprint/UGCPlayerController.lua`。

```lua
UGCVoiceManagerSystem.JoinVoiceRoom(RoomKey)
UGCVoiceManagerSystem.SetMicMode(EVoiceMode.Push)
UGCVoiceManagerSystem.SetMicChannel(EVoiceChannel.Team)
UGCVoiceManagerSystem.SetSpeakerChannel(EVoiceChannel.Team)
```

### 远程消息

```lua
local Handle = UGCGenericMessageSystem.GetRemoteMessageHandle("Shop.Buy")
Handle:Listen(self.OnBuyRequest, self)
Handle:SendServer(ProductID)
```

```lua
local Handle = UGCGenericMessageSystem.GetRemoteMessageHandle("Shop.Buy")
Handle:SendClient(PlayerKey, Result)
```

### 组队招募

`UGCGamePartSystem.TeamRecruit.GetPlayerComponent_TeamRecruit(PC)` 取到 `TeamRecruitPlayerComponent`：`PublishRecruit`、`WithdrawRecruit`、`QueryRecruitList`、`JoinRecruitedTeam`、`CanPublishRecruit/CanRefreshList/CanJoinTeam`（冷却秒数）、`IsRecruiting`。配置见 `../Source/UGCGame/TeamRecruit/UGCTeamRecruitGamePartConfig.lua`（`bEnableRecruit`、宣言/目标文案表）。工程内暂未找到使用示例。

## 约束与坑

1. **废弃项**：`GetTeamComponent`（未给替代，改用具体队伍接口）、`GetLobbyTeamUIDsByUID`→`GetLobbyTeammateUIDsByUID`、`GetLobbyTeamKeysByPlayerKey`→`GetLobbyTeammatePlayerKeysByPlayerKey`、`GetTeamSizeByID`→`GetTeamSizeByTeamID`。
2. **范围**：`ChangePlayerTeamID`、`GetPlayerControllersByTeamID`、`GetTeamIDs`、`GetTeamSizeByTeamID`、`GetTeamLeaderKeyByTeamID`、`GetIsLeaderOrNotByPlayerKey`、`IsTeamIDValid` 仅服务器；`LeaveTeam`、`KickMember`、`InviteInGamePlayer`、`InviteLobbyFriend`、`RespondInvite`、`GetAllTeammatePlayerState`、`GetTeamLeaderPlayerKeyInGame` 仅客户端。`GetPlayerPawnsByTeamID`、`GetPlayerStatesByTeamID`、`GetTeamIDByPlayerKey` 双端。
3. **返回类型**：`GetPlayerKeysByTeamID`、`GetAIPlayerKeysByTeamID`、`GetTeamIDs`、`GetPlayerList`、`GetLobbyTeammateUIDsByUID` 的 `bReturnAsLuaTable` 决定返回 LuaTable 还是引擎数组；需要 Lua 表时显式传 `true`，不要假设固定类型。
4. **变更事件**：服务端只有 `OnTeamMemberChangedDelegate(PlayerKey, OldTeamID, NewTeamID)`，首次入队 `OldTeamID=nil`、退出 DS `NewTeamID=nil`；客户端另有 `OnTeamMemberJoinDelegate/LeaveDelegate/OnTeamIDChangedDelegate`。
5. **大厅 vs 动态**：`GetLobbyTeammate*` 只反映进战斗那一刻的大厅队伍；局内动态组队成员要用 `GetDynamicLobbyTeammateUIDsByUID`（仅客户端）。
6. **阵营枚举**：`ECampRelation` 在存根中未定义；且注释数值不一致（`SetDefaultCampRelation` 写 1/2/3，`SetCampRelation` 写 0/1/2）。不要用裸数字，优先用枚举/统一常量并在工程内自测。
7. **阵营归属**：`SetCampForActor` 面向非玩家 Actor（如怪物）；`SetCampForTeam` 才是整队。设置类接口仅服务器。
8. **语音**：只有客户端接口；`GetPlayerMemberID` 在服务器取 MemberID；客户端静音接口的入参注释在 UID 与 MemberID 之间混用。`GetMicState`/`GetSpeakerState` 注释描述的是复合状态，返回值却标 `boolean`，不要依赖其返回完整状态。存根中「判断当前语音输入是否可检测」只有注释、没有函数名，不要臆造。
9. **聊天开关**：系统/队伍/私聊/房间/气泡频道由工程配置 `[MatchSetting]` 的 `bEnableChat`、`bEnableRoomChat`、`bEnableTeamChat`、`bEnablePrivateChat`、`bEnableFriendChannel`、`bEnableSystemChannel`、`bEnableChatBubble` 控制（见各工程 `.ugcproj`），不是运行时 API。
10. **消息监听**：内置 GMP 与自定义消息必须配对使用 `ListenGlobalMessage`/`ListenUserDefinedGlobalMessage`（对象同理）；自定义消息先 `RegisterUserDefinedMessage`。退出/重进地图前可 `ClearAllListeners()` 清理残留监听。
11. **远程消息**：`SendServer` 仅客户端、`SendClient`/`SendAllClient` 仅服务器；存根把 `SendClient` 的 `PlayerKey` 标为 `string`，其余接口用 `number`，以实际调用为准。工程内暂未找到远程消息与 `UGCMessageSystem` 的调用示例，示例仅来自存根注释。
12. **语音类名**：文件 `UGCVoiceSystem.lua` ≠ 类名；调用 `UGCVoiceManagerSystem`。`EVoiceMode`/`EVoiceChannel` 的注释里又写作 `VoiceMode.*`/`VoiceChannel.*`。

## 相关

- `../AGENTS.md`（LuaHelper 总入口与废弃映射）
- `api-index.md`（社交分类）
- `commerce-template.md`（GamePart 加载、TeamRecruit 所在的功能模板体系）
- `../Source/Lua/ugc/UGCAPI/UGCTeamSystem.lua`、`../Source/Lua/ugc/UGCAPI/UGCCampSystem.lua`、`../Source/Lua/ugc/UGCAPI/UGCVoiceSystem.lua`、`../Source/Lua/ugc/UGCAPI/UGCMessageSystem.lua`、`../Source/Lua/ugc/UGCAPI/UGCGenericMessageSystem.lua`
- `../Source/Lua/ugc/UGCGame/GamePart/TeamRecruit/`、`../Source/UGCGame/TeamRecruit/UGCTeamRecruitGamePartConfig.lua`
- `../../../UGCProjects/Template_CTCompetition2/Script/Blueprint/UGCGameMode.lua`、`../../../UGCProjects/Template_SkillCompetition/Script/Blueprint/UGCGameMode.lua`
- `../../../UGCProjects/Docs/project-guide.md`
