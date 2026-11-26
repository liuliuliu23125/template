# Content AGENTS

游戏与编辑器的资产根目录。除 `LuaHelper/` 外，内容基本以打包资产或第三方媒体形式存在。

## 目录

| 路径 | 说明 | 可改 |
|---|---|---|
| `LuaHelper/` | Lua/蓝图类型存根库（无模板资产）；见 `LuaHelper/AGENTS.md` | 否 |
| `Paks/` | 6 个 `.pak` + 6 个 `.sig`（约 51GB）：`core.pak` + 版本补丁 | 否 |
| `WwiseAudio/` | Wwise 音频资产（约 1.7GB） | 否 |
| `WwiseUGCProject/` | Wwise 工程文件 | 否 |
| `Movies/`、`Splash/` | 启动动画、闪屏 | 否 |
| `Certificates/` | 证书 | 否 |
| `Collections/`、`Developers/`、`pyScripts/` | Collections 空；Developers 下是本机用户的 `Collections`；pyScripts 空/预留 | 否 |

## 规则

- 玩法资产在 `../UGCProjects/<工程>/Asset/`，不要试图改 Pak 内资产。
- 需要查 UGC API/类/枚举：`LuaHelper/AGENTS.md`。
- 音频制作在 Wwise 工程内完成，导出后由编辑器打包。
- 本目录除 `LuaHelper/` 外没有可读的 Lua 源码；`LuaHelper` 里也全是 `---@meta` 存根。
