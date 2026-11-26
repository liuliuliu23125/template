# 特效生成的易错点与排查

> `ugc-vfx-gen` skill 的 L3 细节层。每条都对应一个真实会踩的坑。

---

## 1. `editor_type` 写错（最高频）

| 错误写法 | 现象 |
|---|---|
| `'Particle'` | 找不到编辑器类型 / 创建失败 |
| `'VFX'` / `'Effect'` / `'FX'` | 同上 |
| `'ParticleSystem'` | 同上（那是 **UClass 名**，不是物编 editor_type） |
| **`'Asset'`** ✅ | 正确 |

**记住**：`editor_type` 是**物编编辑器分类**，不是 UClass 名。
`objed_create_asset` **只接受 6 个值**：`Item` / `Skill` / `Entity` / `UI` / **`Asset`** / `DataTable`
（`UEPyObjectEditor.cpp:904` 的报错文案即列出这 6 个；`ConvertEditorTypeStrict` 的严格白名单在 `:52-59`）。

⚠️ 枚举 `EUGCObjectTemplateType`（`UGCObjectTemplateManager.h:12-24`）里还有
`Character` / `DataAsset` / `None`，但**这三个会被 Python 入口拒绝** —— 别照抄枚举全集。

不确定时先查：
```
ue_read { "query_type": "objed", "query_mode": "editor_types" }
```

---

## 2. 猜 `asset_type` / `template_name`

**必须逐级查询，不可跳过**（`UGCAskQObjectEditorQuery.h:17-24` 原文："必须逐级查询，不可跳过"）。

```
editor_types → asset_types(需 editor_type) → templates(需 editor_type + asset_type)
```

`asset_type` 中文名（如"枪械"、"特效"）由项目模板配置决定，换个项目可能完全不同。
直接猜中文名通常报"未找到模板"或创建出错误资产。

---

## 3. ⚠️ `sub_dir` 用中文 —— 文档说可以，实际**会抛错**

- **`asset_name` 必须英文、字母开头**（`ObjectEditorPyMethodProvider.cpp:169` 参数说明原文："资产名称（英文，字母开头）"）。
- **`sub_dir` 也只能 ASCII**。虽然多处文档写"支持中文"（`ObjectEditorPyMethodProvider.cpp:170`、`:181`；
  `UGCAskQPyWorkflowFeature.cpp:334`），但**代码会拒绝**——这是文档与实现的矛盾。

**实测结果**（本机编辑器 `ue_py` 实跑）：
```python
ue.objed_create_asset('Asset', '特效', '空白粒子模板', 'FX_Probe_CN', '技能特效/近战')
# → ValueError: Invalid sub_dir '技能特效': 项目名称不能包含中文字符。
```

**根因**：`sub_dir` 的每一段都送 `FFileHelper::IsFilenameValidForSaving` 校验
（`UEPyObjectEditor.cpp:891`），而该函数在 `WITH_UGC_EDITOR` 下拒绝 `0x3000..0x9fff` 区间的字符
（`UE4181\Engine\Source\Runtime\Core\Private\Misc\FileHelper.cpp:1193-1201`）。
本目标是 UGC 编辑器，`WITH_UGC_EDITOR=1` 确实生效。

```python
# ✅ 正确：ASCII
ue.objed_create_asset('Asset', '特效', '模板', 'FX_Slash', 'SkillFX/Melee')
# ✅ 也可以省略 sub_dir，创建在资产根目录
ue.objed_create_asset('Asset', '特效', '模板', 'FX_Slash')
# ❌ 错误：中文 sub_dir
ue.objed_create_asset('Asset', '特效', '模板', 'FX_Slash', '技能特效/近战')
# ❌ 错误：中文 asset_name
ue.objed_create_asset('Asset', '特效', '模板', '刀光特效')
```

---

## 3b. ⚠️ `create_method == "Derive"` 的模板会静默失败

`objed_query_templates` 返回的每个模板都带 `create_method` 字段（`Duplicate` 或 `Derive`，
见 `UEPyObjectEditor.cpp:617-618`）。而**粒子资产的创建只实现了 `Duplicate` 分支**：

