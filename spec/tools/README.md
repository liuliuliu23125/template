# spec/tools 工具集

| 工具 | 用途 | 文档 |
|---|---|---|
| `ui_contract.py` | UI 控件契约：控件存在性、命名、类型 | 本文 |
| `scene_contract.py` | 场景 Actor 契约：配置字段 + `.umap` 摆放 | `SCENE-README.md` |
| `pie_runner.py` | 内置 MCP 启动/停止 PIE、跑 AutoTestKit、截图与日志报告 | `PIE-README.md` |
| `api_contract.py` | 基于 ApiMetadataCache 的 API 签名/参数/scope/废弃检查 | `API-README.md` |
| `spec_check.py` | spec/INDEX、plan、sync、impl 的结构一致性检查 | `SPEC-README.md` |

## UI 契约工具

> 一个脚本两个子命令，解决两件事：让 Agent 认识 UI 控件，以及防止 Agent 引用不存在的控件。

### 为什么需要

UMG 资产是 cooked 二进制：**控件名可读、控件类型可读、控件树结构标记可读**，
但布局数值（anchors / offsets / 尺寸）无法解析，也无法写回。

因此 UI 只能拆成两半处理：

| 层面 | 谁负责 | 载具 |
|---|---|---|
| 控件存在性、命名、类型 | 编辑器（人建 UMG 时自动写入绑定文件上半部） | `---@field` + uasset 字符串 |
| 控件行为 | Agent | 绑定文件 `--Edit Below--` 之下 |
| 布局数值、美观、手感 | 人 | uasset 二进制 |

Agent 无法改变布局，但**必须知道有哪些控件**。这就是本工具存在的理由。

### 用法

```bash
# 生成契约库（149 个界面 / 1568 个控件）
python -I spec/tools/ui_contract.py index \
  --project "ShadowTrackerExtra/UGCProjects/Withdraw/Script" Withdraw \
  --store "ShadowTrackerExtra/UGCStoreAssets" Store \
  --out spec/ui-contracts

# 校验：Agent 代码是否引用了未声明的控件（有问题时退出码 1）
python -I spec/tools/ui_contract.py check \
  --project "ShadowTrackerExtra/UGCProjects/Withdraw/Script" Withdraw \
  --store "ShadowTrackerExtra/UGCStoreAssets" Store \
  --out spec/ui-contracts
```

`--project` / `--store` 都可重复，格式是 `<脚本目录> <标签>`。
`--project` 指向 `<工程>/Script` 时会自动推导 `<工程>/Asset` 作为资产根；也可用 `--asset-dir` 显式指定。
资产按 `---@class` 的类名在全部资产目录里查找，不依赖目录对应关系。
`--strict` 会检查所有 `self.X` 引用（不再只按控件后缀过滤），可能把 `CachedTarget` 这类非控件字段报出来，需要人工复核。

### 产出

| 文件 | 内容 | 何时读 |
|---|---|---|
| `INDEX.md` | 汇总表 + 命令 | 先看这个 |
| `Withdraw.md` / `Store.md` | 每个界面的控件清单 | 实现某个界面时 |
| `index.json` | 机器可读全量 | 需要脚本化查询时 |
| `CHECK-REPORT.md` | 契约校验结果 | 跑 `check` 后 |

### 检查规则

**代码引用未声明控件**（必须修）：`self.Xxx` 出现在 `--Edit Below--` 之下，
但 `Xxx` 不在上半部 `---@field` 里。这类引用在运行期会是 `nil`，且只有点到那里才暴露。

排除以下情况，实测零误报：

| 排除项 | 原因 |
|---|---|
| `if self.Xxx then` 等 nil 守卫 | 允许控件缺失时降级 |
| 字符串表里的名字（`{ DailyTask5_ReceiveText = "TextBlock_25" }`） | 按名动态取控件 |
| `self.Xxx,` 作为函数引用传参 | 事件回调，不是控件 |
| `self.Xxx = function` | 运行时挂的方法 |
| `self.Slot` / `Padding` 等 | `UUserWidget` 自带属性 |
| `self._xxx` | 私有字段命名约定 |

**声明控件在资产中缺失**（需人工确认）：`---@field` 里有，但 uasset 二进制里搜不到。
已知两种情况：控件在父类里声明；脚本与资产不同步（当前 4 个界面、10 个控件名：Withdraw 2 个、Store 2 个）。

**覆盖统计**：控件名后缀规则只检查 **427/1568（27.23%）**；其余 1141 个名字不在默认检查范围，`CHECK-REPORT.md` 会显示。`--strict` 覆盖全部，但会引入非控件字段误报。

### 实测基线（2026-11-26）

```
界面 149 个（Withdraw 64 / Store 85）
控件 1568 个（Withdraw 1087 / Store 481）
控件名后缀规则覆盖 427/1568（27.23%）
未声明引用 0
资产缺失 4（需人工确认，见 CHECK-REPORT.md）
```

负向测试：注入 `self.RemovedGoldBtn` → 命中并退出码 1；还原后退出码 0。

### 基线机制

退出码只看**新增**问题，不看历史遗留。首次跑用 `--write-baseline --yes` 把现状固化；交互终端会二次确认，非交互环境必须显式 `--yes`：

```bash
python -I spec/tools/ui_contract.py check ... --write-baseline --yes   # 建基线
python -I spec/tools/ui_contract.py check ...                          # 只报新增
```

- `BASELINE.json` 记录已知问题 + `generated_at` + `source_sha256` + `source_files`。
- `CHECK-REPORT.md` 分开列「新增未声明引用（阻断）」「新增资产缺失（不阻断）」与「基线内已知问题」。
- 源哈希变化时报告提示「基线可能过期」；修掉历史问题后重跑 `--write-baseline --yes` 更新。
- 退出码规则：**有新增未声明控件引用时返回 1**；「资产中缺失」只报告不阻断。

### 限制

- 只认 `---@class Xxx_C:父类` + `---@field` 这种编辑器生成格式；手写 Lua 类不在检查范围。
- 资产查找靠类名同名的 `.uasset`；类名与文件名不一致时会报「资产未找到」。
- 不做控件层级的还原：能知道 A 和 B 存在，不能知道 A 是 B 的子控件。

### 何时重跑

- 人新建或修改 UMG 后 → `index`（刷新契约库）
- Agent 每批 UI 改动后 → `check`（属于验证 L2 层，成本约 1 秒）
- 商店包新增下载后 → `index`