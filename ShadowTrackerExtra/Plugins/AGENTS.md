# Plugins AGENTS

`ShadowTrackerExtra/Plugins/` 下的编辑器/游戏插件。绝大多数是打包后的二进制与资源，**不可重新编译**。

## 插件一览

| 插件 | 大小 | 作用 | 何时读 |
|---|---:|---|---|
| `UGCEditor/` | 2.3G | 编辑器核心插件：Python VM（UEP）、AI 技能、Lua 调试、LuaCheck、触发编辑器、CEF/7z/Subversion | 做编辑器工具、AI 生成、Lua 调试 |
| `UniExtend/` | 153M | `opencode.exe` AI 助手 + `Content/pyScripts` 下 7 套 Python DSL（item/entity/monster/skill/gamemode/interactable/vehicle） | 批量生成/修改资产、用 AI 助手 |
| `PixUI/` | 40M | QuickJS + PixUI 运行时，带 FFmpeg/网络库；用于内嵌 UI/视频 | 排查内嵌界面/媒体播放 |
| `UAEItem/` | 97K | 物品编辑器配置与图标（`ItemEditor.ini`：默认保存路径、ItemDB 资产、模板列表） | 改物品编辑器默认行为 |
| `GameAttributeExtend/` | 45K | 属性编辑器图标资源 | 改属性编辑器 UI |
| `WhatTest/` | 100K | Cook/静态测试配置（`TestConfig.ini`、`CookTestConfig.ini`、`BlackList.ini`）与测试日志 | 排查打包/Cook 测试 |
| `TDM/` | 208K | 仅 `Source/TDM/lib/Win64/cacert.pem`，实际实现内嵌在主程序 | 基本不用 |
| `ZipUtility/` | 3.1M | 7zpp 第三方 DLL（`7z.dll`/`7za.dll` Win32/Win64） | 压缩/解压相关 |

## 关键入口

- 编辑器 AI/工具能力：`UGCEditor/`，见 `UGCEditor/AGENTS.md`。
- Python DSL 与 AI 助手：`UniExtend/`，见 `UniExtend/AGENTS.md`。

## 约束

- **不要修改** `.dll`、`.exe`、第三方库（`ZipUtility/ThirdParty/`、`UGCEditor/ThirdParty/Subversion/`、`PixUI/Binaries/`）。
- 插件没有 `.uplugin` 描述文件（发行版已剥离），不能通过常规 UE 插件流程增删。
- `UGCEditor/Config/BuildServer.ini`、`WhatTest/Content/*.ini` 是部署/测试配置，改前确认影响面。
- 需要新增编辑器能力时，优先用 Python 工具集（`UGCEditor/Resources/UEP`）或 DSL，而不是改插件二进制。
