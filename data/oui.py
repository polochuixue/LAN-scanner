"""
MAC OUI 厂商识别模块

by polochuixue
License: MIT License
Copyright (c) 2025 polochuixue
"""

import os
import re
import importlib.util

_DIR = os.path.dirname(os.path.abspath(__file__))
_PY = os.path.join(_DIR, "oui_ieee.py")
_TXT = os.path.join(_DIR, "oui.txt")

_PAT = re.compile(
    r"^([0-9A-Fa-f]{2})-([0-9A-Fa-f]{2})-([0-9A-Fa-f]{2})"
    r"\s+$$hex$$\s+(.+)"
)


def is_random_mac(mac: str) -> bool:
    if not mac or mac == "-":
        return False
    c = mac.upper().replace(":", "").replace("-", "")
    if len(c) < 12:
        return False
    try:
        b = int(c[0:2], 16)
    except ValueError:
        return False
    if b == 0x00 or b == 0xFF:
        return False
    return bool(b & 0x02)


_ieee = {}
_loaded = False


def _load_ieee():
    global _ieee, _loaded
    if _loaded:
        return
    _loaded = True

    # 优先: 加载预编译 py
    if os.path.exists(_PY):
        try:
            spec = importlib.util.spec_from_file_location("oui_ieee", _PY)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            _ieee = getattr(mod, "OUI_IEEE", {})
            if _ieee:
                return
        except Exception:
            pass

    # 备选: 二进制模式解析 txt
    if os.path.exists(_TXT):
        try:
            with open(_TXT, "rb") as f:
                for raw in f:
                    raw = raw.strip()
                    if b"(hex)" not in raw:
                        continue
                    idx = raw.find(b"(hex)")
                    before = raw[:idx].rstrip()
                    if len(before) < 8:
                        continue
                    mac_part = before[-8:]
                    if mac_part[2:3] != b"-" or mac_part[5:6] != b"-":
                        continue
                    try:
                        prefix = mac_part.decode("ascii").replace("-", "").upper()
                        int(prefix, 16)
                    except (ValueError, UnicodeDecodeError):
                        continue
                    vendor = raw[idx + 5:].decode("utf-8", errors="ignore").strip()
                    if vendor and prefix not in _ieee:
                        _ieee[prefix] = vendor
        except Exception:
            pass

# ═══ 内置数据库 (兜底) ═══

