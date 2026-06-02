"""
MAC 厂商识别模块

by polochuixue
License: MIT License
Copyright (c) 2025 polochuixue
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.oui import lookup, get_db_stats


def identify(mac: str) -> dict:
    return lookup(mac)


def identify_batch(mac_list: list) -> list:
    return [identify(mac) for mac in mac_list]


if __name__ == "__main__":
    import argparse
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box

    console = Console()

    parser = argparse.ArgumentParser(description="MAC 厂商识别")
    parser.add_argument("mac", nargs="*", help="MAC 地址")
    parser.add_argument("--stats", action="store_true", help="显示数据库统计")
    args = parser.parse_args()

    if args.stats:
        stats = get_db_stats()
        info = Text()
        info.append("  内置记录:  ", style="dim")
        info.append(f"{stats['builtin']}\n", style="bold cyan")
        info.append("  IEEE 记录: ", style="dim")
        info.append(f"{stats['ieee']}\n", style="bold cyan")
        info.append("  合计:      ", style="dim")
        info.append(f"{stats['total']}\n", style="bold white")
        info.append("  IEEE 数据: ", style="dim")
        if stats["has_ieee"]:
            info.append("已加载", style="bold green")
        elif stats["has_txt"]:
            info.append("oui.txt 已就绪 (运行 fetch_oui.py 解析)", style="yellow")
        else:
            info.append("未找到", style="bold red")

        console.print()
        console.print(Panel(info, title="[bold]OUI 数据库统计[/bold]", border_style="cyan"))
        console.print()

    if args.mac:
        results = identify_batch(args.mac)

        table = Table(box=box.ROUNDED, border_style="cyan", show_lines=True)
        table.add_column("MAC 地址", style="bold white", min_width=20)
        table.add_column("厂商", min_width=25)
        table.add_column("类型", justify="center")

        for r in results:
            if r["is_random"]:
                vendor = Text(r["vendor"], style="bold yellow")
                tag = Text("随机MAC", style="yellow")
            elif r["vendor"] == "Unknown":
                vendor = Text(r["vendor"], style="dim")
                tag = Text("未识别", style="red")
            else:
                vendor = Text(r["vendor"], style="bold cyan")
                tag = Text("真实MAC", style="green")

            table.add_row(r["mac"], vendor, tag)

        console.print()
        console.print(table)
        console.print()
