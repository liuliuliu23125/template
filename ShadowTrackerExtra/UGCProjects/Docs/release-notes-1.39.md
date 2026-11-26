# 1.39 版本增量（编码相关）

> 只摘会影响 Lua/资产/工具链的变更，不抄完整 changelog。
> 本地事实：安装版本 `1.39.13.16220`（`version.txt`），Withdraw 工程版本 `1.39.13.16226`。
> 官方来源：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=oJFtAvFW>

## 使用时先注意

- 编辑器版本以 `version.txt` 为准；**不要默认 16223/16226 的新能力在 16220 编辑器里可用**。
- 升级编辑器后，先看对应小版本的 Release Notes，再改依赖新 API 的代码。
- 本页只记录“影响写法/资产/工具”的条目；bug 修复不展开。

## 16220：功能面

| 变更 | 对开发的影响 |
|---|---|
| AI 创作空间 | 接入图片/视频转动作/角色/音效生成；属于编辑器工具，不是 Lua API |
| 全服存档 | 所有 DS 局共享的全局数值，可做世界 BOSS；区别于按玩家的存档 |
| 源码管理 | 编辑器内接 Perforce/Git，可提交/更新/解决冲突/回溯 |
| 官方公告 | 编辑器内查看公告/版本消息 |
| 角色编辑器 | 创建角色预设、操作预设 |
| 锁定组件 | 自动锁定/瞄准敌人 |
| 相机碰撞检测 | 勾选参数开启，影响第三人称相机 |
| RAF 框架 | 可在内核创建 Module、实现 UI 与 MVVM |
| UGC RAG | 开放给第三方 Agent 使用（外部能力，不在本地 Lua 库） |
| AskQ MCP | 优化稳定性，支持 WorkBuddy/Cursor 等客户端 |
| 模型导入/资产导入 | 同名资产可选覆盖/跳过/重命名 |
| AI 检索 | 新增骨骼网格体、纹理筛选标签 |

## 16220：资源与系统

- 新增近战武器模板：巨斧、双刀、长枪、匕首。
- 新增近战技能、选取型/法术场/直接释放型技能模板（雷云、脉冲雷枪、超闪、蜘蛛诡雷等）。
- 新增 BOSS/精英/小怪模板（美杜莎头颅、血冕真祖、风暴城老将、亡灵骑士等）。
- 新增武装载具：武装皮卡、武装吉普；新增大战场资源（装甲车、防空车、C4、阔剑、无人机）。
- 物品编辑器：拾取物归属条件、武器装备剪影图标、药品/投掷物模板实例化。
- 背包：装备详情快捷按钮、满格卸包顺序、拾取物数量上限回收、UI 连点防护。
- 技能：Skill Task 事件、复活后自动恢复技能/Buff、近战/伤害/音效/冲量/屏幕特效 Task 更新。
- UI：UGC 快捷栏开关、自定义装备栏布局、隐藏攀爬/跳跃/探头/检视按钮、自定义击杀流水。
- 怪物：猎手、古堡领主、感染者骨骼部位映射。
- 其他：自定义拾取/丢弃音效、PCG 工具箱优化、导出表格结果弹窗。

## API 增量

- `EUGCReturnPlayerStatus`：回流玩家状态；用于判断回流玩家。
- 与本地对应：`UGCPlayerStateSystem.QueryPlayerReturnInfos` / `GetPlayerAccountInfo` 等回流相关接口；写逻辑前先在当前安装的 `UGCAPI` 里确认新枚举/函数是否存在。

## 16222–16226：编码相关摘要

| 版本 | 变更 |
|---|---|
| 16222 | AI 创作空间正式开放；新增飞天模型动画；wiki 增加“编辑器封禁策略” |
| 16222.1 | 资源选择卡死、AI 链接修复 |
| 16223 | 新增 wiki：规范接口环境错误、源码管理、Task 事件、角色预设；玩家存档 table 嵌套注意；输入映射支持技能映射；背包 UI 连点防护；PCG 植被编辑；前置检查更新 |
| 16226 | 新增 wiki：官方公告、锁定组件、玩法全服存档、玩法弱网测试；排行榜模板新增全服/好友页签；背包 UI 穿戴装备面板 |

## 与本地文档的对应

- 封禁策略 → `runtime-rules.md`
- 环境错误 → `debugging.md`
- 弱网/重连 → `network-replication.md`
- 角色预设 → `../../Content/LuaHelper/Docs/character.md`
- 背包/物品 → `../../Content/LuaHelper/Docs/item-backpack.md`
- 技能/Buff → `../../Content/LuaHelper/Docs/skill.md`
- GamePart → `../../Content/LuaHelper/Docs/gamepart.md`
- 全服存档 → 官方 wiki 的[玩法全服存档](https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=NrvjOyG6)；本地暂无专门文档，`UGCModeArchiveSystem` 是玩法存档，不是同一机制
- MCP/AskQ → `../../Plugins/UGCEditor/Docs/mcp.md`

## Agent 规则

1. 推荐新 API 前，先在本地 `UGCAPI` 确认存在；不要只凭 Release Notes。
2. 涉及 16223/16226 的新能力，先确认编辑器已升级。
3. 版本相关 bug 先看对应小版本 Notes，不要套用旧版本结论。
4. 不把 changelog 当设计文档；需要机制时看对应专题文档。
