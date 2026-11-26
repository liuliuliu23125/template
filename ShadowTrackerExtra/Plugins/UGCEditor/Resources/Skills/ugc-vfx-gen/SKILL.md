---
name: ugc-vfx-gen
description: >-
  在 UGC 编辑器中生成/创建特效（粒子特效、粒子系统）时使用。触发词：生成特效、做个特效、
  创建特效、加个粒子、刀光、爆炸、冲击波、拖尾、护盾、法力阵、vfx、particle、ps。
  前提：MCP Server 已运行且 UGC 账号已登录。
---

# UGC 生成特效（粒子）

用物编（Object Editor）的 **Asset** 编辑器类型创建粒子特效资产，再用语义搜索找参考特效，
最后按需改属性。**唯一权威创建入口是 `ue.objed_create_asset`**。

## 铁律（先看这段，能避开绝大多数返工）

1. **`editor_type` 必须写 `'Asset'`**，不是 `'Particle'`/`'VFX'`/`'Effect'`。
   物编编辑器**只接受 6 个值**：`Item` / `Skill` / `Entity` / `UI` / **`Asset`** / `DataTable`。
   其中 `Asset` 同时涵盖**粒子特效**与音频（AkEvent），靠 `asset_type` 区分。
2. **`asset_type` 和 `template_name` 不许猜**，必须逐级查询：`editor_types → asset_types → templates`。
   它们是**项目模板配置**驱动的，不同项目取值不同。本工程实测 `asset_type` 为 **`特效`** / `音频`。
3. **⚠️ `sub_dir` 只能用 ASCII，不能含中文**（与本仓库文档描述相反，已实测）。
   `asset_name` 同理必须英文、字母开头。
   ```python
   # ✅ 正确
   ue.objed_create_asset('Asset', '特效', '<template_name>', 'FX_FireSlash', 'SkillFX/Melee')
   # ❌ 实测抛错：ValueError: Invalid sub_dir '技能特效': 项目名称不能包含中文字符。
   ue.objed_create_asset('Asset', '特效', '<template_name>', 'FX_FireSlash', '技能特效/近战')
   ```
   根因：`sub_dir` 每段都过 `FFileHelper::IsFilenameValidForSaving`，该函数在 `WITH_UGC_EDITOR` 下
   拒绝 `0x3000..0x9fff`（即中/日文字符）。**省略 `sub_dir` 或纯英文/数字/下划线。**
4. **⚠️ 只用 `create_method == "Duplicate"` 的模板**。
   `objed_query_templates` 返回的每个模板都带 `create_method` 字段；
   粒子资产只实现了 `Duplicate` 分支，`Derive` 模板**会静默返回 nullptr → 创建失败**。
   ```python
   tpl = json.loads(raw)
   usable = [t for t in tpl['templates'] if t.get('create_method') == 'Duplicate']
   ```
5. **一次不要创建超过 3 个资产**，否则工具调用超时（宿主 API 文档明确警告）。
6. **`objed_query_assets` 返回的是聚合字符串，不是 list**。
   直接 `for x in assets` 会按字符拆分。要么 `if '名字' in text`，要么用 `re.findall` 提路径。
7. **创建后不会自动打开**编辑器（`objed_create_asset` 的既定行为），需要显式 `objed_open_asset`。
8. **⚠️ 要调发射器参数时，遍历 `LODLevels[].Modules` 必须按 `get_path_name()` 去重。**
   多个 LOD **可能返回同一批模块实例**（实测 8 个发射器里 6 个共享）——不去重会把同一个
   参数改 N 次（实测半径 `60 → 210 → 735 → 2572`，资产报废）。发射器内部参数
   （`StartSize` / `StartRadius` / `StartVelocity` / `VelocityScale` / `Lifetime` 等）
   **是可读写的**，写法与全部坑见 `references/pitfalls.md §17`。
   **⚠️ 「按 LOD 去重」还不够 —— 跨发射器共享同一 `Distribution` 实例的情况也真实存在。**
   实测 `魔术烟雾` 模板（E2/E3）共享 `ParticleModuleCameraOffset` 与 `ParticleModuleLocation`
   的 Distribution。若以「发射器序号 + 模块类 + 属性」做主键，同一实例会被缩放两次
   （实测 `CameraOffset 50 → 612.5`，正确值应为 `175`），且**写入时看不出异常**。
   **任何缩放/批量写操作的唯一化主键必须是 `Distribution.get_path_name()`**：
   「拿到实例 → 按实例路径去重 → 每个实例只写一次」，且写入值取**模板绝对值 × 系数**，
   不要用「当前值 × 系数」（重复执行会叠乘，且无法自愈）。