OUI_DB = {
    "5425EA": "Xiaomi", "286F40": "Xiaomi", "7CC294": "Xiaomi",
    "7451BA": "Xiaomi", "08B4B1": "Xiaomi", "584146": "Xiaomi",
    "DCD2FC": "Xiaomi", "2CD05A": "Xiaomi", "D4970B": "Xiaomi",
    "64B473": "Xiaomi", "9C99A0": "Xiaomi", "C46AB7": "Xiaomi",
    "CCEB5E": "Xiaomi", "B8EA98": "Xiaomi", "DC6AE7": "Xiaomi",
    "7CA449": "Xiaomi", "F41A9C": "Xiaomi", "8CD0B2": "Xiaomi",
    "C8BF4C": "Xiaomi", "98FA9B": "Xiaomi",
    "9CB2B8": "Huawei", "00E0FC": "Huawei", "4846FB": "Huawei",
    "CC53B5": "Huawei", "88C397": "Huawei", "E0247F": "Huawei",
    "582AF7": "Huawei", "20F3A3": "Huawei", "E00630": "Huawei",
    "D8DAF1": "Huawei", "54443B": "Huawei", "5C7075": "Huawei",
    "782DAD": "Huawei", "D06158": "Huawei", "244BF1": "Huawei",
    "AC9073": "Huawei", "FC1D3A": "Huawei", "E4BEFB": "Huawei",
    "58F8D7": "Huawei", "9CDBAF": "Huawei", "0C2E57": "Huawei",
    "E8D775": "Huawei", "940EE7": "Huawei", "A8B271": "Huawei",
    "F0A0B1": "Huawei", "404F42": "Huawei", "C04E8A": "Huawei",
    "EC1A02": "Huawei", "F8DE73": "Huawei", "6001B1": "Huawei",
    "2C9452": "Huawei", "ECA62F": "Huawei",
    "7066B9": "Huawei Device", "C4A1AE": "Huawei Device",
    "38FC34": "Huawei Device", "3CF692": "Huawei Device",
    "081AFD": "Huawei Device", "C0BFAC": "Huawei Device",
    "44272E": "Huawei Device", "E8FF98": "Huawei Device",
    "241551": "Huawei Device", "58957E": "Huawei Device",
    "AC3184": "Huawei Device", "503F50": "Huawei Device",
    "0CBEF1": "Huawei Device", "AC936A": "Huawei Device",
    "38A44B": "Huawei Device",
    "009EC8": "Honor", "0CB815": "Honor", "0CB983": "Honor",
    "2CB301": "Honor", "40D4F6": "Honor",
    "E44097": "OPPO", "DCB4CA": "OPPO", "9497AE": "OPPO",
    "0CBD75": "OPPO", "D4BAFA": "OPPO", "74D558": "OPPO",
    "BC64D9": "OPPO", "BCE8FA": "OPPO",
    "E8AA59": "vivo", "8C0EE3": "vivo", "A4E9A3": "vivo",
    "64EC65": "vivo", "6CD199": "vivo",
    "94659C": "OnePlus", "9809CF": "OnePlus", "ACC048": "OnePlus",
    "2C41A1": "TP-Link", "5C6A7D": "TP-Link", "B09575": "TP-Link",
    "EC172F": "TP-Link", "30B49E": "TP-Link", "68DDB7": "TP-Link",
    "14D864": "TP-Link", "AC84C6": "TP-Link",
    "0025B5": "Hikvision", "C056E3": "Hikvision", "0C75D2": "Hikvision",
    "548C81": "Hikvision", "244845": "Hikvision", "ECC89C": "Hikvision",
    "8CE748": "Hikvision", "2428FD": "Hikvision", "ACB92F": "Hikvision",
    "D4E853": "Hikvision", "240F9B": "Hikvision", "C06DED": "Hikvision",
    "2432AE": "Hikvision", "E0BAAD": "Hikvision", "E0CA3C": "Hikvision",
    "DC07F8": "Hikvision", "64DB8B": "Hikvision", "94E1AC": "Hikvision",
    "5803FB": "Hikvision", "4447CC": "Hikvision", "98DF82": "Hikvision",
    "BCAD28": "Hikvision",
    "F8CFC5": "ZTE", "587F66": "ZTE", "C0B47D": "ZTE",
    "F01B24": "ZTE", "98EE8C": "ZTE", "90C710": "ZTE",
    "DC5193": "ZTE", "F42E48": "ZTE", "203AEB": "ZTE",
    "F43A7B": "ZTE", "689E29": "ZTE", "C4EBFF": "ZTE",
    "887B2C": "ZTE", "ACAD4B": "ZTE", "5CBBEE": "ZTE",
    "D8A0E8": "ZTE", "BCF88B": "ZTE", "CC29BD": "ZTE",
    "3CA7AE": "ZTE", "3CF9F0": "ZTE", "6877DA": "ZTE",
    "301F48": "ZTE",
    "706655": "H3C", "3C8C40": "H3C", "04A959": "H3C",
    "708185": "H3C", "148477": "H3C", "14962D": "H3C",
    "E878EE": "H3C", "8C946A": "H3C", "982044": "H3C",
    "7CDE78": "H3C",
    "78465F": "FiberHome", "3086F1": "FiberHome", "7CC74A": "FiberHome",
    "ECE6A2": "FiberHome", "ACCB36": "FiberHome",
    "3C22FB": "Apple", "A483E7": "Apple", "F0D4F6": "Apple",
    "F0EE7A": "Apple", "58AD12": "Apple", "60FDA6": "Apple",
    "80A997": "Apple", "348C5E": "Apple", "201582": "Apple",
    "40921A": "Apple", "10E2C9": "Apple", "A4FC14": "Apple",
    "A81AF1": "Apple", "CC08FA": "Apple", "909B6F": "Apple",
    "7473B4": "Apple", "308216": "Apple", "7C296F": "Apple",
    "40EDCF": "Apple", "8C986B": "Apple", "1C8682": "Apple",
    "8054E3": "Apple", "B8144D": "Apple", "EC28D3": "Apple",
    "086518": "Apple", "2C57CE": "Apple", "B067B5": "Apple",
    "5C5284": "Apple", "C0956D": "Apple", "3C39C8": "Apple",
    "A8ABB5": "Apple", "5864C4": "Apple",
    "641B2F": "Samsung", "9C73B1": "Samsung", "388A06": "Samsung",
    "48BCE1": "Samsung", "D0D003": "Samsung", "842289": "Samsung",
    "80398C": "Samsung", "980D6F": "Samsung", "240935": "Samsung",
    "801970": "Samsung",
    "D0431E": "Dell", "00C04F": "Dell", "00B0D0": "Dell",
    "0019B9": "Dell", "001AA0": "Dell", "002564": "Dell",
    "A4BADB": "Dell", "782BCB": "Dell", "14FEB5": "Dell",
    "180373": "Dell", "74867A": "Dell", "204747": "Dell",
    "000BDB": "Dell", "00123F": "Dell", "A41F72": "Dell",
    "001C23": "Dell", "847BEB": "Dell", "989096": "Dell",
    "801844": "Dell", "9840BB": "Dell", "D481D7": "Dell",
    "54BF64": "Dell", "CCC5E5": "Dell", "4CD98F": "Dell",
    "DCF401": "Dell", "6C2B59": "Dell", "C8F750": "Dell",
    "98E743": "Dell", "185A58": "Dell", "D08E79": "Dell",
    "B44506": "Dell", "E0D848": "Dell", "04BF1B": "Dell",
    "001977": "Extreme Networks", "08EA44": "Extreme Networks",
    "F4EAB5": "Extreme Networks", "B87CF2": "Extreme Networks",
    "E0A129": "Extreme Networks", "A8C647": "Extreme Networks",
    "A473AB": "Extreme Networks", "0C9B78": "Extreme Networks",
    "A4C7F6": "Extreme Networks", "B42D56": "Extreme Networks",
    "887E25": "Extreme Networks",
    "B05B99": "Sagemcom", "ACD75B": "Sagemcom", "CC00F1": "Sagemcom",
    "E80AB9": "Cisco", "481BA4": "Cisco", "6C03B5": "Cisco",
    "908855": "Cisco", "687161": "Cisco", "4CEC0F": "Cisco",
    "5C64F1": "Cisco", "5C3E06": "Cisco", "C828E5": "Cisco",
    "D009C8": "Cisco", "44643C": "Cisco", "24161B": "Cisco",
    "9CE330": "Cisco Meraki", "B4DF91": "Cisco Meraki",
    "B8AB61": "Cisco Meraki", "08F1B3": "Cisco Meraki",
    "644ED7": "HP", "7C4D8F": "HP", "5C60BA": "HP",
    "E4F27C": "Juniper", "60C78D": "Juniper", "3C08CD": "Juniper",
    "485A0D": "Juniper", "84B59C": "Juniper", "5C4527": "Juniper",
    "EC3EF7": "Juniper", "002159": "Juniper", "00239C": "Juniper",
    "50C58D": "Juniper", "28C0DA": "Juniper", "288A1C": "Juniper",
    "40A677": "Juniper", "D818D3": "Juniper", "F04B3A": "Juniper",
    "C042D0": "Juniper", "001BC0": "Juniper", "44ECCE": "Juniper",
    "CCE194": "Juniper", "E45D37": "Juniper", "94F7AD": "Juniper",
    "784F9B": "Juniper", "88D98F": "Juniper", "78507C": "Juniper",
    "F07CC7": "Juniper", "000585": "Juniper", "889009": "Juniper",
    "00CC34": "Juniper", "E030F9": "Juniper", "204E71": "Juniper",
    "D404FF": "Juniper", "84C1C1": "Juniper", "4C734F": "Juniper",
    "D45A3F": "Juniper", "04698F": "Juniper", "7CE2CA": "Juniper",
    "00090F": "Fortinet", "7478A6": "Fortinet", "84398F": "Fortinet",
    "F09FC2": "Ubiquiti", "802AA8": "Ubiquiti", "788A20": "Ubiquiti",
    "7483C2": "Ubiquiti", "E063DA": "Ubiquiti", "245A4C": "Ubiquiti",
    "602232": "Ubiquiti", "E43883": "Ubiquiti",
    "FC59C0": "Arista",
    "B827EB": "Raspberry Pi", "DCA632": "Raspberry Pi",
    "D83ADD": "Raspberry Pi",
    "000C29": "VMware", "005056": "VMware", "080027": "VirtualBox",
    "525400": "QEMU/KVM",
    "10061C": "Espressif", "D48AFC": "Espressif", "E465B8": "Espressif",
    "48E729": "Espressif", "80646F": "Espressif", "348518": "Espressif",
    "B48A0A": "Espressif",
    "601AC7": "Nintendo", "BC9EBB": "Nintendo",
    "40F3B0": "Texas Instruments", "149CEF": "Texas Instruments",
    "80C41B": "Texas Instruments", "3468B5": "Texas Instruments",
    "2CAB33": "Texas Instruments", "28B5E8": "Texas Instruments",
    "3CE064": "Texas Instruments", "E0928F": "Texas Instruments",
    "CC037B": "Texas Instruments",
    "444988": "Intel", "A002A5": "Intel", "E4C767": "Intel",
    "102E00": "Intel", "203A43": "Intel", "C0A5E8": "Intel",
    "906584": "Intel", "28C5D2": "Intel", "C43D1A": "Intel",
    "04E8B9": "Intel", "E02E0B": "Intel", "581CF8": "Intel",
    "AC198E": "Intel", "C85EA9": "Intel",
    "90ECE3": "Nokia", "B851A9": "Nokia", "5C76D5": "Nokia",
    "8C7A00": "Nokia", "40A53B": "Nokia",
    "286FB9": "Nokia Shanghai Bell", "500238": "Nokia Shanghai Bell",
    "80AB4D": "Nokia Solutions and Networks",
    "FC84A7": "Murata", "2CD1C6": "Murata", "5026EF": "Murata",
    "A0CDF3": "Murata",
    "F0748D": "Ruijie", "10823D": "Ruijie",
    "CC40D0": "Netgear",
    "1CBDB9": "D-Link", "28107B": "D-Link", "340804": "D-Link",
    "D077CE": "Edgecore",
    "7085C2": "Lenovo", "CC3D82": "Lenovo", "9CB654": "Lenovo",
    "18A905": "Lenovo", "48C35A": "Lenovo",
    "5016F4": "Motorola (Lenovo)", "C4A052": "Motorola (Lenovo)",
    "F46412": "Sony Interactive", "2C9E00": "Sony Interactive",
    "AC800A": "Sony",
    "70F8AE": "Microsoft", "201642": "Microsoft", "C461C7": "Microsoft",
    "E04735": "Ericsson",
    "C08F20": "Skyworth", "08FF24": "Skyworth", "90B67A": "Skyworth",
    "249AC8": "Skyworth", "28C01B": "Skyworth", "E028B1": "Skyworth",
    "303180": "Skyworth",
    "60706C": "Google", "C82ADD": "Google",
    "10C4CA": "HUMAX",
    "E001C7": "Gaoshengda", "84C8A0": "Gaoshengda",
    "843E1D": "Gaoshengda", "A8169D": "Gaoshengda",
    "287E80": "Gaoshengda",
    "C4A64E": "Quectel", "B4EDD5": "Quectel", "34873D": "Quectel",
    "C44137": "Quectel", "EC1D9E": "Quectel",
    "AC5AF0": "LG Electronics",
    "FC65DE": "Amazon", "F0272D": "Amazon", "A002DC": "Amazon",
    "842859": "Amazon", "2873F6": "Amazon", "E0CB1D": "Amazon",
    "FCD749": "Amazon", "6C0C9A": "Amazon", "089115": "Amazon",
    "74D423": "Amazon", "ECA138": "Amazon", "E0F728": "Amazon",
    "0891A3": "Amazon",
}


# ═══ 对外接口 ═══

def lookup(mac: str) -> dict:
    if not mac or mac == "-":
        return {"mac": mac or "-", "vendor": "-", "is_random": False}

    clean = mac.upper().replace(":", "").replace("-", "")
    prefix = clean[:6]

    if is_random_mac(mac):
        return {"mac": mac.upper(), "vendor": "Random MAC (Private/Hidden)", "is_random": True}

    _load_ieee()
    if prefix in _ieee:
        return {"mac": mac.upper(), "vendor": _ieee[prefix], "is_random": False}
    if prefix in OUI_DB:
        return {"mac": mac.upper(), "vendor": OUI_DB[prefix], "is_random": False}

    return {"mac": mac.upper(), "vendor": "Unknown", "is_random": False}


def get_db_stats() -> dict:
    _load_ieee()
    return {
        "builtin": len(OUI_DB),
        "ieee": len(_ieee),
        "total": len(OUI_DB) + len(_ieee),
        "has_ieee": len(_ieee) > 0,
        "has_py": os.path.exists(_PY),
        "has_txt": os.path.exists(_TXT),
        "txt_size": f"{os.path.getsize(_TXT)/1024/1024:.1f} MB" if os.path.exists(_TXT) else "N/A",
    }
