# 技能与 Buff、属性

> 新技能/Buff 统一走 `UGCPersistEffectSystem`，运行时载体是目标 Actor 上的 `UPersistBaseComponent`；数值走 `UGCAttributeSystem`；技能抛体走 `UGCProjectileSystemV2`（上一代 `UGCProjectileSystem` 未标废弃，仍可用）。旧的 `UGCSkillManagerSystem`、`UGCBuffSystem`、`UGCPawnAttrSystem` 已整体废弃。

## 何时读

- 给角色、怪物、武器挂主动/被动技能或 Buff，需要添加、移除、查询。
- 要做 Buff 层数、持续时间、释放者筛选、按 Tag 查状态。
- 需要打断/禁用某类状态（变身、施法、受击硬直）并做计数。
- 要读写生命、攻击、暴击等属性，或监听属性变化做 UI/派生属性。
- 技能需要发射抛体（直线弹道、高抛物线、追踪弹）。
- 手上是 `UGCSkillManagerSystem` / `UGCBuffSystem` / `UGCPawnAttrSystem` 老代码，要迁移。

## API 一览

| System | 文件 | 状态 | 关键函数 | 生效范围 |
|---|---|---|---|---|
| UGCPersistEffectSystem | [`UGCAPI/UGCPersistEffectSystem.lua`](../Source/Lua/ugc/UGCAPI/UGCPersistEffectSystem.lua) | 规范（21 个） | AddSkillByClass / RemoveSkillInstance / GetSkillsByTag / AddBuffByClass / RemoveBuffByTag / EnterDynamicState / GetPersistBaseComponentByContent | 增删技能/Buff、状态进入离开、打断禁用、GetPersistBaseComponentByContent 仅服务器；GetSkillsBy*/GetBuffsBy*/HasDynamicState 双端；透视与菲涅尔仅客户端 |
| UGCAttributeSystem | [`UGCAPI/UGCAttributeSystem.lua`](../Source/Lua/ugc/UGCAPI/UGCAttributeSystem.lua) | 规范（19 个） | Get/Set/AddGameAttributeValue、AddGameAttributeOperation、AddGameAttributeChangedDelegate、GetCauserFromContext | 读、注册回调双端；写、属性操作、上下文解析仅服务器 |
| UGCProjectileSystemV2 | [`UGCAPI/UGCProjectileSystemV2.lua`](../Source/Lua/ugc/UGCAPI/UGCProjectileSystemV2.lua) | 规范（13 个） | CreateProjectile / CreateProjectileSimple / SetDirection / SetSpeed / SetDamage / GetProjectileListByGroupKey | 全部服务器 |
| UGCProjectileSystem | [`UGCAPI/UGCProjectileSystem.lua`](../Source/Lua/ugc/UGCAPI/UGCProjectileSystem.lua) | 规范（6 个） | SpawnProjectile / SetDestroyAfterHit / SetMoveAfterImpactWithNoLost / GetPMComp | 生成与设置仅服务器；Get* 双端 |
| UGCSkillManagerSystem | [`UGCAPI/UGCSkillManagerSystem.lua`](../Source/Lua/ugc/UGCAPI/UGCSkillManagerSystem.lua) | 废弃（替代 `UGCPersistEffectSystem`，15 个全废弃） | AddSkill / RemoveSkill / UseSkill / GetSkillCD / TriggerStringEvent | 同原函数 |
| UGCBuffSystem | [`UGCAPI/UGCBuffSystem.lua`](../Source/Lua/ugc/UGCAPI/UGCBuffSystem.lua) | 废弃（替代 `UGCPersistEffectSystem`，9 个全废弃） | AddBuff / RemoveBuff / HasBuff / GetCurLayer | 同原函数 |
| UGCPawnAttrSystem | [`UGCAPI/UGCPawnAttrSystem.lua`](../Source/Lua/ugc/UGCAPI/UGCPawnAttrSystem.lua) | 废弃（替代 `UGCAttributeSystem`） | SetHealth / GetHealth / SetHealthMax | 读双端、写服务器 |

## 核心概念

### 组件与对象模型

