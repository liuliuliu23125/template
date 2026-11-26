# UI 界面

> 客户端 UI 分三层能力：`UGCUIManagerSystem` 管理界面注册、层级、互斥与状态机；`UGCWidgetUtility` 负责控件级创建与操作；`UGCWidgetManagerSystem` 暴露和平原生面板入口（56 个函数中 36 个已废弃）。MVVM 与 UMG 扩展控件位于框架层。

## 何时读

- 需要做一个全屏面板、弹窗或设置页，并管理打开/关闭/缓存。
- 需要运行时异步创建 UMG 控件并挂到 UISlot 或视口。
- 需要获取原生主 UI、射击面板、技能面板，或弹 Tips、头顶 UI。
- 正在迁移旧的 `UGCWidgetManagerSystem` 调用。
- 想用 MVVM 绑定属性、命令和列表。
- 需要使用 `NewButton`、`MaskBox`、`DynaCanvasPanel`、`UReuseListC` 等扩展控件。

## API 一览

| System | 文件 | 状态 | 关键函数 | 生效范围 |
|---|---|---|---|---|
| UGCUIManagerSystem | UGCAPI/UGCUIManagerSystem.lua | 规范（25） | RegisterUI / UnregisterUI / Open / Close / Toggle / Preload / PreloadAll / IsOpen / GetState / GetWidget / RegisterViewModel / GetViewModel | 客户端 |
| UGCWidgetUtility | UGCAPI/UGCWidgetUtility.lua | 规范（84） | CreateWidgetAsync / CreateWidget / DestroyWidget / AddToSlot / RemoveFromSlot / ShowWidget / HideWidget / AddToViewport / GetSubWidget / GetAllWidgetsOfClass / PlayWidgetAnimation | 客户端（个别函数未标） |
| UGCWidgetManagerSystem | UGCAPI/UGCWidgetManagerSystem.lua | 规范 20 / 废弃 36 | GetMainUI / GetMainControlUI / GetShootingUIPanel / GetSkillRootPanel / ShowTipsUI / ShowTipsUIByServer / AddObjectPositionUI / ChangeMap / SetVirtualJoystickVisibility | 客户端为主；Tips 与头顶 UI 有服务器侧 |
| UGCCommonUISystem | UGCAPI/UGCCommonUISystem.lua | 规范（2） | AddDragSuccess / RemoveDragSuccess | 客户端 |

## 核心概念

### 层级与状态

`UGCUIManagerSystem.lua` 用 `UI` 类声明四层，参数注解写作 `EUGCUILayer`：

| 值 | 语义 |
|---|---|
| `UI.Background` | 垫底层，位于 BattleHUD 之下 |
| `UI.Normal` | 常规全屏面板，盖住 BattleHUD |
| `UI.Popup` | 弹窗，盖住常规面板 |
| `UI.Top` | UGC 顶层，低于原生全局 Top（Tips/引导） |

`EUGCUIState` 由 `GetState` 返回：

| 状态 | 含义 |
|---|---|
| `Unloaded` | 未加载、实例已销毁，或 Key 未注册 |
| `Loading` | 等待 PlayerController、加载类或创建实例 |
| `Cached` | 实例已缓存但未打开（预加载或关闭后保留） |
| `Open` | 管理器已标记为打开 |

`UGCUIConfig` 字段：`WidgetClassPath`（必填）、`Layer`（默认 `Normal`）、`MutexGroups`、`bPreload`、`bDestroyOnClose`、`AnchorData`。同层后打开者 ZOrder 递增；同互斥组同时只允许一个打开。

### WidgetUtility 生命周期

`CreateWidgetAsync` / `CreateWidget` → `AddToSlot` 或 `AddToViewport` → `ShowWidget` / `HideWidget` / `SetWidgetVisible` → `RemoveFromSlot` / `RemoveFromViewport` → `DestroyWidget`。`AddToSlot` 的 SlotName 默认 `UI.UISlot.MainUISlot_Low`；`AddToViewport` 要求控件没有父容器。

### MVVM（RAF）

