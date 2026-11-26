# 编辑器工具链

> 说明编辑器侧「Python 工具集 / AI 助手 / DSL / 技能 / Lua 调试」如何拼在一起。
> 具体特效流程见 `../Resources/Skills/ugc-vfx-gen/SKILL.md`。

## 分层

```text
AI 助手 / MCP 客户端
  → opencode.exe + CodeBuddy provider        UniExtend/Resources/UGCAskQ/OpenCode/Config/ugcaskq.json
  → MCP 工具 / ue_py Python 调用
      → ue.* / objed_* / ai_search          编辑器 C++ 暴露的 Python 接口
      → toolset_proxy.py                    Python → UGCAskQToolsetBridge → C++ Toolset
      → ugc_*_dsl（可选）                    领域 DSL：规划 → 执行 → 回读校验
  → 资产写入 / 编辑器状态
  → Lua 检查 / 调试                          LuaCheck、LuaDebugTool
```

## Python 工具集（UEP）

- 运行时：`Resources/UEP/`；3.11.1 用 `PythonVM/python.exe`，`Python3/Win64/` 为 3.7.7 遗留；`pyth0n3.dll` 是为规避 DLL 重定向做的改名，`fix.py` 负责修补站点包。
- 暴露面：
  - `ue.*`：编辑器/引擎 Python 接口，如 `ue.objed_create_asset`、`ue.objed_query_templates`、`ue.objed_open_asset`、`ue.ai_search`、`ue.log`。
  - `ue_read`：MCP 风格的只读查询入口（如 `status:`、`objed` 的 `editor_types/asset_types/templates`）。
  - `objed_*`：物编（Object Editor）资产创建/查询/打开。
- 约束：
  - 查询参数需按实际签名传：`objed_query_templates` 只接受位置参数（文档串写错）。
  - 返回值可能是 JSON 字符串或聚合字符串，不要当 list 遍历。
  - 路径/子目录必须 ASCII（编辑器 `IsFilenameValidForSaving` 在 UGC 下拒绝中/日文）。

## toolset_proxy

`UniExtend/Content/pyScripts/toolset_proxy.py` 是 Python → C++ Toolset 的安全桥：

```python
from toolset_proxy import ToolsetProxy

obj_ts = ToolsetProxy("ObjectToolset")
obj_ts.SetProperties(InstancePath="/Game/BP_X", ValuesJson='{"Health":100}')
```

- 强制关键字参数；拒绝裸 UObject wrapper；错误统一为 `ToolsetError`（含 `qualified_name` / `error_detail`）。
- 调用方只需 `try/except ToolsetError`。

## DSL 四接口

7 个领域包（`UniExtend/Content/pyScripts/ugc_*_dsl/`）共享同一套协议：

| 接口 | 作用 |
|---|---|
| `DslSet` | 把 DSL/IR 写入资产；支持 `PlanOnly=True` 只出计划 |
| `DslGet` | 读回资产的 DSL 视图 |
| `PropSet` | 按属性名写少量字段 |
| `PropGet` | 按属性名读回并校验 |

统一信封（`_envelope.py`）：

```python
{"success": bool, "error_code": str|None, "message": str,
 "retryable": bool, "state_changed": bool, "data": any, "warnings": list}
```

调用方只看 `success`；失败时按 `error_code` 处理（`INVALID_ARGUMENT`、`NOT_FOUND`、`VERIFY_FAILED` 等）。

分层实现（每个包一致）：

| 文件 | 职责 |
|---|---|
| `_envelope.py` | 信封、错误码、`@tool` 装饰器、`describe` |
| `_toolchain.py` | 定位/加载外部工具链（如 `ugc-workflow-monster`） |
| `field_table.py` / `scope.py` | 字段表、IR 顶层键范围与预检 |
| `dsl_api.py` | 纯 Python 规划层：DSL/IR → plan |
| `dsl_runner.py` | 编辑器内执行：写入 → 保存 → 重载 → 读回比对 |
| `dsl_toolset.py` | 四接口、Lua 装配、warnings、信封 |
| `__init__.py` | 导出 `TOOLSETS`、`_LOAD_ORDER`、`describe` |

领域包：

