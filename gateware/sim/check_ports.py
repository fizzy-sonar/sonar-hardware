#!/usr/bin/env python3
"""T-020 port bijection gate: rtl/sonar_top.sv <-> constraints/sonar_cmod_a7.xdc.

Asserts an EXACT bijection between the module port list of `sonar_top` and the
active (non-commented) `get_ports` names of the real XDC. The commented DNP
RMII block is excluded. Buses must match bit-for-bit (contiguous [N-1:0] on
both sides). Vivado errors on any get_ports name without a matching port, and
unpinned top-level ports fail bitstream DRC, so both directions are checked.

Run from gateware/:  python3 sim/check_ports.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RTL = ROOT / "rtl" / "sonar_top.sv"
XDC = ROOT / "constraints" / "sonar_cmod_a7.xdc"


def parse_rtl_ports(path):
    """Return {port_name: width} from the sonar_top module header."""
    text = path.read_text()
    text = re.sub(r"//[^\n]*", "", text)  # strip line comments
    m = re.search(r"\bmodule\s+sonar_top\b(.*?)\)\s*;", text, re.DOTALL)
    if not m:
        sys.exit(f"FAIL: could not locate the sonar_top port list in {path}")
    header = m.group(1)
    ports = {}
    for decl in re.finditer(
        r"\b(?:input|output|inout)\s+(?:wire|reg)?\s*(?:signed\s+)?"
        r"(?:\[\s*(\d+)\s*:\s*(\d+)\s*\]\s*)?([A-Za-z_]\w*)",
        header,
    ):
        msb, lsb, name = decl.groups()
        width = abs(int(msb) - int(lsb)) + 1 if msb is not None else 1
        if name in ports:
            sys.exit(f"FAIL: duplicate RTL port {name}")
        ports[name] = width
    return ports


def parse_xdc_ports(path):
    """Return {base_name: sorted_indices_or_None} from active get_ports."""
    ports = {}
    for lineno, raw in enumerate(path.read_text().splitlines(), 1):
        if raw.lstrip().startswith("#"):
            continue  # commented lines (incl. the whole DNP RMII block)
        for m in re.finditer(
            r"\[get_ports\s+\{\s*([A-Za-z_]\w*)\s*(?:\[\s*(\d+)\s*\])?\s*\}\]",
            raw,
        ):
            base, idx = m.group(1), m.group(2)
            if idx is None:
                if base in ports and ports[base] is not None:
                    sys.exit(f"FAIL: {base} mixes scalar and bus refs")
                ports.setdefault(base, None)
                if ports[base] is not None:
                    sys.exit(f"FAIL: {base} mixes scalar and bus refs")
            else:
                if ports.get(base) is None and base in ports:
                    sys.exit(f"FAIL: {base} mixes scalar and bus refs")
                ports.setdefault(base, [])
                ports[base].append(int(idx))
    for base, idxs in ports.items():
        if idxs is not None:
            ports[base] = sorted(idxs)
    return ports


def main():
    rtl = parse_rtl_ports(RTL)
    xdc = parse_xdc_ports(XDC)

    errors = []
    only_rtl = sorted(set(rtl) - set(xdc))
    only_xdc = sorted(set(xdc) - set(rtl))
    for name in only_rtl:
        errors.append(f"RTL port {name} has no XDC constraint (unpinned port)")
    for name in only_xdc:
        errors.append(f"XDC get_ports {name} has no port on sonar_top "
                      "(Vivado errors on this)")
    for name in sorted(set(rtl) & set(xdc)):
        idxs = xdc[name]
        if idxs is None:
            if rtl[name] != 1:
                errors.append(f"{name}: RTL bus (width {rtl[name]}) vs scalar "
                              "XDC ref")
        else:
            want = list(range(rtl[name]))
            if idxs != want:
                errors.append(f"{name}: XDC bits {idxs} do not cover RTL "
                              f"[{rtl[name]-1}:0] exactly")

    if errors:
        print(f"FAIL sonar_top <-> XDC port bijection ({len(errors)} problem"
              f"{'s' if len(errors) != 1 else ''}):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    n_bits = sum(rtl.values())
    print(f"PASS sonar_top <-> XDC port bijection: {len(rtl)} ports / "
          f"{n_bits} bits exact (active get_ports only, DNP block excluded)")


if __name__ == "__main__":
    main()
