# 网络同步、复制与重连

> 多人玩法的数据一致性规则：DS 权威、属性复制从 DS 单向推送到客户端、RPC 双端事件、断线重连后的状态恢复。
> 官方来源：网络同步、Actor 属性复制、弱网与重连指南；本地对应：`Source/Lua/common/unrealnetwork.lua`、各工程 `GetReplicatedProperties`。

## 何时读

- 写多人玩法，需要让客户端看到服务器状态（血量、阶段、积分、机关开关）。
- 客户端要通知服务器（购买、交互、开火、请求数据）。
- 出现“服务器改了但客户端没变”“重连后 UI 不刷新”“RPC 丢了”等问题。
- 设计背包、技能、任务、结算等需要断线恢复的数据。

## 一句话模型

```text
DS 修改状态 → 属性复制 → Client 收到新值 → OnRep_ 回调 / UI 刷新
Client 事件 → RPC → DS 处理
断线重连 → 值复制自动恢复，RPC 不保证恢复
```

- 复制属性固定 **DS → Client**，客户端改值不会回传。
- RPC 是 **事件**，不是状态；重要状态不要只靠 RPC。
- 同一帧内多次改同一属性，只有最后一次值会被同步。

## 属性复制

### 声明方式

在 Actor / Component 的 Lua 类里实现 `GetReplicatedProperties`，返回需要同步的属性名：

```lua
function PeekabooPlayerController:GetReplicatedProperties()
    return "IsUntimely", "IsTransform", "TransformTypes"
end
```

客户端收到后，调用 `OnRep_<属性名>()`；部分模板会带旧值参数（如 `OnRep_CurrentGameStatus(LastGameStatus)`），以实际声明为准，不要假定旧值一定存在：

```lua
function PeekabooPlayerController:OnRep_IsTransform()
    UGCEventSystem:SendEvent(PeekabooModeEventType.IsTransformChange, self, self.IsTransform)
end
```

### 四种复制类型（官方 1.39）

| 类型 | 声明 | 触发 | 适用 |
|---|---|---|---|
| `Lifetime` / Auto | `GetReplicatedProperties` 返回属性名 | 改值后自动比对 | 高频变化：血量、坐标 |
| `RepOnce` / Lazy | `GetReplicatedProperties` 返回 `{ "属性", "Lazy" }` | **必须**主动标记脏 | 绝大多数普通属性 |
| `InitialOnlyList` | `GetInitialOnlyListReplicatedProps` | 首次复制自动下发 | 关卡配置、一次性参数 |
| `Blacklist` | `GetBlackListReplicatedProps` | 永不复制 | 明确不用的父类属性 |

官方推荐的默认选择是 **`RepOnce`（Lazy）**：开销最小、触发时机最可控。

### 标记脏数据

| 场景 | 可用写法 |
|---|---|
| Lua 声明的属性 | 全局 `DOREPONCE(Target, "PropertyName")`，或 `UnrealNetwork.RepLazyProperty(Target, "PropertyName")` |
| C++/蓝图预声明属性 | `DOREPONCE_NATIVE(Target, "PropertyName")` |

- `DOREPONCE` 不在 `unrealnetwork.lua` 的 `---@meta` 中声明，但本地模板可运行：MusicParty、SkillCompetition 等 8 个工程文件在用。
- `UnrealNetwork.RepLazyProperty` 是本地存根声明版本，另有 28 个工程文件在用。
- 两者都是“标记 Lazy 属性为脏”；按所在工程/模板保持一致，不要对同一属性混用。

### 常用约束

- `OnRep_` 回调**不保证顺序**；有强依赖的字段合并到一个 Lua table 同步。
- 客户端不能直接修改复制属性；需要改状态时发 RPC 给服务器。
- 属性是否需要复制按业务判断，默认“不需要就不声明”。
- `InitialOnlyList` 只对首次看到 Actor 的客户端有效，后加入的客户端收不到。
- 值复制适合“状态最终一致”；离散事件（加物品、技能变化）仍需 RPC 或事件补偿。

## RPC

| 接口 | 方向 | 可靠性 |
|---|---|---|
| `UnrealNetwork.CallUnrealRPC(PC, Obj, "Fn", ...)` | 单播，客户端 ↔ 服务器 | 可靠 |
| `UnrealNetwork.CallUnrealRPC_Unreliable(PC, Obj, "Fn", ...)` | 单播 | 不可靠 |
| `UnrealNetwork.CallUnrealRPC_Multicast(Obj, "Fn", ...)` | 服务器 → 所有相关客户端 | 可靠 |
| `UnrealNetwork.CallUnrealRPC_Multicast_Unreliable(Obj, "Fn", ...)` | 广播 | 不可靠 |

### ServerRPC 必须注册

客户端 → 服务器的 RPC，需要在 Controller / Actor 的 `GetAvailableServerRPCs` 中列出函数名：

