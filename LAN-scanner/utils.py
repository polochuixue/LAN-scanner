"""
公共工具函数

by polochuixue
License: MIT License
Copyright (c) 2025 polochuixue
"""

import socket
import platform
import subprocess
import re


def get_local_ip() -> str:
    """获取本机局域网 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def resolve_hostname(ip: str) -> str:
    """反向解析主机名"""
    try:
        return socket.gethostbyaddr(ip)[0]
    except socket.herror:
        return "-"


def _build_arp_cache() -> dict:
    """
    预加载完整 ARP 缓存表，返回 {ip: mac} 字典
    比逐个查询 arp -n <ip> 更可靠
    """
    cache = {}
    try:
        if is_windows():
            output = subprocess.check_output(
                ["arp", "-a"], text=True, stderr=subprocess.DEVNULL
            )
            # Windows 格式:
            #   Internet Address      Physical Address      Type
            #   192.168.3.1           c0-b4-7d-41-f8-31     dynamic
            for line in output.splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    ip_candidate = parts[0]
                    mac_candidate = parts[1]
                    # 验证是否为合法 IP + MAC
                    if (
                        re.match(r"\d+\.\d+\.\d+\.\d+$", ip_candidate)
                        and re.match(
                            r"[0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:]"
                            r"[0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:]"
                            r"[0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}$",
                            mac_candidate,
                        )
                    ):
                        cache[ip_candidate] = mac_candidate.upper()
        else:
            output = subprocess.check_output(
                ["arp", "-n"], text=True, stderr=subprocess.DEVNULL
            )
            # Linux 格式:
            #   192.168.3.1       ether   c0:b4:7d:41:f8:31   C  eth0
            for line in output.splitlines():
                parts = line.split()
                if len(parts) >= 3 and parts[1] == "ether":
                    ip_candidate = parts[0]
                    mac_candidate = parts[2]
                    if re.match(r"\d+\.\d+\.\d+\.\d+$", ip_candidate):
                        cache[ip_candidate] = mac_candidate.upper()
    except Exception:
        pass

    return cache


# 缓存实例（模块加载时构建一次）
_arp_cache = None


def get_mac_from_arp(ip: str) -> str:
    """从 ARP 缓存读取 MAC 地址"""
    global _arp_cache
    if _arp_cache is None:
        _arp_cache = _build_arp_cache()
    return _arp_cache.get(ip, "-")


def refresh_arp_cache():
    """强制刷新 ARP 缓存"""
    global _arp_cache
    _arp_cache = None
    _arp_cache = _build_arp_cache()


def is_windows() -> bool:
    return platform.system().lower() == "windows"
