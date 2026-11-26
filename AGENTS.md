# OasisEraEditor AGENTS

和平精英「绿洲启元」UGC 编辑器（UE4 打包发行版，`version.txt` = `1.39.13.16220`）。开发者用 **Lua + 蓝图** 制作玩法；本目录是完整安装目录，不是源码仓库。

## 快速定位

| 想做什么 | 去哪里 |
|---|---|
| 写/改玩法 Lua | `ShadowTrackerExtra/UGCProjects/<工程>/Script/` |
| 自动跑 PIE / 跑测试 | `spec/tools/pie_runner.py`（见 `spec/tools/PIE-README.md`） |
| UI / 场景 / API / spec 流程检查 | `spec/tools/README.md`（工具总览） |
| 查 UGC API、类型、枚举 | `ShadowTrackerExtra/Content/LuaHelper/`（先看它的 AGENTS.md） |
| 找可参考的完整玩法 | `ShadowTrackerExtra/UGCProjects/Template_*`（见 `ShadowTrackerExtra/UGCProjects/Docs/templates.md`） |
| 改现有项目 | `ShadowTrackerExtra/UGCProjects/Withdraw/`（基地 + 4 图，见其 AGENTS.md） |
| 编辑器工具 / AI 生成 / 调试 | `ShadowTrackerExtra/Plugins/UGCEditor/`（见其 AGENTS.md） |
| 启动、更新、安装问题 | `Docs/layout-and-launch.md` |
| 看运行日志/崩溃 | `ShadowTrackerExtra/Saved/Logs/`、`ShadowTrackerExtra/Saved/Crashes/` |
| 工程开发流程与坑 | `ShadowTrackerExtra/UGCProjects/Docs/project-guide.md` |
| GamePart / 功能模块 | `ShadowTrackerExtra/Content/LuaHelper/Docs/gamepart.md` |
| 属性 / 伤害 / 治疗公式 | `ShadowTrackerExtra/Content/LuaHelper/Docs/attributes-damage.md` |
| 技能/物品/怪物/载具编辑器 | `ShadowTrackerExtra/Content/LuaHelper/Docs/skill-buff-editor.md`、`item-backpack-editor.md`、`monster-ai.md`、`vehicle-editor.md` |
| 网络同步/复制/重连 | `ShadowTrackerExtra/UGCProjects/Docs/network-replication.md` |
| 调试/日志/环境错误 | `ShadowTrackerExtra/UGCProjects/Docs/debugging.md` |
| 性能预算与优化 | `ShadowTrackerExtra/UGCProjects/Docs/performance.md` |
| Lua 运行期硬规则 | `ShadowTrackerExtra/UGCProjects/Docs/runtime-rules.md` |
| 发布/真机/匹配 | `ShadowTrackerExtra/UGCProjects/Docs/release-checklist.md` |
| 官方 wiki 导航 | `ShadowTrackerExtra/UGCProjects/Docs/wiki-map.md` |
| 拆解腾讯文档需求 | `.claude/skills/oasis-design-doc-decompose/SKILL.md`（需腾讯文档链接） |

## 目录树

```text
OasisEraEditor(2001776)/
├── AGENTS.md                       本文件：总入口
├── .claude/skills/
│   └── oasis-design-doc-decompose/ 腾讯文档需求拆解工作流（产物写 spec/）
├── spec/                           需求拆解、契约库与检查产物（见 spec/tools/README.md）
├── Docs/
│   └── layout-and-launch.md        目录职责、启动/更新链路、只读产物
├── Engine/                         打包的 UE4 引擎侧（只读）
│   ├── Binaries/Win64/             仅 CEF 子进程
│   ├── Content/                    Editor/Localization/Slate
│   ├── Plugins/TWeb2/              内嵌浏览器
│   └── Saved/Config/               引擎配置
├── ShadowTrackerExtra/             游戏模块（编辑器与运行时主体）
│   ├── AGENTS.md
│   ├── Binaries/Win64/             编辑器主程序与游戏 DLL、Wwise、腾讯 SDK
│   ├── Content/
│   │   ├── LuaHelper/              Lua 类型库（全部 ---@meta 存根）+ 蓝图类存根
│   │   ├── Paks/                   51GB 打包资产（只读）
│   │   ├── WwiseAudio/             音频包
│   │   └── Certificates/           证书
│   ├── Plugins/                    编辑器/游戏插件（UGCEditor、UniExtend 等）
│   ├── UGCProjects/                所有可编辑玩法工程（业务区）
│   ├── Saved/                      日志、崩溃、缓存等生成物
│   └── SpeedupSync/                luacheck 等辅助
├── FeaturePacks/                   预留功能包位（当前无功能包）
├── TCLS/                           腾讯登录/版本/更新配置
├── WeGameLauncher/                 WeGame 启动器与更新器
├── rail_files/                     WeGame 平台识别与构建信息
├── tiny_cache/                     启动器下载缓存（勿手改）
├── 安卓/                           Android 安装包（同版本 APK）
├── Manifest_NonUFSFiles_Win64.txt  分发文件清单
├── ShadowTrackerExtraUGCEditor.exe 启动入口
└── version.txt
```

## 启动链路

