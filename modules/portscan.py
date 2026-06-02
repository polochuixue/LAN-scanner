"""
端口扫描模块

by polochuixue
License: MIT License
Copyright (c) 2025 polochuixue
"""

import socket
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── 常见端口 -> 服务名映射 ──
WELL_KNOWN_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 80: "HTTP", 110: "POP3", 135: "MSRPC",
    139: "NetBIOS", 143: "IMAP", 443: "HTTPS", 445: "SMB",
    993: "IMAPS", 995: "POP3S", 1433: "MSSQL", 1521: "Oracle",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC",
    6379: "Redis", 8080: "HTTP-Alt", 8443: "HTTPS-Alt",
    8888: "HTTP-Alt", 9090: "Web-Console", 27017: "MongoDB",
}

# ── 默认扫描端口 ──
DEFAULT_PORTS = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143,
                 443, 445, 993, 995, 1433, 3306, 3389, 5432,
                 5900, 6379, 8080, 8443, 8888, 9090, 27017]


def grab_banner(ip: str, port: int, timeout: float = 2.0) -> str:
    """抓取端口 Banner"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))

        # 对 HTTP 端口发送请求
        if port in (80, 8080, 8443, 8888):
            sock.sendall(f"HEAD / HTTP/1.1\r\nHost: {ip}\r\n\r\n".encode())

        banner = sock.recv(1024)
        sock.close()

        text = banner.decode("utf-8", errors="ignore").strip()
        # 截断过长的 Banner
        if len(text) > 120:
            text = text[:120] + "..."
        return text if text else "-"
    except Exception:
        return "-"


def scan_port(ip: str, port: int, timeout: float = 1.0, grab: bool = True) -> dict | None:
    """
    扫描单个端口
    开放返回 dict，关闭返回 None
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()

        if result == 0:
            service = WELL_KNOWN_PORTS.get(port, "Unknown")
            banner = grab_banner(ip, port) if grab else "-"
            return {
                "port": port,
                "state": "open",
                "service": service,
                "banner": banner,
            }
    except Exception:
        pass
    return None


def scan_host(
    ip: str,
    ports: list = None,
    timeout: float = 1.0,
    workers: int = 50,
    grab_banner: bool = True,
) -> list[dict]:
    """
    扫描目标主机的多个端口
    返回开放端口信息列表
    """
    ports = ports or DEFAULT_PORTS
    open_ports = []

    print(f"  [portscan] {ip}  端口数: {len(ports)}")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(scan_port, ip, p, timeout, grab_banner): p for p in ports
        }
        for future in as_completed(futures):
            result = future.result()
            if result:
                open_ports.append(result)

    open_ports.sort(key=lambda x: x["port"])
    return open_ports


def format_results(ip: str, ports: list[dict]) -> str:
    """格式化输出扫描结果"""
    if not ports:
        return f"  {ip:<18} 无开放端口"

    lines = [f"\n  目标: {ip}\n"]
    lines.append(f"  {'端口':<8} {'状态':<8} {'服务':<16} {'Banner'}")
    lines.append("  " + "-" * 70)

    for p in ports:
        lines.append(
            f"  {p['port']:<8} {p['state']:<8} {p['service']:<16} {p['banner']}"
        )

    return "\n".join(lines)


# ── 独立运行 ──
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="端口扫描 + Banner 抓取")
    parser.add_argument("ip", help="目标 IP")
    parser.add_argument("-p", "--ports", type=str, default=None,
                        help="端口列表，逗号分隔 (默认: 常见端口)")
    parser.add_argument("-t", "--timeout", type=float, default=1.0)
    parser.add_argument("-w", "--workers", type=int, default=50)
    parser.add_argument("--no-banner", action="store_true", help="不抓取 Banner")
    args = parser.parse_args()

    ports = [int(p) for p in args.ports.split(",")] if args.ports else None
    results = scan_host(args.ip, ports, args.timeout, args.workers, not args.no_banner)
    print(format_results(args.ip, results))
