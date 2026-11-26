# 基础功能

> 日志、屏幕调试绘制、声音、相机、输入，以及 `UGCGlobal` 提供的容器/委托/转换辅助。主要系统：`UGCGlobal`、`UGCDebugSystem`、`UGCSoundMangerSystem`、`UGCCameraManagerSystem`、`UGCInputSystem`。

## 何时读

- 要打结构化日志、格式化日志、按级别/分类输出，或把 UE 容器转成 Lua table。
- 要在屏幕上打印调试信息、画线/球/盒/射线/碰撞盒。
- 要播 2D/3D/依附 Actor/循环/区间音效，或按音量音高播放。
- 要限制载具内第一人称视角，或给玩家挂自定义相机。
- 要按 InputTag 绑定/解绑/注入输入，并控制输入消耗。
- 要使用 `ULuaArrayHelper` / `ULuaMapHelper` / 委托等 Lua 侧基础类型。

## API 一览

| System | 文件 | 状态 | 关键函数 | 生效范围 |
|---|---|---|---|---|
| UGCGlobal | UGCAPI/UGCGlobal.lua | 规范 | `ugcprint` / `ugcprint_format` / `ugctagprint` / `totable` / `ULuaArrayHelper` / `ULuaMapHelper` | 存根未逐项标注，工程双端均有使用 |
| UGCDebugSystem | UGCAPI/UGCDebugSystem.lua | 规范 | `PrintToScreen` / `DrawDebugLine` / `DrawDebugString` / `FlushDebugLines` | 客户端 |
| UGCSoundMangerSystem | UGCAPI/UGCSoundMangerSystem.lua | 规范 | `PlaySound2D` / `PlaySoundAtLocation` / `PlaySoundAttachActor` / `StopSoundByID` | 客户端 |
| UGCCameraManagerSystem | UGCAPI/UGCCameraManagerSystem.lua | 规范 | `GetInVehicleFPPViewPitchLimitMin` / `SetInVehicleFPPViewYawLimit` | 客户端 |
| UGCInputSystem | UGCAPI/UGCInputSystem.lua | 规范 | `BindInputMapping` / `RemoveBinding` / `InjectInputMapping` | 客户端 |

> 文件名是 `UGCSoundMangerSystem.lua`（Manger），类名是 `UGCSoundManagerSystem`（Manager）；搜文件用前者，调接口用后者。

## 核心概念

### 日志

| 函数 | 用途 | 注意 |
|---|---|---|
| `ugcprint(Log)` | 单串日志 | `UGCGlobal.lua` 存根为一个参数；`common/ugcprint.lua` 另给出 `(Log, Category)` 形式 |
| `ugcprint_withlevel(Log, LogLevel)` | 指定 `ELogLevel` | Log / Warning / Error |
| `ugcprint_with_category_and_level(Log, Category, LogLevel)` | 分类 + 级别 | 仅 `common/ugcprint.lua` 声明 |
| `ugcprint_format(FormatString, ...)` | `string.format` 风格 | 支持 `%s` / `%d` / `%f` |
| `ugcprint_concat(...)` | 多参数 `ExportText` 拼接 | 末参可传 `{string_seperator="..."}` 自定义分隔符 |
| `ugctagprint(FormatString, ...)` | XML 标签占位符 | 用 `<TagType/>`，不是 `%s`；标签类型需已注册 |
| `log_tree(Name, Table)` | Dev 环境打印 table | 两个参数：名称、表 |
| `ugc_profiling_call(StatName, FunctionOrDisplay, ...)` | 性能打点 | 第二参可传 bool 控制展示，或传函数/路径 |
| `TagLogFormatPrint(...)` / `TagLogRawPrint(...)` | 标签日志 | 在 `common/taglog.lua`；带参格式串必须含 `<Any/>` 等占位符，否则拒绝输出；纯字符串可直接输出 |

日志会进 `Saved/Logs/ShadowTrackerExtra.log`；工程日志在 `Saved/Logs/<工程名>/`。

### 容器、转换与委托

