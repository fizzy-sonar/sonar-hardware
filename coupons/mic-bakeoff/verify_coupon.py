#!/usr/bin/env python3
"""T-016 coupon verification suite (run with the KiCad-bundled python):

  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9 \
      coupons/mic-bakeoff/verify_coupon.py

Checks, per coupon variant:
  1. Zone-fill + connectivity: zero unconnected items after fill.
  2. Static copper clearance audit on F.Cu/B.Cu tracks, vias, and pads:
     different-net copper must be >= 0.127 mm apart (JLC 4L min is 0.09/0.127).
  3. Acoustic-port structure: exactly four 0.50 mm NPTH at the mic centres,
     no copper within the Ø1.025 ring interior, pad-1 quadrant per datasheet.
  4. Header pin/net map (assembly/bench-critical).
  5. Board outline, mounting holes, fab note text.

This independent audit supplements, never replaces, full KiCad DRC. First
export fresh schematic XML and ERC reports using check_coupons.sh.
"""

from __future__ import annotations

import math
import re
import sys
from collections import Counter
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[2]
MIN_GAP_MM = 0.127

# Independently transcribed from TI SCAS895B section 5, CDCLVC1112 PW-24
# column. Do NOT import the generator's map: this must detect a wrong generator.
TI_PIN_NAMES = (
    "CLKIN",
    "1G",
    "Y0",
    "GND",
    "VDD",
    "Y4",
    "GND",
    "Y6",
    "VDD",
    "Y9",
    "GND",
    "Y11",
    "VDD",
    "Y10",
    "GND",
    "Y8",
    "Y7",
    "VDD",
    "Y5",
    "GND",
    "Y2",
    "VDD",
    "Y3",
    "Y1",
)
TI_PIN_NETS = {
    str(n): {
        "CLKIN": "CLK_IN",
        "1G": "CLK_EN",
        "Y0": "CLK_Y0",
        "Y1": "CLK_FBR",
        "GND": "GND",
        "VDD": "+3V3_MIC",
    }.get(name, "")
    for n, name in enumerate(TI_PIN_NAMES, 1)
}

failures = []


def check(ok: bool, msg: str) -> None:
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        failures.append(msg)


def mm(v: int) -> float:
    return pcbnew.ToMM(v)


def pad_abs(pad) -> tuple[float, float]:
    pos = pad.GetPosition()
    return mm(pos.x), mm(pos.y)


def collect_copper(board):
    """Return per-layer lists of (net, kind, geometry) for tracks/vias/pads.

    Geometry: ('seg', x0, y0, x1, y1, r) | ('circle', x, y, r) | ('rect', cx, cy, w, h)
    """
    copper = {"F.Cu": [], "B.Cu": []}
    for track in board.GetTracks():
        net = track.GetNetname()
        if not net:
            continue
        if hasattr(track, "GetStart"):  # segment or via
            if track.GetClass() == "VIA" or track.Type() == pcbnew.PCB_VIA_T:
                pos = track.GetPosition()
                for layer in ("F.Cu", "B.Cu"):
                    copper[layer].append(
                        (
                            net,
                            "",
                            "circle",
                            mm(pos.x),
                            mm(pos.y),
                            mm(track.GetWidth(pcbnew.F_Cu)) / 2,
                        )
                    )
                continue
            s, e = track.GetStart(), track.GetEnd()
            layer = track.GetLayerName()
            if layer in copper:
                copper[layer].append(
                    (
                        net,
                        "",
                        "seg",
                        mm(s.x),
                        mm(s.y),
                        mm(e.x),
                        mm(e.y),
                        mm(track.GetWidth()) / 2,
                    )
                )
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            net = pad.GetNetname() or f"NC:{fp.GetReference()}.{pad.GetNumber()}"
            x, y = pad_abs(pad)
            sz = pad.GetSize()
            w, h = mm(sz.x), mm(sz.y)
            rot = pad.GetOrientation().AsDegrees() % 180
            if abs(rot - 90.0) < 1.0:
                w, h = h, w
            shape = pad.GetShape()
            on_f = pad.IsOnLayer(pcbnew.F_Cu)
            on_b = pad.IsOnLayer(pcbnew.B_Cu)
            layers = [ln for ln, on in (("F.Cu", on_f), ("B.Cu", on_b)) if on]
            ref = fp.GetReference()
            if shape == pcbnew.PAD_SHAPE_CUSTOM:
                # Conservative outer extent of the annulus, NOT its small
                # offset anchor. The actual aperture is checked separately.
                center = fp.GetPosition()
                for layer in layers:
                    copper[layer].append((net, ref, "circle", mm(center.x), mm(center.y), 0.8125))
            elif shape == pcbnew.PAD_SHAPE_CIRCLE:
                for layer in layers:
                    copper[layer].append((net, ref, "circle", x, y, w / 2))
            else:
                for layer in layers:
                    copper[layer].append((net, ref, "rect", x, y, w, h))
    return copper