| 包 | Toolset | 领域 |
|---|---|---|
| `ugc_item_dsl` | `ItemDslToolset` | 物品/武器/消耗品 |
| `ugc_entity_dsl` | `EntityDslToolset` | 实体/武器/抛体 |
| `ugc_monster_dsl` | `MonsterDslToolset` | 怪物/刷怪器 |
| `ugc_combat_skill_dsl` | `CombatSkillDslToolset` | 技能/Buff |
| `ugc_gamemode_dsl` | `GamemodeDslToolset` | 玩法模式 DA/GameMode 蓝图 |
| `ugc_interactable_dsl` | `InteractableDslToolset` | 交互物 |
| `ugc_vehicle_dsl` | `VehicleDslToolset` | 载具 |

## MCP Server

编辑器内置本机 MCP（Streamable HTTP），端点 `http://127.0.0.1:<port>/mcp`，端口读 `UGCSettings.ini` 的 `[AskQMCPServer]`（本机 12463）；入口 `窗口 → 开发者工具 → MCP Server`。支持场景/Actor、技能、物品、行为树、蓝图、UMG、数据表、实体与视窗操作；不支持特效/音频编辑器。接入步骤、客户端配置与限制见 `mcp.md`。

## 异步

`ugc_asyncio` 在编辑器主线程上提供 asyncio 事件循环（16ms tick 驱动）：

- `ugc_asyncio.run(coro)`：同步语义跑完协程。
- `ugc_asyncio.schedule(coro)`：后台推进，立即返回，长任务用 `await asyncio.sleep(0)` 让出。
- 禁止 `run_forever` / `run_until_complete` 阻塞主线程。

## AI 技能

- 位置：`Resources/Skills/<skill>/SKILL.md` + `references/`。
- 现有：`ugc-vfx-gen`（粒子特效生成）。
- 结构：frontmatter（`name`/`description`/触发词/前置条件）→ 铁律 → 主线流程 → 参考文件。
- 新增技能时：先写触发条件与硬约束，再把细节放 `references/`，不要在 SKILL.md 里堆长文。

## AI 助手

- `UniExtend/Binaries/Win64/opencode.exe`（约 158MB）。
- 供应商配置：`UniExtend/Resources/UGCAskQ/OpenCode/Config/ugcaskq.json`（CodeBuddy，多模型）。
- 配置目录下 `AGENTS.md` 是该助手的开发测试说明，不是编辑器总规范。

## Lua 调试与静态检查

| 工具 | 位置 | 用途 |
|---|---|---|
| EmmyLua 扩展 | `Resources/LuaDebugTool/UGC_Lua_Visx/` | 断点、调用栈、变量查看 |
| 安装脚本 | `Resources/LuaDebugTool/Install_Visx.bat/.py` | 注册到 VSCode |
| luacheck | `Resources/LuaCheck/x64/luacheck.exe` | 静态检查 |
| 检查配置 | `Resources/LuaCheck/x64/check.json`、`SpeedupSync/luacheck/check.json` | 禁用 `os.*`/`io.*`/`debug.*`/`dofile` 等 |

## 触发器

- 模板：`Resources/UGCTriggerEditor/LuaActionTemplate.lua`、`LuaConditionTemplate.lua`。
- Action：`Execute(...)` 返回布尔；勾选 EnableTick 后每帧 `Update(DeltaSeconds)`。
- Condition：`IsSatisfy(...)` 返回布尔，决定是否执行 Action。
- 生成位置：工程 `Script/gamemode/`。

## 扩展建议

1. **加一个 DSL 领域**：复制现有包结构，保持 `PlanOnly` 规划层纯 Python、执行层可回读校验、四接口与信封一致。
2. **加一个技能**：在 `Resources/Skills/` 新建目录，写 `SKILL.md`，把易错点放 `references/pitfalls.md`。
3. **加批量脚本**：优先用 `ue.*` + `toolset_proxy`，不要直接改 `.uasset`。
4. **先 Plan 后执行**：`PlanOnly=True` 检查计划，再实际写入，最后 `PropGet/DslGet` 校验。
5. **遵守编辑器限制**：路径 ASCII、单次创建 ≤3 个资产、粒子仅 Cascade、无 Niagara。
