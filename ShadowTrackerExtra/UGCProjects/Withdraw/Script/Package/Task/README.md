# Task Package

任务包采用“纯数据定义 + metatable 对象 + 运行时服务”的结构。

```text
Const_Task / Define_Task / Define_TaskStepDef
            ↓
        TaskFactory
            ↓
 Task 基类 → Mode/Single / Chain / Multiple
            ↓
 Progression → Story / Daily
            ↓
      TaskStepFactory
            ↓
 TaskStep 基类 → EventTrigger / DataChange / Custom
            ↓
       Reward/TaskReward
            ↓
       TaskService
            ↓
 Registry_Task / Query
```

## 核心约束

- `task_data.activeTaskList` 保存当前可见任务；主线领奖后移除并推进，日常领奖后保留 `COMPLETED` 到下一周期重置。
- `task_data.completedStoryTaskIndex` 保存已领取奖励的最高主线序号，从 `0` 开始且正常流程只递增。
- `task_data.dailyProgressSequence` 与 `dailyTaskTriggerSequence` 记录日常任务有效推进顺序，供主界面在进度相同时优先展示后触发的任务。
- 存档和复制数据始终是纯 Lua table，不保存 metatable。
- `Task` 基类只持有不可变任务定义，并实现所有公共执行流程。
- `TaskSingle`、`TaskChain`、`TaskMultiple`、`TaskMultipleAndChain` 只覆盖模式差异接口。
- `TaskStep` 子类负责单个步骤的监听、匹配和进度计算。
- `TaskProgression` 子类负责领奖后按任务类别移除当前任务并生成后续任务。
- `TaskService` 负责引擎事件、PlayerDataCore 写入、监听缓存和 UI RPC。
- `TaskReward` 负责把扁平奖励配置校验、规范化为 1–4 个物品奖励项。
- UI 和包外代码只通过 `Registry_Task` 查询或调用任务能力。

## 存档结构

```lua
{
    completedStoryTaskIndex = 0,
    dailyProgressSequence = 0,
    dailyTaskTriggerSequence = {
        [1001] = 0,
        [1002] = 0,
        [1003] = 0,
    },
    activeTaskList = {
        [6001] = {
            taskId = 6001,
            status = 3,
            currentStage = 2,
            activeStepIDs = { 1001, 4001, 1003 },
            stepStepsValue = { 1, 2, 0 },
            stepCustomData = {
                [2] = { collectedItemIDs = { 2001, 2002 } },
            },
        },
    },
}
```

旧存档加载时会根据当前主线补齐 `completedStoryTaskIndex`；当前主线为 N 时记为
N-1，已无活动主线时记为最终主线序号。

## Task 对象

`Task.lua` 使用 `Task.__index = Task`，模式子类通过 `Task:Extend()` 继承。Task 只负责组合步骤和驱动模式迁移，不判断步骤类型。主要接口：

```lua
local task = TaskFactory.Create(taskDefinition, stepDefinitions)
local Const_Task = require("Script.Package.Task.Const_Task")
local state = task:CreateState(Const_Task.Status.ACCEPTED)

task:GetActiveStepIndexes(state)
task:GetListenEntries(state)
task:HandleEvent(pc, state, eventType, params)
task:GetProgress(state)
task:GetActiveStepNames(state)
task:IsPendingReward(state)
```

`HandleEvent` 返回新的纯 table 状态与 `changed` 标记，不直接修改玩家数据。基类在进度变化后调用子类的 `ApplyModeTransition`，因此公共执行流程不需要判断任务模式。

## 编排模式

- `Mode/TaskSingle.lua`：执行唯一步骤，达标后进入 `PENDING_REWARD`。
- `Mode/TaskChain.lua`：只监听和执行 `currentStage`，达标后推进到下一阶段。
- `Mode/TaskMultiple.lua`：所有未完成步骤同时活跃，全部达标后进入 `PENDING_REWARD`。
- `Mode/TaskMultipleAndChain.lua`：按顶层步骤组顺序执行，组内步骤并行，组间阶段串行。

`MULTIPLE_AND_CHAIN` 的任务定义可以写成：

```lua
mode = Const_Task.Mode.MULTIPLE_AND_CHAIN,
steps = {
    { 4004, 4005 },
    1003,
},
```

步骤组在任务对象创建时会展开为扁平步骤索引；`activeTaskList` 仍保存扁平的
`activeStepIDs` 和 `stepStepsValue`，避免改变既有存档结构。仅支持一层步骤组。

模式枚举只允许出现在 `TaskFactory`；`TaskService` 和 UI 不判断具体模式。

## 步骤类型

