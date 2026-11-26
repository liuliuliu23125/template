# 物品与背包编辑器

> 物品编辑器 2.0、物品模板/Handle、实例化数据、背包系统与背包流程。
> 官方来源：物品编辑器、背包系统、背包流程、物品实例化数据；运行时 API 见 `item-backpack.md`。

## 何时读

- 要用物品编辑器创建药品/枪械/投掷物/近战/装备/配件。
- 要理解物品模板、Handle、实例化数据、拾取/丢弃。
- 要排查背包格子、装备槽、仓库、堆叠、拾取物异常。
- 要区分“物品配置问题”和“背包 Lua 逻辑问题”。

## 物品编辑器 2.0

- 模板：药品、枪械、投掷物、近战、装备、配件等；支持实例化模板。
- 关键字段：ItemID、名称/描述长度限制、图标、堆叠、品质、拾取/丢弃音效、归属条件。
- 物品 Handle：
  - `UUGCBattleItemHandleBase`：基础行为。
  - 装备 Handle：授予技能、改属性、附加 Actor。
  - 武器 Handle：枪械/近战/投掷物。
- 授予技能：`EquipPESkillList`（`FUGCSkillV2ConfigArray`）。
- 改属性：`AttrModifyItemSimpleList`。

## 物品实例化数据

- `FItemDefineID`：物品实例身份；`Type`、`TypeSpecificID`（=ItemID）、有效性标记。
- `LoadItemCustomData` / `SaveItemCustomData`：读写实例化数据（服务器）。
- DataID 格式与预设见官方；随机词条、耐久、自定义属性都挂在这里。
- 丢弃后地面 Wrapper 会拿到新的 `FItemDefineID`，但保留原实例数据。

## 背包系统

| 容器 | 要点 |
|---|---|
| 背包格子 | 已装备、已附加、货币不占格 |
| 装备槽 | 槽位名如 `EquipmentSlot.Core.MainSlot1` |
| 附加槽 | 配件挂到武器槽位，随父物品进入装备态 |
| 仓库 | 进出会转换实例 ID |
| 货币 | 默认不占格，可覆写 |
| 地面拾取物 | 由 PickupWrapperManager 管理数量上限与刷新 |

- 容量是抽象概念：默认按格子数，可在背包组件子类改成重量等规则。
- 背包组件实现容器/转移/装备目标接口，统一走 `CheckCanTransfer` / `ExecuteTransfer`。

## 背包流程

```text
AddItemV2（按 ItemID 添加）
  → AddItemByDefineIDV2（按实例 ID 添加）
  → RemoveItemV2 / RemoveItemByDefineIDV2
  → Drop / Use / Equip
```

- `AddItemV2` 自动合并堆叠；带实例化数据的堆叠不合并。
- `AddItemByDefineIDV2` 的 DefineID 必须来自 `UGCItemSystemV2.GetItemDefineID`；一次最多创建一个新堆叠。
- `Remove*` 不产生地面物；`Drop*` 才产生 Wrapper。
- 装备/附加不占格；背包满时卸下失败。
- 客户端写操作会“成功”返回但只在本端生效，必须等服务器同步。
- 客户端查询可能滞后，UI 订阅 `ItemChangeDelegateV2` / `ItemAddDelegateV2`。

## Agent 规则

1. 先确认物品模板和 ItemID 是否存在，再看背包逻辑。
2. 写操作放服务器；客户端只读/订阅。
3. 精确到实例时用 `*ByDefineID*`；只按数量时用普通接口。
4. 丢弃和移除语义不同：`Remove` 不落地，`Drop` 才落地。
5. 背包满/卸下失败先查容量，不要先怀疑网络。
6. 实例化数据不要复用别人的 DefineID。

## 本地参考

- API/运行时：`item-backpack.md`
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=a8WC2li6>（物品编辑器）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=OAv2Lp4x>（背包系统）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=DRFytDXX>（背包流程）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=5GHskaj9>（物品实例化数据）
