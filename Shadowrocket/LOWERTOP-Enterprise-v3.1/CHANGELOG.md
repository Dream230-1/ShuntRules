# CHANGELOG

## 3.1.0-rc1

- 配置拆分为 meta、DNS、profiles、proxy groups、routes、health、audit 七个 YAML 分片。
- OpenAI 拆分 AI-Core 与 AI-Realtime。
- Apple 拆分 Telemetry Reject、Global AI、System Direct、CDN Direct。
- DNS Leak Guard 升级至 v3，并保留 RC3 实机验证的 DoH/IPv6/UDP 基线。
- 远程规则审计加入 ETag 与 Last-Modified 条件缓存。
- 新增 DNS 健康评分，但不自动改变设备 DNS 顺序。
- 保留 AdvertisingLite 并继续执行关键服务碰撞审计。
- 未加入未经验证的 DoQ/DoT 自动回退，也未宣称强制 ECH。