| 类型 | 文件 | 关键接口 |
|---|---|---|
| UGCView | `../Source/Lua/ugc/RAF/Framework/MVVM/UGCView.lua` | SetupViewModel / BindProperty / BindCommand / BindCollection / SetupBindings / CleanUp |
| UGCViewModel | `.../UGCViewModel.lua` | OnInitialize / CreateCommand / CreateCollection / AttachChild / Destroy |
| UGCItemView | `.../UGCItemView.lua` | SetupWithViewModel / OnSetup / BindProperty / BindCommand |
| UGCMVVMCollectionBinder | `.../CollectionBinder.lua` | OnBind / OnItemsAdded / OnItemInserted / OnItemsRemoved / OnItemReplaced / OnReset |
| UGCMVVMProperty | `.../MVVMProperty.lua` | Get / Set / SetDataSource / SetComputeFunc / AddListener |
| UGCMVVMCommand | `.../MVVMCommand.lua` | Execute / SetCanExecute / AddCanExecuteListener |

`EUGCViewBindType` 支持 `Text`、`Visibility`、`Enabled`、`Color`、`Image`、`Progress`、`CheckBox`、`Slider`、`Switcher`；`EUGCMVVMConverterType` 提供 `BoolToVisibility`、`BoolToHitTestInvisible`、`BoolToText`、`NumberToString`、`NumberToPercent` 等转换器。

### UMG 扩展控件（`Source/Client/UMG/`，37 个文件）

| 控件 | 用途 |
|---|---|
| `UNewButton` | 带 `IndexKey` 的按钮；`OnClickedWithIndex` / `OnHoveredWithIndex` / `OnUnhoveredWithIndex` 回调携带索引，支持点击音效 |
| `UMaskBox` | 单子控件遮罩与遮罩动画；可换材质、纹理、缩放/角度/锚点 |
| `UDynaCanvasPanel` | 按名字动态创建/替换/异步加载子控件，支持对象池与自动加载 |
| `UReuseListC` / `UReuseListDiff` / `UReusePageC` | 复用列表、差异刷新、分页列表 |
| `UImageEx` / `UImageHQ` | 扩展图片控件 |
| `UParallaxWidget` / `UPerspectiveWidget` / `UTransformWidget` | 视差、透视、变换容器 |
| `UIParticleEmitterHQ` | UI 粒子发射器 |
| `UCommonSkinRoot` | 通用皮肤根节点 |

HUD、小地图与主 UI 组件在 `../Source/UGCGame/HUD/`、`../Source/UGCGame/Minimap/`、`../Source/UGCGame/WidgetUI/`（如 `UDamageNumberWidget_UGC`、`AUGCMinimapManager`、`UWidgetMainUIManagerComponent`）。

## 典型用法

### 1. 注册并打开受管界面

```lua
UGCUIManagerSystem.RegisterUI("Shop", {
    WidgetClassPath = ShopClassPath,
    Layer = UI.Normal,
    MutexGroups = { "FullScreen" },
    bPreload = true,
})
UGCUIManagerSystem.Open("Shop", shopData)
```

异步等待用 `UGCAsyncUtility.Await(UGCUIManagerSystem.Open(...))`；互斥由 `MutexGroups` 自动处理，不要手写关闭逻辑。

### 2. 异步创建并挂到 UISlot

```lua
UGCWidgetUtility.CreateWidgetAsync(Path, function(Widget)
    UGCWidgetUtility.AddToSlot(Widget, nil, 10)
    UGCWidgetUtility.ShowWidget(Widget)
end)
```

参考 `../../../UGCProjects/Withdraw/Script/Core/UIManager/Mgr_UIManager.lua`（项目自建 UI 管理器：配置表 + 缓存 + 异步创建 + 槽位/视口两种挂载；其异步创建仍调用已废弃的 `UGCWidgetManagerSystem.CreateWidgetAsync`，新代码应改用 `UGCWidgetUtility` 同名接口）与 `../../../UGCProjects/Withdraw/Script/UI/Experience/ExpFloat.lua`（世界坐标转控件坐标、视口定位）。

### 3. 原生和平 UI

