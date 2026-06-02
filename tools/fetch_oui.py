#!/usr/bin/env python3
"""
OUI 解析工具（终极版）
用二进制模式读取，绕开所有编码问题

by polochuixue

用法:
  1. 浏览器打开 https://standards-oui.ieee.org/oui/oui.txt
  2. Ctrl+S 保存到 data/oui.txt (确认 > 20MB)
  3. python tools/fetch_oui.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUI_TXT = os.path.join(ROOT, "data", "oui.txt")
OUI_PY = os.path.join(ROOT, "data", "oui_ieee.py")

# 最低文件大小 (正常 oui.txt 约 25~30MB)
MIN_SIZE = 5 * 1024 * 1024  # 5MB


def parse_hex_line(raw: bytes) -> tuple:
    """
    从原始字节行中提取 MAC 前缀和厂商名
    不依赖编码，直接操作字节
    """
    # 找到 (hex) 标记
    idx = raw.find(b"(hex)")
    if idx < 0:
        return None

    # 提取 (hex) 前面的内容，取最后 8 字节作为 MAC: XX-XX-XX
    before = raw[:idx].rstrip()
    if len(before) < 8:
        return None

    mac_part = before[-8:]  # 取最后 8 字符: "28-6F-B9"
    if mac_part[2:3] != b"-" or mac_part[5:6] != b"-":
        return None

    # 验证是合法的十六进制
    prefix_str = mac_part.decode("ascii", errors="ignore").replace("-", "")
    if len(prefix_str) != 6:
        return None
    try:
        int(prefix_str, 16)
    except ValueError:
        return None

    # 提取厂商名: (hex) 后面的内容
    after = raw[idx + 5:]  # 跳过 "(hex)"
    vendor = after.decode("utf-8", errors="ignore").strip()

    if not vendor:
        return None

    return (prefix_str.upper(), vendor)


def main():
    # ── 检查文件 ──
    if not os.path.exists(OUI_TXT):
        print("\n  [!] 未找到 data/oui.txt")
        print("  请用浏览器打开以下地址，按 Ctrl+S 保存到 data/oui.txt:")
        print("  https://standards-oui.ieee.org/oui/oui.txt\n")
        return False

    size = os.path.getsize(OUI_TXT)
    size_mb = size / 1024 / 1024
    print(f"\n  文件: {OUI_TXT}")
    print(f"  大小: {size_mb:.1f} MB")

    if size < MIN_SIZE:
        print(f"\n  [!] 警告: 文件只有 {size_mb:.1f} MB，正常应 > 20 MB")
        print("  下载可能不完整，但会尝试解析...\n")

    # ── 二进制模式解析 ──
    print("  解析中 (二进制模式)...\n")

    oui = {}
    total = 0
    matched = 0
    first_match_raw = None

    with open(OUI_TXT, "rb") as f:
        for raw_line in f:
            total += 1
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            result = parse_hex_line(raw_line)
            if result:
                prefix, vendor = result
                if prefix not in oui:
                    oui[prefix] = vendor
                    matched += 1
                    if first_match_raw is None:
                        first_match_raw = raw_line

    print(f"  总行数:   {total}")
    print(f"  解析记录: {len(oui)}")

    # ── 调试: 如果匹配数为 0，打印详细信息 ──
    if not oui:
        print("\n  [!] 未解析到任何记录，进入调试模式:\n")

        # 打印文件的原始字节 (前 500 字节)
        print("  文件原始字节 (前 500 字节):")
        with open(OUI_TXT, "rb") as f:
            head = f.read(500)
        # 每行打印 40 字节的 hex dump
        for i in range(0, min(len(head), 200), 40):
            chunk = head[i:i+40]
            hex_str = " ".join(f"{b:02x}" for b in chunk[:20])
            ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk[:20])
            print(f"    {i:04x}: {hex_str:<60} {ascii_str}")

        print("\n  文件前 10 行 (原始):")
        with open(OUI_TXT, "rb") as f:
            for i, raw in enumerate(f):
                if i >= 10:
                    break
                print(f"    [{i}] {repr(raw[:100])}")

        # 尝试找到第一个包含 (hex) 的行
        print("\n  搜索第一个 (hex) 行:")
        with open(OUI_TXT, "rb") as f:
            for i, raw in enumerate(f):
                if b"(hex)" in raw:
                    print(f"    行号: {i+1}")
                    print(f"    原始: {repr(raw[:120])}")
                    print(f"    hex:  {' '.join(f'{b:02x}' for b in raw[:60])}")

                    # 尝试解析
                    result = parse_hex_line(raw.strip())
                    print(f"    解析: {result}")
                    break

        print()
        return False

    # ── 输出统计 ──
    # 厂商数量统计
    vendors = {}
    for v in oui.values():
        vendors[v] = vendors.get(v, 0) + 1

    top = sorted(vendors.items(), key=lambda x: -x[1])[:10]

    print(f"\n  Top 10 厂商:")
    for name, count in top:
        print(f"    {count:>5}  {name}")

    # ── 写入 Python 文件 ──
    print(f"\n  写入 {OUI_PY} ...")

    with open(OUI_PY, "w", encoding="utf-8") as f:
        f.write(f'"""IEEE OUI: {len(oui)} records"""\n\nOUI_IEEE = {{\n')
        for k in sorted(oui):
            v = oui[k].replace("\\", "\\\\").replace('"', '\\"')
            f.write(f'    "{k}": "{v}",\n')
        f.write("}\n")

    out_kb = os.path.getsize(OUI_PY) / 1024
    print(f"\n  完成!")
    print(f"  记录:     {len(oui)}")
    print(f"  厂商数:   {len(vendors)}")
    print(f"  输出文件: oui_ieee.py ({out_kb:.0f} KB)\n")
    return True


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