- `UGCParticleObjectAsset.cpp:132` — `CreateNewAssetNotBroadcast()` 只有 `if (CreateMethod == Duplicate)`，
  **没有 `Derive` 分支** → `NewAsset` 保持 `nullptr` → Python 侧报
  `RuntimeError: CreateNewAsset failed`（`UEPyObjectEditor.cpp:1009-1013`）。
- `UGCParticleObjectAsset.cpp:52-65` — `CreateNewAsset()` 里的 `Derive` 分支**整块被注释掉**。
- 而结构体 `FUGCObjectTemplateInfo` **默认就是 `Derive`**（`UGCObjectTemplateManager.h:57`），
  所以"随手挑一个模板"很可能正好踩中。

```python
import json
tpl = json.loads(ue.objed_query_templates('Asset', '特效'))
usable = [t for t in tpl['templates'] if t.get('create_method') == 'Duplicate']
# 只从 usable 里挑 template_name
```

> 若某 asset_type 下**全是 `Derive` 模板**，则该类型当前无法通过
> `objed_create_asset` 创建粒子资产 —— 换一个 asset_type，或先复制现成资产
> （`ue.objed_duplicate_asset`）。

---

## 4. 把 `objed_query_assets` 当 list 用

```python
# ❌ 错：每个字符都会被当成一项
assets = ue.objed_query_assets('Asset')
for a in assets:      # 遍历的是字符！
    ...

# ✅ 对：子串判断
assets = ue.objed_query_assets('Asset')
if 'FX_Slash' in assets:
    ...

# ✅ 对：正则提完整路径
import re
paths = re.findall(r'/[^\s,]+FX_Slash', assets)
```

文档原文警告（`:116`）：*"返回的是聚合文本而非列表，切勿直接 for x in assets 迭代（会按字符拆分）"*。

---

## 5. 创建后没打开就去找属性

`objed_create_asset` **不会自动打开编辑器**（`:163` 原文："创建后不会自动打开编辑器"）。
要改属性必须先 `objed_open_asset(name, 'Asset')`。

---

## 6. 改完忘记保存

属性写入后必须显式保存，否则重启编辑器丢失：
```python
ue.objed_save_asset('FX_Name', 'Asset')
```

---

## 7. 批量超过 3 个导致超时

`objed_create_asset` / `objed_delete_asset` / `objed_rename_asset` 的文档均标注：
> ⚠️ 批量操作时一次不要超过3个，防止工具调用超时。
（`:163`、`:194`、`:216`）

拆成多轮执行。

---

## 8. 刚创建的特效 `ai_search` 搜不到

`ai_search` 的限制（`UEPyAISearch.cpp:1091` Notes）：
- **只能搜到被 AISearch 烘焙过的资产**；
- 结果里 `exists=False` 表示 AssetRegistry 里查不到该包（可能已删除或未扫描）。

→ 刚创建的资产要等烘焙后才能被语义搜索命中。**不要因为搜不到就判定创建失败**，
用 `objed_query_assets` 确认存在性更可靠。

---

## 9. `ai_search` 在非 GameThread 调用

`ai_search` 会**阻塞游戏线程**直到完成或超时，且**只能在游戏线程调用**（`:1091`）。

- 经 `ue_py` 调用时由宿主派发到 GameThread，正常；
- 但**不要**在 `call_toolset` 的同步契约里对它做长时间阻塞等待；
- 需要异步就用 `ai_search_start` + `ai_search_is_done` 轮询（1 秒一次）。

---

## 10. 混淆 `editor_type='Asset'` 下的粒子与音频

`Asset` 同时涵盖**粒子系统**（`UParticleSystem`）与**音频**（`UAkEventObject`）。
证据：`UGCObjectAssetManager.cpp:210-212` 两行相邻判断，都要求 `TemplateType == Asset`。

→ 查资产时若结果里混入音频，用 `asset_type` 过滤，或在拿到路径后用
`ue_read {"queries":["schema:UParticleSystem"]}` 对照类名确认。

