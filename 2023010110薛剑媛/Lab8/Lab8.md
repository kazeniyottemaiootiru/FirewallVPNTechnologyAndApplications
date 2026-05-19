# Lab8：NAT 与地址转换

## 从 Lab7 到 Lab8——还剩一个问题没解决

Lab7 搭建了一套三节点拓扑，在 `fw` 的 FORWARD 链上对比了无状态规则和有状态规则。为了让防火墙任务能跑通，Lab7 在 `wan` 上配了一条回程路由：

```bash
sudo ip netns exec wan ip route add 10.0.0.0/24 via 192.0.2.1
```

这条路由让 `wan` 知道怎么把回复包送回 `lan`。但**真实互联网上不存在这条路由**。

家庭、企业内网用的是私有地址段（`10.0.0.0/8`、`172.16.0.0/12`、`192.168.0.0/16`），互联网上的服务器没有也不可能有到这些地址的路由——全球有无数个内网在用同一批私有地址，服务器根本不知道该把回复包发给哪个 `10.0.0.2`。

Lab8 的第一步就是删掉这条路由，复现真实情况下会发生什么，然后用 NAT 解决它。

---

## NAT 的工作原理

NAT 部署在内网出口（本实验中就是 `fw`）。当内网包从出口接口发出时，NAT 把源地址从内网地址改成出口接口的公网地址：

```
原始包：  src=10.0.0.2   dst=192.0.2.2   （wan 不认识 10.0.0.2）
NAT 后：  src=192.0.2.1  dst=192.0.2.2   （wan 认识 192.0.2.1，这是 fw 的外侧地址）
```

`wan` 收到后，回复包的目标地址是 `192.0.2.1`（即 `fw` 的外侧地址），`fw` 能收到它。`fw` 再根据 conntrack 里记录的映射关系，把目标地址还原成 `10.0.0.2`，转发给 `lan`：

```
wan 回复：  src=192.0.2.2  dst=192.0.2.1   （fw 收到）
还原后：    src=192.0.2.2  dst=10.0.0.2    （fw 转发给 lan）
```

**NAT 依赖 conntrack**：如果没有 conntrack 记录"这条连接的内网地址是 `10.0.0.2`"，`fw` 就不知道该把回复包转给谁。这就是 Lab7 中学的状态检测和 Lab8 的 NAT 都依赖同一套 conntrack 机制的原因。

### iptables 中的 NAT 表

Lab7 操作的是 `filter` 表的 `FORWARD` 链。NAT 规则写在另一张表——`nat` 表——的 `POSTROUTING` 链上：

| 表 | 链 | 用途 |
| :--- | :--- | :--- |
| `filter` | `FORWARD` | 决定包是否允许通过（Lab7 用的） |
| `nat` | `POSTROUTING` | 包即将从接口发出前，改写源地址（本实验用的） |

`POSTROUTING` 的意思是"路由决策之后"——包已经确定从哪个接口出去，在真正发出的最后一步改写地址。

---

## 网络拓扑（与 Lab7 相同）

```
lan (10.0.0.2) ── fw (10.0.0.1 / 192.0.2.1) ── wan (192.0.2.2)
     内网                  防火墙                      外网
```

Lab7 结束时你保留了拓扑。如果已经删除，或者需要重建干净的环境，先清理残留再重建：

```bash
# 清理残留（可安全重复执行）
sudo ip netns del lan 2>/dev/null; sudo ip netns del fw 2>/dev/null; sudo ip netns del wan 2>/dev/null
sudo ip link del veth-lan 2>/dev/null; sudo ip link del veth-wan 2>/dev/null
```

然后重建（与 Lab7 任务一相同）：

```bash
sudo ip netns add lan
sudo ip netns add fw
sudo ip netns add wan

sudo ip link add veth-lan type veth peer name veth-fw-lan
sudo ip link add veth-wan type veth peer name veth-fw-wan

sudo ip link set veth-lan netns lan
sudo ip link set veth-fw-lan netns fw
sudo ip link set veth-wan netns wan
sudo ip link set veth-fw-wan netns fw

sudo ip netns exec lan ip addr add 10.0.0.2/24 dev veth-lan
sudo ip netns exec lan ip link set veth-lan up
sudo ip netns exec lan ip link set lo up

sudo ip netns exec fw ip addr add 10.0.0.1/24 dev veth-fw-lan
sudo ip netns exec fw ip link set veth-fw-lan up
sudo ip netns exec fw ip addr add 192.0.2.1/24 dev veth-fw-wan
sudo ip netns exec fw ip link set veth-fw-wan up
sudo ip netns exec fw ip link set lo up

sudo ip netns exec wan ip addr add 192.0.2.2/24 dev veth-wan
sudo ip netns exec wan ip link set veth-wan up
sudo ip netns exec wan ip link set lo up

sudo ip netns exec lan ip route add default via 10.0.0.1
sudo ip netns exec wan ip route add 10.0.0.0/24 via 192.0.2.1
sudo ip netns exec fw sysctl -w net.ipv4.ip_forward=1
```

