# 模板目录

> 29 个官方模板。脚本数 = `Script/**.lua` 文件数，仅代表规模。模板说明来自各自 `Note.txt`。
> 新建工程时先复制模板，不要直接在 `Template_*` 上做正式项目。

## 速查表

| 模板 | 类型 | 脚本 | 说明 | 起始地图 | GameMode |
|---|---|---:|---|---|---|
| `Template_SysNullMap` | 空模板 | 6 | 仅含可操作角色与空地图，最干净的起点 | `/Template_SysNullMap/UGCmap` | `UGCGameMode_C` |
| `Template_PlaygroundHub` | 功能演示 | 211 | 编辑器功能大全，覆盖最多 UGC API 的 demo | `/Template_PlaygroundHub/UGCmap` | `UGCGameMode_C` |
| `Template_2dot5` | 2.5D | 15 | 2.5D 视角及操控 | `/Template_2dot5/UGCmap` | `UGCGameMode_C` |
| `Template_TopDown` | 俯视角 | 9 | 俯视相机 + 双摇杆操控 | `/Template_TopDown/UGCmap` | `UGCGameMode_C` |
| `Template_TopDownSurvivor` | 俯视角生存 | 95 | 类吸血鬼幸存者：敌人生成、角色成长、战斗流程、UI | `/Template_TopDownSurvivor/UGCmap` | `UGCGameMode_C` |
| `Template_Transverse` | 横版 | 7 | 横版视角及操控 | `/Template_Transverse/UGCmap` | `UGCGameMode_C` |
| `Template_CTCompetition` | 经典团竞 | 24 | 专用蓝图 + UI，参数蓝图配置流程/属性/装备 | `/Template_CTCompetition/UGCmap` | `ClassicTeamDeathMatchGameMode_C` |
| `Template_CTCompetition2` | 经典团竞（新） | 28 | 同上，较新版本 | `/Template_CTCompetition2/UGCmap` | `UGCGameMode_C` |
| `Template_ArmsTeamCompetition` | 军备团竞 | 31 | 军备竞赛式团竞，参数蓝图配置 | `/Template_ArmsTeamCompetition/UGCmap` | `ArmsTeamDeathMatchGameMode_C` |
| `Template_OTCompetition` | 占点团竞 | 26 | 占点玩法，参数蓝图配置 | `/Template_OTCompetition/UGCmap` | `OccupyTeamDeathMatchGameMode_C` |
| `Template_SkillCompetition` | 技能 PVP | 34 | 完整 PVP 团竞流程 + 英雄选择 + 技能示例 | `/Template_SkillCompetition/UGCmap` | `UGCGameMode_C` |
| `Template_demolition` | 爆破 4v4 | 40 | 多回合流程、AI、完整 UI | `/Template_demolition/Asset/Map/demolition` | `BurstGameMode_C` |
| `Template_PeekabooZ` | 非对称对抗 | 38 | 躲猫猫：多回合/分队/出生点/BUFF/Actor 蓝图 | `/Template_PeekabooZ/UGCmap` | `PeekabooGameMode_C` |
| `Template_Athena` | 防守 PVE | 38 | 守卫雅典娜：完整框架/UI/刷怪/道具/BUFF 技能/场景物件 | `/Template_Athena/Asset/Map_ProtectAthena` | `BPGameMode_ProtectAthena_C` |
| `Template_RogueShooting` | 多人 PVE | 141 | 合作闯关：关卡流程、敌人生成与 AI、成长、战斗、小地图、UI | `/Template_RogueShooting/UGCmap` | `UGCGameMode_C` |
| `Template_TaskAndStory` | 任务剧情 | 56 | 任务系统、任务链、条件、任务 NPC | `/Template_TaskAndStory/UGCmap` | `UGCGameMode_C` |
| `Template_RacingCar` | 竞速 | 56 | 载具制作与控制、小地图、完整 UI | `/Template_RacingCar/UGCmap` | `UGCGameMode_C` |
| `Template_SpawnItem` | 物资刷新 | 14 | 可拾取道具制作、刷新实现与配置 | `/Template_SpawnItem/UGCmap` | `UGCGameMode_C` |
| `Template_planechess` | 飞行棋 | 59 | 4 人棋类：摄像机、棋子/棋盘 Pawn、选择与控制、UI | `/Template_planechess/Asset/Map/ChrisTestMap` | `UGCGameMode_C` |
| `Template_MusicParty` | 音游 | 29 | 歌曲打点工具、节拍输入（单轨单键） | `/Template_MusicParty/UGCmap` | `MusicPartyGameMode_C` |
| `Template_Ty_Forest` | 经典海岛 BR | 14 | 海岛地图，跳伞/信号圈/空投 | `/Game/UGC/UGCMod/Mod/PUBG_Baltic_Classic/Baltic_Main_Classic` | `UGCGameMode_C` |
| `Template_FourMaps` | 经典山谷 BR | 6 | 山谷地图，跳伞/信号圈/空投 | `/Game/ModMaps/FourMaps_Main` | `UGCGameMode_C` |
| `Template_SysBalticMap` | 海岛空图 | 3 | 海岛地图空工程，无游戏逻辑 | `/Game/UGC/UGCMod/Mod/PUBG_Baltic_Classic/Baltic_Main_Classic` | `UGCGameMode_C` |
| `Template_SysBorderlandMap` | 度假岛空图 | 3 | 度假岛空工程 | `/Game/Maps/PUBG_Borderland/PUBG_Borderland_Main` | `UGCGameMode_C` |
| `Template_SysDesertMap` | 沙漠空图 | 4 | 沙漠空工程 | `/Game/Maps/PUBG_Desert02/PUBG_Desert02_Main` | `UGCGameMode_C` |
| `Template_SysDihorOtoMap` | 雪地空图 | 2 | 雪地空工程 | `/Game/Maps/PUBG_DihorOtok/DihorOtok_Main` | `UGCGameMode_C` |
| `Template_SysFourMapsMap` | 山谷空图 | 2 | 山谷空工程 | `/Game/Mod/FourMaps/Maps/FourMaps_Main` | `UGCGameMode_C` |
| `Template_SysNeonMap` | 荣都空图 | 4 | 荣都空工程 | `/Game/Maps/PUBG_Neon/PUBG_Neon_Main` | `UGCGameMode_C` |
| `Template_SysSavageMap` | 雨林空图 | 2 | 雨林空工程 | `/Game/Maps/PUBG_Savage/PUBG_Savage_Main` | `UGCGameMode_C` |

