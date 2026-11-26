# 怪物系统

> 刷怪、AI 行为树、索敌仇恨、动画与血量控制。对应 `UGCGenericCharacterSystem`（主）、`UGCSimpleCharacterSystem`（小动物/简单怪）与已废弃的 `UGCMobPawnSystem`。掉落通过 `UGCDropSystem` 或怪物身上的掉落组件完成。

## 何时读

- 要按怪物类或怪物组表 ID 刷怪，或做圆形范围/分波刷怪。
- 要让怪物移动、停住、改速度，或运行/暂停/停止行为树。
- 要查仇恨目标、强制目标、黑板值，或做拉怪/脱战逻辑。
- 要改怪物血量、播放蒙太奇、覆盖动画资源。
- 要把旧 `UGCMobPawnSystem` 代码迁移到 `UGCGenericCharacterSystem`。

## API 一览

| System | 文件 | 状态 | 关键函数 | 生效范围 |
|---|---|---|---|---|
| UGCGenericCharacterSystem | [`UGCAPI/UGCGenericCharacterSystem.lua`](../Source/Lua/ugc/UGCAPI/UGCGenericCharacterSystem.lua) | 规范（36 个） | SpawnGenericCharacter / SpawnGenericCharacterByGroup / RangeSpawnGenericCharacters* / GetTargetEnemy / RunBehavior / GetBlackboard / GetHealth | 刷怪、移动、行为树、仇恨、血量写入仅服务器；GetHealth/GetHealthMax、IsAlive、IsGenericCharacter、GetCurrentVelocity、GetTargetEnemy、GetPartTypeSockets 双端；蒙太奇与动画覆盖仅客户端 |
| UGCSimpleCharacterSystem | [`UGCAPI/UGCSimpleCharacterSystem.lua`](../Source/Lua/ugc/UGCAPI/UGCSimpleCharacterSystem.lua) | 规范（9 个） | GetHealth / SetHealth / GetHealthMax / SetHealthMax / GetSpeedScale / IsInvincible / IsAlive | 读双端，写服务器 |
| UGCMobPawnSystem | [`UGCAPI/UGCMobPawnSystem.lua`](../Source/Lua/ugc/UGCAPI/UGCMobPawnSystem.lua) | 废弃（替代 `UGCGenericCharacterSystem`，6 个全废弃） | SpawnMob / SpawnMobByMobGroup / RangeSpawnMobs* | 6 个函数均仅服务器 |

## 核心概念

### 对象与状态

- 怪物类 `AUGCGenericCharacter: AGenericCharacter`，定义在 [`UGCGame/Private/NPC/Character/UGCGenericCharacter.lua`](../Source/UGCGame/Private/NPC/Character/UGCGenericCharacter.lua)；底座 [`AGenericCharacter`](../Source/ShadowTrackerExtra/General/GenericCharacter.lua) 提供 `Health`/`HealthMax` 属性、`OnTargetChange_BP`、阵营与主人变化委托。
- 状态集合 `UGCGenericCharacterSystem.GenericPawnState`：Idle / Move / Battle / Turning / Dead / HitFly / Stun；逻辑部件 Tag 集合 `LogicPartTags`：FollowWaypoint / ChooseEnemy / MapCellControl / CallForHelp。
- 类事件：`OnEnterTagState_BP`、`OnLeaveTagState_BP`、`OnInterruptTagState_BP`（双端），`OnBehaviorNotify_BP`、`OnArriveWaypoint_BP`（服务器）。

### 刷怪

| 需求 | 接口 |
|---|---|
| 单只，按类 | SpawnGenericCharacter(WorldContext, Class, Location, Rotation) |
| 单只，按怪物组表 | SpawnGenericCharacterByGroup(WorldContext, GroupID, Location, Rotation) |
| 圆形范围一次多只 | RangeSpawnGenericCharacters / RangeSpawnGenericCharactersByGroup |
| 圆形范围分波 | RangeSpawnGenericCharactersOnTime / RangeSpawnGenericCharactersByGroupOnTime |

范围刷怪会在圆内寻找合适地面，`HeightRange` 限制与中心点的最大高度差，结果返回刷出的怪物列表。分波版本用 `LoopTimes`、`IntervalMinTime` / `IntervalMaxTime`、`FirstDelayTime` 控制节奏，并带 `Callback` / `CallbackSelf`。