---

## tmux 基础操作

本实验需要同时操作四个终端。推荐使用 **tmux** 在一个窗口内管理多个终端面板，避免来回切换窗口。

### 安装 tmux

```bash
sudo apt install tmux   # Debian/Ubuntu
```

### 启动与退出

| 操作 | 命令 |
| :--- | :--- |
| 启动新会话 | `tmux` |
| 启动并命名会话 | `tmux new -s lab8` |
| 退出当前会话（后台保留） | `Ctrl+B`，然后按 `D` |
| 重新连接会话 | `tmux attach -t lab8` |
| 列出所有会话 | `tmux ls` |

> `Ctrl+B` 是 tmux 的**前缀键**，所有快捷键都先按前缀键，松开后再按功能键。

### 面板分割

| 操作 | 快捷键 |
| :--- | :--- |
| 左右分割（新建右侧面板） | `Ctrl+B`，然后按 `%` |
| 上下分割（新建下方面板） | `Ctrl+B`，然后按 `"` |
| 关闭当前面板 | `Ctrl+B`，然后按 `X`，确认 `Y` |

### 面板切换与调整

| 操作 | 快捷键 |
| :--- | :--- |
| 切换到指定方向的面板 | `Ctrl+B`，然后按方向键 |
| 用鼠标点击切换面板 | 先执行 `Ctrl+B` 然后 `:set mouse on` 开启鼠标模式 |
| 调整面板大小 | `Ctrl+B`，按住 `Ctrl` 再按方向键 |

### 推荐布局：四面板

启动 tmux 后，执行以下步骤快速建立四个面板：

```bash
# 1. 左右分割
Ctrl+B %

# 2. 在左侧面板上下分割
Ctrl+B "

# 3. 切换到右侧面板，上下分割
Ctrl+B →
Ctrl+B "
```

得到如下布局：

```
┌─────────────┬─────────────┐
│  终端 A     │  终端 B     │
│  (wan 服务) │  (lan 客户) │
├─────────────┼─────────────┤
│  终端 C     │  终端 D     │
│  (fw 配置)  │  (tcpdump)  │
└─────────────┴─────────────┘
```

### tcpdump 实时输出

tcpdump 默认缓冲输出，只有 Ctrl+C 退出时才会刷新显示。加 `-l` 参数强制每包立即输出：

```bash
sudo ip netns exec fw tcpdump -ni veth-fw-wan -l icmp
```

---

## 准备工作

建议打开四个终端（推荐用上方介绍的 tmux 四面板布局）：

| 终端 | 用途 |
| :--- | :--- |
| 终端 A | 在 `wan` 中运行服务端（一直开着） |
| 终端 B | 从 `lan` 运行客户端或 ping |
| 终端 C | 在 `fw` 上查看和配置规则、conntrack |
| 终端 D | 在 `fw` 上运行 tcpdump（任务三用） |

确认服务端正在运行（终端 A）：

```bash
sudo ip netns exec wan python3 firewall_lab7_server.py
```

命令说明同 Lab7 任务一第五步，此处不再重复。

---

## 任务一：删除回程路由——复现路由不可达

### 第一步：删除 wan 上的回程路由（终端 C）

```bash
sudo ip netns exec wan ip route del 10.0.0.0/24
```

命令说明：

| 部分 | 含义 |
| :--- | :--- |
| `ip route del 10.0.0.0/24` | 从路由表中删除到 `10.0.0.0/24` 的路由条目 |

执行后确认路由已删除：

```bash
sudo ip netns exec wan ip route show
```

命令说明：

| 部分 | 含义 |
| :--- | :--- |
| `ip route show` | 列出当前命名空间的完整路由表 |

输出里应该只剩 `192.0.2.0/24` 这一条直连路由，没有 `10.0.0.0/24`。

### 第二步：从 lan ping wan（终端 B）

```bash
sudo ip netns exec lan ping -c 4 192.0.2.2
```

命令说明：

