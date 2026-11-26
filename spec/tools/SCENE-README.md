# 场景契约工具

> 让 Agent 认识场景里的 Actor：可摆放什么、可调什么、已经摆了多少。

## 为什么和 UI 不一样

UI 有编辑器自动生成的控件清单（`---@field`），场景没有。一个 `.umap` 里摆了 200 个 Actor，
没有任何脚本告诉你「这里有一个刷怪点」。

所以本工具需要**两层数据**，缺一层都不成立：

| 层 | 来源 | 回答什么 |
|---|---|---|
| **属性层** | Actor 绑定脚本的 `---@field` | 这个类可调什么参数 |
| **摆放层** | 扫描 `.umap` 的字符串表 | 这个类真的被摆到图上没有、摆在哪几张图 |

只靠属性层会把技能、特效、物品类都算进来，大部分根本不能摆；
只靠摆放层会丢失配置字段。两层交叉才能收敛到真正可摆放的 Actor。

## 用法

```bash
# 生成契约库
python -I spec/tools/scene_contract.py index \
  --project "ShadowTrackerExtra/UGCProjects/Withdraw/Script" Withdraw \
  --map-dir "ShadowTrackerExtra/UGCProjects/Withdraw" \
  --asset-dir "ShadowTrackerExtra/UGCProjects/Withdraw/Asset" \
  --out spec/scene-contracts

# 校验（有问题时退出码 1）
python -I spec/tools/scene_contract.py check \
  --project "ShadowTrackerExtra/UGCProjects/Withdraw/Script" Withdraw \
  --map-dir "ShadowTrackerExtra/UGCProjects/Withdraw" \
  --asset-dir "ShadowTrackerExtra/UGCProjects/Withdraw/Asset" \
  --out spec/scene-contracts
```

`--map-dir` 是摆放层的数据源；不传则只做属性层与代码引用检查，摆放数全为 0。
`--map-prefix` 可选，默认匹配任意 `/<Project>/Asset/Blueprint/`；地图资产不在该路径时显式传入。

## 产出

| 文件 | 内容 | 何时读 |
|---|---|---|
| `INDEX.md` | 汇总 + Tag 定义 + 运行时约定 | 先看这个 |
| `<标签>.md` | 每个 Actor 的配置字段 / 组件 / 摆放位置 | 实现某类 Actor 逻辑时 |
| `index.json` | 机器可读全量 | 脚本化查询 |
| `CHECK-REPORT.md` | 校验结果 | 跑 `check` 后 |

## 关键过滤规则

从全部绑定类里收敛到可摆放 Actor，靠的是父类链判定：

```
沿 ---@class A_C:B_C 一路向上收集父类名
任一环节命中 SKILL/BUFF/EFFECT/ITEMHANDLE/WEAPON/... → 排除
任一名命中 ACTOR/PAWN/SPAWNER/TELEPORT/CHEST/AREA/MOB/BOSS → 保留
已在 .umap 中出现过的类 → 直接保留（真值优先）
```

「已在图中出现」优先级最高，因为它是**实测真值**，不会错。

## 检查规则

| 规则 | 说明 |
|---|---|
| `LoadClass` 引用的蓝图类未找到 | `LoadClass(GetUGCResourcesFullPath("Asset/Blueprint/..."))` 指向不存在的资产 |
| Tag 字面量未在 TagKey 中定义 | 直接写 `GetAllActorsWithTag(w, "SomeTag")` 而不是 `TagKey.XXX` |

Tag 规则命中的问题说明 Tag 值散落在代码里，改名时不会被发现。

## 实测基线

```
Actor 类       37（可摆放）
已摆放         24
地图           6
绑定类总数     312（其中 275 个被过滤）
代码引用类     9
Tag 使用点     4
问题           1
```

负向测试：注入 `LoadClass(...__NotExist__.uasset)` 与 `GetAllActorsWithTag(g,"NoSuchTag")`
→ 两条都被命中，退出码 1；还原后只剩基线内 1 条，退出码 0。

## 基线机制

退出码只看**新增**问题。当前有 1 条历史遗留（`MobaCamera` 字面量），已写入基线：

```bash
python -I spec/tools/scene_contract.py check ... --write-baseline --yes   # 建/更新基线
python -I spec/tools/scene_contract.py check ...                          # 只报新增
```

- `BASELINE.json` 记录已知问题 + `generated_at` + `source_sha256` + `source_files`。
- 交互终端写基线会二次确认；非交互环境必须显式 `--yes`。
- 源哈希变化时报告提示「基线可能过期」；修掉后重跑 `--write-baseline --yes` 更新。
- 实测：注入 `BrandNewTag` → 新增 1 → 退出码 1；还原 → 退出码 0。

## 限制

- `.umap` 只能读出类名，读不出实例数量、坐标、Transform。所以本库知道「有 4 个刷怪点」，
  但不知道它们在哪。
- 摆放层默认匹配任意 `/<Project>/Asset/Blueprint/`，不绑定具体工程；蓝图不在该路径时用 `--map-prefix` 指定。
- 父类链判定是启发式：新增命名风格特殊的 Actor 类可能被误过滤，检查 `index.json` 数量即可发现。
- 不含商店包（商店包无 `.umap`，且实测 `Oasis_*` 全是美术资源、无 Actor 蓝图）。

## 何时重跑

- 人新增/移动地图 Actor 后 → `index`
- Agent 每批场景逻辑改动后 → `check`（属验证 L2 层，约 1 秒）
- 新增 Actor 绑定脚本后 → `index`