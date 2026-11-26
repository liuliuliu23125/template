# 特效相关 API 参考（UGCEditor / UGCAskQ MCP）

> 本文件是 `ugc-vfx-gen` skill 的 L3 细节层。所有签名均取自本仓库实际注册代码，
> 出处标注为 `文件:行号`。**不要凭记忆改写参数名。**

---

## 1. 物编（Object Editor）Python API

Provider：`Plugins/UGCObjectEditor/.../PythonExt/ObjectEditorPyMethodProvider.cpp`（注册于 `GetMethods()`）

| 函数 | 签名 | 说明 | 出处 |
|---|---|---|---|
| `objed_query_editor_types` | `ue.objed_query_editor_types() -> str` | 列出所有编辑器类型 | `:31-45` |
| `objed_query_asset_types` | `ue.objed_query_asset_types(editor_type) -> str` | 某编辑器下的资产类型 | `:52-68` |
| `objed_query_templates` | `ue.objed_query_templates(editor_type, asset_type, keywords, top_n) -> str(JSON)`<br>⚠️ **只能位置传参** | 模版列表；`keywords` 中文逗号分隔；`top_n=0` 不限 | `:71-105` |
| `objed_query_assets` | `ue.objed_query_assets(editor_type, asset_type='') -> str` | **返回聚合字符串，不是 list** | `:110-130` |
| `objed_open_editor` | `ue.objed_open_editor(editor_type, asset_name='') -> bool` | 打开物编编辑器 Tab | `:135-152` |
| `objed_create_asset` | `ue.objed_create_asset(editor_type, asset_type, template_name, asset_name, sub_dir='') -> str` | 创建；返回完整路径；**创建后不自动打开**；**批量 ≤3 个** | `:157-183` |
| `objed_delete_asset` | `ue.objed_delete_asset(asset_name, editor_type='') -> bool` | 静默删除（不弹确认框）；批量 ≤3 | `:188-205` |
| `objed_rename_asset` | `ue.objed_rename_asset(asset_name, new_name, editor_type='') -> str` | 重命名；检查同名冲突 | `:210-229` |
| `objed_duplicate_asset` | `ue.objed_duplicate_asset(asset_name, new_name='', editor_type='') -> str` | 复制 | `:234-253` |
| `objed_open_asset` | `ue.objed_open_asset(asset_name, editor_type='') -> bool` | 打开资产（`editor_type` 可省，自动识别） | `:258-283` |
| `objed_save_asset` | `ue.objed_save_asset(asset_name, editor_type='') -> bool` | 保存 | `:286` |

### 编辑器类型取值（权威）

**`objed_create_asset` 只接受 6 个值**（`UEPyObjectEditor.cpp:52-59` 的 `ConvertEditorTypeStrict` 严格白名单；
`:904` 的报错文案同样列出这 6 个）：
```
Item, Skill, Entity, UI, Asset, DataTable
```

⚠️ 枚举 `EUGCObjectTemplateType`（`UGCObjectRunTime/Public/UGCObjectTemplateManager.h:12-24`）
还含 `Character` / `DataAsset` / `None`，但**这三个会被 Python 入口拒绝**，不要照抄枚举全集。

- **粒子特效属于 `Asset`**。
  证据：`UGCObjectAssetManager.cpp:210` —
  `if (AssetObj->IsChildOf(UParticleSystem::StaticClass()) && TemplateInfos.TemplateType == EUGCObjectTemplateType::Asset)`
- `Asset` 同时涵盖音频：同一函数紧邻一行判断 `UAkEventObject` 也归 `Asset`（`:206`）。
  因此**必须靠 `asset_type` 区分粒子与音频**，不能只凭 `editor_type`。
- `objed_open_editor` 的文档串也印证：*"支持6种类型：Item(物品)、Skill(技能)、Entity(实体)、UI、Asset(粒子/音频)、DataTable(数据表)"*（`:141`）。
- Tab 确认：`Asset` 对应 `UGCParticleEditorMain`（`UGCAskQMCPServer.Tool.cpp:719`）。

### `asset_type` 的真实取值

项目模板配置驱动，**必须运行时查询**。本工程实测为 **`特效`** / **`音频`**
（配置资产 `/Game/UGCEditor/UGCConfigAsset/UGCObjectParticlelSettings`，
指针在 `Config/DefaultUGCSettings.ini:2454`）。

### ⚠️ `create_method` 必须过滤（否则静默失败）

`objed_query_templates` 的返回里每个模板都有 `create_method`（`Duplicate` | `Derive`，
`UEPyObjectEditor.cpp:617-618`）。**粒子资产只实现了 `Duplicate` 分支**，
`Derive` 会返回 nullptr → `RuntimeError: CreateNewAsset failed`：

