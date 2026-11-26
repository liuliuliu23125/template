# ShadowTrackerExtra AGENTS

游戏模块（等价于 UE 工程的 Content + Binaries + Plugins）。编辑器主程序、UGC 工程、Lua 类型库都在这里。

## 目录

| 路径 | 说明 | 可改 |
|---|---|---|
| `Binaries/Win64/` | 编辑器主程序 `ShadowTrackerExtraUGCEditor.exe`，Wwise、GCloud、MSDK、CrashSight、AntiCheatExpert、SQLite、FastMCP 等 DLL | 否 |
| `Content/LuaHelper/` | Lua/蓝图类型存根库（9068 个 `.lua`，全部 `---@meta`）+ 蓝图类存根 + 模板资产 | 否 |
| `Content/Paks/` | 6 个 `.pak` + 6 个 `.sig`，约 51GB；`core.pak` + 版本补丁 | 否 |
| `Content/WwiseAudio/` | Wwise 音频资产（约 1.7GB） | 否 |
| `Content/WwiseUGCProject/` | Wwise 工程 | 否 |
| `Content/Movies/`、`Splash/` | 启动动画/闪屏 | 否 |
| `Content/Certificates/` | 证书 | 否 |
| `Content/Collections/`、`Developers/`、`pyScripts/` | 空/预留 | 否 |
| `Plugins/` | UGCEditor、UniExtend、PixUI、TDM、UAEItem、GameAttributeExtend、WhatTest、ZipUtility | 见插件文档 |
| `UGCProjects/` | 所有玩法工程（唯一业务区） | 是 |
| `Saved/` | 日志、崩溃、动画录制、缓存、UGC 浏览器数据 | 生成物 |
| `SpeedupSync/` | `luacheck` 配置与 Windows 二进制 | 辅助 |
| `Intermediate/`、`DerivedDataCache/` | 编辑器缓存 | 生成物 |

## 关键事实

- 启动/编辑入口：`Binaries/Win64/ShadowTrackerExtraUGCEditor.exe`。
- 真实玩法代码只在 `UGCProjects/<工程>/Script/`；`Content/LuaHelper` 只是类型库。
- 内容资产以 Pak 形式发布，Pak 内资产不可直接编辑；可编辑资产在工程的 `Asset/`。
- `Saved/Logs/ShadowTrackerExtra.log` 是主日志；`Saved/Logs/<工程名>/` 是按工程的日志子目录。
- `Saved/AnimRecord/` 可达数百 MB，属于编辑器录制缓存。
- `SpeedupSync/luacheck/check.json` 是 Lua 静态检查配置，`luacheck.exe` 在 `Plugins/UGCEditor/Resources/LuaCheck/x64/`。

## 子文档

| 文档 | 何时读 |
|---|---|
| `Content/AGENTS.md` | 区分 LuaHelper、Paks、Wwise 等资产目录 |
| `Content/LuaHelper/AGENTS.md` | 查 UGC API、类、枚举、蓝图类存根 |
| `Content/LuaHelper/Source/AGENTS.md` | 需要在 6 大源码分组中定位 |
| `Content/LuaHelper/Docs/api-index.md` | 77 个 API 库的分类速查 |
| `UGCProjects/AGENTS.md` | 工程选择、目录结构、模板 |
| `UGCProjects/Withdraw/AGENTS.md` | 修改现有撤离项目 |
| `Plugins/AGENTS.md` | 插件能力与边界 |
| `Plugins/UGCEditor/AGENTS.md` | 编辑器工具链、AI 技能、Lua 调试 |
| `Plugins/UniExtend/AGENTS.md` | Python DSL 与 AI 助手 |

## 约束

- 除 `UGCProjects/` 与必要的编辑器配置外，不要写入本模块；更新会覆盖。
- 不要解析/替换 `Content/Paks/*.pak`；需要新资产请在工程 `Asset/` 中制作并由编辑器打包。
- `Saved/` 下内容可删但会丢日志/缓存；排查问题前先保留。
