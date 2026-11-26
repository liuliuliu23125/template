# 物品、背包与掉落

> 物品由 V2 物编配置（`ItemID`）生成本局实例（`FItemDefineID`），装进 `UBackpackComponentV2`（背包/装备槽/附加槽/仓库），丢弃或生成到地面后由 `AUGCPickUpWrapperActor` 承载。主接口是 `UGCBackpackSystemV2` + `UGCItemSystemV2`，掉落表用 `UGCDropSystem`。V1 的 `UGCBackPackSystem` / `UGCItemSystem` 未废弃，但只覆盖经典背包能力。

## 何时读

- 要给玩家/人机发物品、查数量、移除、丢弃。
- 要做装备栏、武器配件、仓库、背包扩容、货币。
- 要在地面生成可拾取物、设置归属者、自定义拾取物表现。
- 要读写物品实例化数据（随机词条、耐久、自定义属性）。
- 要按掉落表/掉落组算奖励，再决定发背包还是落地。
- 手上是 V1 `UGCBackPackSystem` 代码，要判断能不能迁到 V2。

## API 一览

| System | 文件 | 状态 | 关键函数 | 生效范围 |
|---|---|---|---|---|
| UGCBackpackSystemV2 | [`UGCAPI/UGCBackpackSystemV2.lua`](../Source/Lua/ugc/UGCAPI/UGCBackpackSystemV2.lua) | 规范（87 个，需新背包系统） | GetBackpackComponentV2 / AddItemV2 / AddAndEquipItemV2 / EquipItemV2 / UseItemV2 / DropItemV2 / PutInWarehouse / GetBackpackPersistData | 新增/创建/仓库/容量仅服务器；移除、丢弃、使用、装备双端可调但由服务器执行；查询双端；面板与自定义 UI 仅客户端 |
| UGCItemSystemV2 | [`UGCAPI/UGCItemSystemV2.lua`](../Source/Lua/ugc/UGCAPI/UGCItemSystemV2.lua) | 规范（86 个） | GetItemDefineID / GetConfigItemHandle / AddItemByDefineIDV2 / LoadItemCustomData / SaveItemCustomData / SpawnPickupWrapper / TryPickupWrapperItem | 读双端；创建实例、保存实例数据、落地/拾取仅服务器 |
| UGCBackPackSystem | [`UGCAPI/UGCBackPackSystem.lua`](../Source/Lua/ugc/UGCAPI/UGCBackPackSystem.lua) | 规范（25 个，V1 经典背包） | GetBackpackComponent / AddItem / DropItem / UseItem / GetItemCount / GetWeaponsInBackpack | 写操作仅服务器；多数查询双端，GetItemDataByInstanceID 与 GetAllAttachment* 仅服务端 |
| UGCItemSystem | [`UGCAPI/UGCItemSystem.lua`](../Source/Lua/ugc/UGCAPI/UGCItemSystem.lua) | 规范（15 个，V1） | GetItemType / GetItemSubType / GetItemData / GetPickupWrapperClassPath / SetWrapperToGround | GetItem*/品质查询双端；GetPickupWrapperClassPath 与 Wrapper 修改仅服务器 |
| UGCDropSystem | [`UGCAPI/UGCDropSystem.lua`](../Source/Lua/ugc/UGCAPI/UGCDropSystem.lua) | 规范（2 个） | DropItems / DropItemsByGroup | 双端（纯掷表，不生成实体） |

## 核心概念

### 身份链

| 层级 | 对象 | 说明 |
|---|---|---|
| 配置 | `ItemID`（number） | 物编里的物品配置 ID，全工程静态 |
| 配置对象 | `UBattleItemHandleBase` / 完整表行 | `UGCItemSystemV2.GetConfigItemHandle(ItemID)`；手机 UGC 客户端返回 CompleteTable 行数据（table），其余返回 Handle 对象 |
| 实例 | `FItemDefineID` | 字段 `Type`、`TypeSpecificID`（=ItemID）、`bValidItem`、`bValidInstance`；创建用 `UGCItemSystemV2.GetItemDefineID(ItemID)`（服务器），可带预设 `GetItemDefineIDByPreset` |
| 背包内 | `IItemInterface` | `BackpackComponentV2:GetItemV2(DefineID)`，物品行为由 Handle 类实现 |
| 地面 | `AUGCPickUpWrapperActor` | 持 `ItemID`、`ShowCount`，用 `GetDefineID()` 取实例 ID，见 [`UGCPickUpWrapperActor.lua`](../Source/UGCGame/Backpack/UGCPickUpWrapperActor.lua) |