| 对象 | 类 | 要点 |
|---|---|---|
| 技能/Buff 组件 | `UPersistBaseComponent`（[`PersistBaseComponent.lua`](../Source/ShadowTrackerExtra/Character/PersistBaseComponent.lua)） | 挂在 Actor 上，承载全部技能/Buff；角色类自带 `GetPersistBaseComponent()`（`ASTExtraCharacter`、`AGenericCharacter`），Lua 侧也可用 `GetPersistBaseComponentByContent` |
| 技能实例 | `UPersistEffectSkill`（[`PersistEffectSkill.lua`](../Source/ShadowTrackerExtra/Character/PersistSkill/PersistEffectSkill.lua)） | `PESkillSlot`（槽位 Tag）、`SkillGroup`（同组互斥）、`SkillCD`、`CostConsume`、`bDefaultEnable`、`ActivateSkill/DeActivateSkill` |
| Buff 实例 | `UPersistEffectBuff`（[`PersistEffectBuff.lua`](../Source/ShadowTrackerExtra/Character/PersistSkill/PersistEffectBuff.lua)） | `BuffInfo`、`OnStackNumChange`、`OnStackChange_BP`；合并/时长规则见 `EPEBuffMergeType`、`EPEBuffMergeConditionType`、`EPEBuffDurationType` |
| Tag 状态 | 无独立对象 | 由 Tag 字符串/FGameplayTag 表示，在组件内计数 |

- 技能槽位由 `UGCGameplayTag` 标识，Slot 为空时无法自动创建 UI（类字段注释）。
- `AddBuffByClass(Target, BuffClass, Causer, OverrideDuration, StackNum)` 一次可加多层并记录释放者 `Causer`；`RemoveBuffByClass` / `RemoveBuffByTag` 的最后一个参数可按 `Causer` 只移除该来源的 Buff，传空则不筛选。
- Buff 的层数语义由蓝图配置的合并规则决定；`RemoveBuffByClass` 的 `RemoveNum` 只减指定层，`-1`（默认）清空。
- 技能/Buff 蓝图类既可传 `UClass`，也可传蓝图路径字符串；加载方式参考 Withdraw 的 `UGCObjectUtility.LoadClass` + `UGCMapInfoLib.GetRootLongPackagePath()` 拼接。

### 技能、物品、属性的联动

- 物品授予技能：装备类 Handle 的 `EquipPESkillList`（`FUGCSkillV2ConfigArray`）配置 `SkillTemplateClass`、`SkillActiveCondition`（拾取/使用/装备/手动激活）、`OverrideApplyTime`、`bUseSlotStack`，见 [`UGCSkillV2Config.lua`](../Source/UGCGame/Backpack/UGCSkillV2Config.lua)。
- 物品改属性：`UUGCEquipmentItemHandleBase.AttrModifyItemSimpleList`，见 [`UGCBattleItemHandleBase.lua`](../Source/UGCGame/Backpack/UGCBattleItemHandleBase.lua)。
- 技能伤害：伤害计算蓝图 `GetCalculationResult` 内用 `UGCAttributeSystem.GetCauserFromContext` / `GetSourceMagnitudeFromContext` 等取上下文，参考 [`UGCSkillAttackCalculation.lua`](../../../UGCProjects/Template_RogueShooting/Script/Blueprint/Attributes/UGCSkillAttackCalculation.lua)。

### 属性系统

- 属性名实参是字符串（如 `"Health"`、`"BaseHealth"`）。工程内由 `Script/GameAttribute/game_attribute_type.lua` 导出 `UGCNativeGameAttributeType` / `UGCCustomGameAttributeType` 映射表，值就是这些字符串；两种写法等价。
- 修改方式：`SetGameAttributeValue` 直接赋值；`AddGameAttributeValue` 增减；`AddGameAttributeOperation` 返回唯一 ID，按 `EAttrOperator`（Plus/Multiply/PlusMultiply/ExtraMultiply/ExtraPlus/Set/Max，见 [`AttrModifyGlobalQuery.lua`](../Source/Basic/Public/AttrModifyGlobalQuery.lua)）叠加，必须用 `RemoveGameAttributeOperation` 按 ID 撤销。
- 属性有上下限：`GetGameAttributeValueMax` / `GetGameAttributeValueMin`。
- 伤害/治疗上下文 `FGameMagnitudeContext` 的解析函数全部仅服务器。

