# SkillSystem Package

SkillSystem 管理玩家技能配置、`skill_data` 状态和当前 Pawn 上的运行时技能实例。

包外统一通过以下门面访问：

```lua
local Registry_SkillSystem = require("Script.Package.SkillSystem.Registry_SkillSystem")
```

主要 API：

- `GetSkillConfig(skillType)` / `GetSkillAssetPath(skillType)`
- `GetPlayerSkills(pc)` / `IsSkillActive(pc, skillType)`
- `IsSkillLoaded(pc, skillType)`
- `SetSkillState(pc, skillType, active)`
- `RestoreActiveSkills(pc)`
- `FormatSkillData(pc)`

`skill_data` 保持 `{ [skillType] = boolean }`，其中 `skillType` 统一为数字键。读取时会兼容并归一化可识别的字符串数字键。运行时技能实例只保存在内存中，不写入存档。Pawn 重建后调用 `RestoreActiveSkills`，系统会将已激活技能重新挂载到当前 Pawn。

技能资产脚本仍位于 `Script/Blueprint/Prefabs/Skills`，不属于本 Package 的实现模块。