```text
WeGameLauncher/launcher.exe
  → TCLS 登录 / 版本校验（VersionServerConfig.xml、updateconfig.cfg）
  → ShadowTrackerExtra/Binaries/Win64/ShadowTrackerExtraUGCEditor.exe
  → 打开 ShadowTrackerExtra/UGCProjects/<工程>/<工程>.ugcproj
  → 加载 StartMapName 指定的 .umap
  → GameModePath 指定的蓝图；`Script/Blueprint/` 下同名绑定文件按 `---@class <类名>_C` 接管
```

## 硬约束

- **打包产物只读**：`Engine/`、`ShadowTrackerExtra/Content/Paks/*.pak`、`Binaries/*.exe|*.dll`、`安卓/*.apk`、`Manifest_NonUFSFiles_Win64.txt`。改动会在更新或校验时丢失。
- **`Content/LuaHelper/Source` 全部是 `---@meta` 存根**（6412 个 `.lua`）。它们只服务于 EmmyLua/VSCode 补全，不是运行时代码；改了对游戏无效，且会被编辑器更新覆盖。
- **业务代码只写在工程 `Script/` 下**。蓝图绑定文件以 `---@class Xxx_C:父类` 开头；含 `--Edit Below--` 的，用户代码写在其下，无标记的纯 Lua 类文件按普通模块组织。
- **先判断服务端/客户端**：API 注释里都标了「生效范围」。逻辑入口用 `UGCGameSystem.IsServer()` 分流；客户端拿不到全量 PlayerState。
- **优先新 API**：
  - `UGCSkillManagerSystem` / `UGCBuffSystem` → `UGCPersistEffectSystem`
  - `UGCMobPawnSystem` → `UGCGenericCharacterSystem`
  - `UGCPawnAttrSystem` → `UGCAttributeSystem`
  - `UGCPawnSystem` → `UGCPlayerPawnSystem`
  - `UGCWidgetManagerSystem` 的废弃项 → `UGCWidgetUtility`
  - `UGCGameSystem.SpawnActor` → `UGCActorComponentUtility.SpawnActor`
- **状态用复制、事件用 RPC**：客户端改复制属性无效；重连会丢 RPC。详见 `UGCProjects/Docs/network-replication.md`。
- **禁止文件/系统/URL 接口**：`os/io/package/debug` 大部分接口、`package.path`、文件读写、`LaunchURL` 可能封号；详见 `UGCProjects/Docs/runtime-rules.md`。
- **模板是参考，不是工作区**：基于模板开发先复制成新工程；不要直接在 `Template_*` 上做正式项目。
- **不要手改编辑器生成文件**：`UGCLuaBindFiles.txt`、`DeleteFiles.txt`、`ReferenceAssetList.txt`、`Saved/` 下内容由编辑器生成。
- **git 跟踪范围**：仓库跟踪文档、`spec/` 工具与产物、`ShadowTrackerExtra/UGCProjects/Withdraw/` 工程；其余文件被 `.gitignore` 默认忽略，需要时 `git add -f <path>`。
- **需求拆解产物写 `spec/`**：`spec/<模块>/` 放拆解与验收记录，不放进 `UGCProjects/`、`Content/` 或 `Template_*`（后两者在更新 `clean_paths` 里会被清理）。
- 文档约定：细节写进最近的 `Docs/`；`AGENTS.md` 只做索引和硬约束；工具用法写 `spec/tools/*-README.md`（UI 契约工具用 `spec/tools/README.md`），其余地方不新建 README。

## 文档索引

| 文档 | 何时读 |
|---|---|
| `ShadowTrackerExtra/AGENTS.md` | 在游戏模块内找东西、判断哪些能改 |
| `ShadowTrackerExtra/Content/LuaHelper/AGENTS.md` | 查任何 UGC API / 类 / 枚举 |
| `ShadowTrackerExtra/Content/LuaHelper/Docs/api-index.md` | 需要 77 个 API 库的分类速查表 |
| `ShadowTrackerExtra/UGCProjects/AGENTS.md` | 新建/选择工程、理解工程目录 |
| `ShadowTrackerExtra/UGCProjects/Docs/release-notes-1.39.md` | 1.39 新功能/API/封禁策略增量 |
| `ShadowTrackerExtra/Plugins/AGENTS.md` | 找编辑器插件能力 |
| `ShadowTrackerExtra/Plugins/UGCEditor/Docs/mcp.md` | 用 MCP / UGCAskQ 操作编辑器 |
| `ShadowTrackerExtra/Plugins/UniExtend/AGENTS.md` | 用 Python DSL / AI 助手 |
| `spec/tools/README.md` | UI 契约工具与全部 spec 工具总览 |
| `spec/tools/PIE-README.md` | 用内置 MCP 启动/停止 PIE、跑 AutoTestKit、取日志/截图 |
| `spec/tools/API-README.md` | 用 ApiMetadataCache 检查 API 签名/参数/scope/废弃 |
| `spec/tools/SPEC-README.md` | 校验 spec/INDEX、plan、sync、impl 的结构一致性 |
| `spec/tools/SCENE-README.md` | 场景 Actor 契约扫描、摆放层校验与基线 |
| `TCLS/AGENTS.md`、`WeGameLauncher/AGENTS.md` | 登录/更新/启动器问题 |