### 抛体 V1 / V2 区别

| 维度 | UGCProjectileSystem（V1） | UGCProjectileSystemV2（V2） |
|---|---|---|
| 抛体类 | `APVEProjectileBase` | `APESkillProjectileBase` |
| 生成 | `SpawnProjectile(ProjectileSpawnInfo)`，用表描述目标点/追踪/高抛物线/最大距离 | `CreateProjectile` / `CreateProjectileSimple`，直接传位置、方向、速度、重力、伤害 |
| 参数风格 | 一次性配置表（`ProjectileSpawnInfo`） | 创建参数 + 运行时 `SetDirection/SetSpeed/SetGravityScale/SetDamage/SetTarget` |
| 分组 | 无 | `GetProjectileListByGroupKey(Actor, GroupKey)` |
| 适用 | 手雷/技能抛掷、抛物线预演 | 技能弹道、需要逐帧改向改伤 |

## 典型用法

**按技能类型装配/卸载（推荐的最小封装）**
`UGCPersistEffectSystem.AddSkillByClass(Pawn, SkillClass, OverrideApplyTime, Slot)` 返回技能对象，移除必须回传该对象给 `RemoveSkillInstance`。参考 [`Withdraw/Script/Package/SkillSystem/System/System_Skill.lua`](../../../UGCProjects/Withdraw/Script/Package/SkillSystem/System/System_Skill.lua)。

**一次性授予技能 + Buff + Tag 状态**
先 `GetPersistBaseComponentByContent` 拿组件，再用 `GetSkillsByClass` 清点旧技能、`AddSkillByClass` 重建、`EnterDynamicState/LeaveDynamicState` 切 Tag 状态。参考 [`Template_PlaygroundHub/Script/Blueprint/Prefabs/Buffs/testChicken2.lua`](../../../UGCProjects/Template_PlaygroundHub/Script/Blueprint/Prefabs/Buffs/testChicken2.lua)（同文件还演示 V2 背包缺席时回退 V1 的写法）。

**天赋/成长授予技能与 Buff**
模板给 `AddSkillByClass` / `AddBuffByClass` 传 `-2.0`（存根只说明「可选，默认用类内配置时长」，未定义 `-2.0` 的特殊语义；迁移时以自己的蓝图验证为准）：
```lua
UGCPersistEffectSystem.AddSkillByClass(TargetPawn, SelectedSkill, -2.0)
UGCPersistEffectSystem.AddBuffByClass(TargetPawn, SelectedBuff, -2.0)
```
参考 [`Template_RogueShooting/Script/Blueprint/Components/TalentTreeComponent.lua`](../../../UGCProjects/Template_RogueShooting/Script/Blueprint/Components/TalentTreeComponent.lua)。

**移除指定 Buff（带层数）**
`RemoveBuffByClass(Actor, BuffClass, RemoveNum, Causer)`，按释放者筛选时必须传 Causer。参考 [`Template_PlaygroundHub/Script/Blueprint/Prefabs/Skills/WeaponSkills/Thor_M416/ActiveSkill_ThorM416.lua`](../../../UGCProjects/Template_PlaygroundHub/Script/Blueprint/Prefabs/Skills/WeaponSkills/Thor_M416/ActiveSkill_ThorM416.lua)。

**属性读写与变化回调**
`AddGameAttributeChangedDelegate(Owner, AttrName, Callback)` 返回代理，必须在销毁时 `RemoveGameAttributeChangedDelegate`；写操作只在 `IsServer()` 下做。参考 [`Template_PlaygroundHub/Script/Blueprint/Attributes/UGCAttributeGroup.lua`](../../../UGCProjects/Template_PlaygroundHub/Script/Blueprint/Attributes/UGCAttributeGroup.lua)。

**抛体 V1 回调里控制命中行为**
`UGC_ImpactEvent` 中按命中 Actor 类型调用 `SetDestroyAfterHit` / `SetMoveAfterImpactWithNoLost`。参考 [`Template_Athena/Script/BP_Projectile.lua`](../../../UGCProjects/Template_Athena/Script/BP_Projectile.lua)。

