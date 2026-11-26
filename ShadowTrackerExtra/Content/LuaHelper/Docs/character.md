# 角色系统

> 玩家角色（PlayerPawn）的状态、外观、出生/复活与身份链。对应 `UGCPlayerPawnSystem`、`UGCPlayerControllerSystem`、`UGCPlayerStateSystem`，以及已废弃的 `UGCPawnSystem`、`UGCPawnAttrSystem`。

## 何时读

- 需要在 UID / PlayerKey / PlayerController / PlayerPawn / PlayerState 之间互转。
- 要判断/切换角色状态（移动、趴下、开火、倒地、背负、搬运等）。
- 要做出生点、复活、观战、传送、控制旋转。
- 要改角色外观：换全身骨骼体、隐藏骨骼、描边、透视高亮。
- 要读写玩家档案（存档）或查询存活、退出、队伍、战斗数据。

## API 一览

| System | 文件 | 状态 | 关键函数 | 生效范围 |
|---|---|---|---|---|
| UGCPlayerPawnSystem | [`UGCAPI/UGCPlayerPawnSystem.lua`](../Source/Lua/ugc/UGCAPI/UGCPlayerPawnSystem.lua) | 实验性（类与全部 64 个函数） | HasPawnState / EnterPawnState / LeavePawnState / SwitchPoseState / ChangeAvatarMesh / RespawnPlayer / GetCarryState | 查询多为服务器&客户端；状态/复活/背负/搬运写入仅服务器；Pose、外观、描边、透视仅客户端 |
| UGCPlayerControllerSystem | [`UGCAPI/UGCPlayerControllerSystem.lua`](../Source/Lua/ugc/UGCAPI/UGCPlayerControllerSystem.lua) | 规范（11 个） | GetPlayerCharacter / GetTeamID / TeleportTo / SetControlRotation / MountCharacterPreset / NotifyBattleBeginPlay | 查询双端；TeleportTo、Mount/Unmount、NotifyBattleBeginPlay 仅服务器；EnableBulletTrackEffect 仅客户端 |
| UGCPlayerStateSystem | [`UGCAPI/UGCPlayerStateSystem.lua`](../Source/Lua/ugc/UGCAPI/UGCPlayerStateSystem.lua) | 规范（17 个） | IsAlive / IsExit / GetPlayerBattleInfo / Save/GetPlayerArchiveData / GetTeamID / GetPlayerKeyInt64 | 存档与多数玩家数据仅服务器；GetPlayerAccountInfo、GetTableDataSize、GetTeamID、GetPlayerKey* 双端；GetPlayerPlatformGender、ClearPlayerArchiveData 客户端 |
| UGCPawnSystem | [`UGCAPI/UGCPawnSystem.lua`](../Source/Lua/ugc/UGCAPI/UGCPawnSystem.lua) | 废弃（替代 `UGCPlayerPawnSystem`，18 个全废弃） | 同名 1:1 迁移 | 与 `UGCPlayerPawnSystem` 对应函数一致 |
| UGCPawnAttrSystem | [`UGCAPI/UGCPawnAttrSystem.lua`](../Source/Lua/ugc/UGCAPI/UGCPawnAttrSystem.lua) | 废弃（替代 `UGCAttributeSystem`，47 个全废弃） | 血量/信号/能量/速度/视野/跳跃/命中半径 | 血量、信号、能量、速度、跳跃写入仅服务器；FOV、CanSwitchFPP、ShowPlayerName 仅客户端；其余读双端 |

## 核心概念

### 身份链

| 对象 | 含义 | 说明 |
|---|---|---|
| UID | 账号 ID | `number`（`GetUIDByPlayerKey` 返回 `string`） |
| PlayerKey | 对局内玩家唯一 Key | 普通玩家与人机玩家都有，无效返回 `-1` |
| PlayerController | 控制器 | 人机玩家是 `AIController` |
| PlayerPawn | 角色实体 | `ASTExtraPlayerCharacter`；死亡后可能不存在 |
| PlayerState | 对局状态对象 | 存队伍与战斗数据，可反查 PlayerKey/UID |

互转函数都在 `UGCGameSystem`（见 [`UGCAPI/UGCGameSystem.lua`](../Source/Lua/ugc/UGCAPI/UGCGameSystem.lua)），本分类只列角色相关用法：