---

## 11. Toolset 名写成裸类名

```
❌ call_toolset(toolset="UGCObjectToolset", ...)
✅ call_toolset(toolset="UGCAskQ.UGCObjectToolset", ...)
```
Toolset 名 = `<包名末段>.<类名>`（`UGCAskQFunctionLibraryToolset.cpp:121-166`），
权威示例见 `UGCActorToolset.h:49`。不确定就先 `list_toolsets`。

---

## 12. 用 `ue_read` 前缀时忘加冒号

| 意图 | 写法 |
|---|---|
| 查物编查询用法 | `qt:objed`（不是 `qt objed`） |
| 查粒子系统字段 | `schema:UParticleSystem` |
| 看 Python API | `py:index` / `py:guide <cat>` |

裸关键字 `context` / `workflow` 会被自动归一为 `ctx:` / `py:workflow `
（`UGCAskQMCPServer.Tool.cpp:878-880`），但其它前缀不做归一。

---

## 12b. ⚠️ `objed_query_templates` 不吃关键字参数（文档是错的）

文档签名写 `keywords='', top_n=0`，但**实现只接受位置参数**：

```
TypeError: objed_query_templates() takes no keyword arguments
```

**证据**：注册用 `Reg.MethodFlags = METH_VARARGS`（**没有** `METH_KEYWORDS`，
`ObjectEditorPyMethodProvider.cpp:73`），实现是
`PyArg_ParseTuple(args, "ss|si:objed_query_templates", &editor_type, &asset_type, &keywords_utf8, &top_n)`
（`UEPyObjectEditor.cpp`）。这是**文档与实现不符**，以实现为准。

```python
# ✅ 位置参数：editor_type, asset_type, keywords, top_n
raw = ue.objed_query_templates('Asset', '特效', '爆炸,火焰', 12)
# ❌ 报 TypeError
raw = ue.objed_query_templates('Asset', '特效', keywords='爆炸,火焰', top_n=12)
```

（对比：`objed_create_asset` / `ai_search` 等同样是 `METH_VARARGS`，也都只吃位置参数。）

---

## 12c. ⚠️ 模板 JSON 字段是 `template_name`，不是 `name`

`objed_query_templates` 返回的每个模板对象字段为
（`UEPyObjectEditor.cpp:615-645`）：

```
template_name / category / create_method / is_use_lua / tooltip /
template_object_path / template_class_path / score
```

清单包装在 `templates` 数组里，顶层还有 `total` / `returned` / `keywords`。

```python
# ✅ 正确
template_name = t['template_name']
# ❌ 照抄 'name' 会得到一列 None（不会报错，更难发现）
template_name = t['name']
```

> 这类"字段名不符"是静默失败：`t['name']` 在 dict 上抛 KeyError，
> 但 `t.get('name')` 只会静默返回 `None`。**取值前先打印一个样本确认字段名。**

---

## 12d. ⚠️ 没有 `ue.load_asset`；也没有 `get_editor_property`

- **`ue.load_asset` 不存在**（全仓库检索无此注册）。用 **`ue.load_object`**，
  且类要从 `unreal_engine.classes` 导入（见 §15）：
  ```python
  from unreal_engine.classes import ParticleSystem
  ps = ue.load_object(ParticleSystem, '<资产完整路径>')
  ```
  （`load_object` 注册处 `UGCUnrealEnginePython\Private\UEPyModule.cpp:307`。）
- **本 UE4.18 绑定没有 `get_editor_property` / `set_editor_property`**；
  属性直接 **PascalCase** 访问：`ps.Emitters`、`ps.LODDistances`。
- 回读验证示例：
  ```python
  from unreal_engine.classes import ParticleSystem
  ps = ue.load_object(ParticleSystem, path)
  if ps:
      ue.log('class=%s emitters=%d' % (ps.get_class().get_name(), len(ps.Emitters)))
  ```
