# MakeUp Package

MakeUp 负责医疗物品配方查询和服务端制作事务。包外只允许通过
`Script.Package.MakeUp.Registry_MakeUp` 访问制作能力。

## 公共接口

```lua
local Registry_MakeUp = require("Script.Package.MakeUp.Registry_MakeUp")

Registry_MakeUp.GetRecipe(itemID)
Registry_MakeUp.GetCostList(itemID)
Registry_MakeUp.CanCraft(pc, itemID)
Registry_MakeUp.Execute(pc, itemID)
```

`Execute` 仅在服务端执行。它会先校验全部材料，再扣料、发放成品并保存玩家存档；
任一写入失败都会补偿已经完成的物品变更。制作成功后统一提示客户端，并延迟刷新 UI。

配方是包内私有静态数据，当前支持绷带、急救包和医疗箱，单次均产出 1 个。