9. **⚠️ `ue.FVector` 分量是小写 `x/y/z`**；而 Toolset 的 JSON 用大写 `X/Y/Z`。两个通道大小写相反。
   写错会**静默吞掉整条向量缩放逻辑**（只有浮点参数被改，得到半残资产）。

> ⚠️ **没有任何 `ue.particle_*` / `ue.niagara_*` / `ue.vfx_*` Python API**（已全仓库检索确认，不要臆造）。
> **Niagara 在本工程不可用**（`Niagara.uplugin` `EnabledByDefault=false`、`BaseEngine.ini` `EnableNiagara=false`、
> 未登记进 `.uproject`、`Binaries` 下只有 `.pdb` 没有 `.dll`）。
> **唯一可用的粒子系统是 Cascade（`UParticleSystem`）**。

> ⚠️ **发射器（Emitter）无法增删** —— `UParticleSystem::Emitters` 是引擎 internal
> （`ParticleSystem.h:182` 注释 "internal"，`UPROPERTY(instanced)` 且无 `EditDefaultsOnly`）。
> `ps.Emitters` 是只读 Python list 副本，`append` 不会持久化；Toolset 也读不到它。
> **因此做不到"把 A 特效的某几个发射器搬到 B"**。
> 想组合，只能：① 选最接近的模板再调参；② `objed_duplicate_asset` 复制现成特效；
> ③ 运行时在 Actor 上挂多个 `UParticleSystemComponent` 叠加。
> 详见 `references/pitfalls.md §14`。

> ⚠️ **读资产用 `unreal_engine.classes`**：`ue.ParticleSystem` 不存在；
> `from unreal_engine.classes import ParticleSystem` 然后 `ue.load_object(ParticleSystem, path)`。
> **没有 `ue.load_asset`，也没有 `get_editor_property`**（属性直接 PascalCase 访问）。

## 主线流程

### 第 0 步：确认编辑器就绪
```
ue_read { "queries": ["status:"] }     # ready=true 才能继续
```

### 第 1 步：找参考特效（推荐，显著提升质量）
先用语义搜索找项目里已有的相似特效，拿到**真实存在的**粒子系统和贴图路径，再决定新建还是改现有。
```python
r = ue.ai_search('红色弧形刀光', types='ps', max_results=10)
for it in r['results']:
    ue.log('%s  %.3f' % (it['asset_path'], it['score']))
```
- `types='ps'` 是粒子特效的固定别名（等价写法：`'particle'` / `'particlesystem'` / `'particle_system'`）。
- 别名写错会抛 `ValueError`；不确定就先 `ue.ai_search_types()`。
- 想先看有哪些类型可搜：`ue.ai_search_types()`。

> 若搜到高度相似的现成特效，**优先 `objed_duplicate_asset` 复制再改**，比从零建再调参数快得多。

### 第 2 步：逐级查询模板（必做，不许跳过）
```
ue_read { "query_type": "objed", "query_mode": "editor_types" }
ue_read { "query_type": "objed", "query_mode": "asset_types", "editor_type": "Asset" }
ue_read { "query_type": "objed", "query_mode": "templates",   "editor_type": "Asset", "asset_type": "<上一步得到的值>" }
```
或等价的 Python。**⚠️ 两个必须知道的坑（实测确认，文档是错的）**：

```python
import json
ue.log(ue.objed_query_asset_types('Asset'))          # 本工程实测：特效 / 音频

# ⚠️ 坑 1：只能用【位置参数】。写成 keywords=... / top_n=... 会报
#    TypeError: objed_query_templates() takes no keyword arguments
#    （注册用的是 METH_VARARGS，实现是 PyArg_ParseTuple("ss|si")，
#      但文档串却写成 keywords='', top_n=0 —— 文档 bug）
raw = ue.objed_query_templates('Asset', '特效', '爆炸,火焰', 12)
#                                            ^keywords ^top_n（位置）

tpl = json.loads(raw)
# ⚠️ 坑 2：字段名是 template_name，不是 name（照抄 name 会得到一列 None）
#    其他字段：category / create_method / is_use_lua / tooltip /
#             template_object_path / template_class_path / score
usable = [t for t in tpl['templates'] if t.get('create_method') == 'Duplicate']
for t in usable[:5]:
    ue.log('%s  (create_method=%s)' % (t['template_name'], t.get('create_method')))
```

