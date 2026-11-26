# 工具库

> 无状态工具集合：`UGCMathUtility`（数学/向量/旋转/颜色）、`UGCObjectUtility`（UObject 与资源）、`UGCActorComponentUtility`（Actor/组件）、`UGCTimerUtility`（计时器）、`UGCAsyncUtility`（PromiseFuture 异步）、`UGCTweenSystem`（补间）、`UGCStringTextUtility`（文本）、`UGCDelegateUtility`（委托）。

## 何时读

- 需要做向量运算、旋转、插值、随机、范围/盒体判定或颜色转换。
- 需要按路径加载类/对象/软引用，判断对象有效性或释放 Lua 引用。
- 需要在运行时生成 Actor、增删组件、附着、设置 Transform 或 Tick。
- 需要延迟、循环、按帧计时，且要能按名字取消。
- 需要等待资源加载、等待条件成立或并行等待多个异步任务。
- 需要 Tween 移动/旋转/变色，或做字符串处理和自定义事件委托。

## API 一览

| System | 文件 | 状态 | 关键函数 | 生效范围 |
|---|---|---|---|---|
| UGCMathUtility | UGCAPI/UGCMathUtility.lua | 规范（124） | MakeVector / BreakVector / AddVector / Normal / VLerp / VInterpTo / MakeRotator / FindLookAtRotation / Clamp / RandomFloatInRange / HexToRGB | 未标注（纯计算） |
| UGCObjectUtility | UGCAPI/UGCObjectUtility.lua | 规范 31 / 废弃 1 | LoadClass / AsyncLoadClass / LoadObject / AsyncLoadObject / AsyncLoadObjects / MakeSoftObjectPath / IsObjectValid / IsA / MakeWeakObjectPtr / RemoveReferencedObject | 服务器&客户端（个别未标） |
| UGCActorComponentUtility | UGCAPI/UGCActorComponentUtility.lua | 规范（47） | SpawnActor / DestroyActor / GetAllActorsOfClass / GetComponentsByClass / CreateAndRegisterComponent / DestroyComponent / AttachToActor / SetActorTransform / SetActorTickEnabled / GetActorBounds | 读操作双端；写/创建/附着为服务器 |
| UGCTimerUtility | UGCAPI/UGCTimerUtility.lua | 规范（6） | CreateLuaTimer / RemoveLuaTimer / RemoveLuaTimerByName / IsLuaTimerExistByName / CreateUETimer / RemoveUETimer | 服务器&客户端 |
| UGCAsyncUtility | UGCAPI/UGCAsyncUtility.lua | 规范（21） | AsyncDefine / AsyncRun / Await / AwaitSafe / AsyncSleep / AwaitAll / AwaitAllSettled / AwaitAny / WaitFor / WaitForSafe / AsyncFromEvent / AsyncFromCallback | 未标注 |
| UGCTweenSystem | UGCAPI/UGCTweenSystem.lua | 规范（16） | MakeConfig / TweenActorLocation / TweenActorRotation / TweenFloatValue / TweenVectorValue / TweenColorValue / ConfigureTween / ChainTween / PauseTween / KillTween | 服务器&客户端 |
| UGCStringTextUtility | UGCAPI/UGCStringTextUtility.lua | 规范（14） | SplitToArray / JoinArrayIntoString / StartsWith / EndWith / TrimStartOrEnd / LeftChop / RightPad / ComposedOfDigits / LogTree | 未标注 |
| UGCDelegateUtility | UGCAPI/UGCDelegateUtility.lua | 规范（10） | CreateCommonDelegate / CreateLuaDelegate / CreateUEDelegate / DestroyUEDelegate / CopyLuaDelegate | 未标注 |

## 核心概念

### 数学

按用途分组：三角函数（`Sin`/`DegSin`）、随机（`RandomFloat`/`RandomIntegerInRange`/`RandomBoolWithWeight`）、标量（`Lerp`/`Clamp`/`MapRangeClamped`/`FInterpTo`）、向量（`MakeVector`/`Normal`/`DotVector`/`RotateAngleAxis`/`ProjectVectorOnToPlane`）、旋转（`MakeRotator`/`FindLookAtRotation`/`MakeRotFromX`/`ComposeRotators`）、几何（`FindClosestPointOnSegment`/`IsPointInBox`/`MakeBox`）、颜色（`HSVToRGB`/`HexToRGB`/`RGBToHex`）、日期（`Now`/`UtcNow`/`DaysInMonth`）。

### 对象与资源

