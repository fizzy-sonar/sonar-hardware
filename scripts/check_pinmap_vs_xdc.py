#!/usr/bin/env python3
"""T-011 live-source gate: assert the PIN TABLE in scripts/gen_digital_sheet.py
(the single source behind orchestration/pinmap.md, digital.kicad_sch and
gateware/constraints/sonar_cmod_a7.xdc) matches the Digilent Cmod-A7-Master.xdc
44/44 on DIP position + package pin + IO name + clock-capable flag.

Usage:  python3 scripts/check_pinmap_vs_xdc.py [/path/to/Cmod-A7-Master.xdc]
        (default: orchestration/reference/Cmod-A7-Master.xdc — committed copy of the\n        orchestrator's 2026-08-26 live fetch, sha256 56568df3868ef359e938ef8defab33e1814fe4153435e99e13da9260d9db4eaf;\n        re-fetch from github.com/Digilent/digilent-xdc to refresh)
Exit 0 = PASS, 1 = FAIL. Stdlib only.

Why this exists: the 2026-08-25 offline transcription sat rows 15-44 on wrong
DIP positions and an offline "audit" confirmed it from correlated model recall.
Only a parse of the live-fetched XDC caught it. Re-run this after ANY pin edit.
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_digital_sheet as g

SPECIAL = {15: "XADC analog (vaux4)", 16: "XADC analog (vaux12)",
           24: "VU (module 5V)", 25: "GND (only module GND)"}

def parse_xdc(path):
    src = open(path).read()
    gpio = {}
    pat = (r'PACKAGE_PIN\s+(\S+?)\s+IOSTANDARD\s+LVCMOS33\s*\}'
           r'\s*\[get_ports\s*\{\s*(pio\d+)\s*\}\s*\]\s*;\s*#(\S+)\s+Sch=pio\[(\d+)\]')
    for m in re.finditer(pat, src):
        pkg, port, ioname, sch = m.group(1), m.group(2), m.group(3), int(m.group(4))
        assert port == f"pio{sch}", f"{path}: port {port} != Sch=pio[{sch}]"
        gpio[sch] = (pkg, ioname)
    return gpio

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else str(__import__("pathlib").Path(__file__).resolve().parent.parent / "orchestration/reference/Cmod-A7-Master.xdc")
    gpio = parse_xdc(path)
    fails = []
    if len(gpio) != 44:
        fails.append(f"XDC parse: expected 44 GPIO entries, got {len(gpio)}")
    skipped = sorted(set(range(1, 49)) - set(gpio))
    if skipped != sorted(SPECIAL):
        fails.append(f"XDC GPIO skips {skipped}, expected {sorted(SPECIAL)}")

    rows = {p[1]: p for p in g.PINS}          # keyed by DIP position
    if sorted(rows) != list(range(1, 49)):
        fails.append(f"PIN TABLE DIP positions {sorted(rows)} != 1..48")

    checked = 0
    for pos in range(1, 49):
        p = rows.get(pos)
        if p is None:
            fails.append(f"position {pos}: missing from PIN TABLE"); continue
        if pos in SPECIAL:
            if p[0] != "-" or p[6] not in ("NC", "5V", "GND"):  # 5V: unified net name (review B1; was +5V)
                fails.append(f"position {pos}: must be a non-digital row ({SPECIAL[pos]}), "
                             f"got pio={p[0]} net={p[6]}")
            continue
        if pos not in gpio:
            fails.append(f"position {pos}: PIN TABLE has digital row but XDC has no pio{pos}")
            continue
        pkg, ioname = gpio[pos]
        ok = True
        if p[0] != f"pio{pos}":
            fails.append(f"position {pos} ({p[6]}): label {p[0]} != pio{pos}"); ok = False
        if p[2] != pkg:
            fails.append(f"pio{pos} ({p[6]}): pkg {p[2]} != XDC {pkg}"); ok = False
        if p[3] != ioname:
            fails.append(f"pio{pos} ({p[6]}): IO name {p[3]} != XDC {ioname}"); ok = False
        try:
            bank = int(ioname.rsplit("_", 1)[1])
            if p[4] != bank:
                fails.append(f"pio{pos} ({p[6]}): bank col {p[4]} != IO-name bank {bank}"); ok = False
        except (ValueError, IndexError):
            fails.append(f"pio{pos}: cannot parse bank from IO name {ioname}"); ok = False
        cc = "yes" if ("MRCC" in ioname or "SRCC" in ioname) else ""
        if p[5] != cc:
            fails.append(f"pio{pos} ({p[6]}): CC flag {p[5]!r} != IO-name-derived {cc!r}"); ok = False
        checked += ok

    # clock-critical nets must be clock-capable under true labels
    bynet = {p[6]: p for p in g.PINS}
    for net in ("PDM_CLK_FB", "FT_CLKOUT", "ETH_REF_CLK"):
        p = bynet[net]
        if p[5] != "yes":
            fails.append(f"{net} on {p[0]} ({p[3]}) is NOT clock-capable")

    cc_set = sorted(p[1] for p in g.PINS if p[5] == "yes")
    print(f"XDC: {path}")
    print(f"true MRCC/SRCC pio set: {cc_set}")
    if fails:
        print(f"FAIL ({checked}/44 digital rows match):")
        for f in fails: print("  -", f)
        return 1
    print(f"PASS: 44/44 DIP positions match the live master XDC "
          f"(position + pio label + pkg pin + IO name + bank + CC flag); "
          f"special positions 15/16/24/25 = {sorted(SPECIAL)}; "
          f"PDM_CLK_FB/FT_CLKOUT/ETH_REF_CLK all clock-capable.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
