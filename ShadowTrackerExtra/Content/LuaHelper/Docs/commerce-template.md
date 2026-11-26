# 商业化与功能模板

> 用 GamePart 承载的官方功能与商业化链路：商品/货币、发货、邮件、活动、特权、徽章、公告、玩法存档。对应 `UGCGamePartSystem`、`UGCCommoditySystem`、`UGCMailSystem`、`UGCActivitySystem`、`UGCPrivilegeSystem`、`UGCAchievementSystem`、`UGCAnnouncementSystem`、`UGCModeArchiveSystem`、`UGCDataModuleManager`。

## 何时读

- 接入绿洲币/启元币商品，做购买、限购、折扣、批量购买、兑换码。
- 购买成功后要把物品发到虚拟物品、背包或邮件。
- 要启用邮件、活动、任务、排行榜、玩家列表等官方功能模块并取到其对象。
- 判断玩家特权、上报徽章进度、拉取公告。
- 跨对局保存玩法数据（ModeArchive），或注册自己的全局/玩家数据模块。
- 想改某个 GamePart 的默认行为，又不能改官方资源包。

## API 一览

| System | 文件 | 状态 | 关键函数 | 生效范围 |
|---|---|---|---|---|
| UGCGamePartSystem | `UGCAPI/UGCGamePartSystem.lua` | 规范 | `GetGamePartConfig`、`GetGamePartGlobalActor`、`GetGamePartPlayerComponent`、`IsGamePartLoaded`、`GetAllLoadedGameParts` | 前两个显式标注服务器&客户端；`GetGamePartPlayerComponent`、`IsGamePartLoaded`、`GetAllLoadedGameParts`、`GetScriptModule`/`GetPlayerScriptModule`/`GetLocalPlayerScriptModule` 未标注 |
| UGCCommoditySystem | `UGCAPI/UGCCommoditySystem.lua` | 规范 | `BuyUGCCommodity2`、`BuyUGCCommodityBatch`、`UseUGCCommodity2`、`RegBuyCMD`、`UseRedemptionCode`、`GetSellingPriceAfterDiscount` | 购买 V1/V2 客户端；使用 V1 客户端、V2 双端（DS 传 PlayerController）；注册与全量查询服务器；价格/货币/单玩家查询双端 |
| UGCMailSystem | `UGCAPI/UGCMailSystem.lua` | 规范 | `IsMailSystemEnabled`、`GetMailList`、`GetMailInfo`、`ClaimMailAward`、`ReadMail`、`DeleteReadMail`、`PIESendMail` | 全部服务器 |
| UGCActivitySystem | `UGCAPI/UGCActivitySystem.lua` | 规范 | `IsActivityInfoReady`、`GetAllActivityInfos`、`GetActivityInfo`、`GetValidActivityIDs`、`GetNearestPeriodIndex` | 服务器&客户端 |
| UGCPrivilegeSystem | `UGCAPI/UGCPrivilegeSystem.lua` | 规范 | `GetPlayerPrivilegesInformation`、`DoesPlayerHavePrivileges`、`AddPrivilegeEmblemFlagUI`、`RemovePrivilegeEmblemFlagUI` | 查询服务器；徽章 UI 客户端 |
| UGCAchievementSystem | `UGCAPI/UGCAchievementSystem.lua` | 规范 | `AddAchievementProgress` | 服务器 |
| UGCAnnouncementSystem | `UGCAPI/UGCAnnouncementSystem.lua` | 规范 | `GetLatestAnnouncements` | 服务器 |
| UGCModeArchiveSystem | `UGCAPI/UGCModeArchiveSystem.lua` | 规范 | `AsyncCreateIntKey`、`AsyncCreateFloatKey`、`AsyncGetKey`、`AsyncDeleteKey`、`AsyncModifyIntValue`、`AsyncModifyFloatValue` | 服务器 |
| UGCDataModuleManager | `UGCAPI/UGCDataModuleManager.lua` | 规范 | `RegisterDataModule`、`RegisterPlayerDataModule`、`GetDataModule`、`GetPlayerDataModule`、`GetDataModifiedDelegate` | 服务器&客户端 |

