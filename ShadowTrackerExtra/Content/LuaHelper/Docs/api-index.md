# UGC API 总索引

> 数据来源：`Content/LuaHelper/Source/Lua/ugc/UGCAPI/*.lua`。全部为 `---@meta` 存根，不是运行时代码。
> 函数数按 `function ` 行统计；「模板引用」= `UGCProjects/` 下包含该标识符的 `.lua` 文件数。
> 本文件随 LuaHelper 版本变化，查具体签名请直接看对应 `.lua`。

## 使用方式

```bash
# 查函数签名与生效范围
grep -n -A6 "function UGCGameSystem.GetAllPlayerPawn" UGCAPI/UGCGameSystem.lua

# 查废弃接口与替代
grep -rn "@deprecated" UGCAPI/ | head

# 查某系统在工程里的真实用法
grep -rn "UGCBackpackSystemV2\." UGCProjects/Withdraw/Script | head
```

判断顺序：

1. 先看类注释：`【规范】` / `【实验性】` / `【废弃】`。
2. 再看函数头 `---生效范围：服务器 / 客户端 / 服务器&客户端`。
3. 有 `@deprecated` 时看替代项，不要在新代码里使用旧接口。
4. 找示例时优先看 `Template_PlaygroundHub`（功能大全）与 `Withdraw`（完整项目）。

## 分类总表

### 角色

| System | 用途 | 函数数 | 状态 | 替代 / 备注 | 模板引用（top3） |
|---|---|---|---|---|---|
| UGCPlayerPawnSystem | 角色系统接口库 | 64 | 实验性 | 新角色 API | Withdraw(8), RogueShooting(7), SkillCompetition(3) |
| UGCPlayerStateSystem | 玩家数据/状态系统 | 17 | 规范 | | RogueShooting(7), Withdraw(7), ArmsTeamCompetition(6) |
| UGCPlayerControllerSystem | 玩家控制器系统 | 11 | 规范 | | PlaygroundHub(14), ArmsTeamCompetition(4), Withdraw(4) |
| UGCPawnSystem | 旧角色系统 | 18 | 全量废弃 | UGCPlayerPawnSystem | PeekabooZ(2), CTCompetition2(1), demolition(1) |
| UGCPawnAttrSystem | 旧角色属性 | 47 | 全量废弃 | UGCAttributeSystem | demolition(14), RogueShooting(7), PeekabooZ(2) |

### 怪物

| System | 用途 | 函数数 | 状态 | 替代 / 备注 | 模板引用（top3） |
|---|---|---|---|---|---|
| UGCGenericCharacterSystem | 怪物/通用角色系统 | 36 | 规范 | 新怪物 API | Withdraw(20), PlaygroundHub(5), TopDownSurvivor(1) |
| UGCSimpleCharacterSystem | 怪物小动物系统 | 9 | 规范 | |  |
| UGCMobPawnSystem | 旧怪物系统 | 6 | 全量废弃 | UGCGenericCharacterSystem |  |

### 技能

| System | 用途 | 函数数 | 状态 | 替代 / 备注 | 模板引用（top3） |
|---|---|---|---|---|---|
| UGCPersistEffectSystem | 新技能与 Buff 系统 | 21 | 规范 | 旧技能/Buff 的统一替代 | PlaygroundHub(16), RogueShooting(13), SkillCompetition(3) |
| UGCAttributeSystem | 属性系统 | 19 | 规范 | 旧 UGCPawnAttrSystem 的替代 | PlaygroundHub(21), Withdraw(20), RogueShooting(18) |
| UGCProjectileSystemV2 | 技能抛体系统 V2 | 13 | 规范 | | Withdraw(1) |
| UGCProjectileSystem | 抛体系统 | 6 | 规范 | | Athena(1) |
| UGCSkillManagerSystem | 旧技能管理 | 15 | 全量废弃 | UGCPersistEffectSystem |  |
| UGCBuffSystem | 旧 Buff 系统 | 9 | 全量废弃 | UGCPersistEffectSystem | PeekabooZ(1), PlaygroundHub(1) |

### 物品与背包

| System | 用途 | 函数数 | 状态 | 替代 / 备注 | 模板引用（top3） |
|---|---|---|---|---|---|
| UGCBackpackSystemV2 | 背包系统 V2 | 87 | 规范 | 需启用新背包系统 | Withdraw(28), RogueShooting(7), TopDownSurvivor(6) |
| UGCItemSystemV2 | 道具系统 V2 | 86 | 规范 | | Withdraw(13), PlaygroundHub(7), RogueShooting(5) |
| UGCBackPackSystem | 背包系统 V1 | 25 | 规范 | 与 V2 并存，按工程开关选择 | TaskAndStory(4), Athena(2), CTCompetition2(2) |
| UGCItemSystem | 道具系统 V1 | 15 | 规范 | 与 V2 并存 | Withdraw(4), CTCompetition2(3), planechess(1) |
| UGCDropSystem | 掉落系统 | 2 | 规范 | | RogueShooting(2), TopDownSurvivor(1), Withdraw(1) |

