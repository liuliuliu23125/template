# 特效场景配方（UGCEditor）

> `ugc-vfx-gen` skill 的 L3 细节层。每个配方给出**可执行的最小调用序列**。
> 模板名与 asset_type 因项目配置而异 —— 下文用 `<asset_type>` / `<template_name>` 占位，
> 必须先用 §"模板发现"查询真实取值，**不要照抄占位符**。

## 模板发现（所有配方的公共前置）

```
ue_read { "query_type": "objed", "query_mode": "asset_types", "editor_type": "Asset" }
ue_read { "query_type": "objed", "query_mode": "templates",   "editor_type": "Asset", "asset_type": "特效" }
```

⚠️ **拿到模板后必须过滤 `create_method == "Duplicate"`** —— `Derive` 模板对粒子会静默失败（返回 nullptr）。
⚠️ **`sub_dir` 只能用 ASCII**（中文会抛 `ValueError`，与仓库文档描述相反）。
⚠️ **`objed_query_templates` 只吃位置参数**（`keywords=` / `top_n=` 会报 `takes no keyword arguments`）。
⚠️ **模板字段名是 `template_name`**，不是 `name`。

```python
import json
# 位置参数：editor_type, asset_type, keywords, top_n
tpl = json.loads(ue.objed_query_templates('Asset', '特效', '刀光,斩击', 8))
usable = [t for t in tpl['templates'] if t.get('create_method') == 'Duplicate']
for t in usable[:5]:
    ue.log('%s | %s' % (t['template_name'], t.get('category')))
```

---

## 配方 A：近战刀光 / 剑气

**参考搜索**（先找现成的，优先复制改造）：
```python
r = ue.ai_search('红色弧形刀光 剑气拖尾', types='ps', max_results=10)
```
搜索词建议用"形态 + 方向 + 元素 + 颜色"，例如：
`垂直红色弧形刀光`、`水平扩散蓝色冲击波`、`斜向喷射金色火花`。

**创建**：
```python
path = ue.objed_create_asset('Asset', '<asset_type>', '<template_name>',
                             'FX_SlashArc_Red', 'SkillFX/Melee')
ue.objed_open_asset('FX_SlashArc_Red', 'Asset')
ue.objed_save_asset('FX_SlashArc_Red', 'Asset')
```

**若已有高度相似资产，直接复制更省事**：
```python
ue.objed_duplicate_asset('FX_SlashArc_Blue', 'FX_SlashArc_Red', 'Asset')
```

---

## 配方 B：爆炸 / 冲击波

```python
# 1) 先找参考（冲击波通常是环形/球形 + 放射状）
r = ue.ai_search('水平扩散的蓝色冲击波 环形', types='ps', max_results=10)

# 2) 创建
path = ue.objed_create_asset('Asset', '<asset_type>', '<template_name>',
                             'FX_Shockwave_Blue', 'SkillFX/AoE')
ue.objed_open_asset('FX_Shockwave_Blue', 'Asset')
ue.objed_save_asset('FX_Shockwave_Blue', 'Asset')
```

---

## 配方 C：拖尾 / 弹道

```python
r = ue.ai_search('金色火花拖尾 弹道', types='ps', max_results=10)
path = ue.objed_create_asset('Asset', '<asset_type>', '<template_name>',
                             'FX_Trail_Gold', 'SkillFX/Projectile')
```

---

## 配方 D：Buff / 护盾光环

```python
r = ue.ai_search('护盾 光环 上升气流 治疗', types='ps', max_results=10)
path = ue.objed_create_asset('Asset', '<asset_type>', '<template_name>',
                             'FX_Shield_Aura', 'SkillFX/Buff')
```

---

## 配方 E：为已有技能挂特效

技能资产（`editor_type='Skill'`）与特效是两类资产。常见做法是**先生成特效资产，
再在技能编辑器里引用**：

```python
# 1) 生成特效
fx = ue.objed_create_asset('Asset', '<asset_type>', '<template_name>',
                           'FX_FireBall_Hit', 'SkillFX/Fire')

# 2) 打开技能资产（自动识别 editor_type）
ue.objed_open_asset('SK_FireBall')

# 3) 在技能里设置引用了该特效的字段：先查 schema，再写
#    ue_read { "queries": ["schema:<你的 Task 类>"] }
#    call_toolset("UGCAskQ.UGCObjectToolset", "SetProperties", {...})
```

