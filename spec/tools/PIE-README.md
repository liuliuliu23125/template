# PIE 自动化运行器

> `pie_runner.py` 通过编辑器内置 MCP 的 `ue_pie` 工具启动/停止 PIE，替代手工点「调试」按钮；可跑 AutoTestKit、抓 PIE 窗口截图、汇总日志。

## 前置

1. 编辑器已打开目标工程并登录。
2. MCP Server 已启动：
   - 读 `ShadowTrackerExtra/Saved/Config/WindowsUGCEditor/UGCSettings.ini` 的 `[AskQMCPServer]`。
   - `bAutoStart=True` 时随编辑器启动；显示 `Stopped` 时在 `窗口 → 开发者工具 → 命令行 → MCP Server` 点 `Start Server`。
   - 实际端口以配置为准，本机实测为 `12463`。
3. 首次 PIE 可能弹人脸识别。脚本检测到会以退出码 3 停下并保留客户端，账号本人扫码后 `run --resume` 继续。

## 用法

```bash
python -I spec/tools/pie_runner.py status
python -I spec/tools/pie_runner.py run --no-tests
python -I spec/tools/pie_runner.py run --suite Shield
python -I spec/tools/pie_runner.py run --all-suites --test-timeout 900
python -I spec/tools/pie_runner.py run --resume --suite Shield
python -I spec/tools/pie_runner.py stop
```

- `run` 默认启动 PIE、截图、停止；`--suite` / `--all-suites` 才跑测试。无测试时结果为 `smoke_passed`，不是 `passed`。
- `--resume` 复用已启动的 PIE（不重新 start），结束后同样 stop（除非 `--keep-running`）。
- `--keep-running` 不自动停止，便于人工看画面。
- `--no-screenshot` 跳过截图。
- `--report-dir` 指定产物目录；默认 `spec/pie-runs/<时间戳>/`。
- `--test-target ds|client` 选择测试执行端，默认 `ds`。
- `--test-start-lua` / `--test-status-lua` 用自定义 Lua 片段替换内置测试 adapter。
- `--strict-startup` 把启动期 `[LuaException]` 也升级为阻断；默认只记 warning。

## 产物

| 文件 | 内容 |
|---|---|
| `report.json` | start/status/stop、测试摘要、日志扫描、退出码依据 |
| `screenshot.png` | PIE 客户端窗口截图 |
| `blocked.png` | 阻塞时的截图（人脸识别/对话框） |

## 退出码

| 码 | 含义 |
|---|---|
| 0 | 启动/停止成功；测试通过，或无测试的 `smoke_passed` |
| 1 | 运行时错误 |
| 2 | MCP 不可用（编辑器未启动/端口不一致/Server Stopped） |
| 3 | 人脸识别或阻塞对话框，需人工处理后 `run --resume` |
| 4 | 运行失败：AutoTestKit 不通过，或启停期间的日志命中阻断错误 |
| 5 | 启动或等待超时 |

## 测试 adapter

- 内置 adapter 假定工程使用 `Global_AutoTestKit` + `Script.Core.AutoTestKit.TestRunner.TestManager`：用 `doluastring` 在 DS 里 `RunSuite`/`RunAll`，轮询 `GetSummary()` / `IsQueueRunning()`，用 `print` + `ugcprint` 输出 `AUTOTEST|<run_id>|running=...`。
- 其他工程用 `--test-start-lua` / `--test-status-lua` 提供自己的 Lua 片段；占位符 `{run_id}`、`{player_key}`、`{suite}`、`{all_suites}`。start 片段必须输出 `AUTOTEST_STARTED|<run_id>`，status 片段必须输出 `AUTOTEST|<run_id>|running=...|total=...|passed=...|failed=...`。
- `doluastring` 只返回“片段已执行”，不返回 Lua 返回值；脚本解析本地日志：
  `Saved/Logs/<工程名>/DSlog/FullLog/*_ds__<debugid>_realtime.log`。
  即使 `ue_pie status.server.logs` 为空，这个文件仍会生成。
- `--test-target client` 可改在客户端跑，解析该玩家自己的 `Clientlog/FullLog`；只建议跑不依赖服务端的 suite。
- DS 日志里的 `[UGCApiEnvCheck]` 作为 warning 记录，不阻断；editor/client 的 API env 错误和 DS 的运行期 Lua 错误才阻断。

## Lua 异常判定

- `[LuaException]` 的主记录是 Warning 级：`LogScriptPlugin: Warning: [LuaException] <类别>: <消息>`，后面跟 `>> LuaException Lua Stack:` / `stack traceback:`；部分异常还会有一条 `LogTagLog` 错误镜像。**`stack traceback:` 本身不代表报错**：引擎 warning、玩法自己 `print` 的调试栈（`...----traceback = stack traceback:`）都会带。
- 阻断只看消息里的运行期标记：`attempt to ...`、`stack overflow`、`bad argument #n`、`snippet:<行>:`、类别 `lua_check_failed`、`LogScriptPlugin: Error: [LuaException]`。
- 引擎诊断（`FetchUStructFromTable`、`LuaCacheConflict`、`OperationStatistic`、`LuaExtend_GetProp` 等）的消息里没有运行期标记，即使后面跟着整段 traceback 也只记 warning；模块名 `LuaExceptions.` 的行不是异常，直接忽略。
- 默认只把 **进入 PIE 后** 的客户端错误、**测试开始后** 的 DS 错误当阻断；启动期错误写入 `warnings.client_startup_lua`。`--strict-startup` 可把启动期所有 `[LuaException]` 也当阻断。
- 真实错误样例：`[LuaException] lua_check_failed: stack overflow`、DS 的 `[Core_Registry] Tick 失败，已停用: ... attempt to index a nil value`。
- `python -I spec/tools/pie_runner.py self-test` 用三段真实日志片段验证：引擎 warning + 调试 traceback 不阻断、`lua_check_failed: stack overflow` 阻断、玩法运行期 `attempt to` 阻断，同时验证 DS 日志目录能从 `player.log_path` 推导。

## 限制

- 人脸识别不能绕过，必须账号本人扫码；脚本只检测并停下。
- 截图是屏幕区域抓取；PIE 窗口被遮挡时，脚本会先把它置前再截。
- 首次启动前若工程有脏包，MCP `start` 可能不弹保存框；需要可复现时先保存。
- `ue_pie` 的 `status.server.state` 对 RemoteDS 是 `unknown`，这是预期。

## 实测基线（2026-11-26）

- MCP 服务名 `UGCEditor-PIE` 2.0.0，端点 `http://127.0.0.1:12463/mcp`。
- `ue_pie start` → `session.state=active`、`players[].state=available`、`doluastring` 可用。
- `ue_pie stop` → `session.state=idle`，PIE 客户端进程退出。
- Withdraw 注册 36 个 AutoTest suite。
- `run --suite Shield`：DS 侧 `8/8` 通过，DS 日志出现 `[TestManager] 测试完成: 8/8`；引擎级 `[UGCApiEnvCheck]` 记为 warning。
- 首次 PIE 弹人脸识别；同一编辑器会话验证后不再弹。
