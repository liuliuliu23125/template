# UMG_GMControl 菜单文档

## 玩家管理

当前角色操作：开启无敌、关闭无敌、自杀、受击（10点）、回血（回满）、清空背包、背包格子扩展。
新增操作通过 `Player` 服务端指令执行；受击和回血沿用玩家属性组件 RPC。
无敌仅作用于当前角色，不写入存档；自杀使用 `BP_ForceDie` 进入正式死亡流程。
清空背包移除当前 V2 背包物品（包括已装备物品），保留仓库与虚拟货币，并更新存档。
格子扩展默认输入10，可填写1～1000的整数；最多扩到当前配置的背包容量上限。

以下入口已隐藏：客户端打印、服务端打印、缓存存档打印、存档数据打印、背包检测、临时状态打印。
保留原控件及底层函数；蓝图默认设为 Collapsed，Lua 初始化时再次应用隐藏。

## 资源管理

左侧竖排“材料添加 / 金币添加 / 经验增加”，右侧子面板互斥显示。
金币和经验数量使用普通 `EditableTextBox`，输入正整数后确认。

材料添加包含四个入口：

- 一键添加升级材料：8种，各100个。
- 一键添加制作材料：棉纱布、镇定药剂、空药瓶，各100个。
- 一键添加藏品：按预设中的15种物品及数量发放。
- 添加装备：21种装备，每页5个，点击一次添加1件。

清单和顺序由 `Script/Config/GM/Config_GMResources.lua` 维护，使用生成的 `Const_Item`。
新预设通过 `Resource.AddBundle`、`Resource.AddEquipment` 服务端指令发放，每次点击额外添加一份。
使用 ItemSystem 进行配置ID转换和实际入包数量核对；部分添加也保存，并提示未完成项目。
切换资源子面板、其他一级菜单或关闭GM时收起装备列表；重新打开装备列表回到第一页。

自动化测试页使用 6 个固定按钮分页显示已注册 Suite。进入页面时回到第 1 页，上一页/下一页只切换显示内容；点击 Suite 仍通过现有 `Server_RunAutoTest_BySuite` RPC 执行，运行全部测试仍使用原有 `AutoServerTest` 流程。

## 菜单结构

```
GMButton  [top，恒可见]
 └─ GROUP_SUB [一级子开关]
     ├─ DSPatch      → GROUP_DS_FUNC
     │   ├─ DSHall   [叶子：返回大厅]
     │   └─ DSLevel1 [叶子：匹配战局]
     │
     ├─ Module_Test  → GROUP_TEST_FUNC
     │   └─ Module_Print [叶子：建筑测试打印]
     │
     └─ STORE_Mgr    → GROUP_STORE_FUNC
         ├─ STORE_GUNSHOP  [叶子：军火商 UI]
         ├─ STORE_GYM      [叶子：健身房 UI]
         ├─ STORE_INFO     [叶子：信息中心 UI]
         ├─ STORE_MEDIUM   [叶子：医疗中心 UI]
         └─ STORE_STOCK    [叶子：仓库（背包面板）]
```

## 分组说明

| 分组常量 | 字符串 key | 包含按钮 | 说明 |
|---|---|---|---|
| `GROUP_TOP` | `"top"` | `GMButton` | 恒可见，作为菜单总开关 |
| `GROUP_SUB` | `"sub"` | `DSPatch`, `Module_Test`, `STORE_Mgr` | 一级子开关，点击展开各自的叶子 |
| `GROUP_DS_FUNC` | `"ds_func"` | `DSHall`, `DSLevel1` | DSPatch 的叶子按钮 |
| `GROUP_TEST_FUNC` | `"test_func"` | `Module_Print` | Module_Test 的叶子按钮 |
| `GROUP_STORE_FUNC` | `"store_func"` | 5 个 STORE 按钮 | STORE_Mgr 的叶子按钮 |

## 热更新机制

### 核心原理

按钮点击采用 **Dispatcher 模式**，支持热更新后立即生效，无需重新编译运行。

```
点击按钮
  → OnClicked:Add(Dispatcher)
  → Dispatcher(self, "Module_Print")
  → _G.__GMHandlers["Module_Print"](self)
  → self["Module_Print_Real"](self)
```

热更新时：
- `_G.__GMHandlers` 存在 Lua 全局表，跨热更新持久化
- `Dispatcher` 闭包只捕获字符串名字，永远不需要重新绑定
- `self` 是热更新后的新模块表，`self["XXX_Real"]` 是热更新后的新函数

### 核心代码

```lua
-- _G 持久化 handler 表
_G.__GMHandlers = _G.__GMHandlers or {}

-- handler 名 → 函数名的映射
local HANDLER_MAP = {
    GMButton      = "GMButton_Real",
    DSPatch       = "DSPatch_Real",
    -- ... 其他按钮
}

-- 注册：闭包只捕获 funcName，module 在调用时传入
local function RegisterAllHandlers()
    for fieldName, funcName in pairs(HANDLER_MAP) do
        _G.__GMHandlers[fieldName] = function(module)
            return module[funcName](module)
        end
    end
end

-- 分发：按名字查表
local function Dispatcher(self, fieldName)
    local handler = _G.__GMHandlers[fieldName]
    if handler then
        return handler(self)
    end
end

-- 按钮绑定：统一绑定 Dispatcher
self.GMButton.OnClicked:Add(function() Dispatcher(self, "GMButton") end);
```