- 实例化数据挂在 `FItemDefineID` 上：`LoadItemCustomData` 读、`SaveItemCustomData` 写（仅服务器），`GetItemCustomDataSize` 估算存档/同步开销。
- 丢弃指定实例后，地面 Wrapper 会拿到**新的** `FItemDefineID`，但保留原实例的实例化数据。

### 容器模型

| 容器 | 代表接口 | 要点 |
|---|---|---|
| 背包格子 | `GetCellItemCount` / `GetCellCapacity` / `GetAllCellItemDefineIDsV2` / `IsCellCapacityFull` | 已装备、已附加到其它物品、货币都不占格 |
| 装备槽 | `GetEquipSlots` / `EquipItemV2` / `UnEquipItemV2` / `GetEquippedItemBySlotName` | 槽位名如 `EquipmentSlot.Core.MainSlot1`；装备后不占背包格 |
| 附加槽 | `AttachEquipmentToTargetItem` / `DetachEquipmentToTargetItem` / `GetAttachTargetItem` | 配件挂到武器槽位；随父物品一起进入装备态 |
| 仓库 | `PutInWarehouse` / `TakeOutWarehouse` / `GetAllWarehouseItemDefineIDs` / `GetWarehouseCellCapacity` | 转移会转换实例 ID；支持批量与整理 |
| 货币 | `GetCurrencyIDList` / `IsCurrency` | 默认不占格，可用 `DoesOccupyCapacity` 覆写 |
| 地面拾取物 | `SpawnPickupWrapper` / `FindPickupWrapperActorByRange` / `TryPickupWrapperItem` | 由 `UUGCPickupWrapperActorManager` 统一管理数量上限与刷新 |

- 容量是抽象概念：默认按格子数（`CheckCapacity`），可在背包组件子类里改成重量等规则。
- 背包组件同时实现 `IUGCItemContainerInterface` / `IUGCItemTransferInterface` / `IUGCItemEquipTargetInterface`，仓库、背包、其它容器之间可走统一的 `CheckCanTransfer` / `ExecuteTransfer`，见 [`UGCItemTransferInterface.lua`](../Source/UGCGame/Backpack/UGCItemTransferInterface.lua) 与 [`UGCItemWarehouse.lua`](../Source/UGCGame/Backpack/UGCItemWarehouse.lua)。

### 物品能力（Handle 类）

| 类/对象 | 文件 | 用途 |
|---|---|---|
| `UUGCBattleItemHandleBase` | [`UGCBattleItemHandleBase.lua`](../Source/UGCGame/Backpack/UGCBattleItemHandleBase.lua) | `EquipPESkillList`（授技能）、死亡掉落类型 |
| `UUGCEquipmentItemHandleBase` | 同上 | `AttrModifyItemSimpleList`（改属性）、`EquipPESkillList`（授技能）、`AttachActorConfigs`（附加 Actor） |
| `UUGCBackpackAvatarHandle` | [`UGCBackpackAvatarHandle.lua`](../Source/UGCGame/Backpack/UGCBackpackAvatarHandle.lua) | 头/身减伤、背包扩容、耐久、自定义外显 Mesh、`EquipPESkillList` |
| 武器类 Handle | [`UGCGame/Weapons/`](../Source/UGCGame/Weapons/) | `UGCBackpackShootWeaponHandle`、`UGCBackpackMeleeWeaponHandle`、`UGCBackpackThrowWeaponHandle`、`UGCBackpackWeaponAttachHandle` |
| 实例数据管理器 | [`UGCBattleItemInstanceDataManager.lua`](../Source/UGCGame/Backpack/UGCBattleItemInstanceDataManager.lua) | `FindInstanceData` / `SetInstanceData` / `CloneInstanceData` / `CanMerge` |