### 商业化与功能模板

| System | 用途 | 函数数 | 状态 | 替代 / 备注 | 模板引用（top3） |
|---|---|---|---|---|---|
| UGCGamePartSystem | GamePart 功能模板系统 | 51 | 规范 | 功能按 GamePart 插拔 | Withdraw(12), RogueShooting(5) |
| UGCCommoditySystem | 商业化/商品系统 | 20 | 规范 | | Withdraw(10), RogueShooting(8), SkillCompetition(2) |
| UGCMailSystem | 邮件系统 | 7 | 规范 | | Withdraw(3) |
| UGCModeArchiveSystem | 玩法存档（ModeArchive） | 6 | 规范 | 仅服务器 |  |
| UGCActivitySystem | 活动系统 | 5 | 规范 | 需启用活动 GamePart | Withdraw(1) |
| UGCDataModuleManager | 数据模块管理 | 5 | 规范 | |  |
| UGCPrivilegeSystem | 特权系统 | 4 | 规范 | |  |
| UGCAchievementSystem | 徽章系统 | 1 | 规范 | |  |
| UGCAnnouncementSystem | 公告系统 | 1 | 规范 | |  |

### 场景与环境

| System | 用途 | 函数数 | 状态 | 替代 / 备注 | 模板引用（top3） |
|---|---|---|---|---|---|
| UGCPhysicsUtility | 统一物理能力 | 23 | 实验性 | 重叠/射线等 |  |
| UGCMapMarkManagerSystem | 地图标记/小地图标记 | 17 | 规范 | | TaskAndStory(2) |
| UGCSceneQueryUtility | 环境查询工具 | 16 | 规范 | 射线、范围检测 | RogueShooting(13), Withdraw(3), PlaygroundHub(2) |
| UGCCircleManagerSystem | 信号圈系统 | 13 | 规范 | | PlaygroundHub(1), Ty_Forest(1) |
| UGCLevelFlowSystem | 关卡流程系统 | 11 | 规范 | 关卡流/子关卡 | RogueShooting(21), Withdraw(1) |
| UGCNavigationSystem | 寻路导航系统 | 8 | 规范 | | Withdraw(4) |
| UGCWeatherSystem | 天气系统 | 8 | 规范 | |  |
| UGCAirAttachSystem | 轰炸区系统 | 6 | 规范 | 类名；文件 `UGCAirAttackSystem.lua` |  |
| UGCEMPZoneSystem | 电磁干扰区 | 6 | 规范 | |  |
| UGCAirDropManagerSystem | 空投系统 | 5 | 规范 | |  |

### 载具

| System | 用途 | 函数数 | 状态 | 替代 / 备注 | 模板引用（top3） |
|---|---|---|---|---|---|
| UGCVehicleSystem | 载具系统 | 45 | 规范（废弃 1） | 生成/进出/控制 |  |
| UGCVehicleSystemV2 | 载具系统 V2 | 24 | 实验性 | 按蓝图路径生成 |  |
| UGCVehicleSeatSystem | 载具座位系统 | 14 | 规范 | |  |
| UGCVehicleCommonSystem | 载具通用功能 | 12 | 规范 | 血量/油量/爆炸 |  |

### 社交

| System | 用途 | 函数数 | 状态 | 替代 / 备注 | 模板引用（top3） |
|---|---|---|---|---|---|
| UGCTeamSystem | 队伍系统 | 40 | 规范（废弃 4） | 含队伍/大厅邀请 | PeekabooZ(11), demolition(5), RogueShooting(5) |
| UGCVoiceManagerSystem | 语音系统 | 30 | 规范 | 类名；文件 `UGCVoiceSystem.lua` |  |
| UGCGenericMessageSystem | 广播信息/远程消息 | 22 | 规范 | | RogueShooting(12), Withdraw(5), TopDownSurvivor(4) |
| UGCCampSystem | 阵营系统 | 12 | 规范 | | RogueShooting(3), SkillCompetition(1), TopDownSurvivor(1) |
| UGCMessageSystem | 聊天通用接口 | 4 | 规范 | |  |

### 玩法规则

| System | 用途 | 函数数 | 状态 | 替代 / 备注 | 模板引用（top3） |
|---|---|---|---|---|---|
| UGCGameSystem | 游戏通用接口库 | 124 | 规范（废弃 10） | 玩家查找、伤害、流程、关卡、日志 | Withdraw(222), RogueShooting(121), PlaygroundHub(58) |
| UGCGameplayTaskSystem | 异步任务 | 17 | 规范 | | PlaygroundHub(2) |
| UGCTimeSystem | UTC 时间接口 | 15 | 规范 | |  |
| UGCGameplayTagSystem | GameplayTag 接口 | 13 | 规范 | | RogueShooting(10), PlaygroundHub(4), Withdraw(4) |
| UGCMultiMode | 多模式匹配 | 10 | 规范 | | RogueShooting(24), Withdraw(6) |
| UGCGameSettingSystem | 游戏配置 | 4 | 规范 | 设备档位等 | 2dot5(1), Transverse(1), Withdraw(1) |
| UGCRankSystem | 段位系统 | 3 | 规范 | |  |