- 要"写属性"优先走 `UGCAskQ.UGCObjectToolset.SetProperties`（有复杂类型管线与 EditCondition 两段式），
  不要在 Python 里硬赋值。

---

## 13. ⚠️ 臆造不存在的 API（`ue.particle_*` / Niagara）
**全仓库检索确认：不存在任何 `ue.particle_*` / `ue.niagara_*` / `ue.vfx_*` / `ue.emitter_*` /
`ue.effect_*` / `ue.fx_*` / `ue.pfx_*` Python API。** 特效只能走本文档列的 3 条真实通路：
`objed_create_asset`（创建）、`ai_search`（找参考）、Toolset（改属性）。

**Niagara 在本工程不可用**（6 项独立证据）：
| 证据 | 位置 |
|---|---|
| `EnabledByDefault: false` | `UE4181\Engine\Plugins\FX\Niagara\Niagara.uplugin` |
| `EnableNiagara=false` | `UE4181\Engine\Config\BaseEngine.ini:1501-1502` |
| 未登记进工程 | `Survive\ShadowTrackerExtra.uproject` 中 grep `Niagara` → 0 命中 |
| 无二进制 | `Niagara\Binaries\Win64\` 下只有 `.pdb`，**零 `.dll`** |
| 源码引用被版本门控 | `ResScannerUE\...\LevelCheck_PerActorBase.cpp:125-145` 带 `UE_NEWER_THAN_OR_EQUAL(Version,4,25,0)` → 4.18 下为死代码 |

⚠️ 但 `UGCAskQPersistSkillDocQuery.cpp:69-75` 的**文档字符串**宣传了一个
`PlayNiagara` 技能 Task（`NiagaraAsset: TSoftObjectPtr<UNiagaraSystem>`），并写着
"新项目建议优先使用 PlayNiagara"。**这是"文档愿望"，不是可用功能** ——
未找到任何 `UPESkillTask_PlayNiagara` / `PlayEffect` 的 C++ 类，实际只有
`UPESkillTask_SpawnParticle.py` / `UPESkillTask_ScreenParticle.py` 两个 stub。
**不要据此去创建 Niagara 资产。**

**唯一可用的粒子系统是 Cascade（`UParticleSystem`）**：
- 编辑模块 `UGCCascade`（`ICascadeModule::CreateCascade`，`UGCCascade\Public\CascadeModule.h:24`）
- 工厂 `UUGCParticleSystemFactoryNew`（`UGCEditor\...\Factories\ParticleSystemFactoryNew.h:15`，
  `SupportedClass = UParticleSystem`，`ShouldShowInNewMenu() == true`）

> 另有 `UIParticle`（UMG UI 空间粒子，独立资产类型 `UUIParticleAsset` + 独立编辑器）与
> `VFXFlipbookBaker`（把 Cascade 烘焙成 flipbook 贴图）—— 都不是物编特效通路。

---

## 14. ⚠️ 发射器（Emitter）不能增删 —— `Emitters` 是引擎 internal

**结论：当前工具链无法把一个特效的发射器"搬"到另一个特效里。** 已实测确认。

### 实测证据

```python
from unreal_engine.classes import ParticleSystem
ps = ue.load_object(ParticleSystem, '/Game/Arts_Effect/ParticleSystems/Share/P_Fire_03.P_Fire_03')
ue.log(len(ps.Emitters))              # 3
ps.Emitters.append(ps.Emitters[0])    # 看似成功（type=list 副本）
ps2 = ue.load_object(ParticleSystem, PATH)
ue.log(len(ps2.Emitters))             # 仍是 3 → 未持久化
```

- `ps.Emitters` 返回的是 **Python `list` 副本**，不是引擎数组代理 —— 增删只改副本，引擎数据不变（PRV 也报 `has_mutation: false`）。
- `UGCAskQ.UGCObjectToolset.GetProperties` 读 `Emitters` 直接报
  `the following properties could not be read: Emitters`。
- 全仓库**没有任何** `AddEmitter` / `RemoveEmitter` / `InsertEmitter` / `Emitters.Add` API。

### 引擎侧的根因

`Engine\Source\Runtime\Engine\Classes\Particles\ParticleSystem.h:182-183`：
```cpp
/** Emitters - internal - the array of emitters in the system */
UPROPERTY(instanced)
TArray<class UParticleEmitter*> Emitters;
```
- 注释明确写着 **"internal"**；
- 是 `UPROPERTY(instanced)`，**没有 `EditDefaultsOnly`**（对比同文件 `bEnableSeparateRendering` 就带该标记）
  → 不进细节面板、不被属性管线当作可编辑字段。

**可行替代**（按推荐度）：
1. **`objed_create_asset` 选最接近的模板**，再调该模板自带的发射器参数（最稳）；
2. **`objed_duplicate_asset` 复制现成特效**再改参数（保留全部发射器结构）；
3. 期望"多特效叠加"，改用**运行时组件叠加**：在 Actor/蓝图上挂多个
   `UParticleSystemComponent` 各指一个特效 —— 而不是合并成单个 ParticleSystem。

---

## 15. ⚠️ `ue.ParticleSystem` 不存在，要用 `unreal_engine.classes`

```python
# ❌ AttributeError: module 'unreal_engine' has no attribute 'ParticleSystem'
ps = ue.load_object(ue.ParticleSystem, path)