| 部分 | 含义 |
| :--- | :--- |
| `ping` | 发送 ICMP Echo Request，用于测试网络可达性 |
| `-c 4` | 发送 4 个包后自动停止（count） |
| `192.0.2.2` | 目标地址，即 `wan` 的 IP |

### 第三步：理解失败原因

`lan` 发出的 ICMP 包源地址是 `10.0.0.2`，经 `fw` 转发到达 `wan`。`wan` 尝试回复时目标地址是 `10.0.0.2`，但路由表里没有这条路，回复包无处可去，`lan` 收不到任何响应。

可以在 `fw` 上抓包确认：包到达了 `wan` 一侧，但没有回程：

```bash
sudo ip netns exec fw tcpdump -ni veth-fw-wan icmp
```

命令说明：

| 部分 | 含义 |
| :--- | :--- |
| `tcpdump` | 抓包工具，实时捕获并显示经过接口的数据包 |
| `-n` | 直接显示 IP 地址，不做域名反查 |
| `-i veth-fw-wan` | 在 `fw` 的外侧接口上抓包 |
| `icmp` | 过滤器，只显示 ICMP 协议的包 |

在终端 B 再 ping 一次，观察抓包里只有 `echo request`，没有 `echo reply`。

### 第四步：填写下表

| 项目 | 你的填写内容 |
| :--- | :--- |
| ping 是否有回应 |无（100% packet loss）|
| `wan` 收到的请求源地址 |10.0.0.2|
| `wan` 无法回复的原因 |路由表中没有到 10.0.0.0/24 的路由，不知道如何将回复包发送回 lan|

![NAT 前失败](before_nat.png)

---

## 任务二：配置 NAT

### 第一步：在 fw 上添加 MASQUERADE 规则（终端 C）

```bash
sudo ip netns exec fw iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o veth-fw-wan -j MASQUERADE
```

命令说明：

| 部分 | 含义 |
| :--- | :--- |
| `-t nat` | 操作 nat 表（区别于 Lab7 用的 filter 表） |
| `-A POSTROUTING` | 追加到 POSTROUTING 链 |
| `-s 10.0.0.0/24` | 只匹配来自内网的包 |
| `-o veth-fw-wan` | 只匹配从外侧接口发出的包 |
| `-j MASQUERADE` | 把源地址替换为出口接口的当前 IP（`192.0.2.1`） |

`MASQUERADE` 是一种动态 SNAT：它自动读取出口接口的当前 IP 地址来做替换。如果出口 IP 固定不变，也可以写成 `-j SNAT --to-source 192.0.2.1`，效果相同，但出口 IP 变化时需要手动更新规则；`MASQUERADE` 会自动跟随接口 IP 变化，更适合动态拨号场景。

### 第二步：再次 ping wan（终端 B）

```bash
sudo ip netns exec lan ping -c 4 192.0.2.2
```

命令说明同任务一第二步，此处不再重复。

这次应该能收到回复。

### 第三步：填写下表

| 项目 | 你的填写内容 |
| :--- | :--- |
| 加 NAT 后 ping 是否成功 |是（0% packet loss）|

---

## 任务三：用 tcpdump 观察地址变化

### 第一步：在 fw 外侧接口开始抓包（终端 D）

```bash
sudo ip netns exec fw tcpdump -ni veth-fw-wan -l icmp
```

命令说明：

| 部分 | 含义 |
| :--- | :--- |
| `-n` | 直接显示 IP 地址，不做域名反查 |
| `-i veth-fw-wan` | 在 `fw` 外侧接口上抓包 |
| `icmp` | 只显示 ICMP 包（ping 使用的协议） |

### 第二步：从 lan ping wan（终端 B）

```bash
sudo ip netns exec lan ping -c 4 192.0.2.2
```

命令说明同任务一第二步，此处不再重复。

### 第三步：观察终端 D 的抓包输出

注意 ICMP request 包的源地址是 `192.0.2.1`（`fw` 的外侧 IP），而不是 `10.0.0.2`（`lan` 的真实地址）。NAT 在包离开 `fw` 之前完成了地址替换。

### 第四步：填写下表

| 项目 | 你的填写内容 |
| :--- | :--- |
| 抓包中看到的 request 源地址 |192.0.2.1|
| `lan` 的真实地址是什么 |10.0.0.2|
| NAT 把源地址改成了什么 |192.0.2.1|
| reply 包的目的地址是什么 |192.0.2.1|

![NAT 后成功与 tcpdump](after_nat.png)

---

## 任务四：用 conntrack 验证 NAT 映射关系

NAT 依赖 conntrack 记录映射关系。本任务观察 conntrack 在 NAT 场景下存储了哪些额外信息。