| 需求 | 接口 |
|---|---|
| 短名找类 / 完整路径加载类 | `FindClass` / `LoadClass`、异步 `AsyncLoadClass` |
| 路径加载对象 | `LoadObject`、`AsyncLoadObject`、批量 `AsyncLoadObjects` |
| 软引用 | `MakeSoftObjectPath` / `GetPathBySoftObjectPath` / `LoadObjectBySoftPath` |
| 身份与类型 | `GetObjectClass` / `GetObjectName` / `GetObjectPathName` / `IsA` / `ClassIsChildOf` |
| 生命周期 | `IsObjectValid` / `MarkAsGarbage` / `RemoveReferencedObject` |
| 弱引用 | `MakeWeakObjectPtr` / `GetObjectFromWeakObjectPtr` / `IsWeakObjectPtrValid` |

`FindObject` 会遍历所有包，性能差且冲突时只返回其中一个；优先 `LoadObject`。

### Actor 与组件

读接口双端可用：`GetAllActorsOfClass`、`GetAllActorsWithTag`、`GetComponentsByClass`、`GetActorTransform`、`GetActorLocation`、`HasAuthority`、`GetActorBounds`。写接口为服务器：`SpawnActor`、`DestroyActor`、`SetActorTransform`/`SetActorLocation`/`SetActorRotation`/`SetActorScale`、`AttachToActor`/`AttachToComponent`、`CreateAndRegisterComponent`/`DestroyComponent`、`SetActorTickEnabled`。组件激活状态用 `ActivateComponent`/`DeactivateComponent`/`IsComponentActive`，可见性用 `SetComponentVisible`/`IsComponentVisible`。

### 计时器

`CreateLuaTimer(TimeOffset, Callback, bLoop, TimerName, InitDelay, bLog, bCoroutine)` 的时间语义：

| TimeOffset | 行为 |
|---|---|
| `> 0` | 秒级间隔 |
| `== 0` | 每次 tick 执行 |
| `< 0` | 间隔 N 帧后首次执行（N = 绝对值） |
| 配合 `InitDelay` | `InitDelay ~= nil` 时首次在 InitDelay 秒后；`InitDelay == 0` 立即执行第一次 |

传 `TimerName` 后可用 `RemoveLuaTimerByName` / `IsLuaTimerExistByName`；`CreateUETimer` 返回 `FTimerHandle` 与单播委托，需用 `RemoveUETimer` 移除。

### 异步

`UGCAsyncUtility` 基于 `UGCPromiseFuture`：

| 接口 | 用途 |
|---|---|
| `AsyncDefine(Fn)` / `AsyncRun(PF, Opts)` | 定义 async 函数并启动未驱动的 PF；`Opts = { Watched, Interval, Timeout }` |
| `Await` / `AwaitSafe` | 等待单个 PF；Safe 版返回 `(Ok, ...)` |
| `AwaitAll` / `AwaitAllSettled` / `AwaitAny` | 全部等待 / 全部沉降不抛错 / 任一完成 |
| `AsyncSleep` / `WaitFor` / `WaitForSafe` | 等待秒数 / 单点超时 |
| `AsyncFromEvent` / `AsyncFromCallback` | 把委托或回调风格接口转成未驱动 PF |

取消与超时的错误值来自 `UGCAsyncErrorType.Cancelled` / `UGCAsyncErrorType.Timeout`。`WaitFor` 精度受外层 `AutoResume` 的 `Interval` 限制，需要精确计时时把 `Opts.Interval` 设为 0。

### 补间与委托

`UGCTweenSystem.MakeConfig(Delay, RepeatCount, bYoyo, RepeatDelay)` 生成配置；`Tween*Value` 每帧通过 `function(Obj, Value)` 回调返回当前值；`ChainTween` 串联动画，`PauseTween`/`ResumeTween`/`KillTween` 控制，`IsTweenValid` 判活，`BindCompletedDelegate` 完成后回调，`ReleaseTweenDelegates` 释放句柄关联的 Delegate。

`UGCDelegateUtility.CreateCommonDelegate(Type)` 的 `EUGCCommonDelegateType`：`Normal`（普通多次广播）、`Sticky`（新订阅者收到上一次广播）、`Latched`（只广播一次）。委托支持 `Add`/`Remove`/`RemoveAll`/`Broadcast`，可用 `ToUEDelegate` 转成 UE 单播委托。

## 典型用法

### 1. 数学：输入方向合成

参考 `../../../UGCProjects/Template_PlaygroundHub/Script/Blueprint/Prefabs/Character/CharacterControlPreset/testHengAction.lua`：

