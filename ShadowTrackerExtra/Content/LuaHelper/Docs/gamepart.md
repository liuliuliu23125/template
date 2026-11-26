# GamePart 功能模块

> 可插拔的官方玩法功能：在 `DA_GameModeGeneral` 中启用，运行时通过 `UGCGamePartSystem` 取 Config / GlobalActor / PlayerComponent。
> 官方来源：GamePart 模块化、商业化系统、虚拟物品、通用消息系统；本地对应：`UGCGamePartSystem`、`Source/Lua/ugc/UGCGame/GamePart/`。

## 何时读

- 要接入商城、虚拟物品、背包 V2、排行榜、任务、玩家列表、组队招募等官方功能。
- 代码里调 `GetGamePartGlobalActor` 返回 nil。
- 想在 `ReceiveBeginPlay` 里绑定 GamePart 委托但时机不对。
- 需要判断某个功能是“启用 GamePart”还是“直接调 API”。

## 模型

每个 GamePart 由三部分组成：

| 组成 | 基类 | 用途 |
|---|---|---|
| Config | `UUGCGamePartConfig` | 静态配置，`GetGamePartConfig(name)` |
| GlobalActor | `AUGCGamePartGlobalActor` | 全局运行时对象，`GetGamePartGlobalActor(name)` |
| PlayerComponent | `UUGCGamePartPlayerComponent` | 每玩家组件，`GetGamePartPlayerComponent(...)` |

- GamePart 是**编辑器配置启用**的，不是纯代码开关。
- `UGCGamePartSystem` 同时提供命名空间快捷入口：`VirtualItemManager`、`CommodityOperationManager`、`BackpackV2`、`PickUpV2List`、`CircleManager`、`AirDropManager`、`AirAttack`、`EMPZone`、`RankingListManager`、`TaskManager`、`PlayerListManager`、`TeamRecruit`、`PlayerProfileManager`、`SeekTarget`。
- `Activity`、`NewbieGuide`、`SideScrolling`、`TopDown` 在 Lua 框架里有类，但不一定在命名空间里；以实际存根为准。

## 启用

1. 编辑器菜单：`玩法通用设置`，打开 `DA_GameModeGeneral`（生成在 `Asset/Data`）。
2. 在 `Active Game Part Configs` 中添加目标模块，例如：
   - `GP_CommodityOperationManager`（商城/商业化）
   - `GP_VirtualItemManager`（虚拟物品）
   - `GP_BackpackV2`（新背包，具体名称以编辑器下拉列表为准）
3. 保存 `UGCGameState` 的 `Game Mode General Config` 关联。
4. 重新打开工程/进 PIE 生效。

> `.ugcproj` 没有 GamePart 字段，无法从配置文件判断启用了哪些模块；运行时以 `IsGamePartLoaded` / `GetAllLoadedGameParts` 为准。

## 加载时机

GamePart 是异步加载的，`ReceiveBeginPlay` 中可能还没完成：

```lua
local Actor = UGCGamePartSystem.GetGamePartGlobalActor("VirtualItemManager")
if Actor then
    Actor.AddItemResultDelegate:Add(self.OnAddVirtualItemResult, self)
else
    UGCGenericMessageSystem.ListenGlobalMessage(
        self,
        UGCGenericMessageSystem.Messages.UGC.GamePart.GamePartLoaded,
        self,
        self.OnGamePartLoaded)
end
```

`OnGamePartLoaded(GamePartName)` 里再取 Actor、绑委托。按玩家加载的游戏 Part 用 `GamePartLoadedForPlayer`。

## 常用模块

| 模块 | 主要能力 |
|---|---|
| `CommodityOperationManager` | 商品数据、购买校验、限购、CanAfford、GetProductData |
| `VirtualItemManager` | 虚拟物品增删查、持久化、转背包 |
| `BackpackV2` | 新背包组件与 UI 组件 |
| `PickUpV2List` | 新拾取列表 |
| `RankingListManager` | 排行榜 |
| `TaskManager` | 任务 |
| `PlayerListManager` / `PlayerProfileManager` | 局内玩家列表 / 玩家档案 |
| `TeamRecruit` | 组队招募 |
| `CircleManager` / `AirDropManager` / `AirAttack` / `EMPZone` | 信号圈/空投/轰炸/EMP |
| `SeekTarget` | 索敌 |

## 商业化与虚拟物品

商业化依赖两张表（工程默认不存在，需要 `窗口 → Create System Default Table` 创建）：

| 表 | 关键字段 | 限制 |
|---|---|---|
| `UGCObject`（物品表） | `ItemID`、`ItemName`、`ItemDesc`、`ItemSmallIcon` | ItemID 1001–10000；名称 ≤15 字；描述 ≤60 字 |
| `UGCShop`（商品表） | `ProductId`、`ProductType`、价格/物品映射 | ProductId 9000000–9999999 |

- 售卖的是**商品**，购买后获得的是**物品**；商品表引用不存在的 ItemID 会购买失败。
- 商城模板默认依赖 `CommodityOperationManager` 与 `VirtualItemManager`；从商城获得的物品实质是虚拟物品，默认持久化到玩家账户。
- 虚拟物品与背包物品可通过 `UGCObjectMapping` 做单向 1:1 映射；当前版本映射转换在背包满格时有已知 bug，临时用 `RemoveVirtualItem` + `AddItemV2` 组合替代。
- 具体购买/发货链路见 `commerce-template.md`。

## 自定义 GamePart 行为

- 不改官方包：在工程 `Script/GamePartCustom/<模块>/` 写 `BP_<类>_Custom_C`，继承对应 `BP_*_C`，重写虚函数并调 `SuperClass`。
- 资产放 `Asset/GamePartCustom/`。
- 示例：`Withdraw/Script/GamePartCustom/BackpackV2/BP_BackpackComponentV2_Custom.lua`。

## Agent 规则

1. 先判断功能是否由 GamePart 提供；不要绕过 GamePart 直接改官方资产。
2. `GetGamePartGlobalActor` 可能返回 nil；先 `IsGamePartLoaded`，或在 `GamePartLoaded` 事件里再取。
3. 不要把 `ReceiveBeginPlay` 当作 GamePart 已就绪。
4. 启用/关闭 GamePart 是编辑器配置（`DA_GameModeGeneral`），无法只靠 Lua 完成。
5. 商城/虚拟物品先确认两张表和映射表存在，再查购买失败原因。
6. 自定义行为走 `GamePartCustom`，不要改 `ExtendResource/*/OfficialPackage/`。

## 本地参考

- API：`Source/Lua/ugc/UGCAPI/UGCGamePartSystem.lua`
- 框架类：`Source/Lua/ugc/UGCGame/GamePart/`
- 基类：`Source/UGCGame/GamePart/UGCGamePartConfig.lua`、`UGCGamePartGlobalActor.lua`
- 商业化：`commerce-template.md`
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=Z1O-CCF_>（GamePart）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=SX-rx3E_>（虚拟物品）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=73v9VPYQ>（通用消息）
