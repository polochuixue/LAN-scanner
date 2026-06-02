# LAN Scanner

[![Version](https://img.shields.io/badge/Version-1.0-brightgreen.svg)](https://github.com/polochuixue/LAN-scanner)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()
[![License](https://img.shields.io/badge/License-MIT-orange.svg)](LICENSE)

局域网主机综合探测工具，支持 **IPv4 + IPv6 双栈扫描**，提供主机发现、MAC厂商识别、端口扫描、操作系统识别等功能。基于Python模块化架构开发，每个功能模块可独立运行，也可通过主脚本统一调度。

---

## 🚀 快速开始

### 环境要求

| 项目           | 要求                                                   |
| ------------ | ---------------------------------------------------- |
| **Python版本** | **3.10及以上**（使用了 `list[dict]`、`str \| None` 等3.10+语法） |
| **操作系统**     | Windows / Linux / macOS                              |
| **权限**       | 普通用户权限即可运行                                           |
| **唯一依赖**     | `rich` 库（终端美化输出）                                     |

### Python版本兼容性

| Python版本 | 兼容性 | 说明                                     |
|:--------:|:---:| -------------------------------------- |
| 3.13     | ✅   | 完全支持                                   |
| 3.12     | ✅   | 完全支持                                   |
| 3.11     | ✅   | 完全支持                                   |
| 3.10     | ✅   | 完全支持（最低要求版本）                           |
| 3.9      | ❌   | 不支持（`list[dict]`、`str \| None` 等语法不兼容） |
| < 3.9    | ❌   | 不支持                                    |

### 快速使用：克隆仓库运行

```bash
# 克隆项目
git clone https://github.com/polochuixue/LAN-scanner.git
cd LAN-scanner

# 安装依赖
pip install rich

# 运行扫描
python scanner.py
```

---

---

## 📖 基本使用

```bash
# 最简用法：自动检测本机子网，扫描IPv4存活主机
python scanner.py

# 扫描指定子网
python scanner.py 192.168.1.0/24

# IPv4 + IPv6 双栈扫描
python scanner.py --ipv6

# 全部功能：OS识别 + 端口扫描 + IPv6
python scanner.py --full --ipv6

# 指定子网 + 全部功能 + 导出结果
python scanner.py 192.168.1.0/24 --full --ipv6 --export result.csv
```

## 📖 命令参数

```bash
用法: python scanner.py [子网] [选项]

位置参数:
  subnet                    目标子网CIDR (如 192.168.1.0/24)
                            不指定则自动检测本机所在子网

主机发现选项:
  -m, --method {ping,tcp,all}
                            探测方式 (默认: ping)
  -t, --timeout TIMEOUT     超时时间，秒 (默认: 1.0)
  -w, --workers WORKERS     并发线程数 (默认: 100)

模块开关:
  --os                      启用操作系统识别
  --portscan                启用端口扫描
  --ports-list PORTS        自定义端口，逗号分隔 (如 22,80,443,3306)
  --full                    开启全部功能 (--os + --portscan)

IPv6选项:
  --ipv6                    启用IPv6扫描 (与IPv4同时)
  --ipv6-only               仅IPv6扫描

导出选项:
  --export FILE             导出结果，支持 .csv 和 .json 格式
```

## 📖 各模块独立运行

每个模块均可脱离主脚本独立使用

```bash
# 仅主机发现
python -m modules.discovery 192.168.1.0/24 -m all

# 仅MAC厂商识别
python -m modules.vendor DC:A6:32:AA:BB:CC 54:25:EA:DD:EE:FF

# 查看OUI数据库统计
python -m modules.vendor --stats

# 仅端口扫描
python -m modules.portscan 192.168.1.1 -p 22,80,443,3306

# 仅OS识别
python -m modules.osdetect 192.168.1.1 192.168.1.5

# 仅IPv6扫描
python -m modules.ipv6
```

---

---

## 📊 版本特性

- **双栈扫描**：支持IPv4 + IPv6同时扫描，自动发现仅使用IPv6连接的设备
- **智能合并**：同一设备的IPv4和IPv6地址、MAC地址自动合并，不重复显示
- **随机MAC识别**：自动检测Android/iOS设备的随机MAC地址，标注为"Random MAC"
- **OUI数据库**：内置300+常见厂商数据库，支持加载IEEE官方数据库（34000+条）
- **端口Banner**：扫描25个常见端口，自动抓取服务Banner识别信息
- **OS推测**：基于TTL值推测操作系统类型（Windows/Linux/macOS/网络设备）
- **模块化架构**：5个功能模块完全解耦，可独立运行或组合使用
- **美化输出**：基于rich库的终端美化，表格展示、进度条、彩色标识
- **结果导出**：支持导出为CSV和JSON格式

---

---

## ✨ 输出示例

```
╔═══════════════════════════════════════════════════╗
║  LAN Scanner  v1.0                                ║
║  局域网主机综合探测工具  |  IPv4 + IPv6 双栈        ║
║  by polochuixue                                   ║
╚═══════════════════════════════════════════════════╝

╭──────────────────────── 扫描参数 ─────────────────────────╮
  子网: 192.168.1.0/24  方式: ping  并发: 100  超时: 1.0s
╰──────────────────────────────────────────────────────────╯

  Phase 1 IPv4 主机发现
  [██████████████████████████████] 254/254
  ✓ 发现 5 台 IPv4 主机

  Phase 3 IPv6 扫描
  ✓ 合并 5 台  |  新增 3 台纯IPv6设备

╭───────────────────────────── 扫描结果 ─────────────────────────────╮
│ #  │ IPv4            │ MAC              │ 厂商      │ 系统         │ 开放端口        │ 来源  │
├────┼─────────────────┼──────────────────┼───────────┼──────────────┼─────────────────┼───────┤
│  1 │ 192.168.1.1     │ C0:B4:7D:41:F8:31│ ZTE       │ Linux        │ 53/DNS 80/HTTP  │ IPv4  │
│  2 │ 192.168.1.5     │ -                │ -         │ Windows      │ 445/SMB         │ IPv4  │
│  3 │ 192.168.1.10    │ 94:F6:F2:68:09:41│ Honor     │ Linux        │ -               │ v4+v6 │
│  4 │ -               │ DE:AE:37:73:85:06│ Random    │ -            │ -               │ IPv6  │
╰────┴─────────────────┴──────────────────┴───────────┴──────────────┴─────────────────┴───────╯

  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
  │ 设备 │ │ IPv4 │ │ IPv6 │ │ 厂商 │ │ 耗时 │
  │  4   │ │  3   │ │  4   │ │  2   │ │ 8.5s │
  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   扫描完成  |  4台设备  |  8.5s
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

---

## 🛠️ 模块与功能目录

项目拥有 5个核心功能模块，各模块均由独立的 .py 脚本进行管理：

```
LAN-scanner/
├── scanner.py              # 主入口脚本
├── utils.py                # 公共工具函数库
├── modules/                # 功能模块目录（按需独立运行）
│   ├── __init__.py
│   ├── discovery.py        # 主机存活探测 (IPv4)
│   ├── ipv6.py             # IPv6主机发现
│   ├── vendor.py           # MAC厂商识别
│   ├── portscan.py         # 端口扫描 + Banner抓取
│   └── osdetect.py         # TTL操作系统识别
├── data/                   # 数据文件目录
│   ├── oui.py              # 内置OUI厂商数据库（300+条）
│   ├── oui_ieee.py         # IEEE官方OUI（需运行fetch_oui.py生成，34000+条）
│   └── oui.txt             # IEEE官方OUI原始文件（需手动下载）
├── tools/                  # 工具脚本目录
│   └── fetch_oui.py        # OUI数据库加载与解析工具
├── LICENSE                 # MIT开源许可证
└── README.md               # 项目说明文档
```

![image](image\image.png)

#### 1. 主机存活探测 (modules/discovery.py)

IPv4局域网主机存活探测模块，支持多种探测方式：

- **ICMP Ping探测**：使用系统ping命令探测主机是否存活，兼容Windows/Linux/macOS。
- **TCP端口探测**：通过TCP Connect扫描常见端口判断主机是否在线，可穿透部分禁ping防火墙。
- **混合探测**：先Ping后TCP，两种方式组合使用，提高发现率。
- **高并发扫描**：基于ThreadPoolExecutor多线程并发，默认100线程，扫描/24子网约10秒完成。

#### 2. IPv6主机发现 (modules/ipv6.py)

IPv6主机发现模块，解决现代移动设备仅使用IPv6连接的问题：

- **邻居缓存读取**：读取系统IPv6邻居缓存（类似ARP表的IPv6版本），自动过滤组播地址和无效条目。
- **链路本地组播探测**：向ff02::1发送组播Ping，触发邻居缓存刷新，Linux下自动检测网卡接口。
- **mDNS服务发现**：通过mDNS协议探测本地支持组播DNS的设备。
- **智能过滤**：自动过滤组播MAC（33:33:xx:xx:xx:xx）、组播IPv6地址（ff00::/8）、无效全零地址。
- **跨平台兼容**：Windows使用netsh命令，Linux使用ip -6 neigh命令，自动适配。

"⚠️ 已知问题：IPv6主机识别功能在部分Linux发行版上可能存在无法发现主机的情况（如Ubuntu Server、部分云服务器环境），该问题目前正在开发优化中。Windows环境下IPv6功能表现正常。Kali Linux虚拟机环境已通过测试。"

#### 3. MAC厂商识别 (modules/vendor.py)

基于OUI数据库的MAC地址厂商识别模块：

- **内置数据库**：内置300+常见厂商的OUI映射，覆盖小米、华为、苹果、三星、OPPO、vivo、中兴、TP-Link、海康威视、Cisco、Dell等主流品牌。
- **IEEE官方数据库**：支持加载IEEE官方OUI数据库（34000+条），通过tools/fetch_oui.py工具解析本地oui.txt文件。
- **三层查询策略**：优先查IEEE数据库 → 再查内置数据库 → 最后返回Unknown。
- **随机MAC检测**：自动检测Android/iOS设备的随机MAC地址（Locally Administered Bit），标注为"Random MAC (Private/Hidden)"。

#### 4. 端口扫描 (modules/portscan.py)

TCP端口扫描与服务Banner抓取模块：

- **25个常见端口**：默认扫描21/FTP、22/SSH、23/Telnet、80/HTTP、443/HTTPS、445/SMB、3306/MySQL、3389/RDP等常用端口。
- **自定义端口**：支持通过--ports-list参数指定自定义端口列表。
- **Banner抓取**：对开放端口抓取服务Banner信息，识别具体服务和版本号。
- **服务名映射**：内置常见端口到服务名的映射表，自动标注服务类型。
- **多线程扫描**：基于ThreadPoolExecutor并发扫描，默认50线程。

#### 5. 操作系统识别 (modules/osdetect.py)

基于TTL值的操作系统类型推测模块：

- **TTL探测**：通过系统ping命令获取目标主机的TTL值。
- **智能推测**：根据TTL基值推测操作系统类型：
  TTL ≤ 64 → Linux / macOS / Android
  TTL ≤ 128 → Windows
  TTL ≤ 254 → Solaris / AIX / 网络设备
  TTL ≤ 255 → Cisco / BSD / 网络设备
- **多线程批量**：支持批量探测多个主机的OS类型。

---

---

## 📦 扩展OUI数据库

内置OUI数据库包含300+常见厂商，覆盖大部分常见设备。如需更完整的厂商识别能力，可以加载IEEE官方数据库：

### 步骤一：下载OUI文件

用浏览器打开以下地址，按 Ctrl+S 保存到 data/oui.txt：

```text
https://standards-oui.ieee.org/oui/oui.txt
```

"⚠️ 文件大小约 5~8MB，请确保完整下载。必须使用浏览器"另存为"功能，不要复制粘贴页面内容。"

### 步骤二：解析生成Python文件

```bash
python tools/fetch_oui.py
```

### 步骤三：验证数据库

```bash
python -m modules.vendor --stats
```

#### 输出示例：

```bash
OUI数据库统计
────────────────────────────────────────
  内置记录:  350
  IEEE记录:  34000+
  合计:      34350+
  IEEE数据:  已加载
```

---

---

## ✅ 实测环境

以下环境已通过实际测试验证：

| 操作系统             | Python版本 | 测试结果    | 备注                 |
| ---------------- | -------- | ------- | ------------------ |
| Windows 10/11    | 3.12     | ✅ 正常    | 主开发环境，IPv4/IPv6均正常 |
| Ubuntu (阿里云VPS)  | 3.10+    | ✅正常     | 无需sudo权限即可运行       |
| Kali Linux (虚拟机) | 3.11+    | ✅ 正常    | IPv6邻居缓存发现功能正常     |
| macOS            | 3.10+    | ⚠️ 理论支持 | 未经实测，欢迎反馈          |

"关于权限说明：本脚本使用系统原生命令（ping、arp、ip、netsh等）完成探测，在Linux系统上不需要root/sudo权限即可正常运行。"

---

---

## 💡 常见问题

### Q: 为什么有些设备扫描不到？

- 现代手机（Android 10+、iOS 14+）默认使用随机MAC地址和IPv6优先连接WiFi，导致IPv4 ping不通。使用--ipv6参数可解决：

```bash
python scanner.py --ipv6
```

- IPv6模式会读取系统邻居缓存，即使手机不回复ping，只要连接在同一网络上就能被发现。

### Q: Linux下IPv6扫描发现不到主机怎么办？

- 这是目前已知的问题，在部分Linux环境（如Ubuntu Server、云服务器）上IPv6邻居缓存可能为空或组播探测不生效。目前正在开发优化中。

- 临时解决方案：

- 确认目标设备确实启用了IPv6连接

- 先手动触发邻居发现再运行扫描：

```bash
#查看网卡名称
ip link show

#手动发送组播探测（把eth0换成你的网卡名）
ping -c 3 -I eth0 ff02::1

#查看邻居缓存
ip -6 neigh show

#再运行扫描
python scanner.py --ipv6
```

### Q: 如何在手机上查看真实MAC地址？

| 品牌       | 查看路径                               |
| -------- | ---------------------------------- |
| 小米/Redmi | 设置 → WLAN → 已连接网络 → 高级设置 → MAC地址   |
| 华为/荣耀    | 设置 → WLAN → 已连接网络 → 查看MAC          |
| OPPO/一加  | 设置 → WLAN → 已连接网络 → 更多 → MAC地址     |
| iPhone   | 设置 → 无线局域网 → 点击已连接网络旁的 ⓘ → Wi-Fi地址 |

- 也可以在WLAN设置中关闭"使用随机MAC"，改为"使用设备MAC"，扫描器即可直接识别出设备厂商。

### Q: 端口扫描结果为空？

- 如果目标主机有防火墙或所有端口关闭，就不会显示开放端口。可以尝试：

```bash
#降低超时时间
python scanner.py --portscan -t 0.5

#只扫描特定端口
python scanner.py --portscan --ports-list 22,80,443,3306,3389,8080
```

### Q: 如何提高厂商识别准确率？

- 运行 python tools/fetch_oui.py 加载IEEE官方OUI数据库（34000+条），详见上方"扩展OUI数据库"章节。

### Q: Python 3.9能否使用？

- 不能直接使用。本脚本使用了list[dict]、str | None等Python 3.10+语法特性。如需兼容3.9或更低版本，需要将所有类型注解改为typing.List[dict]、typing.Optional[str]等写法。

### Q: 导出的CSV用Excel打开乱码？

- 用Excel打开时选择UTF-8编码导入，或使用WPS/VS Code等工具直接打开CSV文件。

---

---

## 🛠️ 模块化开发指南

您可以极其简单地为本项目增加新的扫描功能。所有模块均支持独立运行，只需在 modules/ 目录下添加一个新的Python脚本。

### 编写规范

1. **文件头部规范**：使用标准docstring文件头部，说明版权、许可与模块描述。
2. **类型注解**：所有函数参数和返回值使用Python 3.10+类型注解语法。
3. **复用工具函数**：优先复用 utils.py 中提供的公共函数，例如 get_local_ip()、resolve_hostname()、get_mac_from_arp() 等。
4. **独立运行支持**：每个模块末尾添加 if __name__ == "__main__": 入口，支持命令行独立运行。
5. **跨平台兼容**：使用 utils.is_windows() 判断系统，确保Windows/Linux/macOS均可运行。

### 模板示例

新建 modules/custom.py：

```python
"""
自定义扫描模块

by polochuixue
License: MIT License
Copyright (c) 2025 polochuixue
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import is_windows


def scan_custom(target: str, timeout: float = 1.0) -> dict:
    """
    自定义扫描逻辑
    返回: {"target": "...", "result": "..."}
    """
    # 业务逻辑代码
    return {"target": target, "result": "ok"}


def scan_batch(targets: list[str], timeout: float = 1.0) -> list[dict]:
    """批量扫描"""
    return [scan_custom(t, timeout) for t in targets]


# ── 独立运行 ──
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="自定义扫描模块")
    parser.add_argument("targets", nargs="+", help="扫描目标")
    parser.add_argument("-t", "--timeout", type=float, default=1.0)
    args = parser.parse_args()

    results = scan_batch(args.targets, args.timeout)
    for r in results:
        print(f"  {r['target']}  ->  {r['result']}")
```

### 集成到主脚本

在 scanner.py 中导入并调用新模块：

```python
from modules.custom import scan_custom

# 在主扫描逻辑中调用
result = scan_custom("192.168.1.1")
```

---

---

## 🏗️ 架构总览

```
scanner.py (主入口)
    │
    ├── modules/discovery.py     主机存活探测
    │       ├── ping()           ICMP Ping
    │       ├── tcp_connect()    TCP端口探测
    │       └── scan_network()   子网批量扫描
    │
    ├── modules/ipv6.py          IPv6主机发现
    │       ├── get_ipv6_neighbors()    读取邻居缓存
    │       ├── multicast_ping_v6()     组播探测
    │       ├── mdns_probe()            mDNS发现
    │       └── scan_ipv6()             综合IPv6扫描
    │
    ├── modules/vendor.py        MAC厂商识别
    │       └── identify()               OUI数据库查询
    │
    ├── modules/portscan.py      端口扫描
    │       ├── scan_port()       单端口扫描
    │       ├── grab_banner()     Banner抓取
    │       └── scan_host()       多端口扫描
    │
    ├── modules/osdetect.py      OS识别
    │       ├── get_ttl()         获取TTL值
    │       ├── guess_os()        TTL推测OS
    │       └── detect()          单主机探测
    │
    ├── data/oui.py              OUI查询核心
    │       ├── is_random_mac()   随机MAC检测
    │       ├── OUI_DB            内置数据库
    │       └── lookup()          查询接口
    │
    └── utils.py                 公共工具
            ├── get_local_ip()
            ├── resolve_hostname()
            ├── get_mac_from_arp()
            ├── refresh_arp_cache()
            └── is_windows()
```

---

---

## 🛣️ 后续计划

- 优化Linux环境下IPv6主机识别能力（开发中）
- 持续监控模式（定时扫描，检测设备上下线告警）
- Web UI面板（浏览器可视化查看扫描结果）
- Wake-on-LAN远程唤醒
- 历史扫描结果对比
- 配置文件支持（YAML/TOML）
- Traceroute路由追踪
- Python 3.9兼容性适配

---

---

## 🤝 参与贡献

 欢迎提交Issue和Pull Request！

 1.Fork 本仓库
 2.创建功能分支（git checkout -b feature/YourFeature）
 3.提交更改（git commit -m 'Add some feature'）
 4.推送到分支（git push origin feature/YourFeature）
 5.创建 Pull Request

---

---

## 📝 开源许可证

本项目基于 MIT License 许可证开源。

---

---

## ⚠️ 免责声明

本工具仅用于合法的网络管理和安全测试目的。使用者应确保在获得授权的网络环境中使用，遵守当地法律法规。因滥用本工具造成的任何后果，由使用者自行承担。
