# Player

负责玩家在本局中的生命周期相关行为。当前只包含死亡盒子定位；属性、物品、任务仍由各自 Package 管理，模式与地图规则仍属于 GameMode。

外部统一通过 `Registry_Player` 调用，不直接依赖 System。Pawn 和 Controller 保留引擎事件及 RPC 接收入口，标记蓝图负责光效和区域检测。

| 模块 | 职责 |
| --- | --- |
| `System/System_PlayerDeadTip.lua` | 死亡序号、真实盒子关联、服务端清理与定向通知 |
| `System/System_PlayerDeadTipClient.lua` | 本地标记生成与替换、复活识别、到达验证和客户端清理 |

调用流程：

- Pawn 死亡 → `OnPlayerDeath`；Controller 创建盒子 → `OnDeadBoxCreated`。
- 本人 Controller 收到 RPC → `ShowDeadTip` / `ClearDeadTip`；复活通知 → `OnPlayerRespawnClient`。
- 标记区域重叠 → `OnDeadTipAreaEntered`；客户端通过原有 RPC 请求服务端 `DismissDeadTip`。
- Controller 结束生命周期 → `OnPlayerEndPlay`，清理计时器、委托和本地 Actor。

状态仍按 Controller 隔离，只在当前对局保留，不进入存档，因此无需 `Package_Meta.lua`。`BeginPlay` 不重复注册死亡监听，也不清空 Actor 已建立的状态。

死亡标记沿用 PlayerDeadTip 的现有软模板粒子；等待关联死亡盒子没有超时限制。到达标记区域、已关联盒子被销毁/隐藏/回收、再次死亡、退出对局时仍清理标记。

死亡时先显示角色位置，随后通过创建回调、Controller 缓存或按 OwnerUniqueID 查找本次新生成的 PlayerTombBox，关联真实死亡箱后同步实际坐标并跟踪移动。场景扫描仅发生在等待关联期间，不会选择其他玩家或死亡前已经存在的箱子。

回归入口：`Suite_PlayerDeadTip`，通过 Registry 调用实际实现。
