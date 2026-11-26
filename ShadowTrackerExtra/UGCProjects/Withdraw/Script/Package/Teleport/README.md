# Teleport

管理地图内 GameTeleport 传送点、区域提示和玩家确认传送。
包外只依赖 Registry_Teleport；Query 负责只读范围与目标查询，
System 负责注册表、重叠成员、计时器、传送和网络/UI 写操作。

## 场景配置

- GameTeleport 继承 TeleportBase，使用父类 Sphere 的重叠事件。
- 在蓝图实例的 TeleportTarget 中指定目标 GameTeleport。
- 目标 Actor 的世界坐标就是落点，请放在角色可站立的位置。
- 源与目标可分别配置，实现单向或双向传送；到达目标后仍需再次点击确认。
- ID 在服务端 BeginPlay 自动分配，不需要增加蓝图 ID 变量或手动编号。
- UI 3007 对应 Asset/UI/Button/TeleportConfirm.TeleportConfirm_C。
  DT_UI_Config 中使用单例配置；缺少该行时已有 UI 加载器提供兜底。

## 接口与数据

- Register / Unregister：注册与销毁清理，由 Actor 生命周期调用。
- Enter / Exit：记录与移除区域内玩家，由 Actor 重叠事件调用。
- RefreshOccupants：定时清理死亡、换 Pawn、掉线或离开区域的记录。
- Confirm：服务端确认；PC 的 Server_ConfirmGameTeleport 仅转发。
- SetPrompt / ApplyResult：客户端 PC RPC 转发到包内 UI 系统。
- RequestConfirm：按钮提交源 ID 和本次进入凭据，不提交目标坐标。
- GetConfirmUIId / GetConfirmText：UI 使用的只读配置入口。

System_Teleport 私有注册表保存 ID → Actor。每个 Actor 的 playersInside
保存 PlayerKey → { pc, pawn, token, consumed }；PC 上不添加任何传送字段。
token 每次进入递增，成功提交后消费，拒绝重复确认与旧请求。
多个区域重叠时显示最后进入的点，离开后恢复仍在范围内的前一个点。
UI 关闭和确认结果均匹配源 ID/token，避免影响抵达后新打开的提示。

只有有成员的传送点运行清理计时器，空区域或 EndPlay 清理计时器。
Register 幂等；Package BeginPlay 不重置场景已登记的点。
全部数据为本局运行时状态，不声明 playerData/gameData，不进入存档。

## 配置与验证

配置位于 Script/Config/Package/Teleport/Config_Teleport.lua：
UI ID、按钮文字、清理间隔和失败提示。目标 Actor 仍通过场景蓝图配置。

本地回归：从项目根目录运行 lua54.exe Tests/GameTeleportTest.lua。
引擎内运行 Teleport AutoTest Suite。实机仍需验证 Sphere 碰撞、
UI 3007 的显示位置、客户端 RPC 和目标落点。
