# tiny_cache AGENTS

WeGame 启动器的 CDN 下载缓存（约 122MB，13 个缓存文件；另有本 AGENTS.md）。

## 内容

| 文件 | 说明 |
|---|---|
| `*_cdn.wgj` | CDN 资源分块（按渠道/版本 ID 命名） |
| `*.manifest` | 分块清单（哈希/序号） |
| `Game_2001776.dat`、`Game_2001776.db` | 启动器本地索引/数据库 |

## 约束

- **不要手改**：格式由 `TenioDL` 维护，改坏会导致更新失败。
- 可安全删除（下次启动会重新下载），但删除前先退出启动器；删除会延长下次启动时间。
- 排查下载问题时，结合 `../WeGameLauncher/log/` 与 `../TCLS/config/updateconfig.cfg`。
