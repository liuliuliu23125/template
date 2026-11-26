# 调试、日志与故障排查

> 面向 Agent 的排查路径：先定位“看哪里”，再按关键字判断“哪一类错误”，最后按规则修复。
> 官方来源：调试日志说明、PIE 日志面板、环境错误排查、HotReload、前置工程检查、PIE 失败排查；本地对应：`ShadowTrackerExtra/Saved/Logs/`、`ShadowTrackerExtra/Plugins/UGCEditor/Resources/LuaCheck/`。

## 何时读

- 功能“没生效”但不崩溃、没有明显报错。
- 需要看 Client / DS 日志、PIE 实时日志、手机日志或服务端日志。
- Lua 报错、堆栈定位、断点调试、热重载。
- PIE 启动失败、上传失败、环境检查报错。
- 需要判断某条日志是业务日志、Lua 异常还是 API 环境错误。

## 日志函数与可见性

| 函数 | PIE Client | PIE DS | 真机 Client | 真机 DS |
|---|---|---|---|---|
| `print` | 是 | 是 | 是 | 是 |
| `ugcprint` | 是 | 是 | **否** | **是** |

- 真机上 `ugcprint` 只进 DS 日志；需要客户端日志时用 `print`。
- 日志量过大会阻塞 DS；高频日志必须加开关或限频，不要在 `Tick` 里直接打。
- 常用：`ugcprint`、`ugcprint_format`、`ugcprint_withlevel`、`ugcprint_concat`、`ugctagprint`。
- 打印对象用 `UE.GetFullName(Obj)` / `UE.GetName` / `UE.GetPathName`，比 `tostring` 更有定位价值。

## 日志位置

| 场景 | 路径 |
|---|---|
| 编辑器主日志 | `ShadowTrackerExtra/Saved/Logs/ShadowTrackerExtra.log` |
| 按工程的 PIE 日志 | `ShadowTrackerExtra/Saved/Logs/<工程名>/Clientlog`、`.../DSlog` |
| 崩溃 | `ShadowTrackerExtra/Saved/Crashes/` |
| CEF/登录页 | `ShadowTrackerExtra/Saved/Logs/cef3.log` |
| 手机客户端日志 | `Android/data/com.tencent.tmgp.projectg/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Logs` |
| 真机服务端日志 | 绿洲启元管理端 → 日志提取 → 项目日志，按 `game_id` 查 |
| MCP 调用日志 | 编辑器 MCP 面板 → Open Log Folder，`MCP_YYYYMMDD.log` |

> 服务端在云端：PIE 下需要停止调试才能拿到完整 DS 日志；真机 DS 日志从管理端下载。

## 三个高频入口

### PIE 日志面板（UGCLogViewer）

- 左侧按当前 PIE 会话列出 Client 1/2、DS 1/2 日志文件。
- 过滤：User Log（`ugcprint*`）、Lua Log（普通 Lua 日志）、Error Log（`LuaException`）、All。
- 搜索只作用于当前选中文件，支持大小写与整词匹配。
- 带 `Script/xxx.lua:行号` 的日志可直接跳转源码。
- `Clear (Keep only new logs)` 只移动显示起点，不删除磁盘文件。

### Lua 控制台

- 先启动 PIE，再打开 Lua 控制台。
- `connect` 连接 DS 或客户端；`help` 查看指令；交互模式可实时执行 Lua。
- 支持热更新 Lua module；Actor 的 `OnHotReload` 会按实例逐个触发。
- 蓝图绑定的原生事件不会自动热更；需要把逻辑放到 Lua 内层函数再热更。

### 角色调试工具

- 技能/Buff/属性三个面板：选中目标，快速增删技能/Buff、改 CD/消耗、查看运行时属性。
- 适合数值与表现迭代，不替代日志。

## 环境错误：最容易被忽略的一类

客户端调用服务器接口、或服务器调用客户端接口时，框架会输出：

```text
[UGCApiEnvCheck] API 调用环境错误:
UGCFakePlayerSystem.GetRandomAIPlayerKey 生效范围[服务器], 当前环境[客户端]
```

- **不会崩溃、不会中断代码**；接口通常返回 `nil/false`，表现为“功能没生效”。
- 调用栈里 `UGCApiEnvCheck.lua` 那一帧是检查层，真正要改的是它下面业务的 `Script/...:行号`。
- 排查：搜关键字 `[UGCApiEnvCheck] API 调用环境错误` → 看接口生效范围 → 调整到 `IsServer()` 分支或改用跨端 RPC。
- 只在接口有 `---生效范围` 标注时触发；未标注接口不会报。

## 静态前置检查

编辑器打开工程后会在后台跑 `UGC Resource Daemon` 实时检查（提示，不阻断）。重点规则：