- `Step/TaskStep.lua`：步骤公共基类，负责目标值、完成判断和进度格式化。
- `Step/TaskStepFactory.lua`：唯一允许判断 `Const_Task.StepType` 的位置。
- `Step/Type/TaskStepEventTrigger.lua`：事件触发型步骤，委托 `TaskEventMatchers` 匹配业务参数。
- `Step/Type/TaskStepDataChange.lua`：数据变化型步骤，收到数据包变更事件后主动查询最新值并比较目标。
- `Step/Data/TaskDataResolver.lua`：统一管理 `dataType` 到变更事件的映射、数据路径读取和比较运算符。
- `Step/Type/TaskStepCustom.lua`：自定义步骤边界，仅执行已显式注册的 handler。

`Step/Event/TaskEventMatchers.lua` 属于任务域，集中维护现有业务事件的参数匹配规则。未知事件始终返回未匹配，不会误推进任务。

## 运行时流程

```text
业务事件
  → TaskService.OnPlayerEvent
  → 按 playerKey/eventType 定位任务
  → task:HandleEvent
  → PlayerDataCore 写回 activeTaskList
  → 重建该玩家该任务的监听缓存
  → ON_PLAYER_TASK_DATA_CHANGE
  → 客户端 UI 刷新
```

`DATA_CHANGE` 步骤监听 PlayerDataCore 已有的分类数据变更事件。事件只用来唤醒检查，完成判定始终以 PlayerDataCore 中的实际数据为准。任务接取和存档加载时也会主动检查一次，避免已达标的玩家必须再次修改数据。

`CUSTOM` 步骤可通过 `stepCustomData` 保存纯 table 的步骤专用状态。任务6001使用箱子收集事件记录不同 ItemID；同一 ItemID 只计一种，物品后续丢弃、消耗或出售不会回退进度。

## 配置入口

- `Const_Task.lua`：任务模式、类别、步骤类型、状态、难度和任务 ID。
- `Data/Define_Task.lua`：任务信息、模式、步骤列表和奖励。
- `Data/Define_TaskStepDef.lua`：步骤事件、目标参数和目标值。
- `Config/Package/Task/Config_TaskReward.lua`：从 `DT_Task` 导入并缓存奖励与任务描述覆盖。

撤离成功事件的参数为 `pc, mapID, evacuationMethod`。撤离方式使用
`Const_GameMode.EvacuationMethod`（位于 `Script/Const/Package/GameMode/`）：`FIXED`、`RANDOM`、`SIGNAL_GUN`。
需要区分撤离方式的事件步骤，在 `eventTargetParams` 中配置
`evacuationMethod`；未配置时只按已有参数（例如 `mapID`）匹配。

敌人死亡统一通过 `On_EnemyKilled(pc, monsterID, monsterType, mapID)` 发送。
敌人类型使用 `Const_Enemy.Type`（位于 `Script/Const/Package/Enemy/`）：`NORMAL`、`ELITE`、`BOSS`；
稳定的敌人标识使用 `Const_Enemy.ID`。任务步骤可在 `eventTargetParams` 中配置
`monsterID`、`monsterType` 和 `mapID`，未配置的字段不参与匹配。

敌人死亡也会进入 DebugKit 的玩家检测线 `EnemyDeath`（ID `1003`）。
首次记录某玩家的敌人死亡时自动创建检测记录，详情包含 `monsterID`、`monsterType` 和 `mapID`；
可使用 `DebugKit Sum EnemyDeath` 查看，使用 `DebugKit Clear EnemyDeath` 清理。

任务可通过 `reset` 配置事件触发后的回退阶段和进度策略：

```lua
reset = {
    listenEvents = { EventType.On_PlayerDeath },
    targetStage = 2,
    progressPolicy = Const_Task.ResetProgressPolicy.CLEAR_FROM_TARGET,
}
```

`CLEAR_FROM_TARGET` 保留目标阶段之前的进度并清空目标阶段及之后的进度；
`CLEAR_ALL` 清空全部进度；`KEEP_ALL` 保留全部进度，仅修改当前阶段。
未配置时兼容旧行为，默认回到阶段 1 并清空全部进度。目标阶段不会超过任务当前阶段，
避免重置时跳过尚未完成的前置步骤。

新增普通任务只需增加任务定义和必要的步骤定义，不需要创建新的任务类文件。

## 奖励领取

任务奖励使用 `itemID, count` 成对的扁平数组，每个任务配置 1–4 种物品：

```lua
reward = {
    items = {
        Util_EnumManager.ItemID.GOLD, 500,
        Util_EnumManager.ItemID.Bandage, 3,
    },
}
```

`TaskReward.ParseDefinition` 会验证 ItemID 枚举、ItemSystem 配置、正整数数量和重复项。
`DT_Task` 通过行名匹配任务 ID；`Reward1_ID/Reward1_Count` 至
`Reward4_ID/Reward4_Count` 中 ID、Count 均非 0 的槽位会按顺序整组覆盖 Lua 奖励。
外部配置缺失、全零或非法时记录日志并回退 Lua 默认奖励。

`DT_Task.taskDesc` 是可选的任务描述覆盖字段。字段存在且不等于空字符串时覆盖
`Define_Task` 中的 Lua 默认描述；字段缺失、为 `nil` 或为空字符串时回退 Lua 默认描述。
描述覆盖与奖励覆盖独立处理，奖励无效不会影响合法的任务描述覆盖。