## 核心概念

### GamePart 是什么

GamePart 是按功能打包、可整体启停的模块。一个 GamePart 通常由三部分组成：

| 组成 | 基类 | 作用 |
|---|---|---|
| Config | `UUGCGamePartConfig`（`UPrimaryDataAsset`） | 该功能的静态配置，`GetGamePartConfig` 取到 |
| GlobalActor | `AUGCGamePartGlobalActor` | 全局运行时对象，`GetGamePartGlobalActor` 取到 |
| PlayerComponent | `UUGCGamePartPlayerComponent` | 每玩家组件，`GetGamePartPlayerComponent` 取到 |

基类定义见 `../Source/UGCGame/GamePart/UGCGamePartConfig.lua`、`../Source/UGCGame/GamePart/UGCGamePartGlobalActor.lua`；框架类在 `../Source/Lua/ugc/UGCGame/GamePart/`。

### 启用与就绪

- 启用入口在编辑器工程内，静态文件里没有对应字段（`.ugcproj` 无 GamePart 项），无法从文件确认具体 UI/配置项。
- 运行时只认加载状态：`IsGamePartLoaded(name)`、`GetAllLoadedGameParts()`。
- 就绪时机用消息：`UGCGenericMessageSystem.Messages.UGC.GamePart.GamePartLoaded`（全局）与 `GamePartLoadedForPlayer`（按客户端），在其回调里取 GlobalActor 才可靠。
- 未加载时 `GetGamePartGlobalActor` 不能假定有值，先判 `IsGamePartLoaded`。

`UGCGamePartSystem` 暴露的命名空间：`CircleManager`、`AirDropManager`、`AirAttack`、`EMPZone`、`BackpackV2`、`PickUpV2List`、`SeekTarget`、`VirtualItemManager`、`CommodityOperationManager`、`RankingListManager`、`TaskManager`、`PlayerListManager`、`TeamRecruit`、`PlayerProfileManager`。`../Source/Lua/ugc/UGCGame/GamePart/` 下的 `Activity`、`NewbieGuide`、`SideScrolling`、`TopDown` 未出现在该命名空间中。

### 商业化链路

以下链路由存根类型、枚举与工程调用归纳；具体内部实现是引擎 C++，不可见。

```text
客户端 BuyUGCCommodity2 / BuyUGCCommodityBatch（二次确认，价格必须来自 GetSellingPriceAfterDiscount）
  → CommodityOperationManager 校验：价格 / 售卖状态 / 限购 / 特权 / 货币类型
  → VirtualItemManager 发货（来源标记 Buy）
  → 背包映射（TransferToBackpack）或邮件附件（Mail，Source = Mail）
  → BuyUGCCommodityResultDelegate / UseUGCCommodityResultDelegate 通知双端
```

关键枚举均在同文件：`EProductType`（Currency/Item）、`ECurrencyType`（OasisCoin/ActivityCoin/OtherCoin）、`EAvailableForSale`、`ELimitType`、`EStoreId`（InGame/Lobby）、`EUseRedemptionCodeResult`。购买校验结果在 `../Source/Lua/ugc/UGCGame/GamePart/CommodityOperationManager/BP_CommodityOperationManager_GlobalActor.lua` 的 `EPurchaseValidationResult`（价格不符/未售卖/超限购/无特权/货币类型错误等）。

`CommodityOperationManager` 提供实例方法：`BuyProduct`（客户端）、`ServerBuyProduct`（服务端，自定义货币）、`CanAfford`、`GetLimitPurchasedTimes`、`GetPurchasedTimes`、`GetProductData`、`GetAllProductData`。`VirtualItemManager` 提供 `AddVirtualItem` / `AddVirtualItems`、`RemoveItem`、`GetItemNum`、`TransferToBackpack`、`GetMappedItemID`。

## 典型用法

### 商品购买与发货