### 第一步：清空旧的 conntrack 条目（终端 C）

```bash
sudo ip netns exec fw conntrack -F
```

命令说明：

| 部分 | 含义 |
| :--- | :--- |
| `conntrack -F` | flush，清空当前命名空间内所有 conntrack 条目，方便观察新产生的条目 |

### 第二步：从 lan ping wan 一次（终端 B）

```bash
sudo ip netns exec lan ping -c 2 192.0.2.2
```

命令说明同任务一第二步，`-c 2` 表示只发 2 个包，产生少量条目便于观察。

### 第三步：查看 fw 的 conntrack 表（终端 C）

```bash
sudo ip netns exec fw conntrack -L
```

命令说明：

| 部分 | 含义 |
| :--- | :--- |
| `conntrack -L` | list，列出当前所有 conntrack 条目的快照 |

> **提示**：与 Lab7 的 TCP 连接不同，ICMP 连接结束很快，这里用 `-L` 即可，不需要 `-E`，因为 ping 结束后条目仍会在表里保留一段时间。

找到 ICMP 条目，格式类似：

```text
icmp  1  29  src=10.0.0.2  dst=192.0.2.2  ...
              src=192.0.2.2 dst=192.0.2.1  ...
```

与 Lab7 里看到的 TCP 条目对比：

- **Lab7（只做状态检测）**：conntrack 记录连接的双向地址，用于判断"这个包属不属于合法连接"
- **Lab8（加了 NAT）**：conntrack 额外记录了地址映射关系——原始源地址 `10.0.0.2` 和 NAT 后的地址 `192.0.2.1`，`fw` 收到 `wan` 的回复后，用这条记录把目标地址从 `192.0.2.1` 还原为 `10.0.0.2`

### 第四步：填写下表

| 项目 | 你的填写内容 |
| :--- | :--- |
| conntrack 条目中 `lan` 的真实源地址 |10.0.0.2|
| `wan` 回复时的目的地址（NAT 前） |192.0.2.1|
| `fw` 收到回复后，目的地址还原为 |10.0.0.2|

简答题：

1. 在 Lab7 中，conntrack 帮助防火墙判断"这个包属不属于合法连接"。在 Lab8 中，conntrack 还额外记录了什么信息？这两个功能都依赖 conntrack，说明了什么？
答：在 Lab8 中，conntrack 还额外记录了 NAT 地址映射关系——即原始源地址 10.0.0.2 被转换成了 192.0.2.1，当回复包到达时，fw 根据这条记录把目的地址从 192.0.2.1 还原回 10.0.0.2。这两个功能都依赖 conntrack，说明 conntrack 是状态检测和 NAT 的共同底层基础，既为 filter 表提供了连接状态信息，也为 nat 表提供了地址映射信息。
2. 如果两台内网主机同时访问同一个外网服务器的同一个端口，NAT 如何区分两条连接的回复分别属于哪台内网主机？
答：NAT 通过修改源端口来区分。fw 会把 10.0.0.2:12345 映射成 192.0.2.1:54321，把 10.0.0.3:12345 映射成 192.0.2.1:54322，conntrack 记录这两条不同的映射关系，当回复包到达时，根据目的端口（54321 或 54322）就能判断应该转发给哪台内网主机。
![conntrack NAT 映射](conntrack_nat.png)

---

## 任务五：验证 NAT 与状态检测可以同时工作

Lab7 配置了有状态防火墙规则，Lab8 又加了 NAT。两者可以同时启用，互不干扰——conntrack 是它们共同的底层机制。

### 第一步：加回 Lab7 的有状态规则（终端 C）

```bash
sudo ip netns exec fw iptables -P FORWARD DROP
sudo ip netns exec fw iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo ip netns exec fw iptables -A FORWARD -p tcp --dport 38070 -m conntrack --ctstate NEW -j ACCEPT
```

命令说明同 Lab7 任务三，此处不再重复。

### 第二步：用客户端访问（终端 B）

```bash
sudo ip netns exec lan python3 firewall_lab7_client.py 192.0.2.2 38070
```

命令说明同 Lab7 任务一第六步，此处不再重复。

应该成功。此时 FORWARD 链有状态规则在控制哪些连接允许建立，nat 表的 MASQUERADE 在处理地址转换，两者独立运作，共用同一份 conntrack 记录。

### 第三步：确认 ping 不通（终端 B）

```bash
sudo ip netns exec lan ping -c 3 192.0.2.2
```

命令说明同任务一第二步，`-c 3` 表示发 3 个包。