- `UGCParticleObjectAsset.cpp:132`（`CreateNewAssetNotBroadcast`）— 只有 `if (Duplicate)`，**无 `Derive` 分支**
- `UGCParticleObjectAsset.cpp:52-65`（`CreateNewAsset`）— `Derive` 分支**整块被注释掉**
- `FUGCObjectTemplateInfo` **默认 `Derive`**（`UGCObjectTemplateManager.h:57`）→ 随手挑容易踩中

```python
import json
tpl = json.loads(ue.objed_query_templates('Asset', '特效'))
usable = [t for t in tpl['templates'] if t.get('create_method') == 'Duplicate']
```

### 三级查询的强制顺序

`UGCAskQObjectEditorQuery.h:17-24` 明确：
```
editor_type(编辑器类型) → asset_type(资产类型) → template_name(模版名称)
"必须逐级查询，不可跳过"
```
对应 `ue_read` 的 `query_type="objed"`，`query_mode` ∈
`editor_types` / `asset_types` / `templates` / `assets`（`:53-57`、`UGCAskQObjectEditorQuery.cpp:46-68`）。

`query_mode="templates"` 返回模板名列表，形如 `TypeName / AssetRootPath`（`UGCAskQObjectEditorQuery.cpp:134-142`）。

---

## 2. AI 语义搜索 API

Provider：`Plugins/UGCEditor/Source/UGCAISearch/Private/PythonExt/UEPyAISearch.cpp`

| 函数 | 签名 | 出处 |
|---|---|---|
| `ai_search` | `ue.ai_search(query, types=None, use_keep_think=True, timeout=30.0, max_results=50, min_score=0.0, proxy='MCPAgent', with_dimensions=False) -> dict` | `:1054-1093` |
| `ai_search_start` | `ue.ai_search_start(query, types=None, use_keep_think=True, proxy='MCPAgent') -> dict` | `:1100-1126` |
| `ai_search_is_done` | `ue.ai_search_is_done(proxy='MCPAgent', pump=True, pump_seconds=1.0) -> dict` | `:1132-1163` |
| `ai_search_get_results` | `ue.ai_search_get_results(max_results=50, min_score=0.0, proxy='MCPAgent', with_dimensions=False) -> list[dict]` | `:1170-1195` |
| `ai_search_types` | `ue.ai_search_types() -> list[dict]` | `:1202-1222` |

### 返回结构
`{success, timeout, query, proxy, types, elapsed, total, count, error, results[]}`；
`results` 每项：`{package_name, asset_path, asset_name, asset_class, exists, type, score, raw_score, rerank_score, reranked, dimensions?}`，按 `score` 降序（`:1073`）。

### 粒子特效的类型别名（权威）

`UEPyAISearch.cpp:69-72`：
```cpp
{ kParticle, TEXT("ps") },
{ kParticle, TEXT("particle") },
{ kParticle, TEXT("particlesystem") },
{ kParticle, TEXT("particle_system") },
```
→ `types='ps'` 最简。

### 全部可搜索类型（`UEPyAISearch.cpp:55-85`）
| 类型 | 别名 |
|---|---|
| 全部 | `all` |
| StaticMesh | `sm`, `staticmesh`, `static_mesh` |
| Material | `mat`, `material` |
| MaterialInstance | `matinst`, `mi`, `materialinstance`, `material_instance` |
| **ParticleSystem** | **`ps`, `particle`, `particlesystem`, `particle_system`** |
| AnimSequence | `anim`, `animation`, `animsequence`, `anim_sequence` |
| Texture2D | `tex2d`, `texture`, `texture2d` |
| SkeletalMesh | `skm`, `skeletalmesh`, `skeletal_mesh` |

⚠️ **别名不做静默兜底**：拼错抛 `ValueError`，不会"搜到别的类型"（`:88` 注释）。

### 关键限制（`:1091` 原文 Notes）
- 会**阻塞游戏线程**直到完成/超时；**只能在游戏线程调用**。
- **只能搜到被 AISearch 烘焙过的资产** —— 刚创建的特效若未烘焙，`ai_search` 搜不到，可能需 `exists=False` 判断。
- 需要网络访问 Embedding 服务。
- `success=False` 时 `results` 仍可能有部分结果，读 `error` 判断原因。

### 推荐轮询写法（`:1148-1157`）
```python
ue.ai_search_start('破旧的木箱', types='SM')
waited = 0.0
while waited < 30.0:
    st = ue.ai_search_is_done()        # 默认 pump_seconds=1.0，内部已等 1 秒
    if st['done']:
        break
    waited += st['suggested_poll_interval']
items = ue.ai_search_get_results(max_results=20) if st['done'] else []
```

---

## 3. 属性读写 Toolset

Provider：`UniExtend/Source/UGCAskQ/Private/Toolsets/UGCObjectToolset.h`