## 重点模板

### Template_PlaygroundHub（211 脚本）

编辑器功能演示合集，按功能分组：

- `Script/Blueprint/Attributes/`：属性组、伤害计算
- `Script/Blueprint/Prefabs/`：技能、Buff、载具、怪物、抛体
- `Script/Blueprint/`：GameMode/GameState/Controller/Pawn/UI
- `Script/Common/`、`Framework/`、`GameAttribute/`、`gamemode/`

查某个 API 怎么用时，先在这里搜，再查正式模板。

### Template_RogueShooting（141 脚本）

多人 PVE 完整框架，适合参考：

- 关卡流程与敌人生成（`Blueprint/AI`、`GameMode`）
- 装备词缀（`Blueprint/Affix`）
- 角色成长/突破（`Blueprint/Arts_UI/.../Breakthrough`）
- HUD/小地图/结算 UI

### Template_TopDownSurvivor（95 脚本）

俯视角生存：`GamePartCustom`、`Wrapper`、`utils` 目录可作为「功能模板 + 背包包装」的参考。

### Template_TaskAndStory（56 脚本）

任务系统分层最完整：`TaskSystem`、`TaskConditionTracker`、`LevelSequence`、`Drop`、`GameConfigs`。

## 选择建议

| 目标 | 模板 |
|---|---|
| 从零开始 | `Template_SysNullMap` |
| 查 API 用法 | `Template_PlaygroundHub` |
| 经典 BR | `Template_Ty_Forest`、`Template_FourMaps` |
| 团竞/技能 PVP | `Template_CTCompetition*`、`Template_ArmsTeamCompetition`、`Template_OTCompetition`、`Template_SkillCompetition` |
| PVE/刷怪 | `Template_Athena`、`Template_RogueShooting` |
| 特殊视角 | `Template_2dot5`、`Template_TopDown`、`Template_TopDownSurvivor`、`Template_Transverse` |
| 载具/任务/棋牌/音游 | `Template_RacingCar`、`Template_TaskAndStory`、`Template_planechess`、`Template_MusicParty` |
| 完整项目参考 | `Withdraw`（见 `Withdraw/AGENTS.md`） |

## 相关

- 工程结构与开发流程：`project-guide.md`
- 工程选择与硬约束：`../AGENTS.md`
- API 速查：`../../Content/LuaHelper/Docs/api-index.md`