- 客户端价格与下单：`GetSellingPriceAfterDiscount` → `BuyUGCCommodity2`。参考 `../../../UGCProjects/Withdraw/ExtendResource/ShopV2/OfficialPackage/Script/ShopV2/Arts_UI/UIBP/Item/ShopV2_CommonButton_UIBP.lua`（价格/图标/描述来源与二次确认）。
- 服务端监听购买结果再发自己的货：参考 `../../../UGCProjects/Withdraw/Script/Service/Svc_ArmsDealer.lua`。该文件按 `(bSucceeded, playerKey, commodityId, count, uid, productId)` 使用 `BuyUGCCommodityResultDelegate`（存根未写 `@param`，参数顺序来自此用法）。

```lua
local Price = UGCCommoditySystem.GetSellingPriceAfterDiscount(ProductID)
local PF = UGCCommoditySystem.BuyUGCCommodity2(ProductID, Icon, Desc, 1)
PF:Then(function(Future) local bOK = Future:Get() end)
```

服务端主动发货到虚拟物品。`EVirtualItemAddItemSource` 区分来源：`Custom` 为直接调用 Add 接口，`Buy`/`Compensate`/`Redeem`/`Mail` 分别对应商业化购买、补偿、兑换、邮件领取：

```lua
local VIM = UGCGamePartSystem.VirtualItemManager.GetGlobalActor()
VIM:AddVirtualItems(PC, { [ItemID] = Count }, "Shop")
```

### 邮件

邮件接口全部服务器生效；附件是 `{[ItemID]=Count}`。`PIESendMail` 仅 PIE 有效，线上邮件由管理后台下发。参考 `../../../UGCProjects/Withdraw/Script/Mail/MailboxAdapter.lua`（服务端校验 UID、领取/已读/删除、失败原因）与 `../../../UGCProjects/Withdraw/ExtendResource/Mail/OfficialPackage/Script/Mail/CMPT/UGCMailboxComponent.lua`（委托绑定与列表 UI）。

服务端领取（客户端只提交 MailID，UID 与附件由服务端取）：

```lua
UGCMailSystem.MailListUpdateDelegate:Add(self.OnMailListUpdate, self)
local Mails = UGCMailSystem.GetMailList(UID)
UGCMailSystem.ClaimMailAward(UID, { Mails[1].ID })
```

### 活动

需启用活动 GamePart（`UGCActivitySystem` 类注释明确）。活动信息就绪用 `IsActivityInfoReady`/`OnActivityInfoReadyDelegate`，有效活动用 `GetValidActivityIDs`，周期序号用 `GetNearestPeriodIndex`（0=永久，-1=不存在或未开启）。参考 `../../../UGCProjects/Withdraw/ExtendResource/Activity/OfficialPackage/Script/Activity/ActivityManager.lua`。

```lua
for _, ActivityID in ipairs(UGCActivitySystem.GetValidActivityIDs()) do
    local Info = UGCActivitySystem.GetActivityInfo(ActivityID)
    local PeriodIndex = UGCActivitySystem.GetNearestPeriodIndex(ActivityID)
end
```

### 取官方 GamePart 对象

参考 `../../../UGCProjects/Withdraw/ExtendResource/Activity/OfficialPackage/Script/Activity/ActivityManager.lua`（先判加载再取）与 `../../../UGCProjects/Withdraw/ExtendResource/ShopV2/OfficialPackage/Script/ShopV2/ShopV2Manager.lua`（`CommodityOperationManager`/`VirtualItemManager` 缓存与委托绑定）。

```lua
if UGCGamePartSystem.IsGamePartLoaded("VirtualItemManager") then
    local Actor = UGCGamePartSystem.GetGamePartGlobalActor("VirtualItemManager")
end
```

### 全局玩家列表 / 排行榜 / 档案

- 玩家列表：`UGCGamePartSystem.PlayerListManager.GetGlobalActor():GetPlayerListData()`，配置 `GetPlayerListConfig()`；参考 `../../../UGCProjects/Withdraw/ExtendResource/GlobalPlayerList/OfficialPackage/Script/SocialChat/Arts_UI/UIBP/WBP_SocialChat_GlobalPlayerList.lua`。
- 排行榜：`UGCGamePartSystem.RankingListManager.GetGlobalActor()` / `GetPlayerComponent_RankingList(PC)`。
- 玩家档案：`UGCGamePartSystem.PlayerProfileManager.GetGlobalActor()` / `GetPlayerComponent_PlayerProfileManager(PC)`。