```lua
local ForwardInput = UGCMathUtility.MultiplyVector(self.ProjectForwardDir, RawInput.Y)
ForwardInput = UGCMathUtility.Normal(ForwardInput)
local RightInput = UGCMathUtility.MultiplyVector(self.ProjectRightDir, -RawInput.X)
local Result = UGCMathUtility.Normal(UGCMathUtility.AddVector(ForwardInput, RightInput))
local TargetRotation = UGCMathUtility.MakeRotFromX(Result)
```

### 2. 对象：软路径加载

参考 `../../../UGCProjects/Template_RogueShooting/ExtendResource/HeroSelect/OfficialPackage/Script/Common/Common.lua`：

```lua
local SoftPath = UGCObjectUtility.MakeSoftObjectPath(SourcePath)
UGCObjectUtility.AsyncLoadObjectBySoftPath(SoftPath, function(Object)
    OnLoaded(Object)
end)
```

### 3. 计时器

参考 `../../../UGCProjects/Template_RogueShooting/ExtendResource/HeroSelect/OfficialPackage/Script/HeroSelection/HeroSelectionManagerImpl.lua`：

```lua
self.TimerHandle_CheckTouchMove = UGCTimerUtility.CreateLuaTimer(
    0.02, function() self:CheckTouchMove() end, true, "CheckTouchMove")
UGCTimerUtility.RemoveLuaTimer(self.TimerHandle_CheckTouchMove)
```

### 4. Tween 数值动画

参考 `../../../UGCProjects/Template_PlaygroundHub/Script/Blueprint/UMG/TweenMove.lua`：

```lua
local Config = UGCTweenSystem.MakeConfig(0, -1, false, 0)
self.TweenHandler = UGCTweenSystem.TweenVectorValue(
    StartLocation, EndLocation, 1.0, self.TweenType,
    function(Obj, Value)
        local Slot = UGCWidgetManagerSystem.SlotAsCanvasSlot(self.TweenImage)
        Slot:SetPosition(KismetMathLibrary.MakeVector2D(Value.X, 0))
    end, Config)
```

### 5. 委托

参考 `../../../UGCProjects/Template_TopDownSurvivor/Script/Blueprint/Interactable/BP_Coin.lua`：用 `UGCDelegateUtility.CreateUEDelegate(self)` 生成委托后传给引擎接口。

### 6. Actor 与组件

参考 `../../../UGCProjects/Template_RogueShooting/Script/Blueprint/Affix/EquipmentAffixManager.lua`（`HasAuthority` 分支）与 `../../../UGCProjects/Template_RogueShooting/Script/Blueprint/Backpack/BP_UGCBackpack.lua`（`GetOwner` 取所属 Actor）。

## 约束与坑

- `UGCMathUtility.FClamp` 已废弃，改用 `Clamp`。
- `UGCObjectUtility.GetAllActorsOfClass` 已废弃，改用 `UGCActorComponentUtility.GetAllActorsOfClass`。
- `UGCActorComponentUtility` 的写接口标注为服务器；客户端分支调用前先 `HasAuthority`，或把逻辑放在服务器侧。
- `SpawnActor` 的 `Scale3D` 注释默认值是 `Vector(0,0,0)`，实际应传 `(1,1,1)` 保持原始比例。
- `CreateLuaTimer` 的 `TimeOffset` 为 0 时等于每帧执行；负值是“帧”不是“秒”。命名计时器便于批量取消。
- `UGCAsyncUtility` 的 PF 未驱动不会自动推进；必须处于 Async 上下文，或用 `AsyncRun` 启动。`Await` 会抛错，不处理异常时用 `AwaitSafe`/`WaitForSafe`。
- Tween 句柄需要保存；`KillTween` 后句柄失效。回调里持有 Lua 闭包时，结束时用 `ReleaseTweenDelegates` 释放引用。
- `UGCStringTextUtility`、`UGCAsyncUtility` 在 `UGCProjects` 模板中未被直接调用；使用前先确认目标工程的运行环境。
- 存根只有签名，`FindObject` 的冲突返回与 `AsyncLoadObjects` 的失败占位（对应项为 nil）以注释为准。

## 相关

- [api-index.md](api-index.md)：全系统速查。
- [ui.md](ui.md)：控件操作与 Tween 的 UI 侧用法。
- [misc.md](misc.md)：枪械、武器、实体查询。
- `../Source/Lua/ugc/UGCAPI/UGCMathUtility.lua`、`UGCObjectUtility.lua`、`UGCActorComponentUtility.lua`、`UGCTimerUtility.lua`、`UGCAsyncUtility.lua`、`UGCTweenSystem.lua`
- `../Source/Lua/common/PromiseFuture.lua`、`../Source/Lua/common/Delegate.lua`