# ✅ 正确
from unreal_engine.classes import ParticleSystem
ps = ue.load_object(ParticleSystem, path)

# ⚠️ 也不接受字符串类名：
# ue.load_object('ParticleSystem', path) → Exception: argument is not a UObject
```

其他常用类同样从 `unreal_engine.classes` 导入（如 `ParticleSpriteEmitter`）。

---

## 16. 参数调整速查（实测可得）

**两类载体，可写范围不同**：

| 载体 | 粒度 | 可写字段数 |
|---|---|---|
| `UParticleSystem`（系统级） | 整体/渲染/LOD | 实测 **47 项** `editable=true` |
| `UParticleEmitter`（发射器级） | 单个发射器 | 实测 **12 项** |
| `UParticleModuleRequired`（材质等） | 发射器外观 | 实测 **59 项** |
| `UParticleModuleSpawn`（发射率） | 生成节奏 | 实测 **10 项** |

**常用系统级字段**（`ListProperties` 实测存在且可写）：
`WarmupTime`、`WarmupTickRate`、`UpdateTime_FPS`、`SystemUpdateMode`、
`LODMethod`、`LODDistances`、`SecondsBeforeInactive`、`bOrientZAxisTowardCamera`、
`bUseFixedRelativeBoundingBox`、`FixedRelativeBoundingBox`、`ThumbnailWarmup`、
`CustomCullDistance`、`CullDistanceCheckTime`。

**改属性的正确方式**（Toolset 走 GameThread + 完备管线）：
```
call_toolset(toolset="UGCAskQ.UGCObjectToolset", tool="ListProperties",
             params="{\"ClassPath\":\"/Script/Engine.ParticleSystem\"}")
call_toolset(toolset="UGCAskQ.UGCObjectToolset", tool="SetProperties",
             params="{\"InstancePath\":\"<资产>\",\"ValuesJson\":\"{\\\"WarmupTime\\\":1.0}\"}")
```

⚠️ **改属性前先提交计划**（PRV）：未提交计划做变更会收到
`PRV VIOLATION: mutation without plan` 警告。先 `ue_plan_submit`。

⚠️ **发射器的 modules 不能增删，但其中的参数分布（`FRawDistribution*`）可以读写。**
"不能增删"与 §14 同源（emitter 的 internal 子对象）；但**改数值是可行的且能落盘**——
早期版本这里写的"只能读不能写"是**错的**，已由 §17 的实测推翻。

---

## 17. ⚠️ 发射器内部参数（Size / Radius / Velocity / Lifetime）**可以**读写 —— 但要按对象去重

§16 旧版写过"modules 只能读、不能写"，**这条已被实测推翻**。模块对象与它们的
`FRawDistribution*` 分配器都能直达，数值可读写、可落盘。
（实测任务：把 `天女散花` 复制出的特效整体放大 ×3.5，最终 58 个分配器全量校验 `passed=58 failed=0`。）

### 17.1 拿到模块与其分配器

```python
from unreal_engine.classes import ParticleSystem
ps = ue.load_object(ParticleSystem, '<资产路径>')
l0 = ps.Emitters[0].LODLevels[0]
for m in l0.Modules:
    ue.log(m.get_class().get_name())      # ParticleModuleSize / ...Velocity / ...Lifetime ...
    ue.log(m.get_path_name())             # 精确对象路径（Toolset 写入要用）