def dist_geom(a, b) -> float:
    ka, kb = a[0], b[0]
    if ka == "circle" and kb == "circle":
        d = math.hypot(a[1] - b[1], a[2] - b[2]) - a[3] - b[3]
        return d
    if ka == "seg" and kb == "seg":
        return seg_seg(a[1:5], b[1:5]) - a[5] - b[5]
    if ka == "seg" and kb == "circle":
        return pt_seg(b[1], b[2], a[1:5]) - a[5] - b[3]
    if ka == "circle" and kb == "seg":
        return pt_seg(a[1], a[2], b[1:5]) - b[5] - a[3]
    # rects: conservative via bounding circle for mixed, exact-ish for rect-rect
    if ka == "rect" and kb == "rect":
        dx = max(0.0, abs(a[1] - b[1]) - (a[3] + b[3]) / 2)
        dy = max(0.0, abs(a[2] - b[2]) - (a[4] + b[4]) / 2)
        return math.hypot(dx, dy)
    if ka == "rect" and kb == "circle":
        dx = max(0.0, abs(a[1] - b[1]) - a[3] / 2)
        dy = max(0.0, abs(a[2] - b[2]) - a[4] / 2)
        return math.hypot(dx, dy) - b[3]
    if ka == "circle" and kb == "rect":
        return dist_geom(b, a)
    if ka == "rect" and kb == "seg":
        return rect_seg(a, b[1:5]) - b[5]
    if ka == "seg" and kb == "rect":
        return rect_seg(b, a[1:5]) - a[5]
    raise ValueError((ka, kb))


def rect_seg(rect, s) -> float:
    """Exact distance between an axis-aligned rect and a zero-width segment."""
    _, cx, cy, w, h = rect
    x0, y0 = cx - w / 2, cy - h / 2
    x1, y1 = cx + w / 2, cy + h / 2
    sx0, sy0, sx1, sy1 = s
    # segment endpoints inside rect?
    for px, py in ((sx0, sy0), (sx1, sy1)):
        if x0 <= px <= x1 and y0 <= py <= y1:
            return 0.0
    edges = [
        ((x0, y0), (x1, y0)),
        ((x1, y0), (x1, y1)),
        ((x1, y1), (x0, y1)),
        ((x0, y1), (x0, y0)),
    ]
    d = min(seg_seg(s, (e[0][0], e[0][1], e[1][0], e[1][1])) for e in edges)
    return d


def pt_seg(px, py, s) -> float:
    x0, y0, x1, y1 = s
    dx, dy = x1 - x0, y1 - y0
    if dx == dy == 0:
        return math.hypot(px - x0, py - y0)
    t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def seg_seg(a, b) -> float:
    def ccw(p, q, r):
        return (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])

    p1, p2 = (a[0], a[1]), (a[2], a[3])
    p3, p4 = (b[0], b[1]), (b[2], b[3])
    d1, d2 = ccw(p3, p4, p1), ccw(p3, p4, p2)
    d3, d4 = ccw(p1, p2, p3), ccw(p1, p2, p4)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(
        pt_seg(p1[0], p1[1], b),
        pt_seg(p2[0], p2[1], b),
        pt_seg(p3[0], p3[1], a),
        pt_seg(p4[0], p4[1], a),
    )


