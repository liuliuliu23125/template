# API 契约检查

> `api_contract.py` 用编辑器 UGC Resource Daemon 已生成的 `ApiMetadataCache.json` 做离线 API 检查：签名是否存在、参数个数、生效范围、废弃映射。

## 数据源

- 默认：`ShadowTrackerExtra/Saved/UGCResourceDaemon/ApiMetadataCache.json`
- 本次实测：`version=1.39.13.16220`，`signatures=47577`
- 每条签名含 `scope`（1=服务器 / 2=客户端 / 3=双端）、`params`、`deprecated`、`replacement`

## 用法

```bash
python -I spec/tools/api_contract.py \
  --project "ShadowTrackerExtra/UGCProjects/<工程>/Script" \
  --out spec/api-contracts
```

- `--project` 可重复；工具不绑定具体工程。
- `--scope auto|off|server|client|both`：默认按路径推断（`UI/`、`Client/` 视为客户端；`Service/`、`Server/` 视为服务器；其余按双端）。
- `--strict`：把参数不足、废弃、scope 警告升级为错误。
- `--cache`：显式指定其他版本的 API 元数据。
- 退出码：0=无错误；1=有错误；2=缓存或工程目录不存在。
- 报告写 `--out`（默认 `spec/api-contracts/`），属运行产物，不入库。

## 检查项

| 项 | 默认 | 说明 |
|---|---|---|
| API 不存在 | 错误 | 模块名在缓存中、函数名不在；本地变量同名会跳过 |
| 参数过多 | 错误 | 实际参数 > 签名参数 |
| 参数不足 | 警告 | 可能使用 C++ 默认参数；`--strict` 升级 |
| 废弃 API | 警告 | 输出 `replacement`；`--strict` 升级 |
| scope 不匹配 | 警告 | 仅服务器 API 出现在客户端路径，或反之 |

## 限制

- `ApiMetadataCache.json` 是编辑器生成物；版本不一致时先重新打开工程刷新。
- 前缀不在缓存中的库（如工程自己的模块）整段跳过；与工程 Lua 文件同名的前缀也跳过，避免把本地模块当 API。
- `UnrealNetwork.CallUnrealRPC`、`UGCGameSystem.SetTimer` 作为已知可变参数函数跳过参数个数检查。
- 内联 `function ... end` 中的逗号会计数修正，但极端表达式仍可能误判。
- scope 的 `auto` 是路径启发式，不是类型推断；不确定时用 `--scope off`。
- 当前不落基线；报告产物在 `spec/api-contracts/`（工作产物，不随仓库提交）。

## 实测基线（2026-11-26）

- 检查 `Withdraw/Script`：610 个文件、1548 个已知 API 调用。
- 错误 0；警告 481（466 参数不足 + 15 废弃 API）。