- `ULuaArrayHelper`：`Add` / `AddUnique` / `Push` / `Insert` / `Remove` / `RemoveAt` / `Pop` / `Get` / `Set` / `Find` / `Contains` / `Empty` / `Reset` / `Num`。
- `ULuaMapHelper`：`Add` / `Remove` / `Get` / `Set` / `Find` / `Empty` / `Reset` / `Num`。
- `ULuaSetHelper`：`Add` / `Remove` / `RemoveAt` / `Get` / `Set` / `Find` / `Contains` / `IsValidIndex` / `Empty` / `Reset` / `Num`。
- 转换：`totable(userdata)` 把 UE 容器/结构体转 Lua table；`isemptytable(t)`、`issimpletable(t, bAllowTableAsValue, bAllowUObjectValue)` 做判定。
- 委托：`ULuaMulticastDelegate` 用 `Add` / `AddInstance` / `Remove` / `RemoveAll` / `Clear` / `Broadcast` / `BroadcastAll`；`ULuaSingleDelegate` 用 `Bind` / `UnBind` / `Execute`，后绑定覆盖先绑定。Lua 侧还可 `require("common.Delegate")`，使用 `Add` / `Remove` / `RemoveAll` / `Broadcast`。

`UGCGlobal` 还声明 `UGCAsyncOptions` / `UGCAsyncFunction`；异步执行入口在 `UGCAsyncUtility.AsyncRun`，类型基础在 `common/Async.lua` 与 `common/PromiseFuture.lua`，见 `toolbox.md`。

### 调试绘制

`UGCDebugSystem` 全部为客户端接口：`PrintToScreen` 在左上角逐行打印；`DrawDebugLine`、`DrawDebugPoint`、`DrawDebugArrow`、`DrawDebugCircle`、`DrawDebugBox`、`DrawDebugSphere`、`DrawDebugCylinder`、`DrawDebugCapsule`、`DrawDebugString` 画基础图形；`DrawDebugActorName` / `DrawDebugActorMoveTrack` / `DrawDebugDistance` / `DrawDebugTargetAimedAt` 画 Actor 信息；`DrawDebugLineTraceSingle` / `DrawDebugLineTraceMulti` 与 Sphere/Box/Capsule 的 Trace 系列可视化射线与命中；`DrawDebugActorCollision` / `DrawDebugActorBounds` 画碰撞/包围盒。颜色为 `FLinearColor`，默认红色；多数绘制 `Duration=0` 表示每帧调用保持一帧（`DrawDebugActorMoveTrack` 为持续保留）。清理用 `FlushOnScreenDebugMessages`（屏幕文本）、`FlushDebugStrings`（场景文本）、`FlushDebugLines`（场景图形）。

### 声音

`UGCSoundManagerSystem` 仅客户端，`AKEvent` 通过 `UE.LoadObject(SoundPath)` 取得。`PlaySound2D` / `PlaySoundAtLocation` / `PlaySoundAttachActor` 返回音效 ID；`PlaySoundWithVolumePitch` 的 Volume 范围 `[-12, 12]`、Pitch 范围 `[-2400, 2400]`，传范围外的值表示不调整；另有 `PlaySoundWithRange`、`PlaySoundWithLoop`、`PlaySoundWith2D`。停止用 `StopSoundByID` / `StopSoundByActor` / `StopAllSound`。`SetSoundListener` 在 `PlayerPawn` 与 `Camera` 间切换收音监听器。

### 相机与输入

- 相机：`UGCCameraManagerSystem` 只负责载具内第一人称 Pitch/Yaw 限制和狭窄座位手雷投掷 Yaw 限制。自定义相机用 `UGCGameplayTaskSystem.Player.AddCustomCameraData.NewTask` / `SetEyeRotationMode.NewTask`（客户端，见 `gameplay-rules.md`）。
- 输入：`BindInputMapping(BindingOwner, InputTag, TriggerEvent, CallbackFunction)` 返回绑定索引，`-1`/`nil` 表示失败；回调参数为 `(InputValue, ElapsedTime, TriggeredTime, InputTag)`。`RemoveBindingToObject` 解绑某对象的全部输入，`RemoveBinding` 按索引解绑；`SetBindingConsumeInput` 控制是否吞掉后续绑定；`InjectInputMapping` 手动触发；`GetInputValue` 取当前值。仅客户端。

## 典型用法

1. **格式化日志与 table 打印**：`ugcprint_format` 写业务日志，`log_tree` 配合 `totable` 查看结算/装备数据。参考 `../../../UGCProjects/Template_RogueShooting/Script/Blueprint/Arts_UI/Game/UIBP/Depot/UGC_Equip_Tips_UIBP.lua`、`../../../UGCProjects/Template_RogueShooting/Script/Blueprint/Backpack/BP_UGCBackpack.lua`。

```lua
ugcprint_format("[Spawn] player=%s count=%d", tostring(PlayerKey), Count)
log_tree("SettlementData", totable(Data))
```

