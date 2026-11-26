# 载具编辑器

> 载具模板/蓝图、属性、座位、武器、刷怪器与常见问题。
> 官方来源：载具编辑器、载具常见问题；运行时 API 见 `vehicle.md`。

## 何时读

- 要用载具编辑器创建/改载具。
- 要配座位、车载武器、载具属性。
- 要排查载具不刷新、UI 异常、特殊载具提示。
- 要区分编辑器配置与 `UGCVehicleSystem` 运行时逻辑。

## 编辑器

- 载具编辑器：从模板创建载具蓝图，配属性、座位、武器、外观。
- 载具蓝图通常放工程 `Asset/Blueprint/...`；具体路径以编辑器生成位置为准。
- 座位与武器编号：V1 从 1 开始，V2 从 0 开始；编辑器配置与运行时接口要对应。
- 载具属性（血量/油量/轮胎）可在编辑器配默认值，运行时用 `UGCVehicleCommonSystem` 改。
- 特殊载具的 UI/提示可通过继承对应的 UI 蓝图并替换 `ExtraUIPath` 实现。

## 刷怪器

- 载具刷新器用于固定点/波次刷新。
- 动态生成用 `UGCVehicleSystem.SpawnVehicleNew` 或 V2 `SpawnVehicle`。
- 生成后不要立刻改位置/传送，等落地停稳；精确落点在生成时给。

## 常见问题

| 现象 | 排查 |
|---|---|
| 莲花载具提示无法关闭 | 继承 `CG032_Nezha_Main`，隐藏 `Border_Tips`，再把载具 `ExtraUIPath` 指到新 UI |
| 载具生成后位置异常 | 生成后立即传送/改位置；等停稳或直接按目标点生成 |
| 座位进错/返回 nil | V1/V2 座位号基数不同；确认 `SeatIndex` |
| 载具武器无法开火 | 仅驾驶位、仅客户端；确认座位配置了武器 |
| 载具不掉血/不爆炸 | 血量/免伤配置；爆炸无 UGCAPI 封装，见 `vehicle.md` 内层说明 |

## Agent 规则

1. 先判断是编辑器配置还是运行时 API。
2. 生成载具优先 `SpawnVehicleNew`/V2；不要用已废弃的 `SpawnVehicle`。
3. 座位号 V1 1 基、V2 0 基；不要混用。
4. 生成后不要立刻传送。
5. 特殊 UI 用继承 + `ExtraUIPath`，不要改官方资产。
6. 载具性能与网络同步按 `performance.md` 配频率/裁剪。

## 本地参考

- API/运行时：`vehicle.md`
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=0b5iBLe3>（载具编辑器）
- 官方：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=149dD2-5>（载具常见问题）