> 技能编辑器侧的完整流程见 `ue_read {"queries":["py:workflow skill"]}`（需先
> `AskQ.Workflow.Set 1` 开启该功能，默认关闭）。

---

## 配方 F：把特效整体放大 / 缩小（做"巨大"或"迷你"版）

Cascade **没有全局 Scale 参数**，"变大"= 把几个**空间量**按同一系数缩放。
推荐系数：空间量 ×3~4、生命周期 ×1.5（巨大版）；空间量 ×0.5、生命周期 ×1 左右（迷你版）。

**要缩放的字段**（按 **Distribution 实例**唯一化，不是按发射器 —— 见 SKILL.md 铁律 8 与 `pitfalls.md §17.2`）：

| 模块类 | 字段 | 语义 |
|---|---|---|
| `ParticleModuleSize[._Seeded]` | `StartSize` | 粒子本身尺寸 |
| `ParticleModuleLocationPrimitiveSphere[._Seeded]` | `StartRadius` | 初始球体分布半径 |
| `ParticleModuleLocationPrimitiveSphere[._Seeded]` | `VelocityScale` | 球体径向速度（⚠️ 易漏，漏了会"铺开但飞不远"） |
| `ParticleModuleLocationPrimitiveCylinder[._Seeded]` | `StartRadius` / `StartHeight` / `VelocityScale` | 柱体分布半径/高度/径向速度 |
| `ParticleModuleVelocity[._Seeded]` | `StartVelocity` / `StartVelocityRadial` | 初速度 |
| `ParticleModuleLifetime[._Seeded]` | `Lifetime` | 存活时长（系数另给） |
| `ParticleModuleLocation` | `StartLocation` | 发射位置偏移（⚠️ 易漏：不缩放会让分层全挤在低处） |
| `ParticleModuleCameraOffset` | `CameraOffset` | 相机方向偏移（保持与粒子尺度的比例） |

> ⚠️ **不要缩放**（无量纲的比例/颜色/角度参数）：`SizeScale`、`SizeMultiplyLife`、
> `ColorOverLife`、`Rotation`、`RotationRate`、`SubUV`、`AccelerationDrag` 系数。

**配套要一起改的**（否则会不一致 / 被裁）：

- `ParticleModuleRequired.MaxDrawCount`：放大后粒子更显眼，可 500 → 1500；`bUseMaxDrawCount` 置 True。
- `UParticleSystem.MacroUVRadius`：若材质用 MacroUV，按同系数放大才能保持纹理密度。
- `UParticleSystem.FixedRelativeBoundingBox`：⚠️ `ue.FBox` 不存在，**只能走 Toolset** 写。
  若原包围盒相对原始粒子尺度已有 ~4× 余量，可先不动（本次 ×3.5 即未改，实测可接受）。

