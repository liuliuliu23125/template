# 安卓 AGENTS

编辑器同版本的 Android 运行包（只读）。

## 内容

- `5826566_20261102101152_CG_Android_ETC2_1.39.13.16220_Shipping_CE_arm64_armv7.unsigned.shell-signed.apk`
  - 约 2.0GB
  - 版本与 `../version.txt`（`1.39.13.16220`）一致
  - 纹理格式 ETC2，架构 arm64 + armv7

## 用途

- 在 Android 真机/模拟器上验证玩法包。
- 不是编辑器的一部分，不参与 Windows 编辑器启动。

## 约束

- 只读；不要解包修改后重签用于发布。
- 玩法工程导出/上传 Android 包由编辑器完成，产物不落在这里。
- 需要确认目标平台时看工程 `.ugcproj` 的 `TargetPlatform`（常见含 `Android_ETC2`）。
