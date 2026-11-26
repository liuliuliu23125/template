# UGCEditor AGENTS

编辑器核心插件（约 2.3GB）。提供编辑器 UI 资源、Python 工具集运行时、AI 技能、Lua 调试/检查、触发编辑器与打包辅助。

## 目录

| 路径 | 说明 |
|---|---|
| `Binaries/Win64/` | CEF（`libcef.dll`、`UGCEditorCefSubProcess.exe`）、DX 编译 DLL |
| `Config/BuildServer.ini` | 构建服务器配置（当前值 `4`） |
| `Content/NoBinaryFile/Web/ProjectBrowser/` | 工程浏览器 Web UI |
| `Resources/UEP/` | **Python 运行时**：3.11.1 用 `PythonVM/`；`Python3/Win64/` 是 3.7.7 遗留；`Win64/` 含 3.11 DLL 与 `Lib/site-packages` |
| `Resources/Skills/ugc-vfx-gen/` | AI 特效生成技能（SKILL.md + references） |
| `Resources/LuaDebugTool/` | VSCode EmmyLua 扩展（`UGC_Lua_Visx`）与安装脚本 |
| `Resources/LuaCheck/x64/` | `luacheck.exe` + `check.json`（禁用 `os.*`、`io.*`、`debug.*`、`dofile` 等） |
| `Resources/UGCTriggerEditor/` | 触发器 Lua 模板：`LuaActionTemplate.lua`、`LuaConditionTemplate.lua` |
| `Resources/UGCAIGC/` | AI 语义搜索提示词与缩略图（动画/材质/粒子/图片） |
| `Resources/UGCCGameTechArtToolkit/`、`Slate/`、`Windows/` | 图标与编辑器 UI 资源 |
| `Resources/7z/x64/` | 7z 压缩工具 |
| `ThirdParty/Subversion/`、`Binaries/` | SVN 与第三方二进制 |

## 关键能力

### Python 工具集（UEP）

- 编辑器 Python 工具集（3.11.1，入口 `PythonVM/`；`Python3/Win64/` 是 3.7.7 遗留），暴露 `ue.*` 与 `objed_*` 接口，用于批量改资产、查询模板、创建资产。
- 与 `UniExtend/Content/pyScripts/toolset_proxy.py` 配合：Python 侧通过 `ToolsetProxy("ObjectToolset")` 调 C++ Toolset。
- 异步：`UniExtend` 的 `ugc_asyncio` 在编辑器主线程上用 tick 驱动事件循环，禁止 `run_forever`。

### AI 特效技能

`Resources/Skills/ugc-vfx-gen/SKILL.md` 是特效生成的操作手册，**做 VFX 前必须先读**。已记录的关键事实：

- 唯一创建入口 `ue.objed_create_asset`，`editor_type` 固定 `'Asset'`（6 种之一）。
- `asset_type`/`template_name` 必须逐级查询，不能猜；`template_name` 字段不叫 `name`。
- 只用 `create_method == "Duplicate"` 的模板。
- `sub_dir`/`asset_name` 必须 ASCII，中文会抛 `ValueError`。
- 改发射器参数必须按 `Distribution.get_path_name()` 去重，否则重复缩放。
- **本工程无 Niagara**，只有 Cascade（`UParticleSystem`）；没有 `ue.particle_*` API。
- 一次创建不超过 3 个资产。

细节见同目录 `references/api-reference.md`、`pitfalls.md`、`workflow-recipes.md`。

### Lua 调试与检查

- `LuaDebugTool/Install_Visx.bat` / `Install_Visx.py`：安装/注册 EmmyLua 扩展。
- `LuaCheck/x64/luacheck.exe` + `check.json`：静态检查；`SpeedupSync/luacheck/check.json` 是工程侧配置。
- Lua 断点调试由 EmmyLua 扩展 + 编辑器内置调试服务完成。
- 自动启动/停止 PIE、跑 AutoTestKit、截图取日志：`spec/tools/pie_runner.py`（走 MCP `ue_pie`），见 `spec/tools/PIE-README.md`。

### 触发器编辑器

- `UGCTriggerEditor/LuaActionTemplate.lua`：`Execute(...)`，可选 `Update(DeltaSeconds)`（需勾选 EnableTick）。
- `UGCTriggerEditor/LuaConditionTemplate.lua`：`IsSatisfy(...)` 返回布尔。
- 生成到工程的 `Script/gamemode/Action_*.lua` / `Condition_*.lua`。

### AI 资源搜索

`UGCAIGC/*Prompt.txt` 定义动画、材质、粒子的语义搜索提示词；`Common_AISearchResource*` 是资源描述索引。配合 Python 侧 `ue.ai_search(...)` / `ue.ai_search_types()`。

## 约束

- 不要改 `Binaries/`、`ThirdParty/`、`Resources/UEP/` 下的 Python 标准库与 DLL。
- 不要绕过 `Skills/ugc-vfx-gen` 的流程臆造粒子 API。
- MCP Server 与 UGC 账号登录是 AI 技能的前置条件；本目录只含技能与工具集，不含 MCP 服务实现。
- 编辑器更新会覆盖本目录；自定义工具放在工程或独立目录。

## 文档

| 文档 | 何时读 |
|---|---|
| `Docs/mcp.md` | 启动/连接 MCP、支持的编辑器能力、安全限制 |
| `Docs/toolchain.md` | Python 工具集、MCP、技能、调试、触发器的整体关系 |
| `Resources/Skills/ugc-vfx-gen/SKILL.md` | 生成/修改粒子特效前 |
| `Resources/Skills/ugc-vfx-gen/references/pitfalls.md` | 特效参数写入、模板、发射器问题 |
