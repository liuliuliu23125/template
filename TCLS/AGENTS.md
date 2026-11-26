# TCLS AGENTS

腾讯客户端登录/版本/更新服务（TCLS）的本地配置。启动器用它做版本校验、登录、目录服务与更新。

## 文件

| 文件 | 作用 | 可读性 |
|---|---|---|
| `mmog_data.xml` | 客户端版本、BranchId、WorldID、演示版本 | 明文 XML |
| `config/VersionServerConfig.xml` | 版本服务器地址与端口（`tcls.rail.qq.com` 等 4 个） | 明文 XML |
| `config/dirserver.xml` | 目录服务器配置（当前 `count=0`） | 明文 XML |
| `config/updateconfig.cfg` | 更新通道/文件列表配置 | 加密 |
| `config/dirsystemconfig.cfg` | 目录服务配置 | 加密 |
| `config/commonconfig.cfg` | 通用配置 | 加密 |
| `config/version.cfg` | 版本计数（`count=0`） | 明文 |
| `config/LoginQ.dat` | 登录备份/后台参数 | 明文 ini |
| `mmog_data.xml.bak/.tmp`、`config/__*.bak/.tmp` | 更新过程备份/临时文件 | 生成物 |

## 何时读

- 登录失败、版本校验失败、更新服务器不可达。
- 需要确认当前客户端版本/Branch（`mmog_data.xml`）。
- 私有化/离线部署时确认服务器地址（`VersionServerConfig.xml`）。

## 约束

- **不要手改**：加密配置改了无效，且更新会覆盖；明文配置也由启动器维护。
- `.bak`/`.tmp` 不是配置源；排查时看与它们同名的正式文件。
- 更新相关日志不在这里，去 `../WeGameLauncher/log/` 与
  `../ShadowTrackerExtra/Saved/Logs/`。
- 网络问题优先确认代理/防火墙与 `VersionServerConfig.xml` 中的 4 个地址是否可达。
