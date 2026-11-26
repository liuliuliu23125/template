# 工程开发指南

> 面向「在 `UGCProjects/<工程>/Script` 里写玩法 Lua」的通用流程。具体 API 见
> `../../Content/LuaHelper/AGENTS.md`；工程清单见 `../AGENTS.md`。

## 1. 从启动到 Lua

```text
编辑器打开 <工程>.ugcproj
  → 加载 StartMapName（.umap）
  → 生成 GameModePath 指定的 GameMode 蓝图
  → 初始化 GameState / PlayerController / PlayerPawn / PlayerState
  → 每个蓝图查找同名 Lua 文件并注入函数
  → Lua 的 ReceiveBeginPlay / ReceiveTick / ReceiveEndPlay 被调用
```

要点：

- **同名绑定**：蓝图资产与同名 Lua 文件绑定，例如 `Asset/Blueprint/UGCGameMode.uasset` ↔ `Script/Blueprint/UGCGameMode.lua`（部分模板的绑定脚本直接放在 `Script/` 根）。
- **文件头声明父类**：`---@class UGCGameMode_C:BP_UGCGameBase_C`，`_C` 后缀表示蓝图生成类。
- **用户代码边界**：含 `--Edit Below--` 的绑定文件只写标记之下（上方由编辑器生成/维护）；没有该标记的 Lua 类文件是纯 Lua 模块，不受此限。
- **生命周期函数**：`ReceiveBeginPlay`、`ReceiveTick(DeltaTime)`、`ReceiveEndPlay`；重写时先调 `SuperClass`。
- **模块返回值**：文件末尾 `return UGCGameMode`。

模板最小示例（`Template_SysNullMap/Script/Blueprint/UGCGameMode.lua`）：

```lua
---@class UGCGameMode_C:BP_UGCGameBase_C
--Edit Below--
local UGCGameMode = {};

function UGCGameMode:ReceiveBeginPlay()
    UGCGameMode.SuperClass.ReceiveBeginPlay(self)
end

return UGCGameMode;
```

## 2. 模块加载

| 方式 | 用途 |
|---|---|
| `require("Script.X.Y")` | 工程内普通模块；返回模块表 |
| `UGCGameSystem.UGCRequire("Script.X.Y")` | **要发布到资源商店时必须用**；替代原生 require |
| `UGCGameSystem.GetUGCResourcesFullPath("Asset/...")` | 把工程相对资源路径转成完整路径，给 `UE.LoadClass` 等使用 |

约束：

- 路径使用点号、从 `Script` 开始，与目录结构一致。
- 顶层 `require` 尽量放在 GameState/PlayerController 的绑定文件里，避免循环依赖。
- 资源路径不要写绝对路径或 `/Game/` 前缀（官方内置资产除外）。

## 3. 服务端 / 客户端

- 服务端判断：`UGCGameSystem.IsServer()`。
  - 注释明确：它依赖 `UGCGameSystem.GameState`，**GameState 初始化前不要调用**。
- 每个 API 的注释都有 `---生效范围：服务器 / 客户端 / 服务器&客户端`；先看范围再调用。
- 客户端可见性：
  - `GetAllPlayerState` 在客户端只返回队友。
  - 客户端只能拿到自己的 `PlayerController`。
  - 敌人 `PlayerKey` 可能因对方无 Pawn 而不全。
- 跨端通信：
  - 远程消息：`UGCGenericMessageSystem.SendServerMessage / SendClientMessage / SendAllClientMessage`，配合 `ListenRemoteMessage`。
  - 属性同步：`UGCAttributeSystem` 的服务端写操作会自动同步到客户端。
  - 工程内事件：Withdraw 用 `UGCEventSystem:AddListener/SendEvent`（项目自建，不是引擎 API）。
- 权威原则：伤害、生成、掉落、结算等写操作放服务端；客户端只做表现与输入。

## 4. 玩家身份链

| 标识 | 含义 | 典型用途 |
|---|---|---|
| `UID` | 账号 UID | 存档、跨局数据 |
| `PlayerKey` | 单局内玩家/人机标识 | 队伍、消息、查找其他对象 |
| `PlayerController` | 玩家控制器 | 输入、本地 UI、Possess |
| `PlayerPawn` | 角色实体 | 位置、属性、动画 |
| `PlayerState` | 玩家状态 | 队伍、击杀、名字 |

互转统一走 `UGCGameSystem`：

```lua
local pc = UGCGameSystem.GetPlayerControllerByPlayerKey(key)
local pawn = UGCGameSystem.GetPlayerPawnByPlayerKey(key)
local state = UGCGameSystem.GetPlayerStateByPlayerKey(key)
local key2 = UGCGameSystem.GetPlayerKeyByPlayerPawn(pawn)
```

做字典 key 时优先用 `PlayerKey`；持久化用 `UID`。

## 5. 常用能力入口

