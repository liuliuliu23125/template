# AttributeSystem Package

AttributeSystem 负责玩家属性的持久化、Pawn 同步、属性修改和经验等级检查。

属性 key 直接使用 UGCNativeGameAttributeType 或 UGCCustomGameAttributeType。
项目属性登记、默认值和运行时同步规则位于
Script/Config/Package/AttributeSystem/Config_Attribute.lua；Define_Attribute
只负责读取配置、建立索引和校验规则。

包外唯一入口：
Script.Package.AttributeSystem.Registry_AttributeSystem

attribute_data 的字段和值结构保持原有格式。系统只持久化项目明确需要的属性，不遍历完整引擎枚举。
属性修改统一通过 Registry。持久化属性先同步 Pawn，再由 PlayerDataCore 写入并自动派发数据事件；非持久化属性只同步 Pawn，不写入存档，也不派发持久化数据事件。Pawn 初始化或重生时按白名单回写存档属性。

`GetAttributeValue` 查询当前 Pawn，`GetPersistedAttributeValue` 查询 `attribute_data`。`AddAttributeValue` 会根据属性是否持久化选择对应的当前值来源。

BeginPlay 幂等，只注册一次玩家实例初始化和属性数据变更监听。
经验升级继续使用现有 Config_PlayerUpgrade 和旧事件链，本次不迁移升级奖励协议。
