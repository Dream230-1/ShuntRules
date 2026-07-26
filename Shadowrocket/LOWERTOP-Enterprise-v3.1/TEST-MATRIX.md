# v3.1 设备测试矩阵

1. DNSLeakTest 扩展测试只显示代理出口相关解析器。
2. IPv6 在 Performance/Strict 中显示不可用或 n/a。
3. `ios.chat.openai.com` 命中 AI，实际节点为日本或美国 AI 节点。
4. `149.154.167.222` 命中 Telegram，实际节点按 Telegram 组选择。
5. `securemetrics.apple.com` 命中 REJECT。
6. Apple Push、iCloud、App Store 正常。
7. 广告域名命中 REJECT，登录、支付、验证码、推送不受影响。
8. Wi-Fi、蜂窝和相互切换后重复 DNS/WebRTC 测试。
9. 与 RC3 在同一网络和节点下比较延迟、首开速度和视频缓冲。
