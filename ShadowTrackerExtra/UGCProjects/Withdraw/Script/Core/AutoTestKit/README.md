# AutoTestKit

AutoTestKit 是项目 Core 层的游戏内自动化测试工具。它通过队列逐帧执行 Suite，并统一记录通过、失败和运行时错误。

## 目录

```text
Script/Core/AutoTestKit/
├── Global_AutoTestKit.lua
├── System_AutoTestKit.lua
├── Config/
│   └── Config_AutoTestKit.lua
├── TestRunner/
│   ├── TestManager.lua
│   └── Assert.lua

Script/Config/AutoTestSuite/
├── Suite_VirtualItem.lua
├── Suite_GymUpgrade.lua
├── Suite_MakeUp.lua
├── Suite_Collect.lua
├── Suite_ExpUpgrade.lua
└── Suite_Durability.lua

Script/Setting/
└── AutoTestSuiteIndex.lua  # 自动生成
```

- `Global_AutoTestKit` 是唯一公共入口。
- `System_AutoTestKit` 转发测试操作。
- `TestManager` 管理 Suite 注册、任务队列、Tick 和结果。
- `TAssert` 是 Suite 中可直接使用的全局断言工具。
- `AutoTestSuiteIndex` 是自动生成的运行时 Suite 索引，不手工维护。

## 当前测试

Withdraw 当前包含虚拟物品、健身房升级、制作、收藏、经验升级和耐久测试 Suite。Suite 索引由生成流程自动更新，运行时不会扫描磁盘。

## 公共接口

```lua
Global_AutoTestKit.BeginPlay()
Global_AutoTestKit.Tick(deltaTime)
Global_AutoTestKit.RunAll(playerController)
Global_AutoTestKit.RunSuite(playerController, "GymUpgrade")
Global_AutoTestKit.RunSingleCase(playerController, "GymUpgrade", "升级前_健身房已激活（等级 >= 1）")
Global_AutoTestKit.Stop()
Global_AutoTestKit.IsRunning()
Global_AutoTestKit.GetProgress()
Global_AutoTestKit.GetSuiteDescriptors()
```

`StartQueue(playerController)` 是 `RunAll(playerController)` 的兼容入口，供 `Server_RunAutoTest` RPC 使用。GM UI 复用现有 6 个按钮，每页显示 6 个 Suite，通过上一页/下一页浏览全部 Suite，并通过服务端 RPC 执行全部或指定 Suite。分页只影响显示，不改变 Suite 注册和执行顺序。

PlayerController 同时提供 `Server_RunAutoTest_ByCase` 和 `Server_StopAutoTest`，供后续增加 Case 选择与停止控件时直接接入。

## 新增 Suite

1. 在 `Script/Config/AutoTestSuite` 或其子目录创建 `.lua` 文件，并 `return` 一个包含 `name` 和 `cases` 的表。
2. 运行项目的“生成 AutoTestSuite 索引”流程，更新 `Script/Setting/AutoTestSuiteIndex.lua`。
3. Case 的 `run` 函数返回 `TAssert` 结果；未显式返回时，TestManager 使用最后一次断言结果。

游戏运行时不会扫描磁盘。新增、移动或删除 Suite 后必须重新生成索引，生成文件不要手动编辑。

```lua
return {
    name = "Example",
    cases = {
        {
            name = "示例",
            run = function()
                return TAssert.equals(2, 1 + 1, "基础加法")
            end,
        },
    },
}
```

## 生命周期接入

- `LifeCycle.OnGameStateInit` 由 `Core_Registry` 调用 `Global_AutoTestKit.BeginPlay()` 注册 Suite。
- `UGCGameState.ReceiveTick` 由 `Core_Registry` 调用 `Global_AutoTestKit.Tick(deltaTime)` 推进队列。
- `UGCPlayerController.Server_RunAutoTest` 调用 `Global_AutoTestKit.RunAll(self)`。
- GM UI 的 `AutoServerTest` 按钮通过现有 RPC 启动测试。