d = m.StartSize.Distribution              # 直接拿到分配器 UObject
ue.log(d.get_path_name())                 # <资产>.<资产>:ParticleModuleSize_6.DistributionStartSize
ue.find_object('<分配器路径>')             # 也可按路径找回
```

分配器类型与可写字段：

| 分配器类 | 字段 | Python 直写 |
|---|---|---|
| `DistributionFloatConstant` | `Constant` (float) | ✅ 直接赋值 |
| `DistributionFloatUniform` | `Min` / `Max` (float) | ✅ 直接赋值 |
| `DistributionVectorUniform` | `Min` / `Max` (FVector) | ❌ 走 Toolset |
| `DistributionVectorConstant` | `Constant` (FVector) | ❌ 走 Toolset |

⚠️ 分配器命名**不可拼字符串猜**：自动生成的叫 `Distribution<属性名>`
（如 `DistributionStartSize`），但**手工改名过的会变成 `DistributionVectorUniform_0`**。
一律以 Python 读出的 `get_path_name()` 或 Toolset 返回的 `RefPath` 为准。

⚠️ 反过来，**分配器的"缺失"要容错**：同一类模块未必每个都有同名属性
（例如只有 `ParticleModuleLocationPrimitiveSphere` 才有 `StartRadius` / `VelocityScale`），
`getattr(m, prop)` + `try/except` 跳过。

### 17.2 ⚠️ 最坑的一条：**多个 LOD 可能共享同一批模块对象**

`emitter.LODLevels[i].Modules` 里，LOD 对象路径各不相同
（`ParticleLODLevel_20/_30/_24`），**但返回的模块可能是同一批实例**。本机实测
（模板 `天女散花`，8 发射器）：

```
E0 / E1 / E2 / E5 / E6 / E7   shared_modules = True    ← 三个 LOD 返回完全相同的模块对象
E3 / E4                       shared_modules = False   ← 部分模块（Sphere/Velocity）每 LOD 各一份
```

**即：不能假设"每个 LOD 一套独立模块"。**

**后果**：写 `for l in e.LODLevels: for m in l.Modules: scale(m)` ——
共享的模块会被改 N 次。实测踩到：半径 `60 → 210 → 735 → 2572`，资产直接报废。

**解法：按 `get_path_name()` 去重，每个唯一对象只写一次。**

```python
seen = {}
for e in ps.Emitters:
    for l in e.LODLevels:
        for m in l.Modules:
            seen[m.get_path_name()] = m        # 路径去重（不要用 id()，UEPy wrapper 每次访问可能是新对象）
for m in seen.values():
    ...                                        # 每个唯一模块只处理一次
```

> 这样写对**两种**情况都正确：共享 → 只改一次；独立 → 各改一次。

### 17.3 `ue.FVector` 的分量是**小写** `x/y/z`

```python
v = ue.FVector(1.0, 2.0, 3.0)
ue.log(v.x, v.y, v.z)      # ✅ 正确
v.X                        # ❌ AttributeError: 'FVector' object has no attribute 'X'
```

（`dir(v)` 也确认：`['cross','dot','x','y','z','length','normalized',...]` 全小写。）

对比：**Toolset 侧 JSON 用大写** —— `{"Min":{"X":0,"Y":0,"Z":700}}`。
两个通道大小写相反，是本主题最容易混淆的一处。

> ⚠️ 这个坑会**静默炸掉整条缩放逻辑**：若 `vecmul()` 里读 `.X`，异常被外层
> `try/except` 吞掉后，**所有向量型参数一个都不会被改，只有浮点型改了** ——
> 得到一个"半残"资产，而且日志里只有一堆 FAIL 容易被忽略。

### 17.4 在 `ue_py` 里直接调 Toolset —— `toolset_proxy`

```python
from toolset_proxy import ToolsetProxy
TS = ToolsetProxy('UGCAskQ.UGCObjectToolset')        # 名字同 call_toolset
TS.SetProperties(InstancePath=d.get_path_name(),
                 ValuesJson='{"Min":{"X":0,"Y":0,"Z":700},"Max":{"X":0,"Y":0,"Z":1750}}')
