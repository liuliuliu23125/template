# 性能预算与优化

> 目标：让玩法在中低端手机上稳定运行。先看预算，再按 CPU / GPU / 内存 / 网络四条线优化。
> 官方来源：性能优化总览、性能检测工具、性能报告、怪物网络优化、网络裁剪、流量优化、防外挂自检。

## 何时读

- 新增 Tick、批量 Actor、大量怪物、复杂 UI、粒子或大场景。
- PIE 帧率下降、手机发热/掉帧、内存持续增长。
- 上线前自查，或需要判断“这个玩法能不能在低端机跑”。
- 设计网络同步、RPC 频率、怪物同步距离。

## 预算参考

| 指标 | 建议 |
|---|---|
| FPS | 60 以上为流畅；持续低于 30 需要重点排查 |
| DrawCall | 100–200；超过 200 优先合批/剔除 |
| 三角形 | 20 万面以下；超出减面或加 LOD |
| 内存 | 关注峰值与增长趋势；中低端机更敏感 |
| 网络 | 不用可靠广播；高频表现走不可靠 RPC；状态走复制 |

> 这些是官方文档中的经验值，不是硬性引擎限制；以目标机型和实测为准。

## 四条优化线

### CPU

- 避免在 `Tick` 里做复杂逻辑、遍历大量 Actor、字符串拼接、频繁日志。
- 用事件/定时器替代每帧轮询。
- 频繁查询的配表建 Lua table 索引，避免每次线性扫描。
- 资源加载用异步，避免同步 `UE.LoadObject` 触发 Flush 卡顿。
- 高频创建的对象（抛体、特效、UI item）用对象池复用，降低 GC 压力。
- 缓存频繁访问的 C++/蓝图属性；每次访问都有查询开销。

### GPU

- 合理配置 LOD；LOD 切换不要过于突兀。
- 小物件开启渲染剔除：`Override Culling Screen` + `Culling Screen Size`，屏幕占比低于阈值不渲染。
- 合批：相近位置、相近尺寸的物件合批；过远/尺寸差异过大反而影响剔除。
- 用热力图看 Shader Complexity 与 Quad Overdraw；大面积红色/白色说明渲染成本过高。
- 控制材质实例数量与复杂材质节点。

### 内存

- 及时释放不用的对象引用；Lua 缓存的 UObject 销毁前置 nil。
- 控制贴图分辨率、模型面数、音视频码率。
- 高频对象池化，避免频繁分配/释放造成内存碎片。
- 用 `.memreport` 看 StaticMesh / SkeletalMesh 占用，定位大资源。
- 资源总量过大也会导致 Cook OOM 和上传失败。

### 网络

- 状态用属性复制，事件用 RPC；不要用 RPC 传关键状态。
- 客户端表现类 RPC（音效、动作、特效）优先 `Unreliable`。
- 高频 RPC 用短函数名；广播参数传 ID，不传完整资源路径。
- 设置 `NetCullDistanceSquared`（厘米的平方）限制同步距离：
  - 50 米 = 25,000,000；100 米 = 100,000,000；150 米 = 225,000,000。
- 怪物按类型设置 `NetUpdateFrequency`：
  - Boss/高速近战 15–20 Hz；普通巡逻 5–10 Hz；站桩/低速 2–5 Hz；背景 NPC 1–2 Hz。
  - `MinNetUpdateFrequency` 默认 1 Hz，必须小于 `NetUpdateFrequency`。
- 怪物数量 ≥50 时，开启距离分档网络优化（按距离自动降频）。
- 大量同屏且不需要辨识度的角色可用同模优化：`Pawn:getAvatarComponent():InitDefaultAvatarByResID(...)`，但要在 Pawn 完全初始化后调用，复活后要重新调用。

## 性能检测工具

| 工具 | 用途 |
|---|---|
| 性能调试信息 | 实时看 FPS、内存、DrawCall、三角形 |
| 性能检测器 | 10 秒采样，预测低/中/高三档设备表现，0–100 分 |
| 热力图 | Shader Complexity、Quad Overdraw、组合模式 |
| UGC Profile | 记录每帧 CSV，路径 `ShadowTrackerExtra/Saved/Profiling/CSV` |
| 性能报告 | GM 面板「性能」页签记录 `.ue4stats`，用 LuaProfiler 打开 |
| 内存记录 | GM 面板输出 `.memreport`，看 StaticMesh / SkeletalMesh |
| 角色调试工具 | 技能/Buff/属性数值迭代 |

- 性能检测器评分：80–100 优秀、50–79 一般、0–49 较差。
- Profile CSV 重点列：`Update`（Tick 时间）、`COUNTS/Update`、`Create`（Spawn 时间）、`Audio`（同步加载）。
- 性能报告适合真机；PIE 的检测器只反映编辑器视口，不等于真机。

## 防外挂底线

- 不信任客户端上行 RPC 的参数：数量、ID、价格、结果都可能被篡改。
- 客户端上报“行为”，服务器校验后执行；不要让客户端上报“结果”。
- 购买/发货：DS 持有货币与条件，按 `WantNum` 重新计算，不按客户端传的 `ItemID/Num` 直接发。
- 随机/强化：随机在 DS 做，客户端只发起请求。
- 高频/关键逻辑：DS 校验 RPC 频率与合理性。

## Agent 规则

1. 新增 `Tick` 前先问：能否用事件/定时器替代。
2. 循环里不要 `SpawnActor`、`LoadObject`、字符串拼接、`ugcprint`。
3. 大量对象用池；大量同屏用同模/LOD/剔除。
4. 网络：状态复制、事件 RPC、表现 Unreliable、距离裁剪。
5. 资源：高频预加载，长尾异步加载；异步回调必须判空 + `UE.IsValid`。
6. 不在客户端做权威判定；所有奖励/伤害/购买由 DS 校验。
7. 上线前用性能检测器 + 真机 Profile + `.memreport` 各跑一遍。

## 本地参考

- 性能日志：`ShadowTrackerExtra/Saved/Profiling/`
- Lua 性能查看器：`Engine/Binaries/ThirdParty/LuaProfiler/Engine/Binaries/Win64/LuaProfiler.exe`
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=yO6_7pTj>（性能总览）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=dOPjZ08Z>（性能检测工具）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=xP_3G1A7>（性能报告与内存）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=hL5HJN26>（怪物网络优化）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=382E8NsD>（网络裁剪）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=7R-agZLS>（流量优化）