| 需求 | API |
|---|---|
| 生成 Actor / 对象 | `UGCActorComponentUtility.SpawnActor`、`UGCGameSystem.NewObject` |
| 伤害 | `UGCGameSystem.ApplyDamage / ApplyRadialDamage / ApplyPointDamage` |
| 定时器 | `UGCGameSystem.SetTimer / ClearTimer`；轻量用 `UGCTimerUtility` |
| 玩家属性 | `UGCAttributeSystem`（旧 `UGCPawnAttrSystem` 已废弃） |
| 技能/Buff | `UGCPersistEffectSystem`（旧 Skill/Buff 系统已废弃） |
| 怪物 | `UGCGenericCharacterSystem` |
| 背包/道具 | `UGCBackpackSystemV2`、`UGCItemSystemV2`（按工程开关选 V1/V2） |
| UI | `UGCUIManagerSystem`（客户端 UI 管理器）或 `UGCWidgetUtility.CreateWidgetAsync` |
| 调试绘制 | `UGCDebugSystem.DrawDebug*`、`PrintToScreen` |
| 日志 | `ugcprint`、`ugcprint_format`、`print` |

## 6. 工程配置

| 文件 | 作用 |
|---|---|
| `<工程>.ugcproj` | 启动地图、GameMode、匹配、多模式、打包目标、特性开关 |
| `Script/luahelper.json` | LuaHelper/EmmyLua 的工程配置（忽略模块、注解规则） |
| `.emmyrc.json` | EmmyLua 诊断开关与库路径（可选） |
| `workspace.code-workspace` | VSCode 工作区，通常包含当前工程、`Content/LuaHelper`、日志目录 |
| `UGCLuaBindFiles.txt` | 编辑器生成的 Lua/资源绑定与上传清单，勿手改 |

## 7. 调试

| 手段 | 说明 |
|---|---|
| `ugcprint(...)` | 进 `ShadowTrackerExtra/Saved/Logs/ShadowTrackerExtra.log`，也常显示在编辑器输出 |
| `UGCDebugSystem.PrintToScreen` | 屏幕文字，带颜色/时长 |
| `UGCDebugSystem.DrawDebugLine/Sphere/Box/...` | 世界内可视化 |
| `ShadowTrackerExtra/Saved/Logs/ShadowTrackerExtra.log` | 主日志；`ShadowTrackerExtra/Saved/Logs/<工程名>/` 为分工程日志 |
| `Saved/Crashes/` | 崩溃转储 |
| Lua 调试器 | `Plugins/UGCEditor/Resources/LuaDebugTool/`（VSCode 扩展） |
| Lua 静态检查 | `ShadowTrackerExtra/Plugins/UGCEditor/Resources/LuaCheck/x64/luacheck.exe`，配置见 `ShadowTrackerExtra/SpeedupSync/luacheck/check.json` |

## 8. 打包与上传

- 目标平台在 `.ugcproj` 的 `[JobOption]` / `[UGCUploadOption]`：
  `LastTargetPlatform`、`TargetPlatform`、`SkipBake`、`PakOnly`。
- 当前常见目标：`LinuxServer+WindowsNoEditor+Android_ETC2+IOS+OpenHarmony_ETC2`。
- 发布到资源商店前，把 `require` 改为 `UGCGameSystem.UGCRequire`。
- 资源命名/子目录受编辑器限制（部分工具链要求 ASCII），以编辑器报错为准。

## 9. 常见坑

1. **改 `LuaHelper` 不生效**：它是 `---@meta` 类型库，不是运行时代码。
2. **写到了 `--Edit Below--` 上方**：被编辑器生成逻辑覆盖。
3. **文件与蓝图不同名 / `---@class` 父类写错**：函数注入不到蓝图，`ReceiveBeginPlay` 不执行。
4. **客户端调服务端接口**：先看 `生效范围`；写操作放服务端。
5. **GameState 初始化前调 `IsServer()`**：注释明确不保证；把依赖逻辑放到生命周期事件之后。
6. **直接遍历 `GetAllPlayerState()` 当全量**：客户端只有队友。
7. **Actor 失效后继续访问**：用 `UGCObjectUtility.IsObjectValid` 判断。
8. **`require` 写法不对**：必须是 `Script.` 开头的点号路径，且文件有 `return`。
9. **在 `Template_*` 上直接开发**：复制成新工程，避免模板污染。
10. **手改生成文件**：`UGCLuaBindFiles.txt`、`DeleteFiles.txt`、`ReferenceAssetList.txt` 会被覆盖。

## 专题

| 文档 | 何时读 |
|---|---|
| `network-replication.md` | 属性复制、RPC、断线重连、弱网 |
| `debugging.md` | 日志、环境错误、PIE/上传失败、HotReload |
| `performance.md` | 预算、Profile、对象池、网络裁剪 |
| `runtime-rules.md` | 封禁接口、UObject 有效性、结构体/容器 |
| `release-checklist.md` | 真机、上传、提审、匹配/补人 |
| `release-notes-1.39.md` | 1.39 编码相关增量 |
| `wiki-map.md` | 官方 wiki 机制/流程/配方索引 |

## 相关

- API 速查：`../../Content/LuaHelper/Docs/api-index.md`
- 分类详解：`../../Content/LuaHelper/Docs/*.md`
- 模板：`templates.md`
- Withdraw 分层规范：`../Withdraw/AGENTS.md`