- 物品读属性可整体重写：`UGCItemSystemV2.RegisterItemPropertyGetOverride(EItemOverrideKey.X, fn)`，DS 与客户端要各自注册；枚举见 [`ItemUtilsV2.lua`](../Source/UGCGame/Backpack/ItemUtilsV2.lua)。
- 物品授予技能/改属性的字段语义见 [`skill.md`](skill.md) 与 [`UGCSkillV2Config.lua`](../Source/UGCGame/Backpack/UGCSkillV2Config.lua)。

### V1 / V2 启用与差异

- 工程 `.ugcproj` 的 `[FeatureFlags]` 中与物品/背包相关的只有「物品编辑器版本」开关，没有独立的背包 V2 字段：V2 物编显式写 `bOpenItemEditor=1`、`bOpenItemEditorV1=0`（PlaygroundHub、RogueShooting、CTCompetition2）；Withdraw 只显式写 `bOpenItemEditorV1=0`；全仓未见 `bOpenItemEditorV1=1` 的工程。未写的键以编辑器实际生成值为准，不要手猜。
- 背包 V2 本体由 GamePart 提供，运行时可判断：`UGCGamePartSystem.BackpackV2.IsLoaded()`、`UGCGamePartSystem.BackpackV2.GetConfig()`、`UGCGamePartSystem.BackpackV2.GetPlayerComponent_BackpackV2_Core(PC)`、`GetPlayerComponent_BackpackV2_UI(PC)`；新拾取列表是 `UGCGamePartSystem.PickUpV2List`。
- V1 只有 `PlayerPawn` + `ItemID`/数字 `InstanceID`，没有装备槽、附加、仓库、格子容量；V2 才有 `FItemDefineID`、装备/仓库/附加/容量/持久化。
- V1 与 V2 的背包组件不是同一类型（`UBackpackComponent` vs `UBackpackComponentV2`），不能混用查询结果。

### 掉落

| 方式 | API | 适用 |
|---|---|---|
| 从背包丢弃 | `UGCBackpackSystemV2.DropItemV2` / `DropItemByDefineIDV2` | 玩家主动丢弃，自动生成地面 Wrapper |
| 直接生成地面物 | `UGCItemSystemV2.SpawnPickupWrapper(Location, ItemID, Count, CustomData)` | 指定点生成，可带实例数据、可 `SetItemOwner` |
| 掷掉落表 | `UGCDropSystem.DropItems(DropID)` / `DropItemsByGroup(DropGroupID)` | 只返回 `{ItemID:数量}`，**不**生成物品 |
| 方案化掉落 | `UGCItemSystemV2.StartCustomizeDrop(...)` | 按产出方案+掉落组生成一批 Wrapper，可指定 `DropActorClass` |

## 典型用法

| 场景 | 推荐 API | 参考模板（看什么） |
|---|---|---|
| 发放初始装备/奖励到背包 | `UGCBackpackSystemV2.AddItemV2(Pawn, ItemID, Count)` | [`Template_TopDownSurvivor/Script/CharacterClassManager.lua`](../../../UGCProjects/Template_TopDownSurvivor/Script/CharacterClassManager.lua)（按职业发武器） |
| 添加后立即装备 | `GetBackpackComponentV2` → `AddItemV2` → `EquipItemV2`，或 `AddAndEquipItemV2` | [`Template_PlaygroundHub/Script/Blueprint/Prefabs/Buffs/testChicken2.lua`](../../../UGCProjects/Template_PlaygroundHub/Script/Blueprint/Prefabs/Buffs/testChicken2.lua)（V2 拿不到时回退 V1） |
| 物品被使用/拾取后挂 Buff、读实例数据 | `LoadItemCustomData` + `UGCPersistEffectSystem.AddBuffByClass` | [`Template_PlaygroundHub/Script/Blueprint/Prefabs/Items/InstanceData/Stamina_Small.lua`](../../../UGCProjects/Template_PlaygroundHub/Script/Blueprint/Prefabs/Items/InstanceData/Stamina_Small.lua) |
| 查询装备槽、自定义背包 UI | `GetEquippedItemBySlotName` / `GetEquipSlots` / `SaveItemCustomData` | [`Template_RogueShooting/Script/Blueprint/Backpack/BP_UGCBackpack.lua`](../../../UGCProjects/Template_RogueShooting/Script/Blueprint/Backpack/BP_UGCBackpack.lua) |
| 自动拾取附近地面物 | `FindPickupWrapperActorByRange` + `TryPickupWrapperItem` | [`Template_TopDownSurvivor/Script/Blueprint/UGCPlayerPawn.lua`](../../../UGCProjects/Template_TopDownSurvivor/Script/Blueprint/UGCPlayerPawn.lua)（用 `DefineID.TypeSpecificID` 过滤） |
| 指定点生成个人专属掉落 | `SpawnPickupWrapper` + `SetItemOwner` | [`Template_PlaygroundHub/Script/Blueprint/TriggerBox/BP_DropBox.lua`](../../../UGCProjects/Template_PlaygroundHub/Script/Blueprint/TriggerBox/BP_DropBox.lua) |

