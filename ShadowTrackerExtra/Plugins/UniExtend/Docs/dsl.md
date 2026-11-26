# Python DSL 使用与扩展

> 位置：`UniExtend/Content/pyScripts/ugc_*_dsl/`。用于在编辑器进程内**按 DSL/IR 批量创建或修改资产**。
> 每个包的 `dsl_toolset.py` docstring 是最权威的接口说明；本文只做导航与共性约定。

## 运行环境

```text
ue_py（编辑器 Python）
  ├─ toolset_proxy.ToolsetProxy        调 C++ Toolset
  ├─ dsl_api.py                        规划层：纯 Python，可离线
  ├─ dsl_runner.py                     执行层：写入 → 保存 → 重载 → 读回比对
  └─ dsl_toolset.py                    接口层：参数校验、信封、warnings
```

- **规划层不连编辑器**：`PlanOnly=True` 时可离线生成计划。
- **执行层必须在编辑器进程**：取不到编辑器模块时返回 `UNAVAILABLE`。
- 调用方式：`from ugc_item_dsl import ItemDslToolset as D`，四个静态方法。

## 四接口与信封

| 接口 | 语义 | 返回值 |
|---|---|---|
| `DslSet` | DSL/IR → 写入 | `data: {plan, result}`，result 含 `ok/saved/pass/total/created/...` |
| `DslGet` | 资产 → DSL 视图 | `data: {dsl, conflicts, not_recoverable, missing, ...}` |
| `PropSet` | 真机字段名 → 写入 | 同 `DslSet` |
| `PropGet` | 真机字段名 → 读回 | `data: {readback, missing, unreadable, unknown}` |

统一信封：

```python
{
  "success": bool,          # 只看这个
  "error_code": str|None,   # INVALID_ARGUMENT / NOT_FOUND / FAILED_PRECONDITION / VERIFY_FAILED / UNAVAILABLE / INTERNAL
  "message": str,
  "retryable": bool,
  "state_changed": bool,    # 已有副作用，重试前先读回
  "data": any,
  "warnings": list,
}
```

成功判据（写入类）：`success` 为真 **且** `data.result.ok` 为真 **且** `data.result.pass == data.result.total`。

warnings 前缀约定：

| 前缀 | 含义 |
|---|---|
| `SKIPPED:` | 仿真专用键，未写入 |
| `MANUAL:` | 需人工处理 |
| `AUTO-GATE:` | 自动门控提示 |
| `NOTE:` | 补充说明（如模板被忽略、Map 旧键保留） |
| `DIFF:` | 表行双侧对账不一致 |
| `GATE-WARN:` | 老编译器警告 |
| `UNKNOWN_KEYS:` | 字段表未登记的键 |

## 各领域

### ugc_item_dsl — 物品

```python
from ugc_item_dsl import ItemDslToolset as D

r = D.DslSet(Asset='ZZ_Test', Dsl={...}, Template=None, Kind='item')
r = D.PropSet(Asset='ZZ_Test', Props={'ItemName': '测试', 'UsingTime': 1.5})
r = D.PropGet(Asset='ZZ_Test', Names=['ItemName', 'UsingTime'])
r = D.DslGet(Asset='ZZ_Test')
```

- `Asset` 是**资产短名**，不是路径。
- 放行通道：标量、软引用、类引用、简单数组、裸结构数组、`{Items: ...}` 数组、Map 新增/改值、双轨/纯表列、清空、Lua 整文件绑定。
- 不放行：Map 删键/清空（`FAILED_PRECONDITION`）；Lua 正文检查不过。
- Lua 正文要求：非空、最后一条语句是 `return <名字>`、不覆写 `OnEquip/OnUnEquip/OnDetach`；**不做语法检查**。
- 清空：引用字段写 `''` 或 `None`；数组写 `[]` / `{Items: []}`；其他标量不接受 `None`。
- Map 键规范成 `'数字.0'`；旧键保留并记 `NOTE:`。

### ugc_entity_dsl — 实体

```python
from ugc_entity_dsl import EntityDslToolset as D

r = D.DslSet(Kind='weapon', Asset='ZZ_Test', Template='AKM', Dsl={...}, Pair='ZZ_Test_Item')
r = D.PropGet(Kind='weapon', Asset='ZZ_Test', Names=['RangeDamage.Radius'])
```

- `Kind`：`weapon` / `throwable` / `projectile` / `melee`。
- 武器/近战/投掷物发奖**必须给 `Pair`**（配对物品），否则会发到官方模板资产。
- `Lua`/`LuaPath` 二选一；IR 的 `params` 会注入 `-- @params-begin/end` 区。
- 近战无资产数值：只建实体+配对物品+写 hooks Lua；`lifesteal` 必须同时给 `hit_heal`/`kill_heal`，并落到 `local HIT_HEAL/KILL_HEAL` 两行。
- `PropSet` 的 `ShootType` 只接受 `1/2/4/8` 或枚举名，会自动打开对应 `bHasXxxFireMode`。
- 读回按宿主分组：`ENTITY / WRAPPER / CDO / CDO_WRAP / ACTION / WRAP / PATH / REG`。

### ugc_monster_dsl — 怪物/刷怪器

