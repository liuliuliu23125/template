# Collect Package

Collect Package 统一管理玩家收藏品、套装完成和套装激活。

Package 外部只通过以下门面访问：

```lua
local Registry_Collect = require('Script.Package.Collect.Registry_Collect')
```

配置、玩家数据、系统操作和查询模块均为 Package 内部实现，不挂载到全局变量。

`collect_data` 的数据结构保持不变。新增类别或物品时修改
`Data/Define_Collect.lua`，并确认 Package Registry 和 Package Meta 索引同步。

套装奖励通过 `rewards` 配置，每条奖励包含统一的 `EventType` 和命名参数：

```lua
rewards = {
    {
        eventType = EventType.PlayerEffect_SkillStateSet,
        params = {
            skillType = Util_EnumManager.SkillType.FIRE_ENCHANT,
            state = true,
        },
    },
}
```

`System_Collect.ActivateSet` 只保存激活状态并发送事件。实际的技能、属性、
背包和仓库效果由 `Script/GamePlay/PlayerEffect` 注册监听并执行，Collect Package
不依赖这些业务 Handler。