| 方向 | 函数 | 范围 |
|---|---|---|
| → PlayerKey | GetPlayerKeyByPlayerController / ByPlayerPawn / ByPlayerState / ByUID | 服务器&客户端 |
| → PlayerController | GetPlayerControllerByPlayerKey / ByPlayerState / ByPlayerPawn | 双端（后两者客户端只能取自己的）；ByUID 仅服务器 |
| → PlayerPawn | GetPlayerPawnByPlayerKey / ByUID / ByPlayerState / ByPlayerController | 双端 |
| → PlayerState | GetPlayerStateByPlayerKey / ByPlayerPawn / ByUID / ByPlayerController | 双端（前三个客户端只返回队友） |
| → UID | GetUIDByPlayerController / ByPlayerState / ByPlayerPawn / ByPlayerKey | 双端 |
| 本地玩家 | GetLocalPlayerController / Pawn / State / Key | 仅客户端 |

`UGCPlayerStateSystem` 另有 `GetPlayerKey(PlayerState)`、`GetPlayerKeyInt64(PlayerState)`（双端）。

### 服务端/客户端可见性

| 接口 | 客户端可见范围 |
|---|---|
| GetAllPlayerController | 仅自己的 PlayerController |
| GetAllPlayerState | 仅所有队友的 PlayerState |
| GetPlayerStateByPlayerKey / ByPawn / ByUID | 仅队友 |
| GetAllPlayerKey / GetAllUID | 含敌人，但通过 Pawn 反查；敌人无 Pawn（死亡/未生成）时结果不全 |
| GetPlayerControllerByPlayerState / ByPlayerPawn | 仅能取当前客户端自己的 Controller |
| GetUIDByPlayerKey | 敌人 Pawn 死亡时结果不全 |

### 角色状态机

- `EPawnState`：移动、Sprint、Stand/Crouch/Prone、Jump、GunFire、GunADS、Dying、Dead、InVehicle、Swim、InParachute、Stun、Carring、CastingSkill 等（见 [`Templates.lua`](../Source/ShadowTrackerExtra/Templates/Templates.lua)）。
- `ESTEPoseState`：Stand / Crouch / Prone / Sprint / CrouchSprint / Crawl / Swim / Dying（见 [`STECharacterTypes.lua`](../Source/ShadowTrackerExtra/Character/STECharacterTypes.lua)）。
- 状态操作：`HasPawnState`、`AllowPawnState`、`EnterPawnState`、`LeavePawnState`（双端），`DisabledPawnState`（服务器），`SwitchPoseState`（仅客户端）。
- `ECarringState`：None / Waitting / PuttingUp / Carring / PuttingDown，用于背负与搬运死亡盒子（见 [`PlayerTypeDefine.lua`](../Source/ShadowTrackerExtra/Player/PlayerTypeDefine.lua)）。

### 外观与角色预设

- 全身骨骼体：`ChangeAvatarMesh` / `RecoverAvatarMesh`（服务器）；外部导入骨骼需 `bIsUseBoneRetarget=true`。
- 显隐与特效：`SetAvatarVisibility`、`HideBoneByBoneName`、`DrawOutline`、`AddOcclusionHighlight` / `RemoveOcclusionHighlight`、`SetOutputBusVolume`（均为客户端）。
- 角色预设：`UCharacterPreset`（[`CharacterPreset.lua`](../Source/UGCGame/Character/CharacterPreset/CharacterPreset.lua)）挂到 Controller 的 `UUGCCharacterManager`（[`UGCCharacterManager.lua`](../Source/UGCGame/Character/CharacterPreset/UGCCharacterManager.lua)），可叠加优先级，返回 Handle。

## 典型用法

**按 PlayerKey 复活**（服务端）
`UGCPlayerPawnSystem.RespawnPlayer(PlayerKey, RespawnDelayTime, IsDestoryAlivePawn, DestroyDelayTime)`；不需要目标 Pawn 对象，死亡后也可复活。参考 [`Withdraw/Script/Blueprint/UGCPlayerPawn.lua`](../../../UGCProjects/Withdraw/Script/Blueprint/UGCPlayerPawn.lua)。

**禁用状态做负重限制**
`UGCPlayerPawnSystem.DisabledPawnState(pawn, EPawnState.Sprint, true)`（仅服务器）。参考 [`Withdraw/Script/Package/Encumbrance/System/System_Encumbrance.lua`](../../../UGCProjects/Withdraw/Script/Package/Encumbrance/System/System_Encumbrance.lua)。

