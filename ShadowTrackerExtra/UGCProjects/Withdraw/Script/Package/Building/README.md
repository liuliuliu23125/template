# Building Package

Building 管理基地建筑的玩家等级、升级配置、激活、升级消耗和升级奖励。

包外唯一入口：

```lua
local Registry_Building = require("Script.Package.Building.Registry_Building")
```

`building_data` 的初始化由 `Package_Meta.playerData` 交给 PlayerDataCore。ArmsDealer 的库存、商品和购买流程仍由独立的 ArmsDealer 系统管理；其等级字段仅保留在玩家建筑数据中。

## 升级配置

`Script/Package/Building/Data/Define_Building.lua` 只负责建筑类型、升级记录默认结构、深拷贝和校验。`Script/Config/Package/Building/Config_BuildingUpgrade.lua` 是配置唯一入口：内部维护四类建筑 1 至 29 级的 Lua 原生奖励配置，并负责读取外置表、合并消耗字段与医疗中心治疗增量、校验和缓存最终配置。消耗不在每级 Lua 配置中重复声明；构建缓存时统一补齐 `Item1..Item4`、`Count1..Count4` 为 0，再使用外置表覆盖。

Building 启动时可以读取四张外置消耗表：

```text
Data/Table/Customized/Building/DT_Building_Gym_Config
Data/Table/Customized/Building/DT_Building_InfoCenter_Config
Data/Table/Customized/Building/DT_Building_Medical_Config
Data/Table/Customized/Building/DT_Building_WareHouse_Config
```

所有建筑的外部表可覆盖 `Item1..Item4`、`Count1..Count4`。外部表不存在、缺少行、缺少字段或字段不是数值时使用缓存中的零值消耗。奖励不使用旧的事件枚举字段；医疗中心额外读取 `Recover_Effect`，覆盖对应等级独立 `rewards` 中的治疗效果增量。该值是本次升级的增量，例如 `0.05` 表示增加 5 个百分点，而非升级后的总倍率。非负有限数值有效，`0` 表示无增量；字段缺失时保留 Lua 默认 `0.05`，非法值记录日志并回退。其他建筑奖励仍使用 Lua 配置。可通过 `Registry_Building.ReloadUpgradeConfigs()` 重载，并用 `GetUpgradeConfigSource(buildingType, level)` 查看 `default_cost` 或 `external_cost` 来源。

升级奖励使用统一 `EventType.PlayerEffect_*` 事件，配置在每级 `rewards` 数组中。升级时通过 `UGCEventSystem:SendEvent(eventType, pc, params)` 发送；`GetUpgradeRewards()` 返回完整奖励，`GetUpgradeReward()` 返回首条奖励的数值用于旧 UI 显示。

默认表中的奖励事件为空表示该等级没有可安全执行的默认升级；外部表缺失时不会扣除资源、改变等级或触发奖励，避免把缺失配置误当成零成本升级。
