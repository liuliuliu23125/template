# Engine AGENTS

打包后的 UE4 引擎侧。**只读**，不含可编译的引擎源码。

## 内容

| 路径 | 说明 |
|---|---|
| `Binaries/Win64/UnrealCEFSubProcess.exe` | 内嵌浏览器子进程；编辑器主程序不在这里 |
| `Content/Editor/` | 编辑器 UI 资源（约 58MB） |
| `Content/Localization/` | 引擎与编辑器本地化（约 575MB） |
| `Content/Slate/` | Slate 图标与样式（约 11MB） |
| `DerivedDataCache/` | 派生数据缓存（可再生成） |
| `Extras/Redist/` | VC 运行库等再分发组件 |
| `Plugins/TWeb2/` | 内嵌 Web 浏览器插件（约 8MB） |
| `Saved/Config/` | 引擎级配置 |

## 事实

- 没有 `Engine/Source/` 与 `Engine/Build/`，无法在此编译 C++ 或新增引擎插件。
- 需要查 UE 类/枚举时，不要去这里：类型存根在
  `../ShadowTrackerExtra/Content/LuaHelper/Engine/Source/`（全部 `---@meta`）。
- 编辑器主程序在 `../ShadowTrackerExtra/Binaries/Win64/ShadowTrackerExtraUGCEditor.exe`。

## 何时读

- 排查内嵌网页、CEF 崩溃、缩放/字体问题。
- 确认引擎本地化文案或 Slate 图标来源。
- 判断某个能力是否属于引擎层（而不是 UGC API 层）。

## 约束

- 不要修改 `Engine/` 下任何文件：升级/校验会覆盖，且没有编译链支撑。
- 不要删除 `DerivedDataCache/` 之外的缓存目录来「优化」；先确认可再生成。
