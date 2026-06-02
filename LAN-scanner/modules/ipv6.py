"""
IPv6 主机发现模块

by polochuixue
License: MIT License
Copyright (c) 2025 polochuixue
"""

import subprocess
import re
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import is_windows


# ══════════════════════════════════════
#  过滤器
# ══════════════════════════════════════

def is_multicast_mac(mac: str) -> bool:
    """检测是否为组播 MAC (33:33:xx:xx:xx:xx)"""
    return mac.upper().startswith("33:33:")


def is_multicast_ipv6(ip: str) -> bool:
    """检测是否为 IPv6 组播地址 (ff00::/8)"""
    return ip.lower().startswith("ff")


def is_loopback(ip: str) -> bool:
    return ip in ("::1", "fe80::1", "::")


def normalize_mac(mac: str) -> str:
    return mac.upper().replace("-", ":")


# ══════════════════════════════════════
#  获取默认网络接口
# ══════════════════════════════════════

def get_default_iface() -> str:
    """获取默认出站网络接口名称"""
    try:
        if is_windows():
            # Windows: 从 netsh 获取接口索引
            output = subprocess.check_output(
                ["netsh", "interface", "ipv6", "show", "route"],
                text=True, stderr=subprocess.DEVNULL, timeout=5
            )
            for line in output.splitlines():
                if "::/0" in line:
                    parts = line.split()
                    for p in parts:
                        if p.isdigit():
                            return p
        else:
            # Linux: ip route 获取默认接口
            output = subprocess.check_output(
                ["ip", "-6", "route", "show", "default"],
                text=True, stderr=subprocess.DEVNULL, timeout=5
            )
            match = re.search(r"dev\s+(\S+)", output)
            if match:
                return match.group(1)

            # 备选: 从 ip -6 addr 找有全局地址的接口
            output = subprocess.check_output(
                ["ip", "-6", "addr", "show", "scope", "global"],
                text=True, stderr=subprocess.DEVNULL, timeout=5
            )
            match = re.search(r"\d+:\s+(\S+)", output)
            if match:
                return match.group(1).replace("@", "").split(":")[0]

            # 最后: 从 /proc/net/route 找默认网卡
            with open("/proc/net/route") as f:
                for line in f:
                    fields = line.strip().split()
                    if fields[1] == "00000000":
                        return fields[0]

    except Exception:
        pass

    # Linux 常见默认网卡名
    if not is_windows():
        import glob
        for name in ["eth0", "wlan0", "ens33", "ens160", "enp0s3", "wlp2s0"]:
            if os.path.exists(f"/sys/class/net/{name}"):
                return name

    return ""


# ══════════════════════════════════════
#  IPv6 邻居缓存读取
# ══════════════════════════════════════

def get_ipv6_neighbors() -> list:
    """
    读取系统 IPv6 邻居缓存
    返回: [{"ip": "fe80::...", "mac": "AA:BB:CC:...", "state": "..."}, ...]
    """
    neighbors = []

    try:
        if is_windows():
            output = subprocess.check_output(
                ["netsh", "interface", "ipv6", "show", "neighbors"],
                text=True, stderr=subprocess.DEVNULL, timeout=10
            )

            for line in output.splitlines():
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                if len(parts) < 2:
                    continue

                ip_candidate = parts[0]
                mac_candidate = parts[1]

                if ":" not in ip_candidate:
                    continue

                ip_clean = re.sub(r"%\d+$", "", ip_candidate)

                if not re.match(r"[0-9a-fA-F]{2}(-[0-9a-fA-F]{2}){5}$", mac_candidate):
                    continue

                mac = normalize_mac(mac_candidate)

                if mac == "00:00:00:00:00:00":
                    continue
                if is_multicast_mac(mac):
                    continue
                if is_multicast_ipv6(ip_clean):
                    continue
                if is_loopback(ip_clean):
                    continue

                state = parts[2] if len(parts) > 2 else "unknown"
                neighbors.append({"ip": ip_clean, "mac": mac, "state": state})

        else:
            # Linux: ip -6 neigh show
            # 输出格式多样，兼容多种变体:
            # fe80::1 dev eth0 lladdr aa:bb:cc:dd:ee:ff router REACHABLE
            # fe80::1 dev eth0 aa:bb:cc:dd:ee:ff STALE
            # fe80::1 dev eth0 lladdr aa:bb:cc:dd:ee:ff nud reachable
            try:
                output = subprocess.check_output(
                    ["ip", "-6", "neigh", "show"],
                    text=True, stderr=subprocess.DEVNULL, timeout=10
                )
            except FileNotFoundError:
                # 某些系统用 ip6tables / ndisc6
                output = ""

            # 同时用 /proc/net/arp6 读取 (如果存在)
            if not output.strip():
                output = _read_proc_neigh6()

            for line in output.splitlines():
                parsed = _parse_neigh_line_linux(line)
                if parsed:
                    neighbors.append(parsed)

    except Exception as e:
        print(f"  [ipv6] 读取邻居缓存失败: {e}")

    return neighbors


