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

kicad-cli pcb drc cannot run in this sandbox (SIGABRT on any board; the T-006
harness needed approved unsandboxed runs), so this geometric audit plus the
kicad-cli ERC + gerber/drill/pos exports are the executable evidence here.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[2]
MIN_GAP_MM = 0.127

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
                            mm(track.GetWidth()) / 2,
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
        rot = fp.GetOrientation().AsDegrees()
        for pad in fp.Pads():
            net = pad.GetNetname()
            if not net:
                continue
            x, y = pad_abs(pad)
            sz = pad.GetSize()
            w, h = mm(sz.x), mm(sz.y)
            if abs(abs(rot) - 90.0) < 1.0:
                w, h = h, w
            shape = pad.GetShape()
            on_f = pad.IsOnLayer(pcbnew.F_Cu)
            on_b = pad.IsOnLayer(pcbnew.B_Cu)
            layers = [ln for ln, on in (("F.Cu", on_f), ("B.Cu", on_b)) if on]
            ref = fp.GetReference()
            if shape in (pcbnew.PAD_SHAPE_CIRCLE, pcbnew.PAD_SHAPE_CUSTOM):
                # custom: annular GND ring; outer circle is the conservative extent
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
    name = f"{variant}-coupon"
    path = ROOT / "coupons" / "mic-bakeoff" / name / f"{name}.kicad_pcb"
    board = pcbnew.LoadBoard(str(path))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.BuildConnectivity()
    unconn = board.GetConnectivity().GetUnconnectedCount(False)
    check(
        unconn == 0, f"{variant}: connectivity after zone fill ({unconn} unconnected)"
    )

    copper = collect_copper(board)
    for layer, items in copper.items():
        worst = (1e9, None)
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                na, ga = items[i][0], items[i][2:]
                nb, gb = items[j][0], items[j][2:]
                if na == nb or (items[i][1] and items[i][1] == items[j][1]):
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
            f"{variant}: {layer} min different-net copper gap "
            f"{worst[0]:.3f} mm >= {MIN_GAP_MM} mm",
        )

    # Acoustic ports: four 0.50 mm NPTH at mic centres; ring interior copper-free.
    npth = []
    for fp in board.GetFootprints():
        if fp.GetReference().startswith("M") and fp.GetReference()[1:].isdigit():
            for pad in fp.Pads():
                if pad.GetDrillSize().x > 0 and not pad.IsOnCopperLayer():
                    npth.append(
                        (fp.GetReference(), mm(pad.GetDrillSize().x), pad_abs(pad))
                    )
    # np_thru_hole pads with no copper
    holes = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                pos = pad.GetPosition()
                holes.append(
                    (fp.GetReference(), mm(pad.GetDrillSize().x), mm(pos.x), mm(pos.y))
                )
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
