# 技能与 Buff 编辑器

> 技能编辑器 1.0/2.0、状态图、Task/Event/Condition、被动/抛体/法术场、状态互斥、Buff 2.0。
> 官方来源：技能编辑器、技能状态图、状态互斥、Buff 编辑器、变参 Buff；运行时 API 见 `skill.md`。

## 何时读

- 要用编辑器做技能/Buff，而不只是调 `UGCPersistEffectSystem`。
- 需要理解技能阶段、状态图跳转、Task/Event/Condition。
- 要做被动技能、技能抛体、法术场。
- 要处理状态互斥（施法/眩晕/无敌/移动）。
- 要排查“技能不触发/不跳阶段/Buff 不叠加”。

## 1.0 与 2.0

| 版本 | 模型 | 适用 |
|---|---|---|
| 1.0 | 阶段 + Action 的线性配置 | 简单技能 |
| 2.0 | 状态图 + Task 事件 + Condition | 复杂技能、被动、法术场、技能抛体 |

新项目优先 2.0；旧技能迁移先确认模板兼容。

## 状态图

| 节点 | 作用 | 关键规则 |
|---|---|---|
| Entry | 唯一入口 | 只能被技能激活事件/跳转条件触发 |
| End | 终止 | 执行到 End 后技能重置为 Entry |
| 技能阶段 | 技能单元 | 可进入/离开；同一时间只有一个阶段激活 |
| 全局事件 | 监听事件 + 条件 | 连动作列表则独立执行；连阶段则立即打断当前阶段 |
| 动作列表 | 一组 Task | 只执行动作，不控制流程；不能作为 End |

- 事件与条件是“且”关系。
- 多条件同时满足时按优先级选唯一路径。
- 动作列表不能作为 End；某阶段后要执行动作时，前一阶段需同时连一个后续阶段，否则流程阻塞。
- 全局事件的跳转只由跳转条件触发。

## Task / Event / Condition

- Task：造成伤害、治疗、播放音效、加冲量、屏幕特效、近战攻击等；多数支持命中/击杀/碰撞事件。
- Event：技能生命周期事件。
- Condition：跳转条件。
- 查询手册：技能 Task / Event / Condition 查询手册（官方 wiki）。
- 技能属性绑定：在技能蓝图里把数值绑定到属性，避免硬编码。

## 被动、抛体、法术场

- 被动技能：独立被动技能蓝图，不依赖主动激活。
- 技能抛体：`UGCProjectileSystemV2`，支持直线/高抛/追踪、逐帧改向/改伤。
- 法术场：范围持续效果，配法术场蓝图与范围检测。
- 状态互斥：用 GameplayTag 表示状态；`EnterDynamicState` / `LeaveDynamicState` 计数；打断 vs 禁用（禁用 = 打断 + 禁用）。

## Buff 2.0

- 蓝图 + BuffAction；支持层数、持续时间、合并/覆盖规则。
- 变参 Buff：同一模板通过参数生成不同效果，减少模板数量。
- BuffListUI：标准 Buff 列表 UI，可直接复用。
- 运行时：`AddBuffByClass` 的层数/时长由蓝图配置决定；移除按层数或 Tag。
- 按释放者筛选移除：`RemoveBuffByClass(..., RemoveNum, Causer)`。
- 状态互斥优先用 Tag，不要用 Buff 名硬编码。

## 调试

- 角色调试工具：
  - 技能面板：增删技能、改 CD/消耗、看运行时数据。
  - Buff 面板：增删 Buff、看层数。
  - 属性面板：看/改属性值。
- 技能调试工具：看阶段、Task、Buff 状态。

## Agent 规则

1. 先判断是编辑器配置还是 Lua 运行时问题。
2. 技能流程优先在状态图里配，Lua 只做条件和运行时逻辑。
3. 事件和条件是 AND；多路径要确认优先级。
4. 状态互斥用 GameplayTag；Enter/Leave 必须成对。
5. Buff 层数/时长以蓝图配置为准，不要在 Lua 里硬编码。
6. 新技能优先 2.0，旧技能迁移先验证模板。

## 本地参考

- API/运行时：`skill.md`
- 状态互斥 API：`UGCPersistEffectSystem.EnterDynamicState/LeaveDynamicState`
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=Yg3yp6_y>（技能编辑器）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=ZbVeL7AG>（状态图）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=NkytpdRS>（状态互斥）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=0Y0pURs->（Buff 编辑器）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=9CMHwnrg>（变参 Buff）