`GetMainUI()`、`GetMainControlUI()`、`GetShootingUIPanel()`、`GetSkillRootPanel()` 返回原生面板实例，可直接 `SetVisibility`。参考 `../../../UGCProjects/Template_ArmsTeamCompetition/Script/Blueprint/ArmsTeamDeathMatchGameState.lua`（获取主控制面板并隐藏主 UI）和 `../../../UGCProjects/Template_CTCompetition2/Script/Blueprint/UGCPlayerController.lua`（`ChangeMap` 替换小地图）。

### 4. MVVM 绑定

`UGCView:BindProperty(Widget, Prop, BindType, Converter)` 绑定属性；`BindCommand(Widget, EventDelegate, Handler)` 绑定命令；`BindCollection(ListWidget, Coll, ItemSetupFunc, BinderClass)` 绑定列表。参考 `../Source/Lua/ugc/RAF/Framework/MVVM/UGCView.lua`。

### 5. 项目实际路径

| 场景 | 文件 |
|---|---|
| 项目级 UI 总入口与打开/关闭/异步 | `../../../UGCProjects/Withdraw/Script/Core/UIManager/Global_UISystem.lua` |
| 控件类查询与背包 UI 扩展 | `../../../UGCProjects/Withdraw/Script/GamePartCustom/BackpackV2/BP_BackpackUIComponentV2_Custom.lua` |
| 复用列表条目 | `../../../UGCProjects/Template_ArmsTeamCompetition/Script/UMG/TMode/UIBP/ArmsRaceMode/TMode_ArmsRace_WeaponSlot_Item_UIBP.lua` |

## 约束与坑

- `UGCUIManagerSystem` 在全部 `UGCProjects` 中未被直接调用；`Withdraw` 自建了 `Global_UISystem`/`Mgr_UIManager`，其底层仍混用 `UGCWidgetManagerSystem` 与 `UGCWidgetUtility`。新代码可直接采用 `UGCUIManagerSystem`。
- `UGCWidgetManagerSystem` 的 36 个废弃项全部指向 `UGCWidgetUtility` 或 `UGCUtility + AddToSlot` 组合；模板中仍大量出现的是 `AddToSlot`、`CreateWidget`、`ShowTipsUI` 等。
- `UGCWidgetUtility` 大多数操作为客户端；服务器只能发起 `ShowTipsUIByServer`、`AddObjectPositionUI` 等少数接口。
- `Close` 默认只 Collapse 并保留缓存；需要销毁时传 `bDestroy = true` 或注册时设 `bDestroyOnClose`。`UnregisterUI` 才会移除配置与实例。
- `ShowWidget` 要求控件已挂载；`AddToViewport` 要求控件没有父容器，槽位中的控件需先 `RemoveFromSlot`。
- `GetState` 在等待层容器时可能仍是 `Cached`，不能据此判断没有 Open 任务；用 `IsOpen` / `GetWidget` 交叉判断。
- `UGCWidgetManagerSystem` 的 `GetAllWidgetsOfClass`、`ProjectWorldLocationToWidgetPosition` 等已废弃，分别换用 `UGCWidgetUtility` 同名/对应接口。
- MVVM 的 `GetViewModel(VMKey, View)` 必须传 `UGCView`（通常 `self`），传普通 table 返回 nil；RAF MVVM 在模板工程中未被直接使用，`Template_RogueShooting` 的 `HeroSelectionViewModel` 是工程内自建 MVVM。
- 存根中没有 `UGCViewModel` 创建 Property 的方法声明，属性定义流程需在工程内验证，不要照搬猜测写法。

## 相关

- [api-index.md](api-index.md)：全系统速查。
- [basic.md](basic.md)：`UGCGameSystem`、相机、输入。
- `../Source/Lua/ugc/UGCAPI/UGCUIManagerSystem.lua`、`../Source/Lua/ugc/UGCAPI/UGCWidgetUtility.lua`
- `../Source/Client/UMG/`、`../Source/Lua/ugc/RAF/Framework/MVVM/`
- `../../../UGCProjects/Docs/project-guide.md`
