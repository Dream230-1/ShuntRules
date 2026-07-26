# LOWERTOP Enterprise v3.1 RC1

v3.1 是在已通过实机 DNSLeakTest 与 RC3 CI 的基础上进行的架构升级。RC1 先采用兼容层复用 RC3 已验证的生成器、远程审计、回归测试和广告碰撞检测，再由 `config/*.yaml` 覆盖版本与策略参数。

## 保持不变

- Performance 继续允许 QUIC/HTTP3。
- 禁止系统 DNS 回退。
- 境外备用 DoH 继续通过 `#proxy`。
- Performance 与 Strict 继续关闭 IPv6。
- UDP 不支持时继续 `REJECT`，不回落到直连。
- AdvertisingLite 继续作为默认广告拦截。
- OpenAI、Apple、Telegram、流媒体、国内与 FINAL 保持策略隔离。

## v3.1 新架构

```text
LOWERTOP-Enterprise-v3.0-RC3  已验证构建内核
                ↓
LOWERTOP-Enterprise-v3.1/config/*.yaml  分层覆盖
                ↓
scripts/build.py  生成临时工作区
                ↓
RC3 静态审计、DNS 审计、回归与在线审计
                ↓
v3.1 Performance / Strict / Experimental
```

## 分层配置

- `config/release.yaml`：版本、项目路径和发布元数据。
- `config/dns.yaml`：DNS、IPv6、QUIC 和 UDP 安全基线。
- `config/features.yaml`：广告拦截、分流和实验功能声明。

## 构建

```bash
python -m pip install -r requirements.txt
python scripts/build.py
```

在线审计：

```bash
python scripts/build.py --online
```

## 准确边界

Shadowrocket 当前已验证配置使用 DoH。v3.1 RC1 不写入未经验证的 DoQ、DoT 或任意多协议自动回退语法。IPv6、HTTPS/SVCB 与潜在 ECH 仍仅保留在 Experimental 配置中。