| 函数 | 签名 | 出处 |
|---|---|---|
| `SetProperties` | `static FString SetProperties(const FString& InstancePath, const FString& ValuesJson)` | `:50` |
| `GetProperties` | `static FString GetProperties(const FString& InstancePath, const FString& PropertyNames)` | `:60` |
| `ListProperties` | `static FString ListProperties(const FString& ClassPath)` | `:82` |
| `GetClassSchema` | `static FString GetClassSchema(const FString& ClassPath)` | `:91` |

**AI 侧调用约定**（前置方案 §6.5）：
```
list_toolsets
describe_toolset(toolset="UGCAskQ.UGCObjectToolset")
call_toolset(toolset="UGCAskQ.UGCObjectToolset", tool="GetClassSchema", params="{\"ClassPath\":\"...\"}")
```
⚠️ Toolset 名格式是 `<包名末段>.<类名>`（含 `UU` 前缀），不是裸类名。
证据：`UGCAskQFunctionLibraryToolset.cpp:121-166`；权威示例 `UGCActorToolset.h:49` 写的就是
`call_toolset("UGCAskQ.UGCActorToolset", "AddComponent", {...})`。

---

## 4. 加载与访问资产（回读验证用）

⚠️ **不存在 `ue.load_asset`**（全仓库检索无此注册）。加载资产用 **`ue.load_object`**，
且类必须从 `unreal_engine.classes` 导入（`ue.ParticleSystem` **不存在**）：

```python
# load_object 注册处：UGCUnrealEnginePython\Private\UEPyModule.cpp:307
#   { "load_object", py_unreal_engine_load_object, METH_VARARGS, "" }
from unreal_engine.classes import ParticleSystem      # ✅ 正确
ps = ue.load_object(ParticleSystem, '/P08272152/Asset/Particles/SkillFX/AoE/FX_FireExplosion')
if ps:
    ue.log('class=%s' % ps.get_class().get_name())
    ue.log('emitters=%d' % len(ps.Emitters))          # 只读副本

# ❌ ue.ParticleSystem        → AttributeError: module 'unreal_engine' has no attribute 'ParticleSystem'
# ❌ ue.load_object('ParticleSystem', path) → Exception: argument is not a UObject
```

**属性访问约定（本 UE4.18 绑定）**：
- **没有 `get_editor_property` / `set_editor_property`**；
- 属性直接 **PascalCase** 访问，如 `ps.Emitters`、`ps.LODDistances`；
- 枚举/结构体成员同样按绑定暴露的名字访问。
- ⚠️ `ps.Emitters` 是**只读 list 副本**，增删不会持久化（详见 `pitfalls.md §14`）。

> 若要"改属性"，优先走 `UGCAskQ.UGCObjectToolset` 的 `SetProperties`（它对复杂类型
> Array/Struct/InstancedObject 有完备管线 + EditCondition 两段式写入），而不是在 Python 里直接赋值。
> 且变更前需先 `ue_plan_submit` 提交计划（否则触发 PRV VIOLATION 警告）。

---

## 5. `ue_read` 的查询前缀（同一工具内可用）
`UGCAskQMCPServer.Tool.cpp:963-1051` 实装的前缀：

| 前缀 | 用途 |
|---|---|
| `status:` | 编辑器就绪状态（UGC 登录门禁）——**先调这个** |
| `ctx:[sub]` | 当前编辑器上下文（工程/关卡/选中 Actor/打开资产） |
| `qt:[name]` | 查询类型索引 / 某类型用法 |
| `py:<kw>` | Python API 文档查询（`py:guide <cat>`、`py:<method>`、`py:workflow <name>`） |
| `schema:<Type>` | UClass/UStruct 反射 schema |
| `subclasses:<Base>` | 子类发现 |
| `bt:[nodes [filter]]` | 行为树节点 |
| `enum:<EnumName>` | 枚举值 |
| `level:[sub]` | 关卡相关 |
| `verify:<...>` | 校验 |

别名归一（`:878-880`）：`context` → `ctx:`、`workflow` → `py:workflow `。

结构化入口：`ue_read { "query_type": "objed", ... }`（`:1084`、`:1256-1265`）。

---

## 6. 常用相关前缀速查

| 目的 | 调用 |
|---|---|
| 看粒子系统类字段 | `ue_read {"queries":["schema:UParticleSystem"]}` |
| 看发射器类字段 | `ue_read {"queries":["schema:UParticleEmitter"]}` |
| 看粒子组件字段 | `ue_read {"queries":["schema:UParticleSystemComponent"]}` |
| 查物编查询类型用法 | `ue_read {"queries":["qt:objed"]}` |
| 列 Python API 分类 | `ue_read {"queries":["py:index"]}` |