```python
import unreal_engine as ue, json
from unreal_engine.classes import ParticleSystem
from toolset_proxy import ToolsetProxy          # 在 ue_py 内直调 Toolset

P, PT = '<新资产路径>', '<模板资产路径>'
S, SL = 3.5, 1.5                                # 空间系数 / 生命周期系数
TS = ToolsetProxy('UGCAskQ.UGCObjectToolset')

SPEC = {
    'ParticleModuleSize': ('StartSize',),
    'ParticleModuleSize_Seeded': ('StartSize',),
    'ParticleModuleLocationPrimitiveSphere': ('StartRadius', 'VelocityScale'),
    'ParticleModuleLocationPrimitiveSphere_Seeded': ('StartRadius', 'VelocityScale'),
    'ParticleModuleLocationPrimitiveCylinder': ('StartRadius', 'StartHeight', 'VelocityScale'),
    'ParticleModuleLocationPrimitiveCylinder_Seeded': ('StartRadius', 'StartHeight', 'VelocityScale'),
    'ParticleModuleVelocity': ('StartVelocity', 'StartVelocityRadial'),
    'ParticleModuleVelocity_Seeded': ('StartVelocity', 'StartVelocityRadial'),
    'ParticleModuleLifetime': ('Lifetime',),
    'ParticleModuleLifetime_Seeded': ('Lifetime',),
    'ParticleModuleLocation': ('StartLocation',),        # 发射位置偏移
    'ParticleModuleCameraOffset': ('CameraOffset',),     # 相机方向偏移
}

ps, tp = ue.load_object(ParticleSystem, P), ue.load_object(ParticleSystem, PT)

# ⚠️ 唯一化主键必须是【Distribution 实例路径】，不是"发射器序号+模块类+属性"：
#    跨发射器共享同一实例的情况真实存在（实测 E2/E3 共享 CameraOffset/Location），
#    以发射器做键会把同一实例缩放两次（实测 50 → 612.5，正确应为 175）。
def collect(ps_obj):
    """返回 (inst_path -> d,  inst_path -> [发射器序号],  inst_path -> 属性名)"""
    out, owner, prop_of = {}, {}, {}
    for ei, e in enumerate(ps_obj.Emitters):
        mods = {}
        for l in e.LODLevels:
            for m in l.Modules:
                mods[m.get_path_name()] = m            # ① LOD 维度先去重
        for m in mods.values():
            for prop in SPEC.get(m.get_class().get_name(), ()):
                try:
                    d = getattr(m, prop).Distribution
                except Exception:
                    continue
                if d is None:
                    continue
                pn = d.get_path_name()                 # ② 实例路径做唯一键
                out[pn] = d
                prop_of.setdefault(pn, prop)
                owner.setdefault(pn, [])
                if ei not in owner[pn]:
                    owner[pn].append(ei)
    return out, owner, prop_of

new_d, new_owner, new_prop = collect(ps)
tpl_d, _, tpl_prop = collect(tp)
for pn, eis in new_owner.items():                      # ③ 共享审计（务必看一眼）
    if len(eis) > 1:
        ue.log('SHARED  %s  <- emitters %s' % (pn.split(':')[-1], eis))

def rd(d):
    cn = d.get_class().get_name()
    if cn == 'DistributionFloatConstant': return ('fc', float(d.Constant))
    if cn == 'DistributionFloatUniform':  return ('fu', float(d.Min), float(d.Max))
    if cn == 'DistributionVectorUniform':
        return ('vu', (d.Min.x, d.Min.y, d.Min.z), (d.Max.x, d.Max.y, d.Max.z))   # ⚠️ 小写 x/y/z
    if cn == 'DistributionVectorConstant':
        return ('vc', (d.Constant.x, d.Constant.y, d.Constant.z))
    return ('?',)

def scale_to(d, base, f):
    """按【模板绝对值 × 系数】写入 —— 不要用"当前值 × 系数"（重复执行会叠乘且无法自愈）"""
    if base[0] == 'fc':
        d.Constant = base[1] * f; return True
    if base[0] == 'fu':
        d.Min, d.Max = base[1] * f, base[2] * f; return True
    if base[0] == 'vu':                           # 向量 → Toolset（JSON 用大写 X/Y/Z）
        TS.SetProperties(InstancePath=d.get_path_name(), ValuesJson=json.dumps({
            'Min': {'X': base[1][0]*f, 'Y': base[1][1]*f, 'Z': base[1][2]*f},
            'Max': {'X': base[2][0]*f, 'Y': base[2][1]*f, 'Z': base[2][2]*f}})); return True
    if base[0] == 'vc':                           # ⚠️ DistributionVectorConstant 也必须处理，
        v = base[1]                               #    否则 StartSize/StartLocation 这类常量会被静默跳过
        TS.SetProperties(InstancePath=d.get_path_name(), ValuesJson=json.dumps(
            {'Constant': {'X': v[0]*f, 'Y': v[1]*f, 'Z': v[2]*f}})); return True
    return False

# 1) 缩放：遍历【唯一 Distribution 实例】，每个实例只写一次
ok = fail = 0
for pn, d in new_d.items():
    if pn not in tpl_d:
        fail += 1; ue.log('  no template base: %s' % pn.split(':')[-1]); continue
    # ⚠️ 生命周期系数按【属性名】判定。旧写法 `'Lifetime' in k`（k 为 Distribution 子对象名）
    #    永不命中 → SL 静默失效，生命周期被按空间系数放大。
    f = SL if new_prop.get(pn) == 'Lifetime' else S
    if scale_to(d, rd(tpl_d[pn]), f): ok += 1
    else:
        fail += 1; ue.log('  unscalable %s type=%s' % (pn.split(':')[-1], rd(tpl_d[pn])[0]))
ue.log('scaled ok=%d fail=%d  (S=%.2f SL=%.2f)' % (ok, fail, S, SL))

# 2) 配套
for e in ps.Emitters:
    for l in e.LODLevels:
        r = l.RequiredModule
        if r: r.bUseMaxDrawCount = True; r.MaxDrawCount = 1500
ps.MacroUVRadius = float(tp.MacroUVRadius) * S

# 3) 保存 + 容差校验（不要用 ==）
ue.objed_save_asset('<资产名>', 'Asset')
```