领取仅在 `PENDING_REWARD` 状态执行。服务端按配置发放全部物品；部分添加或任务状态写入失败时，已发物品按逆序回滚。成功后主线任务从 `activeTaskList` 移除并自动创建配置的下一任务；日常任务保留 `COMPLETED` 状态，直到每日周期重置。整个列表只写入一次，重复 RPC 不会重复发奖。

主线顺序通过任务定义中的 `nextTaskId` 显式串联，最终主线使用 `isFinalStoryTask = true`。旧存档中遗留的 `COMPLETED` 状态会在玩家数据加载时被清理并续接下一主线。

## 日常任务生命周期

日常任务与主线任务共用 `activeTaskList`，通过 `category = Const_Task.Category.DAILY`
选择 `TaskDailyProgression`。当前实际定义了三个日常任务：制作医疗物品、出售物品累计获得金币、
使用信号枪撤离；`Const_Task.ID` 中的日常任务 4 仍是预留 ID，尚未加入
`Define_Task.TaskDefinitions`。

日常任务使用 `task_data.dailyTaskCycle` 记录所属周期。周期边界按 DS 本地时间每天 12:00
计算：12:00 前属于前一日周期，12:00 起属于当日周期。

每次日常任务产生有效进度时，`dailyProgressSequence` 递增，并写入该任务在
`dailyTaskTriggerSequence` 中的序号。主界面先比较完成百分比，再比较最后触发序号；旧存档
没有顺序信息时补为 0，并以任务 ID 保证稳定排序。跨周期时两个顺序字段一起清零。

```text
新玩家初始化
  → 创建全部已定义日常任务，状态为 ACCEPTED

领取日常奖励
  → 保留任务记录并标记为 COMPLETED
  → 同周期内不再响应事件或重复领奖

玩家数据加载
  → EnsureDailyTaskState 检查周期
  → 跨周期时重建全部已定义日常任务
  → 迁移或重置发生变化时保存存档

在线跨过 12:00
  → 定时器触发周期检查
  → 保存存档并重建监听缓存
  → 数据变化事件经 RPC 通知客户端刷新 UI
```

`EnsureDailyTaskState` 会遍历 `Define_Task.GetTaskIdsByCategory(DAILY)`，因此新增日常任务定义后，
新玩家初始化、旧存档补建、离线跨周期和在线定时重置都会自动纳入该任务。任务专属 UI、奖励展示、
领奖按钮绑定和对应 AutoTest 仍需显式接入。

## 当前范围

`EVENT_TRIGGER` 和 `DATA_CHANGE` 已完整接通；`CUSTOM` 已接通箱子物品种类与指定物品数量收集处理器，其他自定义需求仍需分别注册 handler。物品奖励领取、主线自动接取、可配置的任务级事件重置，以及日常任务每日 12:00 的在线/离线周期重置均已接通。

当前内容包括 11 个主线任务和 4 个日常任务。日常任务 4（芯片收集）使用 `BACKPACK_ITEM` 步骤，
仅统计背包中 5065～5068 四种芯片，每种目标 2 个；旧物品也计入，仓库不计入。
任务定义的 `realtimeBackpack` 使待领奖步骤继续监听数量变化，丢弃、出售、存仓后可回退为进行中。
`submitBackpackItems` 使领奖先核验并扣除每种 2 个芯片，再发奖、提交任务状态。
领取中使用任务锁；失败按实际扣除量退还材料、撤销奖励，补偿未完成时记录到任务存档，阻止新领取并在重试时继续补偿。
已领奖保持 COMPLETED 到每日 12:00 重置；新周期重新读取现有背包。背包恢复未完成时延迟检查。
服务端背包回调合并刷新，未领奖期间每秒兜底校准；进度未变化时不重复写入任务状态。

## GM 主线任务工具

入口：GMTest → 功能测试 → 主线任务。完成当前主线、重置主线是直接操作按钮；
只有点击“跳转主线任务”才展开分页列表。列表从任务定义读取全部11个主线，
每页3项，共4页，末页仅显示任务10、11。

- 完成当前主线：补齐当前任务全部步骤进度并设为 `PENDING_REWARD`，由玩家手动领奖，
  不自动发奖或推进下一任务。
- 重置主线任务：重建任务1并将已完成主线序号归零，保留非主线任务和其他玩家数据。
- 跳转主线任务：复用 `SetCurrentStoryTask`，设定目标任务及对应的已完成主线序号。
  选择当前任务时保留其现有进度。

按钮分别调用服务端 `Task.CompleteCurrentStory`、`Task.ResetStory`、`Task.SetStoryTask`
指令；通过 PlayerDataCore 同步并保存存档，存档失败会明确提示。
主线奖励领取或补偿未完成时拒绝修改进度。
临时离线验证不在项目中创建 `Tests` 目录，使用标准输入或项目外的 ProjectCache。