**挂载角色预设**
```lua
if self:HasAuthority() then
    local PlayerController = OwnerActor:GetPlayerControllerSafety()
    self.Handle = UGCPlayerControllerSystem.MountCharacterPreset(PlayerController, self.CharacterPreset)
end
```
参考 [`Template_PlaygroundHub/Script/Blueprint/Prefabs/Buffs/testChicken.lua`](../../../UGCProjects/Template_PlaygroundHub/Script/Blueprint/Prefabs/Buffs/testChicken.lua)（同目录 `testHuan*.lua`、`testMagic.lua` 为同类示例）。

**玩家档案读写**
`UGCPlayerStateSystem.SavePlayerArchiveData(UID, Data)` / `GetPlayerArchiveData(UID)`，仅服务器，PIE 下不能跨对局。参考 [`Template_RogueShooting/Script/Blueprint/UGCPlayerState.lua`](../../../UGCProjects/Template_RogueShooting/Script/Blueprint/UGCPlayerState.lua) 与 [`Withdraw/Script/Core/PlayerDataCore/System_PlayerDataCore.lua`](../../../UGCProjects/Withdraw/Script/Core/PlayerDataCore/System_PlayerDataCore.lua)。

**传送与控制旋转**
`UGCPlayerControllerSystem.TeleportTo(PC, X, Y, Z)`（服务器）、`SetControlRotation(PC, Rotator.New(Roll, Pitch, Yaw))`（双端）。参考 [`Template_PlaygroundHub/Script/Blueprint/UGCPlayerController.lua`](../../../UGCProjects/Template_PlaygroundHub/Script/Blueprint/UGCPlayerController.lua)。

**无敌开关**
`GetIsInvincible`（双端）+ `SetIsInvincible`（服务器）。参考 [`Template_CTCompetition2/Script/Blueprint/UGCGameState.lua`](../../../UGCProjects/Template_CTCompetition2/Script/Blueprint/UGCGameState.lua) 与 [`Withdraw/Script/Blueprint/ChallengeManager.lua`](../../../UGCProjects/Withdraw/Script/Blueprint/ChallengeManager.lua)。

## 约束与坑

- `UGCPlayerPawnSystem` 整体是【实验性】，签名可能随版本变化；新项目也需要按当前存根核对。
- 状态/复活/背负/搬运类的 `Set*` 多在服务器生效；外观类 `SetAvatarVisibility`、`SetOutputBusVolume`、`SetEightWayUniformSpeedEnabled` 与 `SwitchPoseState` 仅客户端。
- 客户端拿不到敌人 PlayerState，按敌人 PlayerKey 查 State 会失败；需要敌人身份时用 `GetPlayerPawnByUID` / `GetAllUID`。
- `GetAllPlayerKey` / `GetAllUID` 走 Pawn 反查，敌人无 Pawn 时缺失；不要当作完整名单。
- `RespawnPlayer` 的 `DestroyDelayTime` 不能为 0，否则未死亡角色不销毁。
- `UGCPawnSystem.ChangeAvatarMesh` 旧签名只收路径字符串；新签名收 `UClass|string` 且多一个 `bIsUseBoneRetarget`，迁移时不能只改系统名。
- `SetAvatarVisibility` 形参名是 `bVisible`，注释却写「bHide：true显示，false隐藏」，两者矛盾；以实际运行验证为准。
- `UGCPawnAttrSystem` 的 `GetPlayerKey` / `GetTeamID` 等查询已由 `UGCGameSystem` / `UGCPlayerStateSystem` 覆盖，不要继续调用旧系统。
- `UGCGameSystem` 中的 `SetPlayerRespawnInfo`、`RespawnPlayer`、`RespawnAllPlayers`、`GetRespawnComponent` 也已标记废弃并指向 `UGCPlayerPawnSystem`。

## 相关

- 同目录：[`api-index.md`](api-index.md)（全量速查）、[`monster.md`](monster.md)（怪物系统）。
- 属性迁移目标 `UGCAttributeSystem`、队伍/阵营接口见 `api-index.md` 中「技能」「社交」分类。
- 底座类：[`STExtraPlayerCharacter.lua`](../Source/ShadowTrackerExtra/Player/STExtraPlayerCharacter.lua)、[`STExtraPlayerState.lua`](../Source/ShadowTrackerExtra/Player/STExtraPlayerState.lua)、[`Source/ShadowTrackerExtra/Character/`](../Source/ShadowTrackerExtra/Character/)。
- 工程指南：[`UGCProjects/Docs/project-guide.md`](../../../UGCProjects/Docs/project-guide.md)。
