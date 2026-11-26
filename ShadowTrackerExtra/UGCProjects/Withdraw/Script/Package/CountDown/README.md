# CountDown 倒计时系统

游戏时长倒计时模块，用于在特定时间点触发里程碑事件。

## 撤离点开启规则

实际生效的配置为 `Script/Package/CountDown/Data/Define_Milestones.lua`。

| 面板中的撤离点类型 | 枚举值 | 开启时间 |
|---|---|---|
| Normal（默认开启） | `NORMAL = 0` | 开局可用 |
| Random（随机开启） | `RANDOM = 1` | 本局战斗开始后 600 秒，最多随机开启 2 个 |
| Delayed（三分钟后开启） | `DELAYED = 2` | 始终可见，本局战斗开始后 180 秒允许撤离 |

在地图中放置或复制一个 `EvacuateArea`，选中实例，在 **细节 → 撤离设置 →
撤离点类型** 中选择。变量名为 `EvacuateType`，每个实例独立配置，默认 `Normal`。
枚举选项使用英文标识，因为编辑器会将选项名直接导出为 Lua 字段名，中文会导致语法错误。
枚举资源位于 `Asset/Enum/E_EvacuateType.uasset`；Lua 常量位于
`Util_EnumManager.EvacuateType`，两者值必须一致，不要重排已有枚举项。

枚举只是配置入口：`ReceiveBeginPlay` 在服务端和客户端分别调用
`ApplyEvacuateTypeTags`，动态生成 Actor Tag，无需手工添加：

- 默认开启：不带这两种撤离类型 Tag。
- 随机开启：自动添加 `RandomEvacuateArea`。
- 三分钟后开启：自动添加 `DelayedEvacuateArea`。

同步只清理互斥的撤离类型 Tag，保留其他用途 Tag，重复调用不会累加。
现有撤离点已根据原 Tag 迁移为枚举配置；业务逻辑仍使用 `ActorHasTag` 和
`GetAllActorsWithTag`，延迟点不会占用随机名额。
这是关卡实例的初始化配置；运行中直接改枚举不会自动重新计算激活状态。

延迟点开局即可见，开启前不能撤离；玩家进入时仅向该玩家提示
“请等待XX分钟后可以撤离。”。等待时间按本局距180秒的剩余时间计算，
以整分钟向上取整（不足一分钟显示1分钟），玩家重新进入不会重置计时。
开启时会检查 Sphere 内已重叠的玩家，开始原有的
3 秒撤离读条。该点按 `FIXED` 方式记录撤离，离开区域仍取消读条。
服务端通过 `is_active` 复制可撤离状态，普通点和延迟点在所有客户端开局就可见，
无需等待首次状态同步；仅随机点按激活状态同步显隐，支持晚加入。180 秒后在仍运行的
对局中生成的新延迟点会立即开启。大厅不会启动战斗倒计时，提前强制结束也不会
补发开启里程碑。

`Suite_CountDown` 覆盖枚举自动生成 Tag、类型互斥、保留无关 Tag、重复同步、179/180 秒、等待提示及接收玩家、已在区域内、客户端/晚加入、随机名额和提前结束。

## 架构

```
CountDown/
├── Registry_CountDown.lua    -- 入口，注册 BeginPlay/Tick，暴露 Query 接口
├── System_CountDown.lua      -- 核心系统，管理计时器状态
├── Data/
│   └── CountDown_Data.lua    -- 数据初始化与格式化（GameDataCore 调度入口）
├── Adapter.lua              -- 引擎适配层，封装 UGCEventSystem
├── EventType.lua           -- 事件类型常量（无依赖，避免循环依赖）
├── Config/
│   └── Config_CountDown.lua -- 里程碑配置
├── Package_Meta.lua         -- 元数据声明（含 gameData 字段，接入 GameDataCore）
└── Test/
    ├── TestUnit/            -- 单元测试
    └── Bat/                 -- 测试脚本
```

## 数据同步架构

CountDown 的倒计时数据通过 **GameDataCore** 同步给所有客户端：

```
GameState (countdown_data 字段，Replicated)
    ↑
    │ _SyncToGameState() 每帧写入
    │
System_CountDown.Tick(dt)
    ↑ 服务端本地状态 (g_elapsedTime / g_isRunning / g_currentIndex)
    ↑
Registry_CountDown.Tick(dt)  ← UGCGameState:ReceiveTick() 调用
```