| 规则 | 典型提示/修复 |
|---|---|
| Lua 语法 | `Lua 语法错误：...`，按行号修 |
| 文件位置 | Lua 在 `Asset/`、蓝图在 `Script/`，放回正确目录 |
| 全局变量 | 漏写 `local`，补 `local` 或改名 |
| API 上下文 | 服务器/客户端接口用错，移入 `IsServer()` 分支 |
| 参数个数 | 与签名不一致 |
| 废弃 API | 按提示换替代接口 |
| RPC/复制 | `CallUnrealRPC` 未指定 Reliable/Unreliable；有复制属性但缺 `OnRep_` |
| Tick 日志 | `Tick` 中打日志，移出或加开关 |
| 路径写法 | 绝对路径/反斜杠，改为 `Script` 根相对路径、`/` 分隔 |
| 资源引用 | 引用了不存在的资源；`DataTable` 会带行/列 |

- 结果出口：错误弹窗、Output Log 的 `UGC Resource Daemon` 页签、`UGCLogViewer → DaemonLog`。
- 每条结果给 `描述 + (文件:行号) + => 修复建议`，优先按 `=>` 改。
- 确有例外可用成对独占行注释放行：

```lua
--- UGC-CHECK-DISABLE-BEGIN
--- UGC-CHECK-DISABLE-END
```

## HotReload

- 触发：PIE 窗口底部「HotReload Lua」按钮；自动扫描 `Script/` 变更并下发到 DS 与客户端。
- 生效：函数逻辑替换、模块变量保留、upvalue 嫁接、LuaBind 蓝图函数重绑定。
- 不生效：新增变量的初始化表达式、已注册 timer/协程里的旧闭包、非 LuaBind 的蓝图绑定。
- 模块实现 `OnHotReload(self)` 可重新订阅事件、刷新缓存、重启 timer/协程。
- 硬限制：模块名必须以 `Script` 开头；重新 PIE 后要等客户端重新注册；DS 热更需要至少一个客户端中转。
- 热更友好的写法：状态放模块表字段、纯函数逻辑、timer 回调引用模块表函数、只改函数体不改结构。

## PIE / 上传失败速查

| 日志关键字 | 含义 | 处理 |
|---|---|---|
| `remaining debug count is zero` | 当日调试次数用完 | 次日恢复 |
| `debug precondition check failed` | 未登录/工程未打开 | 检查登录与工程 |
| `invalid type of asset detected` | 不支持的资产 | 看 Output Log 路径，删除/修复 |
| `SubModeID=... does not exist` | 子模式配置不一致 | 对齐 `.ugcproj` 与代码 |
| `upload file name validation failed` | 文件名含中文/空格/过长 | 改英文数字下划线短名 |
| `lua file validation failed` | Lua 校验失败 | 看 Lua 错误详情 |
| `DS Failed!` | DS 启动失败 | 看 DS 日志，多为工程逻辑错误 |
| `Illegal API calls found in Lua` | 使用了不合法 API | 按文件列表移除 |
| `Illegal file types found` | 工程含 exe/dll/bat 等 | 移除非法文件 |
| `Daily upload limit reached` | 当日上传次数上限 | 次日恢复 |
| `Version mismatch` | 编辑器/服务端版本不匹配 | 按推荐版本更新 |

上传失败的工程侧高频原因（约 65% 集中在 1、2）：

1. `ReferenceAssetList` 引用了不存在/已删除/重命名的资源。
2. 引用了其它工程的资源（UGC 工程资源隔离）。
3. 资源过大导致 Cook OOM；清理无用资源、降分辨率、LOD、软引用/异步加载。
4. `DataTable` 的 `RowStruct` 丢失。
5. Shader 编译崩溃，常与跨工程引用或复杂材质叠加。

## Agent 排查顺序

1. **确认现象**：没生效、报错、崩溃、还是超时。
2. **确定端**：Client / DS / 手机 / 管理端；`ugcprint` 真机只在 DS。
3. **先搜关键字**：`LuaException`、`stack traceback`、`a nil value`、`[UGCApiEnvCheck]`、`PIE debug failed`、`DS Failed`。
4. **再看静态检查**：`UGC Resource Daemon` / `DaemonLog`，优先按 `=>` 修复。
5. **需要实时状态**：PIE 日志面板、Lua 控制台、角色调试工具。
6. **改完验证**：热重载或重启 PIE；不要用“日志没打出来”判断逻辑没执行，先确认端和日志级别。

## 本地参考

- 日志目录：`ShadowTrackerExtra/Saved/Logs/`
- Lua 检查配置：`ShadowTrackerExtra/SpeedupSync/luacheck/check.json`、`ShadowTrackerExtra/Plugins/UGCEditor/Resources/LuaCheck/x64/check.json`
- Lua 调试扩展：`Plugins/UGCEditor/Resources/LuaDebugTool/`
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=CplApOBZ>（调试日志）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=RFFDnLNY>（PIE 日志面板）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=ztKMBEKK>（环境错误）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=7g3Yj6l8>（HotReload）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=EI7solUb>（前置检查）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=fl1TFNAM>（PIE 失败）
