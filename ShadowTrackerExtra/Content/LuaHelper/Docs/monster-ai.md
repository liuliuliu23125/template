# 怪物与 AI

> 怪物模板、阵营/实体类型、行为树、导航网格、刷怪器与调试。
> 官方来源：怪物快速配置、行为树、导航网格；运行时 API 见 `monster.md`。

## 何时读

- 要新建怪物、改模型/动画/血量/阵营。
- 怪物不移动、不攻击、打不到。
- 行为树/黑板/装饰器/服务节点配置。
- 需要烘焙或动态更新导航网格。
- 要配刷怪器或批量刷怪。

## 前置依赖

- **导航网格**：`Nav Mesh Bounds Volume` 覆盖可移动区域，构建后生成 Navmesh 数据（项目 `Navmesh/` 目录）。
- **AI World Volume**：识别场景交互对象、筛选怪物目标；一个关卡只能放一个，覆盖整个场景。
- **GameMode 配置**：`UGCGameMode` 的 Component Manager 加 `ESS_Navigation`、`ESS_MonsterCrowdMove`；DataManager 加 `GMData Source Navigation`；编译保存。
- **世界设置**：游戏模式重载蓝图必须与当前 `UGCGameMode` 一致。

## 快速配置

1. 实体编辑器 → 怪物模板 → 创建怪物蓝图（`Asset/Blueprint/Prefabs/Monsters`）。
2. 配基础信息：名称、血条、阵营；阵营不对会导致打不到/不攻击。
3. 配实体类型：在怪物模板/编辑器配置；运行时查询用 `UGCEntityTypeSystem.IsActorOfEntityTypeByTag` / `IsActorOfEntityType`、`UCommonEntityTypeFuncLib`。本地存根未暴露 `SetEntityTypeTag` / `GetEntityTypeTag`，wiki 写法需在编辑器/工程验证。
4. 配行为树：模板自带 `UGC怪物行为树`；行为控制组件 `BehaviorControlComp` 反射黑板变量。
5. 配技能/属性/掉落。
6. 刷怪：刷怪器或 `UGCGenericCharacterSystem`。

```lua
local Tag = UGCGameplayTagSystem.RequestGameplayTag("LogicPart.Filter.EntityType.Melee")
local IsMelee = UGCEntityTypeSystem.IsActorOfEntityTypeByTag(MonsterObject, Tag)
```

## 行为树

- 执行顺序：从上到下、从左到右。
- 节点：
  - Root：唯一入口，只能连一个合成节点。
  - Composite：Selector（任一成功）、Sequence（全部成功）、Simple Parallel。
  - Decorator：条件/观察者，挂在分支根。
  - Service：分支执行期间周期性运行。
  - Task：实际动作，可挂 Lua。
- 黑板：key-value 数据；Task/Decorator/Service 共享。
- 条件判断优先用 Decorator，不要塞进 Task。
- 自定义节点可挂 Lua；模板节点见“任务/装饰器/服务节点查询手册”。

## 导航

- `Nav Mesh Bounds Volume` 圈出可移动区域 → 构建。
- 构建后按 `P` 查看；浅蓝色区域可走。
- 场景改动后：
  - 重新烘焙，或
  - 运行时 `UGCNavigationSystem.AsyncBuildNavmesh` / 增量构建。
- 导航构建是服务器操作；同步构建会阻塞。
- 找不到路时先查：NavMesh 覆盖、障碍、`AIWorldVolume`、GameMode 子系统配置。

## 刷怪

- 刷怪器（Spawner）适合固定点/波次；运行时 API 适合动态逻辑。
- `UGCGenericCharacterSystem.SpawnGenericCharacter*` 返回 `AActor`，可能为 nil。
- 范围刷怪会找地面；分波刷怪用 `LoopTimes`/`Interval`/`FirstDelayTime`。
- 怪物数量多时按性能文档配 `NetUpdateFrequency` / `NetCullDistanceSquared`。

## 调试

- 怪物调试工具：行为树、黑板、目标、状态。
- 角色调试工具：技能/Buff/属性面板。
- 打不到先查阵营；不移动先查导航/AIWorldVolume；不攻击查行为树/索敌组件。

## Agent 规则

1. 先分清是“模板配置”“AI 行为树”还是“运行时 Lua”。
2. 怪物不移动优先查导航与 GameMode 子系统，不要先改代码。
3. 打不到优先查阵营/实体类型；实体类型设置先看编辑器/本地存根，不要照 wiki 直接调 `SetEntityTypeTag`。
4. 行为树条件放 Decorator，Task 只做动作。
5. 刷怪返回可能为 nil，先判空。
6. 大量怪物按性能预算降频/裁剪。

## 本地参考

- API/运行时：`monster.md`
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=JKHitxoV>（怪物快速配置）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=3sWJbxiD>（行为树）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=3cTqxkya>（导航网格）