客户端读取时从 `gameState.countdown_data` 取:

```lua
Registry_CountDown.Query_ElapsedTimeFromGS()   -- 从 GS 的 replicated 字段读
Registry_CountDown.Query_IsRunningFromGS()
```

## 模块职责

| 模块 | 职责 |
|------|------|
| `Registry_CountDown` | 入口点，注册 BeginPlay 和 Tick，暴露 Query 接口 |
| `System_CountDown` | 核心计时逻辑，Tick 驱动，检查里程碑，同步到 GameState |
| `CountDown_Data` | GameDataCore 调度入口：DataInit(gs) / DataFormat(gs) |
| `Adapter` | 引擎适配，封装事件系统的发送和监听 |
| `Config_CountDown` | 配置里程碑名称和触发阈值 |
| `EventType` | 事件类型常量，所有模块共享，无循环依赖 |

## 生命周期

```
BeginPlay
  └─> Registry_CountDown.BeginPlay()
        └─> System_CountDown.BeginPlay()
              └─> System_CountDown.Start()
                    └─> 设置 g_isRunning = true

Tick(dt)
  └─> Registry_CountDown.Tick(dt)
        └─> System_CountDown.Tick(dt)
              └─> 累加 g_elapsedTime += dt
                    └─> _CheckMilestones()
                          └─> 到达阈值时: _OnMilestoneReached(name)
                                └─> Adapter.SendEvent(EventType.On_MilestoneReached, name)

Service.On_MilestoneReached(name)
  └─> 根据 name 执行对应业务
```

## 里程碑配置

在 `Script/Package/CountDown/Data/Define_Milestones.lua` 中配置：

```lua
Define_Milestones.config_data = {
    { name = "DelayedEvacuateShow", threshold = 3 * 60 }, -- 3分钟
    { name = "RandomEvacuateShow", threshold = 10 * 60 },  -- 10分钟
    { name = "EvacuateFail", threshold = 25 * 60 },         -- 25分钟
}
```

添加新里程碑：
1. 在 `Define_Milestones.config_data` 中按时间升序添加条目，保留到期里程碑在最后
2. 在 `Registry_CountDown.MilestoneName` 中添加常量
3. 在 `Service.On_MilestoneReached()` 中添加处理逻辑

## 依赖关系

为避免循环依赖，采用分层架构：

```
         EventType.lua  (最底层：无依赖)
                    ↑
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
   System      Service    Registry
   _CountDown    .lua     _CountDown
        │           │           │
        └───────────┼───────────┘
                    │
                    ▼
            Registry_CountDown
```

### 为什么要拆分 EventType？

- **问题**：如果事件类型定义在 `Registry_CountDown` 中，`System` 和 `Service` 都需要 require 它，而 `Registry` 又 require `System`，形成循环依赖
- **解决**：将常量提取到独立的 `EventType.lua`，作为无依赖的底层模块

## 单元测试

```bash
# 运行所有测试
Test\Bat\run_all_tests.bat

# 单独运行
Test\Bat\run_test.bat        # Service 测试
Test\Bat\run_test_config.bat # Config 测试
```

测试使用原生 Lua 5.4，需要先配置 `D:\dev\Lua\lua54.exe`。

## Mock 说明

单元测试通过 `package.preload` 和 `_G` Mock 引擎依赖：

| 引擎依赖 | Mock 方式 |
|----------|-----------|
| `UGCEventSystem` | `package.preload` 拦截 + `_G.UGCEventSystem` |
| `UGCGameSystem` | `_G.UGCGameSystem` |
| `GameplayStatics` | `_G.GameplayStatics` |
| `Util_EnumManager` | `_G.Util_EnumManager` |
| `UGCMultiMode` | `_G.UGCMultiMode` |

### 元表拦截机制

使用元表拦截 `_G` 访问，mock 数据存储在局部表 `mockGlobals` 中，避免直接在测试文件写入 `_G.UGCGameSystem = ...`：

```lua
local mockGlobals = {
    UGCGameSystem = { IsServer = function() return true end, ... },
    GameplayStatics = { ... },
}

setmetatable(_G, {
    __index = function(_, key) return mockGlobals[key] end,
    __newindex = function(_, key, value) mockGlobals[key] = value end
})
```

测试结束后恢复原始元表：

```lua
setmetatable(_G, originalMetatable)
```
