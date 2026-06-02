"""
主机存活探测模块

by polochuixue
License: MIT License
Copyright (c) 2025 polochuixue
"""

import subprocess
import socket
import ipaddress
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_local_ip, is_windows


def ping(ip: str, timeout: float = 1.0) -> bool:
    """ICMP Ping 探测"""
    param = "-n" if is_windows() else "-c"
    timeout_flag = "-w" if is_windows() else "-W"
    try:
        result = subprocess.run(
            ["ping", param, "1", timeout_flag, str(int(timeout)), ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except Exception:
        return False


def tcp_connect(ip: str, ports: list = None, timeout: float = 1.0) -> bool:
    """TCP 端口探测"""
    ports = ports or [80, 443, 22, 445, 139, 3389, 8080, 135]
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            if sock.connect_ex((ip, port)) == 0:
                sock.close()
                return True
            sock.close()
        except Exception:
            continue
    return False


def scan_host(ip, method="ping", timeout=1.0, ports=None) -> str | None:
    """扫描单个主机，存活返回 IP，否则返回 None"""
    ip_str = str(ip)
    if method == "ping":
        return ip_str if ping(ip_str, timeout) else None
    elif method == "tcp":
        return ip_str if tcp_connect(ip_str, ports, timeout) else None
    elif method == "all":
        if ping(ip_str, timeout) or tcp_connect(ip_str, ports, timeout):
            return ip_str
    return None


def scan_network(
    subnet: str,
    method: str = "ping",
    timeout: float = 1.0,
    workers: int = 100,
    ports: list = None,
) -> list[str]:
    """
    扫描整个子网，返回存活主机 IP 列表
    """
    try:
        network = ipaddress.ip_network(subnet, strict=False)
    except ValueError as e:
        print(f"[!] 无效子网: {e}")
        return []

    hosts = list(network.hosts())
    alive = []
    done = 0
    total = len(hosts)

    print(f"  [discovery] 目标: {total} | 方式: {method} | 并发: {workers}")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(scan_host, ip, method, timeout, ports): ip for ip in hosts
        }
        for future in as_completed(futures):
            done += 1
            print(f"\r  [discovery] 进度: {done}/{total}", end="", flush=True)
            result = future.result()
            if result:
                alive.append(result)

    print()
    alive.sort(key=lambda x: tuple(int(p) for p in x.split(".")))
    return alive


# ── 独立运行 ──
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="主机存活探测")
    parser.add_argument("subnet", help="子网 CIDR，如 192.168.1.0/24")
    parser.add_argument("-m", "--method", default="ping", choices=["ping", "tcp", "all"])
    parser.add_argument("-t", "--timeout", type=float, default=1.0)
    parser.add_argument("-w", "--workers", type=int, default=100)
    parser.add_argument("-p", "--ports", type=str, default=None)
    args = parser.parse_args()

    ports = [int(p) for p in args.ports.split(",")] if args.ports else None
    result = scan_network(args.subnet, args.method, args.timeout, args.workers, ports)

    print(f"\n  存活主机: {len(result)}")
    for ip in result:
        print(f"    {ip}")