def verify_variant(variant: str) -> None:
    report = (ROOT / f"build/t016/{variant}-erc.rpt").read_text()
    blocks = re.split(r"^\[", report, flags=re.M)[1:]
    actual_erc = Counter(
        (b.split("]")[0], tuple(re.findall(r"Symbol (\w+) Pin (\d+)", b))) for b in blocks
    )
    expected_erc = Counter(
        {
            ("power_pin_not_driven", (("M1", "2"),)): 1,
            ("power_pin_not_driven", (("M1", "5"),)): 1,
            ("pin_to_pin", (("M1", "1"), ("M2", "1"))): 1,
            ("pin_to_pin", (("M3", "1"), ("M4", "1"))): 1,
        }
    )
    check(actual_erc == expected_erc, f"{variant}: ERC matches four exact reviewed waivers")
    name = f"{variant}-coupon"
    path = ROOT / "coupons" / "mic-bakeoff" / name / f"{name}.kicad_pcb"
    board = pcbnew.LoadBoard(str(path))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.BuildConnectivity()
    unconn = board.GetConnectivity().GetUnconnectedCount(False)
    check(unconn == 0, f"{variant}: connectivity after zone fill ({unconn} unconnected)")

    u1 = next(fp for fp in board.GetFootprints() if fp.GetReference() == "U1")
    actual = {p.GetNumber(): p.GetNetname() for p in u1.Pads()}
    check(actual == TI_PIN_NETS, f"{variant}: all 24 U1 pads vs independent TI map")
    bypass = {
        fp.GetReference()
        for fp in board.GetFootprints()
        if fp.GetReference() in ("C5", "C6", "C7", "C8", "C11")
        and fp.GetValue() == "100nF X7R"
        and {p.GetNetname() for p in fp.Pads()} == {"+3V3_MIC", "GND"}
    }
    check(len(bypass) == 5, f"{variant}: five 100 nF buffer bypass capacitors")
    xml = ET.parse(ROOT / f"build/t016/{variant}-net.xml").getroot()
    nodes = {}
    for net in xml.findall("nets/net"):
        name = net.attrib["name"].lstrip("/")
        if name.startswith("unconnected-"):
            name = ""
        for node in net.findall("node"):
            nodes[(node.attrib["ref"], node.attrib["pin"])] = name
    pcb_nodes = {
        (fp.GetReference(), p.GetNumber()): p.GetNetname()
        for fp in board.GetFootprints()
        for p in fp.Pads()
        if p.GetNumber()
    }
    check(nodes == pcb_nodes, f"{variant}: schematic/PCB exact pin-net parity ({len(nodes)} pads)")
    pins = xml.findall("libparts/libpart[@part='CDCLVC1112PWR_T016']/pins/pin")
    pin_names = {p.attrib["num"]: p.attrib["name"].rsplit("_", 1)[0] for p in pins}
    check(
        pin_names == dict(zip(map(str, range(1, 25)), TI_PIN_NAMES)),
        f"{variant}: schematic symbol pin names vs independent TI table",
    )

    copper = collect_copper(board)
    for layer, items in copper.items():
        worst = (1e9, None)
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                na, ga = items[i][0], items[i][2:]
                nb, gb = items[j][0], items[j][2:]
                if na == nb:
                    continue
                d = dist_geom(ga, gb)
                if d < worst[0]:
                    worst = (d, (na, ga, nb, gb))
                if d < MIN_GAP_MM - 1e-6:
                    print(
                        f"    VIOLATION {variant} {layer}: {items[i][1]} {na} {ga} vs {items[j][1]} {nb} {gb} gap={d:.3f}"
                    )
        check(
            worst[0] >= MIN_GAP_MM - 1e-6,
            f"{variant}: {layer} min different-net copper gap {worst[0]:.3f} mm >= {MIN_GAP_MM} mm",
        )

    check(
        apertures_clear(board), f"{variant}: actual copper/paste polygons clear all port interiors"
    )

    # Acoustic ports: four 0.50 mm NPTH at mic centres; ring interior copper-free.
    npth = []
    for fp in board.GetFootprints():
        if fp.GetReference().startswith("M") and fp.GetReference()[1:].isdigit():
            for pad in fp.Pads():
                if pad.GetDrillSize().x > 0 and not pad.IsOnCopperLayer():
                    npth.append((fp.GetReference(), mm(pad.GetDrillSize().x), pad_abs(pad)))
    # np_thru_hole pads with no copper
    holes = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                pos = pad.GetPosition()
                holes.append((fp.GetReference(), mm(pad.GetDrillSize().x), mm(pos.x), mm(pos.y)))
    mic_holes = [h for h in holes if h[0].startswith("M")]
    check(
        len(mic_holes) == 4 and all(abs(h[1] - 0.5) < 1e-6 for h in mic_holes),
        f"{variant}: exactly 4x 0.50 mm NPTH acoustic ports ({len(mic_holes)} found)",
    )
    expected_x = [15.0, 27.0, 39.0, 51.0]
    got_x = sorted(h[2] for h in mic_holes)
    check(
        all(abs(g - e) < 1e-6 for g, e in zip(got_x, expected_x))
        and all(abs(h[3] - 18.0) < 1e-6 for h in mic_holes),
        f"{variant}: ports at mic centres ({got_x})",
    )

    # Header pin map (J1 bench connector).
    j1 = next(fp for fp in board.GetFootprints() if fp.GetReference() == "J1")
    pin_net = {pad.GetPadName(): pad.GetNetname() for pad in j1.Pads()}
    expected = {
        "1": "+3V3_IN",
        "2": "GND",
        "3": "D0",
        "4": "D1",
        "5": "GND",
        "6": "CLK_IN",
        "7": "CLK_EN",
        "8": "GND",
        "9": "CLK_FB",
        "10": "GND",
    }
    check(pin_net == expected, f"{variant}: J1 pin/net map {pin_net == expected}")

    # Mic pad-1 (DATA) quadrant: datasheet PCB-side orientation.
    quadrant = {"sph": (-1, 1), "ics": (1, -1)}[variant]
    ok = True
    for fp in board.GetFootprints():
        if not (fp.GetReference().startswith("M") and fp.GetReference()[1:].isdigit()):
            continue
        fpos = fp.GetPosition()
        fx, fy = mm(fpos.x), mm(fpos.y)
        for pad in fp.Pads():
            if pad.GetPadName() == "1":
                px, py = pad_abs(pad)
                dx = 1 if px > fx else -1
                dy = 1 if py > fy else -1
                if (dx, dy) != quadrant:
                    ok = False
    check(ok, f"{variant}: mic pad 1 (DATA) in datasheet quadrant {quadrant}")

    holes_mount = [h for h in holes if not h[0].startswith("M")]
    check(
        len(holes_mount) == 4 and all(abs(h[1] - 2.2) < 1e-6 for h in holes_mount),
        f"{variant}: 4x M2 mounting holes",
    )

    # Negative tests mutate memory only, then restore. The previous checker
    # passed the actual bad designs; prove the same defect classes are caught.
    pad11 = next(p for p in u1.Pads() if p.GetNumber() == "11")
    saved = pad11.GetNetCode()
    pad11.SetNetCode(next(p.GetNetCode() for p in u1.Pads() if p.GetNumber() == "5"))
    check(
        {p.GetNumber(): p.GetNetname() for p in u1.Pads()} != TI_PIN_NETS,
        f"{variant}: negative test rejects wrong U1 supply pin",
    )
    pad11.SetNetCode(saved)
    cap = next(fp for fp in board.GetFootprints() if fp.GetReference() == "C1")
    pads = list(cap.Pads())
    saved_pos = pads[1].GetPosition()
    pads[1].SetPosition(pads[0].GetPosition())
    items = [i for i in collect_copper(board)["F.Cu"] if i[1] == "C1"]
    check(
        dist_geom(items[0][2:], items[1][2:]) < MIN_GAP_MM,
        f"{variant}: negative test detects same-footprint supply short",
    )
    pads[1].SetPosition(saved_pos)
    unused = next(p for p in u1.Pads() if p.GetNumber() == "6")
    saved_pos = unused.GetPosition()
    unused.SetPosition(pad11.GetPosition())
    items = [i for i in collect_copper(board)["F.Cu"] if i[1] == "U1"]
    nc = next(i for i in items if i[0] == "NC:U1.6")
    check(
        any(i[0] != nc[0] and dist_geom(nc[2:], i[2:]) < MIN_GAP_MM for i in items),
        f"{variant}: negative test detects no-net pad touching ground",
    )
    unused.SetPosition(saved_pos)
    mic = next(fp for fp in board.GetFootprints() if fp.GetReference() == "M1")
    ring = next(p for p in mic.Pads() if p.GetNumber() == "3")
    saved_size = ring.GetSize()
    ring.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.625), pcbnew.FromMM(1.625)))
    check(
        not apertures_clear(board), f"{variant}: negative test rejects copper/paste anchor in port"
    )
    ring.SetSize(saved_size)


def apertures_clear(board):
    # Sample each 0.50 mm-radius clear interior at 10 um Cartesian spacing.
    # The nominal ring inner radius is 0.5125 mm. Use KiCad's actual polygon
    # (anchor UNION primitives), so a ring-shaped source string is not enough.
    for fp in board.GetFootprints():
        if fp.GetReference() not in ("M1", "M2", "M3", "M4"):
            continue
        pos = fp.GetPosition()
        points = [
            pcbnew.VECTOR2I(pos.x + pcbnew.FromMM(dx / 100), pos.y + pcbnew.FromMM(dy / 100))
            for dx in range(-50, 51)
            for dy in range(-50, 51)
            if dx * dx + dy * dy <= 2500
        ]
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            for layer in (pcbnew.F_Cu, pcbnew.F_Paste):
                if pad.IsOnLayer(layer):
                    poly = pad.GetEffectivePolygon(layer)
                    if any(poly.Contains(p) for p in points):
                        return False
    return True


def main() -> int:
    for variant in ("sph", "ics"):
        verify_variant(variant)
    if failures:
        print(f"VERIFY: {len(failures)} FAILURES")
        return 1
    print("VERIFY: all coupon checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