### AI 与索敌

- 行为树：`RunBehavior(Path)`、`StopBehavior(Reason)`、`PauseBehavior(Reason)`、`ResumeBehavior(Reason)`；`GetBehaviorTreeSetting` / `OverrideBehaviorTreeSetting` 读写 `FBehaviorTreeReflectSetting`。
- 黑板：`GetBlackboard(Actor)`；怪物类自身也有 `GetBlackBoardComponent()`。
- 仇恨：`GetTargetEnemy`（双端）；`SetForceHatredTarget` / `RemoveForceHatredTarget` / `AddTargetHatredValue`（服务器，类方法）。
- 移动：`MoveTo` / `StopMove` / `EnableMovement` / `DisableMovement` / `SetMaxSpeed` / `SetAvoidanceGroup`。存根明确提示 `MoveTo` / `StopMove` 会与行为树移动冲突。

### 掉落

`UGCGenericCharacterSystem` 本身没有掉落接口，实践有两种：

1. 怪物死亡时调用 `UGCDropSystem.DropItems(DropID)` 或 `DropItemsByGroup(DropGroupID)` 掷出 `{物品ID:数量}`，再交给业务生成拾取物；存根标注双端，模板都在服务器死亡流程中调用。参考 [`Template_TopDownSurvivor/Script/Blueprint/UGCGameMode.lua`](../../../UGCProjects/Template_TopDownSurvivor/Script/Blueprint/UGCGameMode.lua)、[`Withdraw/Script/Manager/Mgr_LootManager.lua`](../../../UGCProjects/Withdraw/Script/Manager/Mgr_LootManager.lua)。
2. 怪物蓝图挂 `UUGCCommonProduceDropItemComponent`（[`UGCCommonProduceDropItemComponent.lua`](../Source/UGCGame/Private/DropItemFeature/UGCCommonProduceDropItemComponent.lua)），死亡时 `StartDrop(DropItemActor, Killer, TraceIgnoreActors, AttachComponent)`，服务器执行、按配置表掉落。参考 [`Withdraw/Script/Blueprint/Prefabs/Monsters/BossMob/BossArmedGorilla.lua`](../../../UGCProjects/Withdraw/Script/Blueprint/Prefabs/Monsters/BossMob/BossArmedGorilla.lua)。

## 典型用法

**按怪物组表刷一只**
```lua
local mob = UGCGenericCharacterSystem.SpawnGenericCharacterByGroup(self, group_id, center, rotation)
if not mob then return nil end
```
参考 [`Withdraw/Script/Tool/Tool_SpawnNavigation.lua`](../../../UGCProjects/Withdraw/Script/Tool/Tool_SpawnNavigation.lua)（同函数还演示了按类刷怪与地面/胶囊校验）。

**按类刷一只并保存引用**
`self.CurrentMonster = UGCGenericCharacterSystem.SpawnGenericCharacter(self, self.SpawnMonsterClass, Location, Rotation)`。参考 [`Template_PlaygroundHub/Script/Blueprint/TriggerBox/BP_MonsterSingleExample.lua`](../../../UGCProjects/Template_PlaygroundHub/Script/Blueprint/TriggerBox/BP_MonsterSingleExample.lua) 与同目录 `BP_BuffSingleExample.lua`、`BP_HeroSkillSingleExamples.lua`。

**强制击杀**
`UGCGenericCharacterSystem.KillGenericCharacter(mob)`（服务器）。参考 [`Template_PlaygroundHub/Script/Blueprint/TriggerBox/BP_MonsterSingleExample.lua`](../../../UGCProjects/Template_PlaygroundHub/Script/Blueprint/TriggerBox/BP_MonsterSingleExample.lua)、[`Template_TopDownSurvivor/Script/Blueprint/Prefabs/Skills/Monster/Monster_AutoBoom.lua`](../../../UGCProjects/Template_TopDownSurvivor/Script/Blueprint/Prefabs/Skills/Monster/Monster_AutoBoom.lua)。

