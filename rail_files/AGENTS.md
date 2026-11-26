# rail_files AGENTS

WeGame（Rail）平台的识别与构建元数据。启动器/平台客户端据此识别游戏并做完整性校验。

## 文件

| 文件 | 内容 |
|---|---|
| `rail_game_identify.json` | `{"game_id":2001776}`，游戏 ID |
| `rail_game_build_info.dat` | 本次构建元数据；含 `clean_paths` 清理列表（安卓、Paks、部分模板等） |
| `RailKeyFileList.dat` | 关键文件清单（加密/签名） |

## 约束

- **只读**：修改会导致平台校验/启动失败，更新会覆盖。
- 不要用它判断版本；版本看根目录 `version.txt`、`TCLS/mmog_data.xml`。
- 排查启动器问题先看 `../WeGameLauncher/log/` 与 `../TCLS/`。