### 为什么不用直接绑定

```lua
-- 旧方案（不支持热更新）
self.GMButton.OnClicked:Add(self.GMButton_Real, self);
-- 问题：底层存的是函数指针，热更新后 self 是新表，指针不变 → 调用旧代码

-- 新方案（支持热更新）
self.GMButton.OnClicked:Add(function() Dispatcher(self, "GMButton") end);
-- 按钮只绑 Dispatcher（固定闭包），点击时按名字查表 → 热更新后取到新函数
```

## 核心函数

### ShowGroups(...)
控制按钮显隐。

- `groupName == GROUP_TOP` → 始终可见
- 其余分组 → 在 `showSet` 中则 Visible，不在则 Collapsed
- 不传参 → 全部折叠（仅 top 可见）

```lua
-- 示例：展开 DSPatch 的叶子
self:ShowGroups(GROUP_SUB, GROUP_DS_FUNC)

-- 示例：收起全部
self:ShowGroups()
```

### IsGroupOpen(groupName)
判断某分组当前是否展开。以分组内**第一个按钮**的可见性为整组代表。

```lua
if self:IsGroupOpen(GROUP_DS_FUNC) then
    -- GROUP_DS_FUNC 已展开，需要收起
else
    -- GROUP_DS_FUNC 已收起，需要展开
end
```

## 新增功能扩展指南

### 添加新按钮（完整步骤）

假设新增按钮 `MyNewButton`（叶子）和 `MyNewParent`（子开关），需要：

**1. 在 UMG Blueprint 中添加按钮字段**（编辑器内绑定）

**2. 在文件顶部 `@field` 声明**
```lua
---@field MyNewButton UButton
---@field MyNewParent UButton
```

**3. 在 `HANDLER_MAP` 中注册**
```lua
local HANDLER_MAP = {
    -- 现有映射...
    MyNewButton = "MyNewButton_Real",
    MyNewParent = "MyNewParent_Real",
}
```

**4. 在 `BtnGroups` 中注册分组**
```lua
self.BtnGroups = {
    -- 现有分组...
    [GROUP_MYNEW_FUNC] = { self.MyNewButton },
}
```

**5. 添加新分组常量**
```lua
local GROUP_MYNEW_FUNC = "mynew_func"
```

**6. 绑定点击事件**
```lua
self.MyNewButton.OnClicked:Add(function() Dispatcher(self, "MyNewButton") end);
self.MyNewParent.OnClicked:Add(function() Dispatcher(self, "MyNewParent") end);
```

**7. 实现业务函数（命名规范：`XXX_Real`）**
```lua
function UMG_GMControl:MyNewParent_Real()
    if self:IsGroupOpen(GROUP_MYNEW_FUNC) then
        self:ShowGroups(GROUP_SUB)
    else
        self:ShowGroups(GROUP_SUB, GROUP_MYNEW_FUNC)
    end
    return nil;
end

function UMG_GMControl:MyNewButton_Real()
    ugcprint("[GM] MyNewButton_Real")
    -- 业务逻辑...
    self:ShowGroups()
    return nil;
end
```

### 点击函数的三种模式

| 模式 | 场景 | 代码 |
|---|---|---|
| 叶子（触发功能） | `DSHall`、`Module_Print` 等 | `self:ShowGroups()`（收起菜单） |
| 子开关（展开叶子） | `DSPatch`、`Module_Test` 等 | `ShowGroups(GROUP_SUB, GROUP_XXX_FUNC)` |
| 总开关（展开子开关） | `GMButton` | `ShowGroups(GROUP_SUB)` |

### 所有按钮绑定一览

| 按钮 | 函数 | 类型 | 功能 |
|---|---|---|---|
| `GMButton` | `GMButton_Real` | 总开关 | 展开/收起一级子开关 |
| `DSPatch` | `DSPatch_Real` | 子开关 | 展开/收起 GROUP_DS_FUNC |
| `DSHall` | `DSHall_Real` | 叶子 | 请求返回大厅 |
| `DSLevel1` | `DSLevel1_Real` | 叶子 | 请求战局匹配 |
| `Module_Test` | `Module_Test_Real` | 子开关 | 展开/收起 GROUP_TEST_FUNC |
| `Module_Print` | `Module_Print_Real` | 叶子 | 遍历建筑类型，打印等级/消耗/效果数据 |
| `STORE_Mgr` | `STORE_Mgr_Real` | 子开关 | 展开/收起 GROUP_STORE_FUNC |
| `STORE_GUNSHOP` | `STORE_GUNSHOP_Real` | 叶子 | 打开军火商 UI |
| `STORE_GYM` | `STORE_GYM_Real` | 叶子 | 打开健身房 UI |
| `STORE_INFO` | `STORE_INFO_Real` | 叶子 | 打开信息中心 UI |
| `STORE_MEDIUM` | `STORE_MEDIUM_Real` | 叶子 | 打开医疗中心 UI |
| `STORE_STOCK` | `STORE_STOCK_Real` | 叶子 | 打开仓库（背包面板） |

### 热更新测试流程

1. 修改某个 `XXX_Real` 函数里的代码
2. 热更新（Ctrl+Shift+R 或编辑器热重载）
3. 直接点击对应按钮
4. 查看输出是否为修改后的新代码