2. **调试射线**：Withdraw 的房顶可见性工具用 `DrawDebugLineTraceSingle` 画出检测射线。参考 `../../../UGCProjects/Withdraw/Script/Tool/Tool_RoofVisibility.lua`。

3. **音效播放/停止**：Withdraw 序章用 `pcall` 包住 `PlaySound2D`，保存返回 ID 后用 `StopSoundByID` 停止。参考 `../../../UGCProjects/Withdraw/Script/UI/Prologue/Prologue.lua`；RogueShooting 天赋树 UI 直接播按钮音效，见 `../../../UGCProjects/Template_RogueShooting/Script/Blueprint/Arts_UI/Lobby/UIBP/TalentTree/TalentTree_Main_UIBP.lua`。

```lua
local id = UGCSoundManagerSystem.PlaySound2D(self.MusicEvent)
UGCSoundManagerSystem.StopSoundByID(id)
```

4. **输入绑定**：Withdraw 客户端先取 `Input.Action.Interact` 的 Tag，再绑定 `ETriggerEvent.Triggered`，结束时按对象解绑。参考 `../../../UGCProjects/Withdraw/Script/Blueprint/UGCPlayerController.lua`。

```lua
local tag = UGCGameplayTagSystem.RequestGameplayTag("Input.Action.Interact")
local handle = UGCInputSystem.BindInputMapping(self, tag, ETriggerEvent.Triggered, self.OnInteract)
UGCInputSystem.RemoveBindingToObject(self)
```

5. **自定义相机**：PlaygroundHub 的 Buff 用 `AddCustomCameraData.NewTask` 设置偏移/FOV/弹簧臂，用 `ReplaceAnim.NewTask` 换动画。参考 `../../../UGCProjects/Template_PlaygroundHub/Script/Blueprint/Prefabs/Buffs/testChicken2.lua`。

6. **容器转换**：RogueShooting 属性面板把 `AttrModifyItemSimpleList` 等 UE 容器 `totable` 后按 Lua 表遍历。参考 `../../../UGCProjects/Template_RogueShooting/Script/Blueprint/Arts_UI/Game/UIBP/Depot/Depot_Attribute_Group_UIBP.lua`。

## 约束与坑

- `UGCDebugSystem`、`UGCSoundManagerSystem`、`UGCCameraManagerSystem`、`UGCInputSystem` 全部仅客户端；服务器调用不会生效。
- `ugctagprint` / `TagLogFormatPrint` 不是 `string.format`：占位符必须是已注册的 `<Tag/>`，用 `%s` 会被拒绝或无法解析。普通格式化统一用 `ugcprint_format`。
- `ugcprint_concat` 的字段名按存根为 `string_seperator`（拼写如此），不是 `separator`。
- `UGCSoundManagerSystem` 的 Volume/Pitch 只有落在规定范围才调整；传范围外值表示保持原值。`PlaySoundWithRange` 的存根注释列出 `ID` 参数，但函数签名未包含该参数且无返回值，实际以签名文件为准。
- 相机管理器不是通用相机 API：它只改载具 FPP 视角限制；自由相机/相机参数用 `UGCGameplayTaskSystem.Player` 下的任务。
- 输入回调只在客户端；Tag 可能取到 nil（Withdraw 在绑定时判空），绑定失败返回 `-1` 或 nil，必须检查。对象销毁/结束时用 `RemoveBindingToObject` 清理。
- `ULuaArrayHelper` / `ULuaMapHelper` / `ULuaSetHelper` 在存根中只有方法，没有构造入口；它们通常作为 UE 容器字段的 Lua 视图使用（工程里以 `ULuaArrayHelper<T>` 标注字段类型），不要假设有 `New`。
- `UGCGlobal` 的函数多数未写「生效范围」，不能据此推断仅服务器；日志/容器在双端工程代码中都有使用。
- `log_tree` 面向 Dev 环境，不要用它替代正式埋点；玩法数据用 `UGCGameSystem.SendTLog` / `SendGameTlog`（见 `gameplay-rules.md`）。

## 相关

- 分类总表：`api-index.md`
- 玩法流程、TLog、GameplayTag：`gameplay-rules.md`
- 角色/控制器/相机相关能力：`character.md`
- 异步工具、Timer、Tween、数学/对象工具：`toolbox.md`
- UI 与控件：`ui.md`
- 其他系统：`misc.md`
- API 总入口：`../AGENTS.md`
- 工程指南：`../../../UGCProjects/Docs/project-guide.md`
