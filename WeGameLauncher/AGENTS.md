# WeGameLauncher AGENTS

WeGame 启动器与下载更新器（Tenio TP Framework）。负责启动编辑器前的登录、版本校验、下载/更新与异常上报。

## 目录

| 路径 | 说明 |
|---|---|
| `launcher.exe` | 启动器主程序（约 2.8MB） |
| `Tenio.ini` | Tenio 框架配置（UTF-16；DLL 列表、日志开关） |
| `Tenio/` | `TenioTPF.dll`、`TenFact.dll`、`xRender.dll`、`June.dll` 等 |
| `TenioDL/` | 下载器 `TenioDL.exe`、`TNProxy.dll`、P2P、VC90 运行库 |
| `config/Launcher.json`、`Game.json`、`Launcher_remote.json` | 启动器/游戏配置（加密） |
| `config/Cursor.xml`、`CustomEvent.xml`、`name2id.xml`、`uiconfig.xml` | UI 光标、事件、ID 映射、界面配置（明文） |
| `game/` | 登录页/图标/Logo 资源 |
| `tpf_ui/` | Tenio UI：`layout/*.tpf`、`localization/*.xml`、`res/*` |
| `log/` | 启动器日志：`WegameLauncher.<时间戳>.<pid>` |
| `bugreport.exe`、`bugreport_config.ini`、`crash_report_helper.dll`、`dbghelp.dll`、`platform_health.dll` | 崩溃/异常上报 |

## 启动流程（与整机关系）

```text
launcher.exe
  → Tenio 框架 + config/Launcher.json
  → TCLS 登录/版本校验（../TCLS/）
  → TenioDL 下载/更新（缓存见 ../tiny_cache/）
  → 拉起 ../ShadowTrackerExtra/Binaries/Win64/ShadowTrackerExtraUGCEditor.exe
```

## 何时读

- 启动器打不开、登录页异常、更新卡住、下载失败。
- 需要确认日志目录或异常上报配置。
- 需要调整启动器 UI 文案/布局（`tpf_ui/`）前确认影响。

## 约束

- **不要修改** `launcher.exe`、`Tenio*/` DLL、`config/*.json`（加密）。
- `tpf_ui/layout/*.tpf` 是 Tenio 私有 UI 格式，改错会导致启动器白屏。
- `log/` 可安全读取；`tiny_cache/` 是下载缓存，不要手改，清理前先退出启动器。
- 版本/更新服务器配置在 `../TCLS/`，不在本目录。