- 添加并装备的最小写法（`DefineIDs` 只在新建分堆时返回，堆叠合并时可能为空）：
```lua
local Added, DefineIDs = UGCBackpackSystemV2.AddItemV2(Pawn, ItemID, 1)
if Added > 0 and DefineIDs and DefineIDs[1] then
    UGCBackpackSystemV2.EquipItemV2(Pawn, "EquipmentSlot.Core.MainSlot1", DefineIDs[1])
end
```
- 掉落表用法：先 `UGCDropSystem.DropItemsByGroup(GroupID)` 拿 `{ItemID:Count}`，再逐项 `AddItemV2` 或 `SpawnPickupWrapper`；参考 [`Template_RogueShooting/Script/Blueprint/ItemSpawner/ItemSpawner.lua`](../../../UGCProjects/Template_RogueShooting/Script/Blueprint/ItemSpawner/ItemSpawner.lua) 与 [`Template_TopDownSurvivor/Script/Blueprint/UGCGameMode.lua`](../../../UGCProjects/Template_TopDownSurvivor/Script/Blueprint/UGCGameMode.lua)。
- 自定义背包行为优先继承 `BP_BackpackComponentV2_C` 覆写事件，不要直接改引擎组件；参考 [`Withdraw/Script/GamePartCustom/BackpackV2/BP_BackpackComponentV2_Custom.lua`](../../../UGCProjects/Withdraw/Script/GamePartCustom/BackpackV2/BP_BackpackComponentV2_Custom.lua)（`CanDrop/CanRemove/OnAdd/OnMerge/OnUse`）。

## 约束与坑