```python
from ugc_monster_dsl import MonsterDslToolset as D

r = D.DslSet(Kind='monster', Asset='ZZ_Test', IrPath='...', PlanOnly=True)
```

- `Kind`：`monster` / `spawner`。
- 依赖工程内 `ugc-workflow-monster` 工具链，以及 ugcvm/gate/editor 模块。
- 支持 `PlanOnly`、`CaseDir`、读侧 `DslGet/PropGet`。

### ugc_combat_skill_dsl — 技能/Buff

```python
from ugc_combat_skill_dsl import CombatSkillDslToolset as D

r = D.DslSet(Kind='skill', Asset='ZZ_Test', IrPath='...', PlanOnly=True)
r = D.PropSet(Kind='buff', Asset='ZZ_Test', Props={...})
```

- `Kind`：`skill` / `buff`。
- 依赖 `combat_skill_pipeline`；规划层可离线。

### ugc_gamemode_dsl — 玩法模式

```python
from ugc_gamemode_dsl import GamemodeDslToolset as D

r = D.DslSet(IrPath='.../X.gamemode.ir', PlanOnly=True)
r = D.PropSet(Target='...', Props={...}, CaseDir='...')
```

- 只 **patch 既有蓝图**（`DA_GameModeGeneral` 与 GameMode 蓝图），不创建蓝图。
- 落地必须给已过交付检查的 `CaseDir`；只规划用 `PlanOnly=True`。
- 不支持 `all/lua/three` 模式（含蓝图创建语义）。
- `PropGet` 必须给字段名列表。

### ugc_interactable_dsl — 交互物

```python
from ugc_interactable_dsl import InteractableDslToolset as D

r = D.DslSet(Asset='ZZ_Test', IrPath='...', PlanOnly=True)
```

- 输入 `.interactable.ir`；支持 `Asset`/`IrPath`/`IrText`/`BaseDir`/`CaseDir`。
- `PropSet/PropGet` 用 `Kind='interactable'`。

### ugc_vehicle_dsl — 载具

```python
from ugc_vehicle_dsl import VehicleDslToolset as D

r = D.DslSet(IrPath='...', PlanOnly=True)
r = D.PropSet(Asset='ZZ_Test', Props={...}, Target='CDO')
```

- `Target`：`CDO` 或 `SCS:<组件变量名>`。
- 执行层依赖老载具工具链；verify 是**同进程内存回读**，不是保存后重载。
- 运行时属性 Lua 会写到 plan 同目录，需随案交付。

## 典型流程

```python
# 1) 只规划，检查 plan 与 warnings
r = D.DslSet(..., PlanOnly=True)
if not r['success']:
    raise RuntimeError(r['error_code'] + ': ' + r['message'])
print(r['data']['plan'])

# 2) 实际写入
r = D.DslSet(...)
assert r['success'] and r['data']['result']['ok']
assert r['data']['result']['pass'] == r['data']['result']['total']

# 3) 读回校验
r = D.PropGet(Asset='ZZ_Test', Names=[...])
if not r['success']:
    ...
print(r['data']['readback'])
```

## 新增领域包

1. 复制现有包结构：`_envelope.py`、`_toolchain.py`、`field_table.py`/`scope.py`、`dsl_api.py`、`dsl_runner.py`、`dsl_toolset.py`、`__init__.py`。
2. `__init__.py` 导出 `TOOLSETS = {"XxxDslToolset": XxxDslToolset}` 与 `_LOAD_ORDER`。
3. 规划层保持纯 Python；字段知识只放 `field_table.py`。
4. 执行层按「写入 → 保存 → 重载 → 读回比对」判定，失败返回 `VERIFY_FAILED`。
5. 接口层只做参数校验、通道范围检查、warnings 组装。
6. 不要引入裸 UObject 参数；统一走 `toolset_proxy`。

## 坑

- **位置参数不可用**：所有接口只收关键字参数。
- **`Asset` 是短名**，不是 `/Game/...` 路径。
- **字段名以字段表为准**：拼错会在规划层被拒；仿真别名会被点名真名。
- **`None` 的语义因字段而异**：引用字段可清空，标量字段拒绝。
- **Lua 不做语法检查**：正文需先在本地验证。
- **写入前整案拒绝**：字段错误时不会产生部分写入；但成功后的校验失败可能已有副作用，看 `state_changed`。
- **工具链依赖**：monster/vehicle/gamemode 需要工程内对应工具链，缺了会返回 `FAILED_PRECONDITION`。
- **规划层可离线，执行层不行**：CI 里只能跑 `PlanOnly`。

## 文件索引

| 文件 | 看什么 |
|---|---|
| `ugc_<domain>_dsl/__init__.py` | 包说明、导入方式、TOOLSETS |
| `ugc_<domain>_dsl/dsl_toolset.py` | 四接口完整 docstring、参数、成功判据 |
| `ugc_<domain>_dsl/field_table.py` | 字段名与宿主映射 |
| `ugc_<domain>_dsl/dsl_api.py` | 规划层，DSL → plan |
| `ugc_<domain>_dsl/dsl_runner.py` | 执行层，写入与回读 |
| `toolset_proxy.py` | Python → C++ 桥 |
| `ugc_asyncio/__init__.py` | 编辑器异步运行时 |
