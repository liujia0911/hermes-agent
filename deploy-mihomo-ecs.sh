#!/bin/bash
# 小马服务器 - 链式代理部署脚本
# 在 ECS (120.24.220.126) 上以 root 执行

set -e

# 1. 下载 mihomo
Mihomo_URL="https://github.com/MetaCubeX/mihomo/releases/download/v1.19.4/mihomo-linux-amd64-go120-v1.19.4.gz"
INSTALL_DIR="/opt/mihomo-proxy"

mkdir -p "$INSTALL_DIR"
cd /tmp
curl -L -o mihomo.gz "$Mihomo_URL"
gunzip -f mihomo.gz
mv mihomo "$INSTALL_DIR/mihomo"
chmod +x "$INSTALL_DIR/mihomo"

# 2. 配置文件
cat > "$INSTALL_DIR/config.yaml" << 'YAML'
# Mihomo 链式代理 - 自动更新订阅
# 机场: 八戒 | 住宅IP: kookeey

port: 7891
socks-port: 7892
allow-lan: false
mode: rule
log-level: info
external-controller: 127.0.0.1:9091
unified-delay: true
tcp-concurrent: true
ipv6: false

dns:
  enable: true
  listen: 127.0.0.1:1054
  ipv6: false
  enhanced-mode: fake-ip
  fake-ip-range: 28.0.0.1/8
  default-nameserver:
    - 223.5.5.5
    - 119.29.29.29
  nameserver:
    - https://223.5.5.5/dns-query
    - https://doh.pub/dns-query
    - 119.29.29.29
    - 223.5.5.5
  fallback:
    - https://223.5.5.5/dns-query
    - https://doh.pub/dns-query

proxy-providers:
  airport:
    type: http
    url: "https://bj.bmjsub.org/api/v1/client/subscribe?token=07ac75c0c37a87f282c12c0955000616"
    interval: 86400
    health-check:
      enable: true
      url: http://www.YouTube.com/generate_204
      interval: 600

  kookeey:
    type: inline
    override:
      dialer-proxy: auto-select
    payload:
      - { name: US-LA-Residential, type: socks5, server: us462.kookeey.info, port: 29094, username: '3c30d0ee', password: c9b3c078, udp: true }

proxy-groups:
  - { name: Proxy, type: select, use: [airport, kookeey], proxies: [auto-select, Residential, DIRECT] }
  - { name: auto-select, type: url-test, use: [airport], url: 'http://www.YouTube.com', interval: 600, tolerance: 100, lazy: true }
  - { name: Residential, type: select, use: [kookeey] }

rules:
  - DOMAIN-SUFFIX,feishu.cn,DIRECT
  - DOMAIN-SUFFIX,bytedance.com,DIRECT
  - DOMAIN-SUFFIX,larksuite.com,DIRECT
  - DOMAIN-SUFFIX,weixin.qq.com,DIRECT
  - DOMAIN-SUFFIX,wechat.com,DIRECT
  - DOMAIN-SUFFIX,qq.com,DIRECT
  - IP-CIDR,127.0.0.0/8,DIRECT,no-resolve
  - IP-CIDR,172.16.0.0/12,DIRECT,no-resolve
  - IP-CIDR,192.168.0.0/16,DIRECT,no-resolve
  - IP-CIDR,10.0.0.0/8,DIRECT,no-resolve
  - GEOIP,CN,DIRECT
  - MATCH,Proxy
YAML

# 3. 测试配置
echo "=== Testing config ==="
"$INSTALL_DIR/mihomo" -t -f "$INSTALL_DIR/config.yaml"

# 4. 安装 systemd 服务
cat > /etc/systemd/system/mihomo-proxy.service << 'UNIT'
[Unit]
Description=Mihomo Chain Proxy (IEPL + Residential)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/opt/mihomo-proxy/mihomo -d /opt/mihomo-proxy -f /opt/mihomo-proxy/config.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now mihomo-proxy

# 5. 验证
sleep 5
echo "=== Verifying ==="
curl -x http://127.0.0.1:7891 https://httpbin.org/ip 2>/dev/null || echo "Waiting for subscription download..."

echo ""
echo "Done! Proxy running on 127.0.0.1:7891"
echo "API: http://127.0.0.1:9091"
echo ""
echo "Switch proxy group:"
echo "  Residential: curl -X PUT http://127.0.0.1:9091/proxies/Proxy -d '{\"name\":\"Residential\"}'"
echo "  auto-select: curl -X PUT http://127.0.0.1:9091/proxies/Proxy -d '{\"name\":\"auto-select\"}'"
