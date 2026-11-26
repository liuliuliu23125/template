# 属性与伤害/治疗公式

> 属性管理器定义属性，`AttrModifyComp` 挂到对象上，`UGCAttributeSystem` 运行时读写，属性修改器负责临时/永久/持续修改，全局伤害/治疗公式负责最终结算。
> 官方来源：通用属性系统、属性修改器、全局伤害公式、全局治疗公式、受击数据资产。

## 何时读

- 要加血量、攻击、暴击、移速等角色/武器/载具属性。
- 要改属性但不想污染基础值（Buff、装备、技能加成）。
- 要做全局伤害/治疗覆写、暴击、部位倍率、减伤。
- 要在 Lua 里读属性名，或排查“属性值不对/还原不回去”。

## 属性从哪来

| 页签 | 适用对象 | 说明 |
|---|---|---|
| 基础属性 | 角色、怪物、载具等挂了 `AttrModifyComp` 的对象 | 通用属性 |
| 人物属性 | 玩家角色、新怪物 | 角色专属，含固化属性 |
| 武器属性 | 枪械 | 武器专属，含固化属性 |
| 载具属性 | 载具 | 载具专属，含固化属性 |
| 伤害公式 / 治疗公式 | 全局 | 最终结算覆写 |

- 固化属性由系统预置，不能在属性管理器改，但可被 `AttrModifyComp` 覆盖初始值。
- 自定义属性：属性名只允许英文和下划线，不能重名；支持 `Health|MaxHealth` 复合名；默认值必须在 min/max 之间。
- 即时属性只能“永久修改”。
- 属性名不能与系统预置属性重名，否则行为不可预期。
- 属性管理器编辑后自动导出到 `Script/GameAttribute/game_attribute_type.lua`：
  - `UGCNativeGameAttributeType` / `UGCCustomGameAttributeType`
  - `...CommentMap`（属性名 → 描述）

## 对象必须挂 AttrModifyComp

- `AttrModifyComp` 是 ActorComponent；只有挂载它的对象才能引用属性管理器里的属性。
- 在组件的 `Custom Game Attribute → 属性初始值配置` 中覆盖该对象的初始值（只对该对象生效）。
- 无组件时 `UGCAttributeSystem` 读写不到属性。

## 运行时读写

```lua
UGCGameSystem.UGCRequire('Script.GameAttribute.game_attribute_type')

local Hp = UGCAttributeSystem.GetGameAttributeValue(
    OwnerActor, UGCNativeGameAttributeType.Character_Health)
```

- 属性名实参是字符串；用导出的枚举/映射表，不要手写字符串。
- 读：服务器 & 客户端；写、属性操作、上下文解析：服务器。
- 支持：Get/Set/Add、上下限、`AddGameAttributeOperation`（返回 ID，需按 ID 撤销）、变化委托。
- 伤害/治疗上下文用 `FGameMagnitudeContext` 解析。

## 属性修改器

属性最终值 = 基础值经过修改器计算：

| 修改类型 | 行为 |
|---|---|
| 临时修改 | 不改基础值，效果结束可还原 |
| 永久修改 | 直接改基础值，后续基于新基础值 |
| 持续修改 | 按 Tick 持续计算，取最新值，结束还原基础值 |

运算符：

| 运算符 | 行为 |
|---|---|
| Plus | 加法，多修改器合并 |
| Multiply | 乘法，多修改器合并 |
| Set | 值覆盖，多个时最后一个生效 |
| Extra Multiply | 独立乘法，不参与合并，仅临时 |
| Extra Plus | 独立加法，不参与合并，仅临时 |

临时修改公式：

```text
Set ? Set : (X + Plus1 + Plus2...) * (Multiply1 + Multiply2...) * ExtraMul1 * ... + ExtraAdd1 + ...
```

- 临时/持续修改通过固定公式计算，不受还原顺序影响。
- 永久修改按执行顺序做四则运算，顺序不同结果不同。
- Set 没有优先级，只有时序最后一个生效；尽量保证同时只有一个 Set。
- 过度使用临时修改会增加性能开销。
- 技能/Buff/装备的属性修改底层都是这套修改器。

## 全局伤害公式

启用：`属性管理器 → 伤害公式 → 推导`，生成：

- `Asset/Blueprint/Attributes/UGCGlobalDamageCalculation`
- `Script/Blueprint/Attributes/UGCGlobalDamageCalculation.lua`

核心回调：

```lua
function UGCGlobalDamageCalculation:GetCalculationResult(Context, ExtraResult)
    local Base = UGCAttributeSystem.GetSourceMagnitudeFromContext(Context)
    return Base
end
```

- `Context: FGameMagnitudeContext`：`SourceObject`、`Instigator`、`Causer`、`TargetActor`、`SrcMagnitude`、`RestrictedDamageType`、`DamageTypeTags`、`AdditionalDamageData`、`ResultTags`、`IsFatal`、`RecoverTags`。
- 返回值：最终伤害 + `FExtraDamageCalculationResult`（可加 `ResultTags`）。
- 可用 `UGCAttributeSystem.GetVictimFromContext` / `GetSourceMagnitudeFromContext` / `GetDamageTypeFromContext` / `GetDamageTagsFromContext`。
- 过滤：内置通用伤害修改过滤选项，勾选后该类伤害不进入公式。
- 事件：`UGCGenericMessageSystem.Messages.UGC.PlayerPawn.PreTakeDamage` / `PostTakeDamage`。
- 对怪物仅新怪物系统支持伤害公式。

## 全局治疗公式

启用：`属性管理器 → 治疗公式 → 推导`，生成 `UGCGlobalRecoveryCalculation`。

- 所有 `RecoverGenericCharacterHealth` 的治疗进入 `GetCalculationResult(Context, ExtraResult)`。
- 参数/返回值与伤害公式一致；`ExtraResult` 可加治疗标记。
- 对怪物仅新怪物系统支持治疗公式。

## 受击数据资产

- 受击数据资产定义受击表现/参数（部位、特效、音效等）。
- 伤害流程可结合 `DamageTypeTags`、`ResultTags` 做表现分支。
- 具体字段以工程内资产为准，不在本文展开。

## Agent 规则

1. 属性名从 `game_attribute_type.lua` 取，不手写字符串。
2. 对象必须有 `AttrModifyComp`，否则读写无效。
3. 写属性只在服务器；客户端只读/监听。
4. Buff/装备/技能加成优先用属性修改器，不要直接 Set 基础值。
5. 临时修改用固定公式，永久修改注意顺序；Set 尽量唯一。
6. 推导属性避免互相依赖成环。
7. 全局伤害/治疗公式是最终结算入口；不要在多个类里重复覆写伤害。
8. 改伤害前先确认是否被“内置过滤选项”排除。

## 本地参考

- 属性类型：`UGCProjects/Withdraw/Script/GameAttribute/game_attribute_type.lua`
- 属性组：`UGCProjects/Withdraw/Script/Blueprint/Attributes/UGCAttributeGroup_Character.lua`
- 伤害公式：`UGCProjects/Withdraw/Script/Blueprint/Attributes/UGCGlobalDamageCalculation.lua`
- 治疗公式：`UGCProjects/Withdraw/Script/Blueprint/Attributes/UGCGlobalRecoveryCalculation.lua`
- API：`Source/Lua/ugc/UGCAPI/UGCAttributeSystem.lua`
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=b4_7IAOg>（通用属性）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=y24mx0rF>（属性修改器）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=gu0cVbhR>（伤害公式）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=XotPYsFn>（治疗公式）
