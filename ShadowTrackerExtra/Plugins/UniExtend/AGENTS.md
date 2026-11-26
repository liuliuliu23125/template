# UniExtend AGENTS

编辑器扩展插件：AI 助手 + 一组 Python DSL，用于**程序化创建/修改 UGC 资产**（物品、实体、怪物、技能、玩法模式、交互物、载具）。

## 目录

| 路径 | 说明 |
|---|---|
| `Binaries/Win64/opencode.exe` | AI 助手宿主（约 158MB） |
| `Content/pyScripts/toolset_proxy.py` | Python → C++ Toolset 的安全桥（强制 kwargs、错误归一化） |
| `Content/pyScripts/ugc_asyncio/` | 编辑器主线程 asyncio 运行时（tick 驱动） |
| `Content/pyScripts/ugc_item_dsl/` | 物品/武器 DSL |
| `Content/pyScripts/ugc_entity_dsl/` | 实体/抛体 DSL |
| `Content/pyScripts/ugc_monster_dsl/` | 怪物/刷怪器 DSL |
| `Content/pyScripts/ugc_combat_skill_dsl/` | 技能/Buff DSL |
| `Content/pyScripts/ugc_gamemode_dsl/` | 玩法模式 DA/GameMode DSL |
| `Content/pyScripts/ugc_interactable_dsl/` | 交互物 DSL |
| `Content/pyScripts/ugc_vehicle_dsl/` | 载具 DSL |
| `Resources/UGCAskQ/OpenCode/Config/ugcaskq.json` | AI 供应商配置（CodeBuddy，多模型） |
| `Resources/UGCAskQ/OpenCode/Config/AGENTS.md` | AI 助手的开发测试说明（不是编辑器总规范） |

## DSL 共同协议

每个领域包都导出 `XxxDslToolset`，四个接口：

| 接口 | 用途 |
|---|---|
| `DslSet` | DSL/IR → 资产 |
| `DslGet` | 资产 → DSL 视图 |
| `PropSet` | 按属性名写字段 |
| `PropGet` | 按属性名读回校验 |

统一返回信封，调用方只看 `success`：

```python
{"success": bool, "error_code": str|None, "message": str,
 "retryable": bool, "state_changed": bool, "data": any, "warnings": list}
```

标准用法：

```python
from ugc_item_dsl import ItemDslToolset as D

r = D.DslSet(Asset='ZZ_Test', Dsl={...}, PlanOnly=True)
if not r['success']:
    print(r['error_code'], r['message'])
```

规则：

- **所有参数必须用关键字传入**；位置参数会报 `INVALID_ARGUMENT`。
- 先 `PlanOnly=True` 看计划，再实际写入，最后 `PropGet`/`DslGet` 校验。
- 写入成功后通过「保存 → 重载 → 读回比对」判定，失败返回 `VERIFY_FAILED`。
- `state_changed=True` 表示已有副作用，重试前先读回状态。
- 字段以各包的 `field_table.py` 为唯一数据源，不要猜。

## 各领域

| 包 | Toolset | 主要参数 | 外部依赖 |
|---|---|---|---|
| `ugc_item_dsl` | `ItemDslToolset` | `Asset`、`Dsl`/`Template`/`Lua`/`LuaPath`、`Kind='item'` | `toolset_proxy` |
| `ugc_entity_dsl` | `EntityDslToolset` | `Kind`、`Asset`、`Dsl`、`Template`/`Pair`/`ItemTemplate` | `toolset_proxy` + `projectile_effect_dict.json` |
| `ugc_monster_dsl` | `MonsterDslToolset` | `Kind`（monster/spawner）、`Asset`、`IrPath`/`IrText`、`CaseDir` | `ugc-workflow-monster` 工具链、ugcvm/gate/editor 模块 |
| `ugc_combat_skill_dsl` | `CombatSkillDslToolset` | `Kind`（skill/buff）、`Asset`、`IrPath`/`IrText`、`Template`、`PlanOnly` | `combat_skill_pipeline` |
| `ugc_gamemode_dsl` | `GamemodeDslToolset` | `IrPath`、`CaseDir`、`DaPath`/`GmBp`、`PlanOnly` | 老 gamemode 工具链 |
| `ugc_interactable_dsl` | `InteractableDslToolset` | `Asset`、`IrPath`/`IrText`、`BaseDir`、`CaseDir`、`Kind='interactable'` | `toolset_proxy` |
| `ugc_vehicle_dsl` | `VehicleDslToolset` | `IrPath`、`Asset`、`SubDir`、`PlanOnly`、`Target='CDO'` | 老载具工具链 |

细节见 `Docs/dsl.md` 与各包 `__init__.py` / `dsl_toolset.py` 的 docstring。

## 约束

- 不修改 `opencode.exe` 与 `ugcaskq.json` 的供应商配置，除非明确要换模型/供应商。
- 不依赖编辑器私有模块做离线规划：规划层（`dsl_api.py`）应纯 Python 可跑；执行层才进编辑器。
- 新增领域包时沿用 `_envelope / _toolchain / field_table / dsl_api / dsl_runner / dsl_toolset / __init__` 结构。
- 所有资产路径/子目录用 ASCII；单次批量控制在工具限制内。
- AI 助手配置里的 `AGENTS.md` 只作用于该助手工作区，不要把它当项目级规范。

## 文档

| 文档 | 何时读 |
|---|---|
| `Docs/dsl.md` | 需要用 Python 批量建/改资产，或新增 DSL 领域 |
| `../UGCEditor/Docs/toolchain.md` | 想看 UEP、toolset_proxy、技能、调试的整体关系 |
| `../UGCEditor/Resources/Skills/ugc-vfx-gen/SKILL.md` | 做粒子特效 |