def _parse_neigh_line_linux(line: str) -> dict | None:
    """解析 Linux ip -6 neigh 的一行"""
    parts = line.split()
    if len(parts) < 4:
        return None

    ip_str = parts[0]
    ip_clean = re.sub(r"%.*$", "", ip_str)

    if is_multicast_ipv6(ip_clean):
        return None
    if is_loopback(ip_clean):
        return None

    # 提取 MAC 地址 (lladdr 后面的 或者直接在 dev 后面的)
    mac = None
    mac_pattern = re.compile(r"([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})")

    # 尝试找 lladdr
    lladdr_idx = -1
    for i, p in enumerate(parts):
        if p == "lladdr" and i + 1 < len(parts):
            mac = normalize_mac(parts[i + 1])
            lladdr_idx = i
            break

    # 没有 lladdr 关键字，尝试直接匹配 MAC
    if mac is None:
        for p in parts[2:]:
            m = mac_pattern.match(p)
            if m:
                mac = normalize_mac(m.group(1))
                break

    if not mac or mac == "00:00:00:00:00:00":
        return None
    if is_multicast_mac(mac):
        return None

    # 提取状态
    state = parts[-1] if len(parts) > 3 else "unknown"

    # 提取接口名
    iface = ""
    for i, p in enumerate(parts):
        if p == "dev" and i + 1 < len(parts):
            iface = parts[i + 1]
            break

    return {"ip": ip_clean, "mac": mac, "state": state, "iface": iface}


def _read_proc_neigh6() -> str:
    """从 /proc/net/ndisc6 或系统工具读取 (备用)"""
    # 尝试用 ndisc6 或其他工具
    try:
        output = subprocess.check_output(
            ["ip", "-6", "neigh"],
            text=True, stderr=subprocess.DEVNULL, timeout=5
        )
        return output
    except Exception:
        return ""


# ══════════════════════════════════════
#  IPv6 组播 Ping (刷新缓存)
# ══════════════════════════════════════

def multicast_ping_v6(timeout: float = 3.0, iface: str = "") -> int:
    """
    向 ff02::1 发送 ping，刷新邻居缓存
    Linux 必须通过 -I 指定网卡接口
    """
    count = 0
    try:
        if is_windows():
            # Windows: 可以用 %* 通配接口
            output = subprocess.check_output(
                ["ping", "-n", "1", "-w", str(int(timeout * 1000)), "ff02::1"],
                text=True, stderr=subprocess.DEVNULL, timeout=timeout + 5
            )
            count = len(re.findall(r"回复自|Reply from", output))
        else:
            if not iface:
                iface = get_default_iface()

            if not iface:
                print("  [ipv6] 无法获取默认网络接口，跳过组播探测")
                return 0

            print(f"  [ipv6] 使用接口: {iface}")

            # Linux: ping -c 1 -W timeout -I interface ff02::1
            output = subprocess.check_output(
                ["ping", "-c", "1", "-W", str(int(timeout)), "-I", iface, "ff02::1"],
                text=True, stderr=subprocess.DEVNULL, timeout=timeout + 5
            )
            count = len(re.findall(r"from\s+[0-9a-f:]+", output))

    except subprocess.TimeoutExpired:
        pass
    except subprocess.CalledProcessError:
        # ping 组播地址可能返回非零退出码，但仍有响应
        pass
    except Exception as e:
        print(f"  [ipv6] 组播探测异常: {e}")

    return count


# ══════════════════════════════════════
#  Linux 补充: 用 ip neigh 触发邻居发现
# ══════════════════════════════════════

