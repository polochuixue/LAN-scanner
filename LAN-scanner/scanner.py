#!/usr/bin/env python3
"""
局域网主机综合探测工具 v1.0
IPv4 + IPv6 双栈扫描

by polochuixue
License: MIT License
Copyright (c) 2025 polochuixue
"""

import argparse
import csv
import json
import time

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import box

from modules.discovery import scan_network
from modules.vendor import identify as vendor_identify
from modules.osdetect import detect as os_detect
from modules.portscan import scan_host as port_scan
from modules.ipv6 import scan_ipv6
from utils import get_local_ip, resolve_hostname, get_mac_from_arp, refresh_arp_cache

console = Console()


# ══════════════════════════════════════
#  工具函数
# ══════════════════════════════════════

def normalize_mac(mac: str) -> str:
    if not mac or mac == "-":
        return "-"
    return mac.upper().replace("-", ":")


def colorize_vendor(vendor: str, is_random: bool) -> Text:
    if is_random:
        return Text(f"{vendor} [随机]", style="bold yellow")
    if vendor in ("Unknown", "-"):
        return Text(vendor, style="dim")
    known = [
        "Xiaomi", "Huawei", "Apple", "Samsung", "OPPO", "vivo", "Honor",
        "OnePlus", "Google", "Microsoft", "Sony", "Nintendo", "Dell",
        "HP", "Lenovo", "Cisco", "TP-Link", "Hikvision", "ZTE", "H3C",
        "Ubiquiti", "MikroTik", "Raspberry", "Amazon", "Realme", "Intel",
    ]
    for k in known:
        if k.lower() in vendor.lower():
            return Text(vendor, style="bold cyan")
    return Text(vendor, style="white")


def colorize_os(os_guess: str) -> Text:
    if os_guess == "-" or os_guess.startswith("未知"):
        return Text(os_guess, style="dim")
    if "Windows" in os_guess:
        return Text(os_guess, style="bold blue")
    if "Linux" in os_guess or "Android" in os_guess:
        return Text(os_guess, style="bold green")
    if "macOS" in os_guess or "Apple" in os_guess:
        return Text(os_guess, style="bold white")
    return Text(os_guess, style="yellow")


def format_ports(open_ports: list) -> Text:
    """把端口信息合并到一个单元格"""
    if not open_ports:
        return Text("-", style="dim")

    parts = []
    for p in open_ports:
        part = f"{p['port']}/{p['service']}"
        banner = p.get("banner", "-")
        if banner and banner != "-":
            if len(banner) > 40:
                banner = banner[:40] + "..."
            part += f" ({banner})"
        parts.append(part)

    text = Text()
    for i, part in enumerate(parts):
        if i > 0:
            text.append("\n")
        port_str = part.split("/")[0]
        rest = part[len(port_str):]
        text.append(port_str, style="bold yellow")
        text.append(rest, style="bright_black")

    return text


def make_banner():
    title = Text()
    title.append("  LAN Scanner  ", style="bold white on dark_cyan")
    title.append(" v1.0 ", style="bold cyan")

    subtitle = Text()
    subtitle.append("  局域网主机综合探测工具  |  IPv4 + IPv6 双栈", style="dim")
    subtitle.append("\n  by polochuixue", style="dim italic")

    console.print()
    console.print(Panel(
        Text.assemble(title, "\n", subtitle),
        border_style="cyan",
        box=box.DOUBLE,
        padding=(0, 2),
    ))
    console.print()


# ══════════════════════════════════════
#  主扫描逻辑
# ══════════════════════════════════════

