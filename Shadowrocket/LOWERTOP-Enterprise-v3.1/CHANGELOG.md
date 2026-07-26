# CHANGELOG

## 3.1.0-rc1

### Added
- 分层 `config/release.yaml`、`dns.yaml` 与 `features.yaml`。
- v3.1 兼容层生成器，复用已通过验证的 RC3 构建与审计内核。
- 独立 v3.1 GitHub Actions 构建与在线审计。

### Preserved
- Performance 的 QUIC/HTTP3。
- 系统 DNS 回退禁用。
- 境外备用 DoH 通过 `#proxy`。
- 发布版关闭 IPv6。
- AdvertisingLite 默认启用。
- OpenAI、Apple、Telegram、流媒体、中国大陆与 FINAL 分流顺序。

### Not included
- 未经 Shadowrocket 实测确认的 DoQ/DoT 多协议回退语法。
- 主力配置中的 IPv6 或强制 ECH。
- 尚未验证的多平台代理输出。
