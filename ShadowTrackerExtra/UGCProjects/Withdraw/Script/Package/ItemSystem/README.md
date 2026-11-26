# ItemSystem

ItemSystem 是物品配置与玩家物品数量的唯一公共入口。业务模块只依赖
`Registry_ItemSystem`，不直接访问背包系统或 VirtualItemManager。

## 分层

- `Registry_ItemSystem.lua`：稳定公共 API。
- `Query/Query_Item.lua`：配置缓存、ID 转换、图标与数量查询。
- `System/System_Item.lua`：服务端增减物品、实际变化量计算和客户端变化委托。

## 写接口约定

`AddItemCount` 和 `RemoveItemCount` 返回 `ok, actualCount, message`。
扣减允许部分完成；购买、制作等完整交易必须检查
`actualCount == requestedCount`。客户端写入及非法参数不会修改物品。

枪械和护甲的跨关存档仍由 `Tool_BackitemPersist` 独立处理，不属于本包。

## 物品 ID 常量

跨模块共享的物品 ID 位于 `Script/Const/Generate/Const_Item.lua`，由 GenKit
生成，不属于包内可变数据。业务统一通过局部变量引用：

```lua
local ItemID = require("Script.Const.Generate.Const_Item")
Registry_ItemSystem.GetItemCount(pc, ItemID.GOLD)
```

`Util_EnumManager.ItemID` 仅兼容旧调用，并引用同一张常量表。
保留历史成员大小写，`FlareGun` 已按 Withdraw 物品表纠正为 `5069`。
常量源 CSV 保留在 `E:/Project/AgentHelper/WithDrawCache/ProjectCache/ItemConstants/Item/DT_Item_Config.csv`，
初始数据从 Withdraw 的实际物品表导出。后续使用 TestHelper 的 GenKit 表常量
生成器；确认目标项目为 Withdraw、CSV 根目录为外部缓存中的
`E:/Project/AgentHelper/WithDrawCache/ProjectCache/ItemConstants`，并使用 `nameCase = "preserve"`。
临时生成脚本已删除，勿使用其他项目的 CSV 覆盖本项目常量。