### UI

| System | 用途 | 函数数 | 状态 | 替代 / 备注 | 模板引用（top3） |
|---|---|---|---|---|---|
| UGCWidgetUtility | UI 控件工具 | 84 | 规范 | 新 UI 创建/查询首选 | Withdraw(11) |
| UGCWidgetManagerSystem | UI 控件管理器 | 56 | 大量废弃(36) | 废弃项改用 UGCWidgetUtility | Withdraw(37), RogueShooting(28), SkillCompetition(8) |
| UGCUIManagerSystem | UI 管理器（客户端） | 25 | 规范 | 层级/状态/主界面 |  |
| UGCCommonUISystem | UI 通用响应 | 2 | 规范 | 拖拽等通用交互 |  |

### 工具库

| System | 用途 | 函数数 | 状态 | 替代 / 备注 | 模板引用（top3） |
|---|---|---|---|---|---|
| UGCMathUtility | 数学工具 | 124 | 规范 | | PlaygroundHub(11), RogueShooting(6), Withdraw(5) |
| UGCActorComponentUtility | Actor/组件工具 | 47 | 规范 | 组件增删查 | RogueShooting(24), Withdraw(14), TopDownSurvivor(6) |
| UGCObjectUtility | UObject 基础工具 | 32 | 规范（废弃 1） | 有效性/类/路径 | RogueShooting(48), Withdraw(28), TopDownSurvivor(12) |
| UGCAsyncUtility | 异步工具 | 21 | 规范 | 协程/异步加载 |  |
| UGCTweenSystem | Tween 动画 | 16 | 规范 | | PlaygroundHub(3), Withdraw(2) |
| UGCStringTextUtility | 文本工具 | 14 | 规范 | |  |
| UGCDelegateUtility | 委托工具 | 10 | 规范 | | TopDownSurvivor(2), PlaygroundHub(1), RogueShooting(1) |
| UGCTimerUtility | 计时器工具 | 6 | 规范 | | RogueShooting(26), TopDownSurvivor(7), CTCompetition2(5) |

### 基础功能

| System | 用途 | 函数数 | 状态 | 替代 / 备注 | 模板引用（top3） |
|---|---|---|---|---|---|
| UGCGlobal | 全局接口（日志/平台/本地化/商品枚举等） | 53 | 规范 | |  |
| UGCDebugSystem | 调试系统 | 28 | 规范 | 画线/打印/GM | RogueShooting(2), PlaygroundHub(1), SkillCompetition(1) |
| UGCSoundManagerSystem | 声音管理 | 11 | 规范 | 类名；文件 `UGCSoundMangerSystem.lua`；2D/3D 音效 |  |
| UGCCameraManagerSystem | 相机管理 | 6 | 规范 | |  |
| UGCInputSystem | 输入系统 | 6 | 规范 | | Withdraw(1) |

### 其他

| System | 用途 | 函数数 | 状态 | 替代 / 备注 | 模板引用（top3） |
|---|---|---|---|---|---|
| UGCGunSystem | 枪械系统 | 42 | 规范 | 枪械/配件/开火 | Withdraw(7), PlaygroundHub(5), TopDown(1) |
| UGCEntityTypeSystem | 实体类型查询 | 24 | 规范 | | Withdraw(1) |
| UGCWeaponManagerSystem | 武器管理 | 11 | 规范 | 武器组件/切枪 | PlaygroundHub(18), Withdraw(14), RogueShooting(6) |
| UGCScriptModuleManager | 脚本模块管理 | 6 | 规范 | |  |
| UGCFakePlayerSystem | 假人玩家 | 3 | 规范 | |  |
| UGCMiscFunctionSystem | 杂项函数 | 3 | 部分废弃 | | Ty_Forest(1) |

## 相关

- 分类详解：同目录 `character.md`、`monster.md`、`skill.md`、`item-backpack.md`、`commerce-template.md`、`gamepart.md`、`attributes-damage.md`、`skill-buff-editor.md`、`item-backpack-editor.md`、`monster-ai.md`、`vehicle-editor.md`、`scene.md`、`vehicle.md`、`social.md`、`gameplay-rules.md`、`ui.md`、`toolbox.md`、`basic.md`、`misc.md`。
- 类/蓝图 API：`../Source/AGENTS.md`。
- 工程结构与开发流程：`../../../UGCProjects/Docs/project-guide.md`。
- 运行时专题：`../../../UGCProjects/Docs/network-replication.md`、`debugging.md`、`performance.md`、`runtime-rules.md`、`release-checklist.md`、`wiki-map.md`。