```lua
function PeekabooPlayerController:GetAvailableServerRPCs()
    return "ServerRPC_ReRandomTransformTypes", "ServerRPC_SelectTransformType", "ServerRPC_LikePlayerByPlayerKey"
end
```

服务器 → 客户端的 ClientRPC 不需要注册。

### 选型

| 场景 | 选择 |
|---|---|
| 低频率、必须送达（Tips、结算、关键交互） | 可靠单播 |
| 高频率、允许丢失（表现、临时音效、位置预测） | 不可靠 |
| 状态同步（血量、积分、阶段） | 属性复制，不用 RPC |
| 广播给所有客户端 | 谨慎用可靠广播；高频广播会拥塞 |

- 同一 Actor 内发送的 RPC 能保证接收顺序；**不同 Actor 之间不保证**。
- 不要把 `CallUnrealRPC` 当状态通道；重连时 RPC 可能丢失。

## 断线重连

### 三种网络状态

| 状态 | 进程 | 判定 | 玩家表现 |
|---|---|---|---|
| 网络波动 | 存在 | 0–5 秒，引擎自动处理 | 短暂卡顿/延迟 |
| 静默断线 | 存在 | 5 秒无包判定断线；300 秒内恢复可重连 | “竞赛服务器响应超时，是否尝试重连” |
| 进程终止 | 不存在 | 300 秒内重新登录可回原局 | “是否重新进入竞赛” |

### 事件

| 事件 | 触发端 | 场景 |
|---|---|---|
| `PlayerControllerLostDelegate` | 服务器 | 静默断线、进程终止断线 |
| `PlayerControllerRecoveredDelegate` | 服务器 | 静默重连成功 |
| `ClientPlayerControllerRecoveredDelegate` | 客户端 | 静默重连成功 |
| `PlayerControllerReconnectedDelegate` | 服务器 & 客户端 | 进程终止后重连成功 |

> 想拿到正确的重连回调，服务端需要同时绑定 `PlayerControllerRecoveredDelegate` 与 `PlayerControllerReconnectedDelegate`。

### 数据恢复差异

| 数据 | 静默重连 | 进程终止重连 |
|---|---|---|
| 复制属性 | 自动恢复最终值 | 自动恢复最终值 |
| 断线期间可靠 RPC | 可收到 | 丢失 |
| 断线期间不可靠 RPC | 丢失 | 丢失 |
| 客户端通过 RPC 缓存的本地状态 | 保留 | 丢失 |

### 处理建议

- **静默重连**：底层已同步数据，只需在客户端重连回调里刷新 UI、关闭断线提示。
- **进程终止重连**：重建 UI、重新请求全量数据、重新初始化玩家状态。
- **重要事件**：可靠 RPC + 客户端缓存，重连时用缓存恢复表现。
- **重要状态**：一律用复制属性，不要用 RPC 传递。

```lua
function PlayerController:OnClientRecovered()
    self:RefreshAllUI()
    if self.NetworkTipWidget then
        self.NetworkTipWidget:RemoveFromParent()
        self.NetworkTipWidget = nil
    end
end

function PlayerController:ReceiveBeginPlay()
    self.SuperClass.ReceiveBeginPlay(self)
    self.ClientPlayerControllerRecoveredDelegate:Add(self.OnClientRecovered, self)
end
```

> 不能只定义同名函数；`OnClientPlayerControllerRecovered` 不是引擎自动调用的回调，必须绑定 `ClientPlayerControllerRecoveredDelegate`。

## Agent 规则

1. 先判断数据是“状态”还是“事件”：状态走复制，事件走 RPC。
2. 复制属性默认用 Lazy/RepOnce；只有高频变化才用 Auto。
3. 改完 Lazy 属性必须显式标记脏（`DOREPONCE` 或 `RepLazyProperty`，按工程写法），否则客户端永远收不到。
4. 不要在客户端写复制属性；不要用 RPC 传关键状态。
5. 同一帧多次改同一属性只保留最后值；强依赖字段合并到一个 table。
6. 重连必须处理两个分支：静默刷新、进程终止重建。
7. 高频/临时表现优先不可靠 RPC；关键通知才用可靠 RPC。

## 本地参考

- 网络库存根：`Source/Lua/common/unrealnetwork.lua`
- 复制声明示例：`UGCProjects/Template_PeekabooZ/Script/Blueprint/PeekabooPlayerController.lua`
- Lazy 标记示例：`UGCProjects/Template_CTCompetition2/Script/Blueprint/UGCGameMode.lua`
- 双端分流示例：`UGCProjects/Withdraw/Script/Blueprint/UGCPlayerController.lua`
- 网络同步 wiki：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=HCf5tKhn>
- Actor 属性复制 wiki：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=mM_eq7bJ>
- 重连机制 wiki：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=lnxVHurr>
- 弱网处理 wiki：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=O9Nh02pZ>