ping 用的是 ICMP，不是 TCP，当前 FORWARD 规则只允许 TCP 38070 的新连接。ICMP 的 ping 包会被 DROP。这是预期行为：FORWARD 链没有放行 ICMP 的规则。

### 第四步：填写下表

| 项目 | 你的填写内容 |
| :--- | :--- |
| TCP 38070 访问是否成功 |是|
| ping 是否成功 |否（100% packet loss）|
| ping 失败的原因 |FORWARD 链默认策略为 DROP，且只放行了 --ctstate ESTABLISHED,RELATED 和 tcp --dport 38070 --ctstate NEW，没有放行 ICMP 协议的新连接请求|

---

## 任务六：清理拓扑

实验结束后删除所有命名空间，其中的接口、路由、iptables 规则会自动清除：

```bash
sudo ip netns del lan
sudo ip netns del fw
sudo ip netns del wan
```

命令说明：

| 部分 | 含义 |
| :--- | :--- |
| `ip netns del <名称>` | 删除命名空间，其中所有接口、路由、iptables 规则随之销毁 |

确认已清理：

```bash
sudo ip netns list
```

命令说明：

| 部分 | 含义 |
| :--- | :--- |
| `ip netns list` | 列出当前系统中所有存在的网络命名空间 |

输出为空即可。

---

## 思考题

1. 为什么私有地址（如 `10.0.0.0/8`）的主机通常无法被互联网直接访问？NAT 是怎么解决这个问题的？

   > 答：私有地址只在局域网内有效，互联网上的路由器没有到私有地址的路由，因为全球无数内网都在使用相同的私有地址段，无法唯一标识。NAT 把内网私有地址转换为出口接口的公网地址，让外网服务器认为请求来自防火墙本身，回复包被防火墙收到后再根据 conntrack 映射关系转给内网主机。

2. `MASQUERADE` 和 `SNAT --to-source 192.0.2.1` 在本实验中效果相同。实际场景中应如何选择？

   > 答：出口 IP 固定不变时用 SNAT 效率更高且规则清晰；出口 IP 动态变化（如DHCP）时用 MASQUERADE，因为它会自动跟随接口 IP 变化，不需要手动更新规则。

3. NAT 对外隐藏了内网拓扑，但它给哪些应用层协议带来了麻烦？为什么？

   > 答：FTP、SIP、IPsec 等协议会在应用层数据中携带 IP 地址和端口号，NAT 只修改 IP 层和传输层的地址，不修改应用层数据，导致应用层内的地址信息失效。解决办法是使用应用层网关（ALG）或 NAT 穿透技术。

4. 状态检测和 NAT 都依赖 conntrack，从这个角度看，为什么家用路由器通常把这两个功能集成在一起？

   > 答：因为两者共用同一套 conntrack 表——状态检测用 conntrack 判断包是否属于合法连接，NAT 用 conntrack 记录地址映射关系。集成在一起可以避免维护两套独立的跟踪表，提高效率、降低复杂度。

5. 任务五里 ping 被 FORWARD 链拦截。如果要在保留现有规则的基础上，让 ICMP 也能通过，应该怎么写规则？

   > 答：添加一条规则放行 ICMP 的新连接请求，例如：sudo ip netns exec fw iptables -A FORWARD -p icmp --icmp-type echo-request -m conntrack --ctstate NEW -j ACCEPT。

---

## 截图要求

- 截图须清晰，终端文字可读。
- 所有截图与本 `Lab8.md` 放在**同一目录**下。

| 截图内容 | 文件名 |
| :--- | :--- |
| 未配置 NAT 时 ping 失败或无响应 | `before_nat.png` |
| 配置 NAT 后 ping 成功与 tcpdump 地址变化 | `after_nat.png` |
| conntrack 中的 NAT 映射条目 | `conntrack_nat.png` |

具体要求：

1. `before_nat.png`：能看到 ping 无响应（或 tcpdump 中只有 request 没有 reply）。
2. ###### `after_nat.png`：能看到 ping 成功，以及 tcpdump 中源地址已被转换为 `192.0.2.1`。
3. `conntrack_nat.png`：能看到 conntrack 条目中的原始源地址（`10.0.0.2`）和 NAT 映射关系。

---

## 提交要求

在自己的文件夹下新建 `Lab8/` 目录，提交以下文件：

```text
学号姓名/
└── Lab8/
    ├── Lab8.md
    ├── before_nat.png
    ├── after_nat.png
    └── conntrack_nat.png
```

---

## 截止时间

2026-05-22，届时关于 `Lab8` 的 PR 将不会被合并。
