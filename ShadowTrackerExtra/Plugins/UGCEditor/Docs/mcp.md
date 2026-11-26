# MCP / UGCAskQ 接入

> 编辑器内置的本机 MCP（Model Context Protocol）服务，让 AI 客户端直接读取/操作当前工程。
> 官方来源：UGCAskQ MCP 使用说明；本地相关：`Docs/toolchain.md`、`Resources/Skills/ugc-vfx-gen/`。

## 何时读

- 需要让 Agent 直接操作编辑器（摆 Actor、改技能/物品、配行为树、改 UMG、读写数据表）。
- 需要确认 MCP 是否可用、端口、客户端配置。
- 需要判断某个编辑器模块是否支持 AI 操作。
- 需要在自动化前设计“先读后写、分步验证”的流程。

## 它是什么

```text
AI 客户端（Claude / Cursor / CodeBuddy / WorkBuddy …）
  → MCP（Streamable HTTP）：http://127.0.0.1:<port>/mcp
  → 编辑器内置 MCP Server
  → 当前工程的场景 / 资产 / 数据表
```

- 仅本机访问（默认 `127.0.0.1`），不支持远程。
- 工作方式是“先读后写”：先查询当前值/选中对象，再下修改指令。
- 仍处于**实验性**阶段：可能不稳定，操作前备份工程，改完人工校验。

## 启动与连接

### 1. 启动 MCP Server

编辑器菜单：`窗口 → 开发者工具 → MCP Server`。

- 面板显示 `Running (Port: <port>)` 即正常。端口以面板和 `[AskQMCPServer]` 配置为准（本机为 `12463`，配置在 `ShadowTrackerExtra/Saved/Config/WindowsUGCEditor/UGCSettings.ini`）。
- 未启动时点 `Start Server`；端口冲突改 Port 再启动。

### 2. 配置 AI 客户端

以 Claude 为例，在工作区根目录创建 `.mcp.json`：

```json
{
  "mcpServers": {
    "ugcaskq": {
      "type": "http",
      "url": "http://127.0.0.1:12463/mcp"
    }
  }
}
```

- 端口以面板实际显示为准。
- 合并写入，不要删除已有 MCP 配置。
- 不同客户端类型名可能是 `http` / `streamable-http`，按客户端格式转换；旧版 SSE 地址不适用。
- Cursor / VS Code 在 MCP 设置里以 HTTP（Streamable HTTP）类型添加同一地址。

### 3. 验证

连接后问：

- “当前场景里有哪些 Actor？”
- “你现在能在编辑器里做哪些操作？”

能正确回答即生效。

## 面板配置

| 配置 | 说明 | 建议 |
|---|---|---|
| Port | 监听端口，读 `[AskQMCPServer]`（本机 12463） | 冲突时改 |
| Enforce Level | PRV 安全策略级别 | `Observe`（警告不阻断） |
| Enable MCP Call Logging | 每日调用日志 | 开启 |
| Idle Boundary (sec) | 空闲超时，超过后开新任务段 | 90 秒 |

- 调用日志：面板 `Open Log Folder`，文件 `Saved/log/MCP_YYYYMMDD.log`。

## 支持的编辑器能力

| 模块 | 能做什么 |
|---|---|
| 场景与 Actor | 创建/摆放、改 Transform/标签/父子、批量操作 |
| 技能编辑器 | 创建技能、读取配置、改冷却/消耗等基础数值 |
| 物品编辑器 | 创建物品、设置类型/名称/图标、查列表、改数值 |
| 行为树 | 创建/读取行为树、增改节点、给节点挂 Lua |
| 蓝图 | 创建蓝图、查变量/函数、加变量、加黑板键 |
| UMG | 创建 Widget、加控件、改位置/大小/锚点/文本/颜色 |
| 数据表 | 读行、加行、改行（物品/技能/掉落等） |
| 实体编辑器 | 查/改怪物/NPC 属性、读组件 |
| 资产与视窗 | 搜资产、移动编辑器摄像机、聚焦 Actor |

**不支持**：特效编辑器、音频编辑器等暂无 MCP 接口；这些仍需在编辑器内手动完成。

## 典型流程

1. **连上先摸底**：让 AI 报告当前工程对象、选中项、目标当前值。
2. **一次改一件事**：改完保存，确认后再改下一个字段。
3. **改完验证**：在编辑器点校验或进 PIE；AI 改完不代表过了平台校验。
4. **复杂链路拆分**：怪物系统拆成血量 → 掉落 → 刷怪；不要一句话做完整套。

## 安全与限制

- 操作直接作用于工程：先保存/备份。
- 仅本机连接，不要把端口暴露到公网。
- 实验性功能：建议每次只执行一小步，逐步验证。
- 部分操作完成后需要手动刷新面板（例如蓝图变量添加后重新打开蓝图）。
- 校验弹窗原文直接丢给 AI，比“好像有问题”有效；最终以编辑器校验与进游戏为准。

## 与本地工具链的关系

- MCP 服务由**编辑器内置**；`Plugins/UGCEditor/` 目录只有 Python VM、工具集、技能与调试资源，不是 MCP 服务本体。
- Python 侧工具集（`ue.*` / `objed_*` / `toolset_proxy`）与 MCP 可以配合：MCP 负责编辑器操作，Python/DSL 负责批量资产。
- 特效生成优先走 `Resources/Skills/ugc-vfx-gen/SKILL.md`；其前置条件就是 MCP Server Running + 账号登录。
- 工具链总览见 `toolchain.md`。

## Agent 规则

1. 操作前确认 MCP Server 为 Running，端口与客户端配置一致。
2. 先读后写；不确定当前值时先查询。
3. 一次只改一个字段/一个资产，保存并验证后再继续。
4. 不把端口暴露到公网；不绕过编辑器的校验。
5. 不支持 MCP 的模块（特效/音频编辑器）不要臆造工具，转为人工步骤或 Python 工具集。
6. 失败时先看 `MCP_YYYYMMDD.log` 与编辑器 Output Log。

## 官方链接

- MCP 使用说明：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=JHtqP3zo>
- 通过 UGC-AskQ 生成特效：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=nufmUYhR>
- 通过 UGC-AskQ 制作编辑器工具：<https://developer.gp.qq.com/oasiswikiweb/#/wiki?h=Qj8dHM7b>
