# Shield

当前整套停用：`Enabled = false`。UI隐藏、特效清理、不吸收伤害、不恢复、GM护盾指令禁用。
改为 `Enabled = true` 可恢复；运行中的 PIE 热重载后也会清理旧状态，重新开启时存活玩家获得满盾。
启用时玩家本局护盾默认上限100，出生满盾，连续5秒未受有效伤害后每秒恢复20。
配置入口：`Script/Config/Package/Shield/Config_Shield.lua`。

- 唯一外部入口 `Registry_Shield`；当前值不进入 PlayerDataCore 存档。
- Pawn BeginPlay 初始化，Tick 服务端恢复，死亡停用，EndPlay 清理；重生使用新 Pawn 状态。
- 服务端全局伤害公式在所有既有倍率、PVE和收藏减伤完成后吸收护盾；返回值仅为生命溢出伤害。
- 正伤害无论是否穿盾都重置恢复等待；0、负数和非法数值不消耗护盾、不推迟恢复。
- `ShieldCurrent / ShieldMax / ShieldRecharging / ShieldHitSequence` 是 Pawn 蓝图复制字段。
- 客户端通过复制快照显示球形护盾、受击反馈，以及 ZJM 中的 `ShieldPanel / ShieldBar / ShieldValue / ShieldStatus / ShieldIcon`。
- 满盾吸收后的最终伤害0不能触发耐久参数的正数回退。装备耐久只扣溢出生命的部分。
- GM 指令：`cmd -s default -t server -Shield -Fill`、`-Shield -Clear`、`-Shield -Hit`。
- `Suite_Shield` 验证吸收、溢出、恢复时序、死亡清理和服务端权限。

常驻护盾使用 `Asset/Blueprint/Module/ShieldEffectActor`，各客户端按复制数值生成并附加到玩家根组件。
玩家存活且护盾大于0时每名玩家只保留一个实例，破盾/死亡/EndPlay隐藏并销毁，恢复后重新生成。
新进入视野也会根据当前值补建，实例意外失效时限频重建。Actor无碰撞，蓝图不启用复制。
配置的 EffectActorPath / EffectOffset / EffectRotation / EffectScale 控制资源和相对变换。
Actor沿用蓝图粒子组件的软模板和组件缩放；软粒子绑定模式下 Template 为空是正常的，应检查 SoftTemplate。
旧 ShieldAura 停用；UGCPlayerPawn 的 ShieldHitEffect 继续提供受击反馈，未修改引擎资源。
新增复制字段或更改蓝图后需要重新启动 PIE；纯 Lua 调整可使用 reloadlua。