def _linux_trigger_discovery(iface: str, timeout: float = 2.0):
    """
    Linux 上用多种方式触发 IPv6 邻居发现:
    1. ping 组播地址
    2. 对已知前缀的地址做 neighbor solicitation
    """
    if not iface:
        return

    # 方式 1: 组播 ping (已在 scan_ipv6 中调用)

    # 方式 2: 尝试 ping 一些常见 IPv6 地址 (网关等)
    try:
        output = subprocess.check_output(
            ["ip", "-6", "route", "show", "default"],
            text=True, stderr=subprocess.DEVNULL, timeout=3
        )
        match = re.search(r"via\s+([0-9a-f:]+)", output)
        if match:
            gw = match.group(1)
            gw_clean = re.sub(r"%.*$", "", gw)
            subprocess.run(
                ["ping", "-c", "1", "-W", "1", "-I", iface, gw_clean],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3
            )
    except Exception:
        pass

    # 方式 3: 发送 ICMPv6 Router Solicitation
    try:
        subprocess.run(
            ["ping", "-c", "1", "-W", "1", "-I", iface, "ff02::2"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3
        )
    except Exception:
        pass


# ══════════════════════════════════════
#  mDNS 探测
# ══════════════════════════════════════

def mdns_probe(timeout: float = 3.0) -> list:
    """通过 mDNS 探测本地设备"""
    results = []
    try:
        import socket as sock_module

        MDNS_ADDR = "224.0.0.251"
        MDNS_PORT = 5353

        query = bytearray()
        query += b"\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00"
        for label in ["_services", "_dns-sd", "_udp", "local"]:
            query += bytes([len(label)]) + label.encode()
        query += b"\x00\x00\x0c\x00\x01"

        sock = sock_module.socket(sock_module.AF_INET, sock_module.SOCK_DGRAM, sock_module.IPPROTO_UDP)
        sock.setsockopt(sock_module.SOL_SOCKET, sock_module.SO_REUSEADDR, 1)
        sock.settimeout(timeout)

        try:
            sock.sendto(bytes(query), (MDNS_ADDR, MDNS_PORT))
        except Exception:
            pass

        start = time.time()
        seen = set()
        while time.time() - start < timeout:
            try:
                _, addr = sock.recvfrom(4096)
                if addr[0] not in seen and not addr[0].startswith("224."):
                    seen.add(addr[0])
                    results.append({"ip": addr[0], "source": "mDNS"})
            except Exception:
                break

        sock.close()
    except Exception:
        pass

    return results


# ══════════════════════════════════════
#  综合 IPv6 扫描
# ══════════════════════════════════════

def scan_ipv6(timeout: float = 3.0) -> list:
    """
    综合 IPv6 扫描
    返回已过滤组播地址的真实设备列表
    """
    iface = get_default_iface()

    if not is_windows():
        if iface:
            print(f"  [ipv6] 默认接口: {iface}")
        else:
            print("  [ipv6] 警告: 未能自动检测到网络接口")

    # 1. 组播探测 + 邻居触发
    print("  [ipv6] 发送链路本地组播探测...")
    responses = multicast_ping_v6(timeout, iface)
    print(f"  [ipv6] 组播响应: {responses} 个")

    # Linux 补充触发
    if not is_windows() and iface:
        _linux_trigger_discovery(iface, timeout)

    # 2. 读取邻居缓存
    print("  [ipv6] 读取 IPv6 邻居缓存...")
    neighbors = get_ipv6_neighbors()
    print(f"  [ipv6] 发现真实设备: {len(neighbors)} 个")

    # 3. mDNS
    print("  [ipv6] mDNS 服务发现...")
    mdns = mdns_probe(timeout)
    print(f"  [ipv6] mDNS 响应: {len(mdns)} 个")

    # 4. 合并去重 (按 MAC)
    devices = {}
    for n in neighbors:
        mac = n["mac"]
        if mac not in devices:
            devices[mac] = {
                "ipv6": n["ip"],
                "mac": mac,
                "state": n.get("state", ""),
                "source": "neighbor_cache",
            }

    return list(devices.values())


# ── 独立运行 ──
if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box

    console = Console()
    console.print()
    console.print(Panel("[bold]IPv6 主机发现[/bold] [dim]by polochuixue[/dim]", border_style="magenta"))
    console.print()

    results = scan_ipv6()

    if results:
        table = Table(box=box.ROUNDED, border_style="magenta", show_lines=True)
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("IPv6 地址", style="bold magenta", min_width=38)
        table.add_column("MAC 地址", style="white", min_width=19)
        table.add_column("状态", style="green")

        for idx, d in enumerate(results, 1):
            table.add_row(str(idx), d["ipv6"], d["mac"], d.get("state", "-"))

        console.print()
        console.print(table)
        console.print()
        console.print(f"  [green]✓[/green] 共发现 [bold]{len(results)}[/bold] 个 IPv6 设备\n")
    else:
        console.print("\n  [yellow]未发现 IPv6 设备[/yellow]\n")
