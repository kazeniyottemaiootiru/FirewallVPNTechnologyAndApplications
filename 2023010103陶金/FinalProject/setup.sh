#!/bin/bash

set -e

echo "[1] 清理旧环境..."
for ns in fw office guest dmz internet remote; do
    sudo ip netns del $ns 2>/dev/null || true
done

echo "[2] 创建 namespaces..."
for ns in fw office guest dmz internet remote; do
    sudo ip netns add $ns
done

echo "[3] 创建 veth 对..."

# office
sudo ip link add veth-fw-office type veth peer name veth-office
sudo ip link set veth-fw-office netns fw
sudo ip link set veth-office netns office

# guest
sudo ip link add veth-fw-guest type veth peer name veth-guest
sudo ip link set veth-fw-guest netns fw
sudo ip link set veth-guest netns guest

# dmz
sudo ip link add veth-fw-dmz type veth peer name veth-dmz
sudo ip link set veth-fw-dmz netns fw
sudo ip link set veth-dmz netns dmz

# internet
sudo ip link add veth-fw-inet type veth peer name veth-inet
sudo ip link set veth-fw-inet netns fw
sudo ip link set veth-inet netns internet

# vpn
sudo ip link add veth-fw-vpn type veth peer name veth-vpn
sudo ip link set veth-fw-vpn netns fw
sudo ip link set veth-vpn netns remote

echo "[4] 配置 IP 地址..."

# fw
sudo ip netns exec fw ip addr add 10.20.0.1/24 dev veth-fw-office
sudo ip netns exec fw ip addr add 10.30.0.1/24 dev veth-fw-guest
sudo ip netns exec fw ip addr add 10.40.0.1/24 dev veth-fw-dmz
sudo ip netns exec fw ip addr add 203.0.113.1/24 dev veth-fw-inet
sudo ip netns exec fw ip addr add 10.10.10.1/24 dev veth-fw-vpn

# office
sudo ip netns exec office ip addr add 10.20.0.2/24 dev veth-office
sudo ip netns exec guest ip addr add 10.30.0.2/24 dev veth-guest
sudo ip netns exec dmz ip addr add 10.40.0.2/24 dev veth-dmz
sudo ip netns exec internet ip addr add 203.0.113.10/24 dev veth-inet
sudo ip netns exec remote ip addr add 10.10.10.2/24 dev veth-vpn

echo "[5] 启动接口..."

for ns in fw office guest dmz internet remote; do
    sudo ip netns exec $ns ip link set lo up
done

sudo ip netns exec office ip link set veth-office up
sudo ip netns exec guest ip link set veth-guest up
sudo ip netns exec dmz ip link set veth-dmz up
sudo ip netns exec internet ip link set veth-inet up
sudo ip netns exec remote ip link set veth-vpn up

sudo ip netns exec fw ip link set veth-fw-office up
sudo ip netns exec fw ip link set veth-fw-guest up
sudo ip netns exec fw ip link set veth-fw-dmz up
sudo ip netns exec fw ip link set veth-fw-inet up
sudo ip netns exec fw ip link set veth-fw-vpn up

echo "[6] 配置路由..."

sudo ip netns exec office ip route add default via 10.20.0.1
sudo ip netns exec guest ip route add default via 10.30.0.1
sudo ip netns exec dmz ip route add default via 10.40.0.1
sudo ip netns exec internet ip route add default via 203.0.113.1
sudo ip netns exec remote ip route add default via 10.10.10.1

echo "[7] 开启 fw IP 转发..."
sudo ip netns exec fw sysctl -w net.ipv4.ip_forward=1

echo "基础网络搭建完成"