def run_full_scan(args):
    make_banner()

    start = time.time()
    devices = {}

    # ──────────────────────────────────
    #  Phase 1: IPv4
    # ──────────────────────────────────

    if not args.ipv6_only:
        subnet = args.subnet
        if subnet is None:
            local_ip = get_local_ip()
            parts = local_ip.split(".")
            subnet = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"

        ports = [int(p) for p in args.ports_list.split(",")] if args.ports_list else None

        info = Text()
        info.append("  子网: ", style="dim")
        info.append(f"{subnet}  ", style="bold white")
        info.append("方式: ", style="dim")
        info.append(f"{args.method}  ", style="bold white")
        info.append("并发: ", style="dim")
        info.append(f"{args.workers}  ", style="bold white")
        info.append("超时: ", style="dim")
        info.append(f"{args.timeout}s", style="bold white")
        console.print(Panel(info, title="[bold]扫描参数[/bold]", border_style="blue"))

        console.print()
        console.print("  [bold cyan]Phase 1[/bold cyan] [dim]IPv4 主机发现[/dim]")
        alive_ips = scan_network(subnet, args.method, args.timeout, args.workers, ports)
        console.print(f"  [green]✓[/green] 发现 [bold]{len(alive_ips)}[/bold] 台 IPv4 主机\n")

        refresh_arp_cache()

        console.print("  [bold cyan]Phase 2[/bold cyan] [dim]设备信息采集[/dim]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("  扫描中", total=len(alive_ips))

            for ip in alive_ips:
                progress.update(task, description=f"  [cyan]{ip}[/cyan]")

                hostname = resolve_hostname(ip)
                raw_mac = get_mac_from_arp(ip)
                mac = normalize_mac(raw_mac)
                vendor_info = vendor_identify(raw_mac)

                entry = {
                    "ipv4": ip,
                    "ipv6": [],
                    "hostname": hostname,
                    "mac": mac,
                    "vendor": vendor_info["vendor"],
                    "is_random_mac": vendor_info["is_random"],
                    "os_guess": "-",
                    "open_ports": [],
                    "source": "ipv4",
                }

                if args.os or args.full:
                    os_info = os_detect(ip, args.timeout)
                    entry["os_guess"] = os_info["os_guess"]

                if args.portscan or args.full:
                    entry["open_ports"] = port_scan(ip, ports, args.timeout)

                # 按 MAC 合并
                if mac != "-" and mac in devices:
                    devices[mac]["ipv4"] = ip
                    if hostname != "-":
                        devices[mac]["hostname"] = hostname
                    if entry["open_ports"]:
                        devices[mac]["open_ports"] = entry["open_ports"]
                    if entry["os_guess"] != "-":
                        devices[mac]["os_guess"] = entry["os_guess"]
                    devices[mac]["source"] = "ipv4+ipv6"
                else:
                    key = mac if mac != "-" else f"_no_mac_{ip}"
                    devices[key] = entry

                progress.advance(task)

        console.print()

    # ──────────────────────────────────
    #  Phase 2: IPv6
    # ──────────────────────────────────

    if args.ipv6 or args.ipv6_only:
        console.print("  [bold magenta]Phase 3[/bold magenta] [dim]IPv6 扫描[/dim]")
        console.print()

        ipv6_results = scan_ipv6(timeout=args.timeout)

        merged = 0
        new = 0
        for dev in ipv6_results:
            mac = normalize_mac(dev["mac"])
            ipv6_ip = dev["ipv6"]

            if mac in devices:
                if ipv6_ip not in devices[mac]["ipv6"]:
                    devices[mac]["ipv6"].append(ipv6_ip)
                devices[mac]["source"] = "ipv4+ipv6"
                merged += 1
            else:
                vendor_info = vendor_identify(dev["mac"])
                devices[mac] = {
                    "ipv4": "-",
                    "ipv6": [ipv6_ip],
                    "hostname": "-",
                    "mac": mac,
                    "vendor": vendor_info["vendor"],
                    "is_random_mac": vendor_info["is_random"],
                    "os_guess": "-",
                    "open_ports": [],
                    "source": "ipv6",
                }
                new += 1

        console.print(f"  [green]✓[/green] 合并 [bold]{merged}[/bold] 台  |  新增 [bold]{new}[/bold] 台纯 IPv6 设备")

    # ══════════════════════════════════════
    #  输出结果
    # ══════════════════════════════════════

    report = list(devices.values())

    def sort_key(e):
        if e["ipv4"] != "-":
            return (0, tuple(int(p) for p in e["ipv4"].split(".")))
        return (1, e["mac"])
    report.sort(key=sort_key)

    elapsed = time.time() - start

    # ── 主表格 ──
    table = Table(
        title="[bold]扫描结果[/bold]",
        box=box.ROUNDED,
        show_lines=True,
        title_style="bold white",
        border_style="bright_black",
        padding=(0, 1),
    )

    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("IPv4", style="bold green", min_width=16)
    table.add_column("IPv6", style="bold magenta", min_width=26)
    table.add_column("MAC", style="white", min_width=19)
    table.add_column("厂商", min_width=22)
    table.add_column("系统", min_width=18)
    table.add_column("开放端口", min_width=20)
    table.add_column("来源", justify="center", width=6)

    for idx, entry in enumerate(report, 1):
        ipv4 = Text(entry["ipv4"], style="bold green") if entry["ipv4"] != "-" else Text("-", style="dim")

        if entry["ipv6"]:
            ipv6_text = entry["ipv6"][0]
            if len(entry["ipv6"]) > 1:
                ipv6_text += f"  [+{len(entry['ipv6'])-1}]"
            ipv6 = Text(ipv6_text, style="magenta")
        else:
            ipv6 = Text("-", style="dim")

        mac = Text(entry["mac"], style="white") if entry["mac"] != "-" else Text("-", style="dim")
        vendor = colorize_vendor(entry["vendor"], entry["is_random_mac"])
        os_text = colorize_os(entry["os_guess"])
        ports_text = format_ports(entry["open_ports"])

        src = entry["source"]
        if src == "ipv4+ipv6":
            source = Text("v4+v6", style="bold green")
        elif src == "ipv4":
            source = Text("IPv4", style="bold blue")
        elif src == "ipv6":
            source = Text("IPv6", style="bold magenta")
        else:
            source = Text(src, style="dim")

        table.add_row(
            Text(str(idx), style="dim"),
            ipv4, ipv6, mac, vendor, os_text, ports_text, source,
        )

    console.print()
    console.print(table)

    # ── 统计面板 ──
    ipv4_count = sum(1 for e in report if e["ipv4"] != "-")
    ipv6_count = sum(1 for e in report if e["ipv6"])
    random_count = sum(1 for e in report if e["is_random_mac"])
    port_count = sum(len(e["open_ports"]) for e in report)
    vendor_set = set(
        e["vendor"] for e in report
        if e["vendor"] not in ("-", "Unknown", "Random MAC (Private/Hidden)")
    )

    stats = []
    for label, value, color in [
        ("设备", str(len(report)), "white"),
        ("IPv4", str(ipv4_count), "blue"),
        ("IPv6", str(ipv6_count), "magenta"),
        ("随机MAC", str(random_count), "yellow"),
        ("厂商", str(len(vendor_set)), "cyan"),
        ("端口", str(port_count), "green"),
        ("耗时", f"{elapsed:.1f}s", "white"),
    ]:
        t = Text()
        t.append(f"{label}\n", style="dim")
        t.append(f" {value}", style=f"bold {color}")
        stats.append(Panel(t, border_style=color if color != "white" else "bright_black", width=13))

    console.print()
    console.print(Columns(stats, equal=True, expand=True))

    # ── 厂商分布 ──
    vendor_stats = {}
    for e in report:
        v = e["vendor"]
        if v not in ("-", "Unknown", "Random MAC (Private/Hidden)"):
            vendor_stats[v] = vendor_stats.get(v, 0) + 1

    if vendor_stats:
        vtable = Table(
            title="[bold]厂商分布[/bold]",
            box=box.SIMPLE_HEAVY,
            border_style="bright_black",
            title_style="bold white",
            show_header=True,
            padding=(0, 1),
        )
        vtable.add_column("厂商", style="cyan", min_width=22)
        vtable.add_column("数量", justify="right", style="white", width=6)
        vtable.add_column("", style="green")

        max_c = max(vendor_stats.values())
        for name, count in sorted(vendor_stats.items(), key=lambda x: -x[1]):
            bar_len = int(count / max_c * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            vtable.add_row(name, str(count), Text(bar, style="green"))

        console.print()
        console.print(vtable)

    # ── 完成 ──
    console.print()
    console.print(Panel(
        Text(f"  扫描完成  |  {len(report)} 台设备  |  {elapsed:.1f}s\n  by polochuixue", style="bold green", justify="center"),
        border_style="green",
        box=box.HEAVY,
    ))
    console.print()

    # ── 导出 ──
    if args.export:
        export_file = args.export
        if export_file.endswith(".json"):
            out = []
            for e in report:
                entry_out = dict(e)
                entry_out["ipv6"] = e["ipv6"][0] if e["ipv6"] else "-"
                out.append(entry_out)
            with open(export_file, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
        else:
            with open(export_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["IPv4", "IPv6", "MAC", "Vendor", "Random", "OS", "Ports"])
                for e in report:
                    ipv6_str = "; ".join(e["ipv6"]) if e["ipv6"] else "-"
                    port_str = "; ".join(
                        f"{p['port']}/{p['service']}" for p in e["open_ports"]
                    ) if e["open_ports"] else "-"
                    writer.writerow([
                        e["ipv4"], ipv6_str, e["mac"], e["vendor"],
                        "Y" if e["is_random_mac"] else "N",
                        e["os_guess"], port_str,
                    ])
        console.print(f"  [green]✓[/green] 已导出: [bold]{export_file}[/bold]\n")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="局域网主机综合探测工具 v1.0 (IPv4 + IPv6) by polochuixue",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("subnet", nargs="?", default=None)
    parser.add_argument("-m", "--method", default="ping",
                        choices=["ping", "tcp", "all"])
    parser.add_argument("-t", "--timeout", type=float, default=1.0)
    parser.add_argument("-w", "--workers", type=int, default=100)
    parser.add_argument("--os", action="store_true")
    parser.add_argument("--portscan", action="store_true")
    parser.add_argument("--ports-list", type=str, default=None)
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--ipv6", action="store_true")
    parser.add_argument("--ipv6-only", action="store_true")
    parser.add_argument("--export", type=str, default=None)

    args = parser.parse_args()
    run_full_scan(args)


if __name__ == "__main__":
    main()