**脱战：暂停行为树并清仇恨**
```lua
UGCGenericCharacterSystem.PauseBehavior(mob, LEASH_SUPPRESS_REASON)
UGCGenericCharacterSystem.StopMove(mob)
local blackboard = UGCGenericCharacterSystem.GetBlackboard(mob)
```
恢复时调用 `ResumeBehavior(mob, reason)`。参考 [`Withdraw/Script/Blueprint/Prefabs/Monsters/UGCMobSpawner/BP_MobSpawner.lua`](../../../UGCProjects/Withdraw/Script/Blueprint/Prefabs/Monsters/UGCMobSpawner/BP_MobSpawner.lua)。

**改血量**
`SetHealthMax` 后再 `SetHealth`（服务器）；当前血量不会随上限提升自动变大。参考 [`Withdraw/Script/Tool/Tool_Spawn.lua`](../../../UGCProjects/Withdraw/Script/Tool/Tool_Spawn.lua)。

## 约束与坑

- 刷怪、移动、行为树、仇恨、血量写入、`KillGenericCharacter` 都只在服务器有效；客户端可读 `GetHealth` / `GetHealthMax` / `IsAlive` / `IsGenericCharacter` / `GetCurrentVelocity` / `GetTargetEnemy` / `GetPartTypeSockets`。
- 刷怪函数返回 `AActor`，可能为 `nil`；先判空，再用 `IsGenericCharacter` 或类型转换使用。
- `RangeSpawnGenericCharactersOnTime` 系列是异步分波，回调在服务器触发；刷怪引用需自行持有，不会自动回收。
- `MoveTo` / `StopMove` 与行为树驱动冲突，存根已注明；有行为树的怪优先用 `PauseBehavior` / `ResumeBehavior`。
- 怪物组表 ID 来自编辑器配置，`SpawnGenericCharacterByGroup` 传入无效 GroupID 的行为未在存根中说明，需自行判空。
- `UGCMobPawnSystem` 六个函数与 `UGCGenericCharacterSystem` 一一对应，迁移是改名而非改逻辑。

| 旧 | 新 |
|---|---|
| SpawnMob | SpawnGenericCharacter |
| SpawnMobByMobGroup | SpawnGenericCharacterByGroup |
| RangeSpawnMobs | RangeSpawnGenericCharacters |
| RangeSpawnMobsByMobGroup | RangeSpawnGenericCharactersByGroup |
| RangeSpawnMobsOnTime | RangeSpawnGenericCharactersOnTime |
| RangeSpawnMobsByMobGroupOnTime | RangeSpawnGenericCharactersByGroupOnTime |

- `GenericPawnState.*`、`LogicPartTags.*` 在存根里都是 `nil` 占位，实际值由运行时注入；类型检查时不要把它们当字面量。
- `UGCSimpleCharacterSystem` 没有刷怪函数，存根也不含创建接口；`UGCProjects` 中没有任何工程直接调用它。如需生成小动物/简单怪，只能用 `UGCActorComponentUtility.SpawnActor`（规范，服务器）自行验证。
- `UGCSimpleCharacterSystem.SetHealth` 注释写明「不会超过血量最大值」；`SetHealthMax` 降低上限会连带压低当前血量。
- `UUGCCommonProduceDropItemComponent:StartDrop` 仅服务器；`UGCDropSystem` 存根标注服务器&客户端，但模板均在服务器死亡流程中调用，掉落实体生成应放在服务器权威流程。
- 模板中的 `UGCPresetCommonDropItemComponent` 未出现在 LuaHelper 存根中（是模板怪物蓝图上的组件）；Lua 侧可查的规范类是 `UUGCCommonProduceDropItemComponent`。

## 相关

- 同目录：[`api-index.md`](api-index.md)（全量速查）、[`character.md`](character.md)（玩家角色）。
- 掉落与拾取属「物品背包」分类，见 `api-index.md` 中 `UGCDropSystem`；技能/Buff 见「技能」分类。
- 类与底座：[`UGCGenericCharacter.lua`](../Source/UGCGame/Private/NPC/Character/UGCGenericCharacter.lua)、[`GenericCharacter.lua`](../Source/ShadowTrackerExtra/General/GenericCharacter.lua)、[`STExtraSimpleCharacter.lua`](../Source/ShadowTrackerExtra/Character/STExtraSimpleCharacter.lua)。
- 工程与模板：[`UGCProjects/Docs/templates.md`](../../../UGCProjects/Docs/templates.md)。