> 返回体结构：`{"total":N, "returned":N, "keywords":[...]（仅按关键词过滤时）, "templates":[{...}]}`

### 第 3 步：创建特效资产
```python
path = ue.objed_create_asset(
    'Asset',            # editor_type —— 固定 Asset
    '特效',              # asset_type —— 第 2 步查到的真实值
    '<template_name>',  # 第 2 步查到的、且 create_method == 'Duplicate' 的模板
    'FX_FireSlash',     # asset_name：英文、字母开头
    'SkillFX/Melee'     # sub_dir（可选）：⚠️ 只能 ASCII，中文会抛 ValueError
)
ue.log(path)
```

### 第 4 步：打开并确认
```python
ue.objed_open_asset('FX_FireSlash', 'Asset')   # 打开资产
# 或只打开该编辑器 Tab：ue.objed_open_editor('Asset')
```

### 第 5 步（可选）：改属性
先查 schema 再写，不要猜字段名：
```python
# 列属性（标注 scalar/complex）
ue.log(ue.objed_query_assets('Asset'))          # 确认资产已存在
```
通过 Toolset 读写（**Toolset 走 GameThread，能安全操作 UObject**）：
```
list_toolsets
describe_toolset(toolset="UGCAskQ.UGCObjectToolset")
call_toolset(toolset="UGCAskQ.UGCObjectToolset", tool="GetClassSchema", params="{\"ClassPath\":\"...\"}")
call_toolset(toolset="UGCAskQ.UGCObjectToolset", tool="SetProperties",  params="{\"InstancePath\":\"...\",\"ValuesJson\":\"{...}\"}")
```

### 第 6 步：保存
```python
ue.objed_save_asset('FX_FireSlash', 'Asset')
```

## 完整最小示例

```python
import unreal_engine as ue
import json

# 1) 就绪（先做）
ue.log(ue.objed_query_asset_types('Asset'))          # 本工程实测：特效 / 音频

# 2) 找参考（可选，但能显著提升质量）
r = ue.ai_search('蓝色冲击波', types='ps', max_results=5)

# 3) 逐级查询模板（位置参数！），并只保留 create_method == 'Duplicate' 的
raw = ue.objed_query_templates('Asset', '特效', '冲击波,爆炸', 8)
tpl = json.loads(raw)
usable = [t for t in tpl['templates'] if t.get('create_method') == 'Duplicate']
template_name = usable[0]['template_name'] if usable else None   # 字段是 template_name
assert template_name, 'no Duplicate-method template for this asset_type'

# 4) 创建（sub_dir 用 ASCII，中文会 ValueError）
path = ue.objed_create_asset('Asset', '特效', template_name, 'FX_BlueShockwave', 'SkillFX/AoE')
ue.log('created: ' + str(path))

# 5) 打开 + 保存
ue.objed_open_asset('FX_BlueShockwave', 'Asset')
ue.objed_save_asset('FX_BlueShockwave', 'Asset')

# 6) 落地验证（回读）：确认类与发射器
from unreal_engine.classes import ParticleSystem   # ⚠️ ue.ParticleSystem 不存在
ps = ue.load_object(ParticleSystem, path)          # ⚠️ 用 load_object，没有 ue.load_asset
if ps:
    ue.log('class=%s  emitters=%d' % (ps.get_class().get_name(), len(ps.Emitters)))
    # ⚠️ 本 UE4.18 绑定没有 get_editor_property；属性直接 PascalCase 访问（如 ps.Emitters）
    # ⚠️ ps.Emitters 是只读副本，不能增删发射器（详见 references/pitfalls.md §14）
```

## 更多细节（按需读取，不要预读）

- 完整 API 签名与参数表 → `references/api-reference.md`
- 场景配方（刀光/爆炸/冲击波/拖尾/护盾/Buff 光环）→ `references/workflow-recipes.md`
- 易错点与失败排查 → `references/pitfalls.md`