**验证**：按【唯一 Distribution 实例】比对 `new ≈ template × factor`（容差 `1e-3`），
抽样打印关键值。
⚠️ 验证必须与写入用同一套唯一化主键 —— 若按发射器维度比对，共享实例会命中多次而**报假失败**
（或掩盖真失败），这是本配方旧版最容易误判的地方。
本次实测：`FX_LargeFire` 18/18、`FX_LargeSmoke` 17/17，补完 `StartLocation`/`CameraOffset` 后 8/8，
`failed=0`；`MacroUVRadius 200 → 700`、`MaxDrawCount 500 → 1500`、发射器数 5+5 保持不变。

> ⚠️ 想要"巨大"却只改 `StartSize` 是常见误区 —— 那只是粒子更大，
> **整个烟花还是原来的大小**。决定"大不大"的是 **Radius + Velocity + VelocityScale + Lifetime**。

---

## 属性微调（创建之后）

**原则：先查 schema，再写值。不要猜字段名。**

```python
# ① 看类上有哪些字段（含类型/默认值/EditCondition/枚举可选值）
#    ue_read { "queries": ["schema:UParticleSystem"] }
#    ue_read { "queries": ["schema:UParticleSystemComponent"] }

# ② 读当前值
#    call_toolset(toolset="UGCAskQ.UGCObjectToolset", tool="GetProperties",
#                 params="{\"InstancePath\":\"<资产路径>\",\"PropertyNames\":\"\"}")

# ③ 写值
#    call_toolset(toolset="UGCAskQ.UGCObjectToolset", tool="SetProperties",
#                 params="{\"InstancePath\":\"<资产路径>\",\"ValuesJson\":\"{\\\"Field\\\":value}\"}")
```

⚠️ **EditCondition 门控字段需两段式写入**：先写门控 bool 为 true，再写目标字段。
详见 `ue_read {"queries":["py:workflow property"]}`。

⚠️ **修改后必须保存**：`ue.objed_save_asset('<name>', 'Asset')`。

---

## 批量创建

```python
names = ['FX_Hit_Fire', 'FX_Hit_Ice', 'FX_Hit_Lightning']
for n in names:
    ue.objed_create_asset('Asset', '<asset_type>', '<template_name>', n, 'SkillFX/Hit')
    ue.objed_save_asset(n, 'Asset')
```
⚠️ **一次不要超过 3 个**（宿主文档警告：`objed_create_asset` / `objed_delete_asset` /
`objed_rename_asset` 均标注"批量操作时一次不要超过3个，防止工具调用超时"）。
超过 3 个请拆成多轮，或分批之间告知用户进度。

---

## 命名建议

| 前缀 | 用途 | 例 |
|---|---|---|
| `FX_` | 粒子特效 | `FX_FireSlash` |
| `NS_` | （若项目引入 Niagara） | `NS_FireSlash` |

- `asset_name` 必须**英文、字母开头**。
- `sub_dir` **只能 ASCII**、可多级：`'SkillFX/Melee/Slash'`（中文会抛 `ValueError`，见 pitfalls.md §3）。
- 建议按 `SkillFX/<功能域>` 归类（ASCII），便于 `objed_query_assets` 检索。
