# LOWERTOP Enterprise v3.1 RC1

v3.1 将 RC3 的单一 manifest 重构为可组合配置分片，同时保持已经实机验证的 Performance 路由、DNS 防旁路和 AdvertisingLite。

## 关键边界

- 主力 Performance 继续允许 QUIC/HTTP3。
- 发布版继续关闭 IPv6，禁止系统 DNS 回退。
- 境外备用 DoH 必须携带 `#proxy`。
- AdvertisingLite 继续作为默认广告拦截，并显式阻止 rmonitor.qq.com、clarity.ms 与 securemetrics.apple.com。
- Apple 遥测 `securemetrics.apple.com` 显式 REJECT；Apple Core/CDN 仍直连。
- IPv6/SVCB 只在 Experimental 配置启用，不宣称强制 ECH。

## 架构

`manifest.yaml` 只负责加载 `config/*.yaml`。规则拆为 Probe、AI Core、AI Realtime、Apple Telemetry、Apple Global、Apple System、Apple CDN 七个模块。

## 构建

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/config_audit.py
python scripts/generate.py --profile all-release --mode inline
python scripts/generate.py --profile ipv6_svcb_experimental --mode inline --out-dir experimental
python scripts/regression.py --offline
python scripts/dns_audit.py
```

在线审计增加远程规则条件缓存、规则漂移、广告碰撞、服务健康、DNS 健康评分和非阻断性能报告。