### 自定义 GamePart 行为

不改官方包：在工程 `Script/GamePartCustom/<模块>/` 下写 `BP_<类>_Custom_C`，继承对应 `BP_*_C`，重写虚函数并调用 `SuperClass`；资产放 `Asset/GamePartCustom/`。参考 `../../../UGCProjects/Withdraw/Script/GamePartCustom/BackpackV2/BP_BackpackComponentV2_Custom.lua`。

### 玩法存档（ModeArchive）

仅服务器、异步、PromiseFuture 风格。`AsyncCreate*Key` 固定「仅当不存在时创建」；float 标记不可逆；单玩法最多 1000 个 BizName，QPS 约 5000。参考存根注释与 `UGCAsyncUtility.AsyncRun`。

```lua
local PF = UGCAsyncUtility.AsyncRun(UGCModeArchiveSystem.AsyncModifyIntValue("TotalKills", 1))
PF:Then(function(Task) local ErrCode, NewValue = Task:Get() end)
```

## 约束与坑

1. **范围**：`BuyUGCCommodity*` / `UseUGCCommodity` / `OpenRedeemPage` / `ShowRechargeEntryUI` / `ClearCommodity` 仅客户端；`RegBuyCMD`、`RegUseCMD`、`UseRedemptionCode`、`GetAllPlayerUGCCommodityList`、`GetAllPlayerUGCProductList` 仅服务器。`UseUGCCommodity2` 双端（DS 端必须传 PlayerController）。
2. **价格**：`BuyUGCCommodity`/`BuyUGCPrivilegeCommodity` 的 `Cost` 必须传 `GetSellingPriceAfterDiscount` 的返回值，否则与 `CommodityOperationManager` 的校验不一致。
3. **发货来源**：虚拟物品来源用 `EVirtualItemAddItemSource` 区分 Buy/Compensate/Redeem/Mail/Custom，便于对账；邮件领取会再触发 `ClaimMailsResultDelegate`。
4. **邮件时机**：非 PIE 时 `MailListUpdateDelegate` 一般只在进局时触发一次，局内后台新邮件下一局才可见。
5. **PIE 特例**：`PIESendMail` 仅 PIE 有效；`UseRedemptionCode` 在 PIE 下固定返回成功；特权查询在 PIE 返回 nil/false。
6. **徽章**：`AddAchievementProgress` 是覆盖累计而非增量，单场内多次调用不会累加，需自行汇总后一次调用。
7. **公告**：`GetLatestAnnouncements` 是服务器异步请求，只返回最新 5 条，返回 PromiseFuture。
8. **ModeArchive**：全部接口仅服务器；DS 本地会拦截非服务器调用、参数错误，并约 10 秒兜底超时。`create` 不覆盖已有值，重置需先 `AsyncDeleteKey` 再创建（非原子）。
9. **活动**：`UGCActivitySystem` 类注释要求先启用活动 GamePart；`bPermanentTime` 为真时不要用 `GetNearestPeriodIndex` 取周期。
10. **GamePart**：存根中 `GetGamePartPlayerComponent`、`IsGamePartLoaded`、`GetAllLoadedGameParts` 等未标 `生效范围`，不要据此断定服务端可用；以实际调用点与消息回调为准。`GetLocalPlayerScriptModule` 名称指向当前客户端。

## 相关

- `../AGENTS.md`（LuaHelper 总入口与废弃映射）
- `api-index.md`（商业化与功能模板、社交分类）
- `social.md`（队伍/阵营/消息）
- `../Source/Lua/ugc/UGCAPI/UGCGamePartSystem.lua`、`../Source/Lua/ugc/UGCAPI/UGCCommoditySystem.lua`
- `../Source/Lua/ugc/UGCGame/GamePart/`（各 GamePart 实现类）、`../Source/Lua/ugc/UGCCommoditySystem/UI/UGC_SecondaryConfirmation_UIBP.lua`
- `../../../UGCProjects/Withdraw/AGENTS.md`（ExtendResource 包清单与分层约束）
- `../../../UGCProjects/Docs/project-guide.md`
