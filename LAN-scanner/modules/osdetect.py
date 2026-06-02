"""
操作系统识别模块（基于 TTL 推测）

by polochuixue
License: MIT License
Copyright (c) 2025 polochuixue
"""

import subprocess
import re
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import is_windows


# ── TTL -> OS 映射表 ──
TTL_OS_MAP = [
    (64,   "Linux / macOS / Android"),
    (128,  "Windows"),
    (254,  "Solaris / AIX / 网络设备"),
    (255,  "Cisco / BSD / 网络设备"),
]


def get_ttl(ip: str, timeout: float = 2.0) -> int | None:
    """通过 ping 获取 TTL 值"""
    param = "-n" if is_windows() else "-c"
    timeout_flag = "-w" if is_windows() else "-W"
    try:
        output = subprocess.check_output(
            ["ping", param, "1", timeout_flag, str(int(timeout)), ip],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        # Windows: TTL=64  Linux: ttl=64
        match = re.search(r"[Tt][Tt][Ll][=:]?\s*(\d+)", output)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return None


def guess_os(ttl: int) -> str:
    """根据 TTL 推测操作系统"""
    if ttl is None:
        return "未知 (主机不可达)"

    # TTL 每经过一跳减 1，所以找最近的基值
    best_match = "未知"
    best_diff = 999

    for base_ttl, os_name in TTL_OS_MAP:
        if ttl <= base_ttl:
            diff = base_ttl - ttl
            if diff < best_diff:
                best_diff = diff
                best_match = os_name

    return best_match


def detect(ip: str, timeout: float = 2.0) -> dict:
    """
    探测单个主机的 OS
    返回: {"ip": "...", "ttl": ..., "os_guess": "..."}
    """
    ttl = get_ttl(ip, timeout)
    os_guess = guess_os(ttl)
    return {"ip": ip, "ttl": ttl, "os_guess": os_guess}


def detect_batch(
    ip_list: list[str],
    timeout: float = 2.0,
    workers: int = 30,
) -> list[dict]:
    """批量探测"""
    results = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(detect, ip, timeout): ip for ip in ip_list}
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda x: tuple(int(p) for p in x["ip"].split(".")))
    return results


def format_result(info: dict) -> str:
    ttl_str = str(info["ttl"]) if info["ttl"] else "-"
    return f"  {info['ip']:<18} TTL={ttl_str:<6} {info['os_guess']}"


# ── 独立运行 ──
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TTL 操作系统识别")
    parser.add_argument("ips", nargs="+", help="目标 IP 地址")
    parser.add_argument("-t", "--timeout", type=float, default=2.0)
    args = parser.parse_args()

    results = detect_batch(args.ips, args.timeout)
    print()
    print(f"  {'IP 地址':<18} {'TTL':<8} {'推测系统'}")
    print("  " + "-" * 55)
    for r in results:
        print(format_result(r))
    print()