- **由服务器实际执行**：`AddItemV2`、`AddItemByDefineIDV2`、`AddAndEquipItemV2`、`AddAndEquipItemToSlotV2`、`PutInWarehouse`、`TakeOutWarehouse`、`AddCellCapacity`、`AddMaxCellCapacity`、`SpawnPickupWrapper`、`TryPickupWrapperItem`、`StartCustomizeDrop`、`SaveItemCustomData`、`GetItemDefineID` 仅服务器。
- `RemoveItemV2`、`DropItemV2`、`UseItemV2`、`EquipItemV2`、`UnEquipItemV2`、`SwapEquipSlotV2`、`Attach/DetachEquipmentToTargetItem` 在双端都可调用，但真正执行在服务器；客户端只知道调用成功，不知道结果。
- 客户端调用 Remove/Drop/Use/Equip 时接口会「成功」返回：`Remove/Drop` 返回 `0`，`Use/Equip` 固定返回 `true`；本地数据要等服务器同步，不能拿返回值当结果。
- 客户端查询（`GetItemCountV2`、`GetAllItemDefineIDsV2`、`GetEquippedItemBySlotName` 等）可能滞后，UI 应订阅 `ItemChangeDelegateV2` / `ItemAddDelegateV2` / `ItemOperationInfoDelegateV2`（见 [`BackpackComponentV2.lua`](../Source/UGCGame/Backpack/BackpackComponentV2.lua)）。
- 客户端只能取到自己的 `UBackpackComponentV2`（`GetBackpackComponentV2` 注释）。
- `AddItemV2` 会自动合并到已有堆叠，超过最大堆叠会分堆；**新物品不会合并到带实例化数据的堆叠**；返回值第二个才是「新建的实例 ID」，纯合并时为空。
- `AddItemByDefineIDV2` 是高级接口：`DefineID` 必须来自 `UGCItemSystemV2.GetItemDefineID`，复用别的实例 ID 会造成 ID 混乱；一次最多创建一个新堆叠，装不下的部分直接失败。
- `Remove*` 不产生地面物；`Drop*` 才产生 Wrapper。`RemoveItemV2` / `DropItemV2` 只按数量匹配，`RemoveItemByDefineIDV2` / `DropItemByDefineIDV2` 才精确到实例。
- 装备/附加中的物品不占背包格；卸下时若背包已满会失败，这是 `UnEquipItemV2` 的常见失败原因。
- `SwapEquipSlotV2` 不触发 `OnEquip/OnUnEquip`，而是触发 `OnSwapEquipSlot`；不要用交换去模拟「卸下再装上」来等装备事件。
- 仓库进出会转换实例 ID（`PutInWarehouse`/`TakeOutWarehouse` 注释），不要把旧 ID 继续当仓库内 ID 使用。
- `UGCBackpackSystemV2.AddMaxCellCapacity` 增加的容量不持久化（组件版 `AddMaxCellCapacity(Count, bPersist)` 可指定）；`RemoveMaxCellCapacity` 减少后跨对局可能超容，超容物品默认自动丢弃（`HandleExceedCellCapacity` 可覆写保底）。
- `UGCDropSystem` 只做权重/概率掷表，不生成任何物品或 Actor；范围虽标双端，实际应与发货逻辑一起放服务器。
- V1 `UGCBackPackSystem` 未废弃但能力有限：只接受 `PlayerPawn` 和人机，装备/仓库/容量都缺失；新功能一律用 V2。V1 的 `UGCItemSystem.GetPickupWrapperClassPath` 仅服务器，`UGCBackPackSystem.GetPickupWrapperClassPath` 双端，别记混。
- `UGCItemSystemV2.GetConfigItemHandle` 在手机 UGC 客户端返回完整表行（table），在 DS/PC 返回 Handle 对象；跨端代码必须做类型分支。
- 背包 UI 打开后物品变更是延时刷新的，注释明确不要在添加物品后立即取格子自定义控件。
- `OpenBackpackPanel(Mode)`：1/2/3 为全屏（背包+装备、背包+仓库、三者），4/5/6 为对应半屏；仅客户端。

## 相关

- 同目录：[`api-index.md`](api-index.md)、[`skill.md`](skill.md)（物品授予技能、属性修改）、[`character.md`](character.md)（玩家/人机 Pawn）。
- 背包内核组件：[`BackpackComponentV2.lua`](../Source/UGCGame/Backpack/BackpackComponentV2.lua)、事件结构 `FItemOperationInfoV2`、`EUGCCommonItemReason`。
- 拾取物管理：[`UGCPickupWrapperActorManager.lua`](../Source/UGCGame/Backpack/UGCPickupWrapperActorManager.lua)、[`UGCItemSystemV2.lua`](../Source/Lua/ugc/UGCAPI/UGCItemSystemV2.lua) 的 `GetPickupWrapperListBy*`。
- 背包 V2 UI 流程：[`BackpackManager.lua`](../Source/Lua/ugc/UGCGame/GamePart/BackpackV2/BackpackManager.lua)。
- 官方背包 V2 说明：`https://developer.gp.qq.com/wikieditor/#/catalog/20104`（存根类注释内给出的链接）。
- 工程指南：[`UGCProjects/Docs/project-guide.md`](../../../UGCProjects/Docs/project-guide.md)。
- 全量速查：[`api-index.md`](api-index.md)；总入口：[`../AGENTS.md`](../AGENTS.md)。
