# 目录与启动链路

> 本文解释编辑器安装目录「谁负责什么、哪些不能改、出问题先看哪里」。API 与玩法开发见 `../ShadowTrackerExtra/Content/LuaHelper/AGENTS.md` 与 `../ShadowTrackerExtra/UGCProjects/AGENTS.md`。

## 版本

- 安装版本：`version.txt` → `1.39.13.16220`
- 工程版本（Withdraw）：`1.39.13.16226`（`.ugcproj` 的 `Version`）
- 启动器配置版本：`TCLS/config/version.cfg`

## 顶层目录职责

| 路径 | 职责 | 可改 |
|---|---|---|
| `.claude/skills/` | 本机 Claude Code skill（需求拆解工作流等） | 可改（文档） |
| `spec/` | 需求拆解产物（按需生成，工作区） | 可改 |
| `Engine/` | 打包的 UE4 引擎侧：Editor 资源、本地化、Slate、TWeb2 浏览器、CEF 子进程 | 否 |
| `ShadowTrackerExtra/` | 游戏模块：编辑器主程序、游戏 DLL、Content、Plugins、UGCProjects | 业务区之外只读 |
| `ShadowTrackerExtra/Content/LuaHelper/` | Lua/蓝图 **类型存根库**（全部 `---@meta`），供 IDE 补全 | 否（会被更新覆盖） |
| `ShadowTrackerExtra/Content/Paks/` | 6 个 `.pak` + 6 个 `.sig` 共约 51GB，游戏与编辑器资产 | 否 |
| `ShadowTrackerExtra/UGCProjects/` | 所有可编辑玩法工程；唯一日常业务区 | 是（工程内 `Script/`、`Asset/`） |
| `ShadowTrackerExtra/Plugins/` | 编辑器/游戏插件，见 `Plugins/AGENTS.md` | 否（工具配置除外） |
| `ShadowTrackerExtra/Saved/` | 日志、崩溃、缓存、UGC 浏览器缓存 | 生成物，不手改 |
| `FeaturePacks/` | 预留功能包目录，当前为空 | 否 |
| `TCLS/` | 腾讯登录/版本/目录服务配置 | 否 |
| `WeGameLauncher/` | WeGame 启动器与下载更新器 | 否 |
| `rail_files/` | WeGame 平台识别：`game_id=2001776`、构建信息、关键文件清单 | 否 |
| `tiny_cache/` | 启动器 CDN 下载缓存（`.wgj`、`.manifest`） | 否 |
| `安卓/` | 同版本 Android APK（约 2GB） | 否 |
| `Manifest_NonUFSFiles_Win64.txt` | 分发文件清单（约 5.5MB） | 否 |
| `*卸载.exe` | 两个卸载器：标准版、兼容性适配版 | 否 |

## 启动链路

```text
WeGameLauncher/launcher.exe
  ├─ Tenio/、TenioDL/          启动器 UI 与下载框架
  ├─ config/Launcher.json     启动器配置（加密）
  ├─ config/Game.json         游戏配置（加密）
  ├─ log/                     启动器日志
  └─ 拉起 ShadowTrackerExtra/Binaries/Win64/ShadowTrackerExtraUGCEditor.exe
        └─ 读取 ShadowTrackerExtra/Saved/Config 与 UGCProjects/<工程>.ugcproj
              ├─ StartMapName     起始地图（.umap）
              ├─ GameModePath     蓝图 GameMode（.uasset）
              └─ Script/          同名 Lua 通过 `--Edit Below--` 绑定到蓝图
```

根目录的 `ShadowTrackerExtraUGCEditor.exe`（136KB）是入口/引导程序；真正的编辑器主程序在 `ShadowTrackerExtra/Binaries/Win64/`，同目录还有 Wwise、GCloud、MSDK、CrashSight、反作弊等 DLL。

## 更新与版本校验

- `TCLS/config/VersionServerConfig.xml`：版本服务器地址（`tcls.rail.qq.com` 等 4 个）。
- `TCLS/config/updateconfig.cfg`：更新通道/文件列表配置。
- `TCLS/mmog_data.xml`、`TCLS/config/*.cfg/.xml`：登录与目录服务配置。
- `TCLS/` 下的 `*.bak`、`*.tmp` 是更新过程备份/临时文件，不要当作配置源。
- `rail_files/rail_game_build_info.dat` 记录本次构建的清理路径（`clean_paths`）等元数据。
- `clean_paths` 当前包含 `ShadowTrackerExtra/Content` 与多个 `Template_*`；`spec/`、`.claude/`、`UGCProjects/Withdraw` 不在其中。写拆解产物或做正式工程时避开会被清理的目录。

## 平台与产物

- Windows：编辑器 + 打包运行。
- Android：`安卓/5826566_..._Android_ETC2_1.39.13.16220_Shipping_CE_arm64_armv7.unsigned.shell-signed.apk`。
- 上传/打包目标由 `.ugcproj` 的 `[JobOption]/[UGCUploadOption]` 决定，现工程默认：
  `LinuxServer+WindowsNoEditor+Android_ETC2+IOS+OpenHarmony_ETC2`。
- 本地打包产物通常在项目的 `Saved/` 或编辑器任务目录；上传包不落在 `UGCProjects/` 根。

## 日志与故障定位

| 现象 | 先看 |
|---|---|
| 编辑器启动失败/崩溃 | `ShadowTrackerExtra/Saved/Crashes/`、`Saved/Logs/ShadowTrackerExtra.log` |
| 玩法 Lua 报错 | `Saved/Logs/ShadowTrackerExtra.log`、`Saved/Logs/Withdraw/`（按工程分目录） |
| TagLog/埋点 | `Saved/Logs/ShadowTrackerExtra_TagLog.log` |
| 内嵌网页/登录页 | `Saved/Logs/cef3.log`、`Saved/webcache/` |
| 启动器/更新失败 | `WeGameLauncher/log/`、`TCLS/` 配置、`tiny_cache/` |
| UGC 工程浏览器异常 | `Saved/UGCProjectBrowser/`、`Saved/UGCResourceDaemon/ApiMetadataCache.json` |

## 常见误区

- 在 `Engine/` 或 `Content/Paks/` 里找 Lua 源码：源码在 `LuaHelper`（存根）与 `UGCProjects/*/Script`（真实业务）。
- 修改 `LuaHelper` 期望改变运行逻辑：不会生效。
- 把 `TCLS`/`WeGameLauncher` 的配置当普通 ini 改：会导致登录/更新失败，且更新会覆盖。
- 清理 `tiny_cache/` 或 `Saved/` 来「修问题」：会丢失缓存与日志，先备份再动。