**抛体 V2 按组回收**
`GetProjectileListByGroupKey(OwnerActor, AroundKey)` 取回自己发射的抛体列表，再逐个 `SetDirection/SetSpeed`。参考 [`Withdraw/Script/Blueprint/Prefabs/Skills/Player/Test1.lua`](../../../UGCProjects/Withdraw/Script/Blueprint/Prefabs/Skills/Player/Test1.lua)（UGCProjects 中唯一 V2 使用点）。

## 约束与坑

- **服务端/客户端写反是首要错误**：`AddSkillByClass`、`RemoveSkillInstance`、`AddBuffByClass`、`RemoveBuffByClass`、`RemoveBuffByTag`、`EnterDynamicState`、`LeaveDynamicState`、`InterruptDynamicState`、`SetDynamicStateDisabled`、`ResetDynamicStateDisabled`、`GetPersistBaseComponentByContent`、全部属性写操作都只服务器生效；客户端只做 `Get*` / `Has*` / 事件监听。
- `AddOcclusionHighlight`、`RemoveOcclusionHighlight`、`AddFresnelEffect` 仅客户端；服务端调用无效果。
- `LeaveDynamicState` 返回值是「是否还有剩余计数」：移除一层后仍有剩余返回 `False`，全部清空才返回 `True`，不要当成功标志。
- `EnterDynamicState` 是计数式的，多次进入必须多次离开；`InterruptDynamicState` 直接打断并清状态。
- `SetDynamicStateDisabled(..., true)` 会先打断并把禁用计数 +1；禁用计数大于 0 期间该状态不可进入，配对调用 `false` 才是减计数。
- 旧的 `UGCBuffSystem` 用 Buff 名 + `BuffSystemComponent`，新的用 Buff 蓝图类 + `UPersistBaseComponent`；两者不是换个函数名就能迁移，`GetCurLayer/GetMaxLayer` 需改为读取 Buff 实例的层数事件。
- 旧的 `UGCSkillManagerSystem` 以「技能短名/完整路径」定位技能，新的以技能实例对象定位；Persist 体系没有 `UseSkill` / `TriggerSkillEvent` 同名函数，技能释放与事件由 `UPersistEffectSkill` 的方法与技能事件配置承担。
- `UGCPawnAttrSystem` 只覆盖血量、信号、能量、速度等固定项；自定义属性必须改用 `UGCAttributeSystem` + 工程导出的 `UGCCustomGameAttributeType`。
- `UGCAttributeSystem` 注释明确「暂不支持带属性组件的普通 Actor」，只支持玩家、枪械等已有属性体系的对象。
- `AddGameAttributeOperation` 返回的 ID 必须保存并成对撤销，否则属性残留；重复注册回调也会叠加触发。
- `GetLastUpdateCompBeforeStop` 的返回类型在存根里写成 `boolean`，但 Athena 模板直接访问返回值的 `.MoveIgnoreActors`，实际是组件对象；`GetPMComp` 同样是 boolean 标注，按组件使用前先打印类型确认。
- `UGCProjectileSystemV2` 全部接口仅服务器；客户端要表现需依赖复制或自行预测。

## 相关

- 同目录：[`api-index.md`](api-index.md)、[`character.md`](character.md)（角色/Pawn 状态与外观）、[`item-backpack.md`](item-backpack.md)（物品授予技能、装备属性）。
- 属性回写存档与运行时同步：[`Withdraw/Script/Package/AttributeSystem/System/System_Attribute.lua`](../../../UGCProjects/Withdraw/Script/Package/AttributeSystem/System/System_Attribute.lua)。
- Tag 状态查询示例：[`Template_TopDownSurvivor/Script/Blueprint/Prefabs/Skills/Player/Passive/Passive_AutoAim.lua`](../../../UGCProjects/Template_TopDownSurvivor/Script/Blueprint/Prefabs/Skills/Player/Passive/Passive_AutoAim.lua)。
- 全量速查：[`api-index.md`](api-index.md)。
- 工程指南：[`UGCProjects/Docs/project-guide.md`](../../../UGCProjects/Docs/project-guide.md)。
- 总入口：[`../AGENTS.md`](../AGENTS.md)。
