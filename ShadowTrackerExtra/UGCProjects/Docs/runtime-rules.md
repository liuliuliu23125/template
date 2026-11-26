# Lua 运行期硬规则

> 这些不是风格建议，而是会导致封号、崩溃、静默失效或 Shipping/CE 行为不一致的硬约束。
> 官方来源：绿洲启元 Lua 脚本开发指南（重点说明、编辑器封禁策略）、前置工程检查。

## 何时读

- 写任何会进真机/线上的 Lua。
- 需要文件读写、系统命令、动态加载、外部 URL。
- 访问 UObject / 结构体 / 容器 / C++ 默认参数。
- 代码在 PIE 正常、真机异常，或 Shipping 行为不同。
- 需要确认哪些写法会被编辑器静态检查或封禁。

## 封禁行为（可能封号）

以下操作在编辑器运行时会触发封禁策略，**不要写**：

| 类别 | 禁止项 |
|---|---|
| `os` | `os.execute`、`os.exit`、`os.getenv`、`os.remove`、`os.rename`、`os.setlocale`、`os.tmpname` |
| `io` | `io.close`、`io.flush`、`io.input`、`io.lines`、`io.open`、`io.output`、`io.popen`、`io.read`、`io.stderr`、`io.stdin`、`io.stdout`、`io.tmpfile`、`io.type`、`io.write` |
| `package` | `package.loadlib`、`package.searchpath`、`package.seeall`、`dofile`、`loadfile` |
| `debug` | `debug.debug`、`debug.gethook`、`debug.getlocal`、`debug.getuservalue`、`debug.sethook`、`debug.setlocal`、`debug.setmetatable` |
| 包路径 | 修改 `package.path`、`package.cpath` |
| 文件 C++ 接口 | `FileExists`、`FileSize`、`IsReadOnly`、`GetTimeStamp`、`GetAccessTimeStamp`、`DirectoryExists`、`GetStatData`、`IterateDirectory*`、`DeleteFile`、`MoveFile`、`SetReadOnly`、`SetTimeStamp`、`OpenRead/OpenWrite`、`DeleteDirectory`、`CreateDirectory*` |
| 外部 URL | `UKismetSystemLibrary.LaunchURL`、`CanLaunchURL` |

- 需要读表/配置时，用工程内 DataTable/资源，不要读本地文件。
- 需要外部链接时，走平台/UI 能力，不要直接 `LaunchURL`。

## UObject 与有效性

- UE 销毁的 UObject 在 Lua 里**不是 nil**，而是 invalid object；判断必须用 `UE.IsValid` / `UGCObjectUtility.IsObjectValid`。
- 销毁后建议手动把 Lua 引用置 nil，避免长期持有 invalid 对象。
- 异步加载回调、定时器回调、事件回调里访问 Actor 前先判空 + `IsValid`。
- 不要缓存 UE 管理的 C++ 指针数组的 `Copy()` 结果，UE 释放后会崩溃；用 `ToTable` 缓存。

```lua
local Actor = SpawnActor(...)
Actor:K2_DestroyActor()
if not UE.IsValid(Actor) then
    Actor = nil
end
```

## C++ 默认参数

- Lua 调用 C++ 方法时，省略的默认参数会按 `0x0` 处理，**不是** C++ 声明的默认值。
- 需要默认值时显式传入。

```lua
CPPFunction(1)
```

## 结构体与容器

- 结构体在 Lua 中是 `userdata`，引用传递；属性可直接读写。
- 用 table 给结构体赋值时，未赋字段用 `0x0` 填充；只写部分字段会覆盖其余字段。
- 高频传结构体给 UE 时优先 `Vector.New(...)` / 真实结构体，不要传 table（额外转换开销）。
- `TArray` / `TSet` 在 Lua 中索引是 **1 基**（`[1, N]`），不是 0 基。
- `TMap` 用 key 访问；`pairs()` 可遍历。
- `totable` 仅用于调试：Dev 支持全部结构体/容器，**Shipping 只支持容器**；不要用它做线上逻辑。

## 访问 UObject 数据

- Lua 通过 UE 反射访问：只能访问 `UProperty` 与 `UFunction`。
- 蓝图变量/方法/代理可访问；BPActor 的 Component 默认都是变量。
- UMG 子控件只有勾选 `IsVariable` 才在 Lua 中可见。
- 可重写函数：C++ 的 `BlueprintNativeEvent` / `BlueprintPure`，以及蓝图函数。
- 重写时先调 `SuperClass`：

```lua
function UGCGameMode:ReceiveBeginPlay()
    UGCGameMode.SuperClass.ReceiveBeginPlay(self)
end
```

## 性能相关

- 缓存频繁访问的 C++/蓝图属性；每次访问都有查询开销。
- 避免每帧创建 table/字符串；高频对象用池。
- 不在 `Tick` 里打日志；日志加开关并限频。
- 大量同屏角色可同模，但要在 Pawn 初始化完成后调用，复活后重调。

## 静态检查会命中的写法

| 写法 | 正确做法 |
|---|---|
| 漏写 `local` 的全局变量 | 私有变量加 `local` |
| Lua 放 `Asset/`、蓝图放 `Script/` | 各回各目录 |
| 服务器接口写在客户端分支 | 放进 `IsServer()` 分支，或 RPC 转发 |
| `CallUnrealRPC` 未指定可靠/不可靠 | 明确用 `CallUnrealRPC` 或 `_Unreliable` |
| 有复制属性但缺 `OnRep_` | 补回调或移除复制声明 |
| `Tick` 里打日志 | 移出或加开关 |
| 绝对路径 / 反斜杠 `require` | `Script` 根相对路径、`/` 分隔、不以 `/` 开头 |
| 引用不存在的资源 | 修路径或删除引用 |

- 静态检查结果在 `Output Log → UGC Resource Daemon` / `UGCLogViewer → DaemonLog`。
- 确有例外可用 `--- UGC-CHECK-DISABLE-BEGIN/END` 包裹，但不要用它掩盖真实问题。

## Agent 规则

1. 不写文件、不执行系统命令、不 `LaunchURL`、不改 `package.path`。
2. 所有 UObject 访问先 `IsValid`；销毁后置 nil。
3. C++ 默认参数显式传；结构体用真实类型，不传 table。
4. `TArray/TSet` 按 1 基索引。
5. 不在 `Tick` 打日志；不在循环里创建大量对象。
6. 写完后用前置检查/`luacheck` 自查：全局变量、API 上下文、RPC 可靠性、`require` 路径。

## 本地参考

- 官方 Lua 指南：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=NGuCmpdG>
- 封禁策略：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=NGuCmpdG&anchor=bian-ji-qi-feng-jin-ce-lve>
- 前置检查：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=EI7solUb>
- 本地检查配置：`ShadowTrackerExtra/SpeedupSync/luacheck/check.json`、`ShadowTrackerExtra/Plugins/UGCEditor/Resources/LuaCheck/x64/check.json`
- 相关：`debugging.md`（日志与错误）、`network-replication.md`（复制与 RPC）