```

好处：**一次 `ue_py` 里循环处理几十个分配器**，不必几十次 `call_toolset` 往返
（实测 58 个分配器一次脚本搞定，耗时 ~250ms）。

### 17.5 其它实测缺口

| API | 状态 |
|---|---|
| `ue.FBox` | **不存在** → 无法从 Python 写 `FixedRelativeBoundingBox`（FBox 要用 Toolset 的结构体递归写） |
| `obj.mark_package_dirty()` | **不存在**；改完直接 `objed_save_asset` 即可（返回 True，uasset 的 mtime 会更新） |
| `obj.get_path_name()` | ✅ 可用，是唯一可靠的对象标识（UEPy wrapper 每次访问可能新建，**别用 `id()`**） |
| `ue.scene_capture()` | 只抓**当前 active 编辑器视口**，实测恒为关卡视口；`objed_open_asset` 置前也无效 —— **拍不到粒子编辑器预览**，视觉验证得在编辑器里手动播放 |

### 17.6 改数值前先留"模板基准"

要能回滚。**动手前把模板的原始值抓一份**，出问题用**绝对值回写**恢复
（本次 `RESTORE ok=18 / fail=0`）。按系数"除回去"容易漏项、误差累积。

### 17.7 校验要用容差，不要用 `==`

`0.4 * 1.5 == 0.6000000238418579` → **False**（float32 存储 + 精度）。
用 `==` 会把**成功的写入误报成失败**（本次 5 条假失败）。

```python
ok = abs(new - tpl * factor) <= 1e-3 * max(1.0, abs(tpl * factor))
```

---

## 快速自检清单

- [ ] `ue_read {"queries":["status:"]}` 返回 `ready=true`
- [ ] `editor_type` 用的是 **`Asset`**（不是 Particle/VFX/Effect）
- [ ] `asset_type`（本工程为 `特效`）与 `template_name` 来自逐级查询，不是猜的
- [ ] `objed_query_templates` 用的是**位置参数**（不要写 `keywords=` / `top_n=`）
- [ ] 模板取值用的是 **`t['template_name']`**（不是 `t['name']`）
- [ ] `template_name` 的 `create_method == "Duplicate"`（`Derive` 会静默失败）
- [ ] `asset_name` 是英文、字母开头
- [ ] **`sub_dir` 是纯 ASCII**（中文会抛 `ValueError`）
- [ ] 批量创建 ≤ 3 个
- [ ] 回读用 `ue.load_object`（**没有** `ue.load_asset` / `get_editor_property`）
- [ ] 改属性前先 `GetClassSchema` / `ListProperties` 查过字段名
- [ ] 遍历 `LODLevels[].Modules` 时**按 `get_path_name()` 去重**（LOD 可能共享模块对象，见 §17.2）
- [ ] `FVector` 分量用小写 `x/y/z`；Toolset JSON 用大写 `X/Y/Z`（见 §17.3）
- [ ] 改发射器数值前**先抓模板基准值**，便于绝对值回滚（见 §17.6）
- [ ] 浮点校验用**容差**，不要用 `==`（见 §17.7）
- [ ] 改动后 `objed_save_asset` 保存过
- [ ] 用 `objed_query_assets`（子串/正则）而非迭代确认存在性
- [ ] 没有臆造 `ue.particle_*` / Niagara API
