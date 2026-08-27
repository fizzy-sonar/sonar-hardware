#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Generate the T-016 microphone bake-off coupon KiCad projects.

Two variants (SPH0641LU4H-1, ICS-41352), each a four-mic coupon with the
production-intent CDCLVC1112PWR worst-case four-load clock branch, 0.50 mm NPTH
acoustic ports, per-mic 100 nF X7R bypass, current-break jumper, and bench
header. All KiCad artifacts (symbols, footprints, schematic, PCB) are emitted
from this single data-driven source so a dimension correction is a one-line
change followed by regeneration.

Dimension provenance (primary datasheets, local PDF copies):
- SPH0641LU4H-1: Knowles Rev B 2015-04-06. Land pattern: sheet 10
  "EXAMPLE LAND PATTERN" (PCB-side view). Pin table: sheet 9
  (1=DATA, 2=SELECT, 3=GND ring, 4=CLOCK, 5=VDD). Body 3.50x2.65x0.98 mm,
  acoustic port Ø0.325 +/-0.05 mm.
- ICS-41352: TDK/InvenSense DS-000048 Rev 1.0. PCB orientation: Figure 3
  "Pin Configuration (Top View, Terminal Side Down)"; land dimensions:
  Figure 16 + Figure 18 (bottom view). Pin table 9
  (1=DATA, 2=SELECT, 3=GND ring, 4=CLK, 5=VDD). Body 3.50x2.65x0.98 mm,
  sound port Ø0.375 mm; PCB hole 0.5-1.0 mm recommended.
- CDCLVC1112PWR pin map: **UNVERIFIED** (datasheet not available offline).
  The map lives in BUFFER_PIN_MAP below and MUST be confirmed against the TI
  CDCLVC11xx datasheet before ordering (see README pre-order checklist).
"""

from __future__ import annotations

import uuid
from pathlib import Path

OUT = Path(__file__).resolve().parent


_uid_counter = 0


def uid() -> str:
    """Deterministic UUIDs so regeneration is a no-op diff."""
    global _uid_counter
    _uid_counter += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"t016-coupon-{_uid_counter}"))


# --- Canonical geometry ----------------------------------------------------------
# Mic footprints: origin at the acoustic port (GND ring centre). Coordinates mm.
MIC_FOOTPRINTS = {
    "SPH": {
        "name": "MIC_SPH0641LU4H-1_T016",
        "mpn": "SPH0641LU4H-1",
        # pad: (number, net_role, x, y, w, h)  per Knowles sheet 10 example land pattern
        "pads": [
            (1, "DATA", -0.8375, 2.335, 0.725, 0.522),
            (2, "SELECT", -0.8375, 1.513, 0.725, 0.522),
            (4, "CLK", 0.8375, 1.513, 0.725, 0.522),
            (5, "VDD", 0.8375, 2.335, 0.725, 0.522),
        ],
        "ring_outer": 1.625,  # pad 3, GND
        "ring_inner": 1.025,
        "body": (2.65, 3.50, (0.0, 0.971)),  # w(x), h(y), centre rel port
        "courtyard": (3.15, 4.00, (0.0, 0.971)),
        "port_note": "port Ø0.325±0.05 (sheet 9); NPTH 0.50 per T-008 rule 2",
    },
    "ICS": {
        "name": "MIC_ICS-41352_T016",
        "mpn": "ICS-41352",
        # per DS-000048 Fig.3 orientation + Fig.16/18 dimensions
        "pads": [
            (1, "DATA", 2.074, -0.838, 0.522, 0.725),
            (2, "SELECT", 2.074, 0.837, 0.522, 0.725),
            (4, "CLK", 1.252, 0.837, 0.522, 0.725),
            (5, "VDD", 1.252, -0.838, 0.522, 0.725),
        ],
        "ring_outer": 1.625,  # pad 3, GND
        "ring_inner": 1.025,
        "body": (3.50, 2.65, (0.710, 0.0)),
        "courtyard": (4.00, 3.15, (0.710, 0.0)),
        "port_note": "sound port Ø0.375 (Fig.18); PCB hole 0.5-1.0 mm (Fig.16 text)",
    },
}

# TI CDCLVC1112PWR (TSSOP-24) pin map -- UNVERIFIED, confirm vs TI datasheet.
BUFFER_PIN_MAP = {
    1: "CLKIN",
    2: "1G",
    3: "GND",
    4: "Y0",
    5: "Y1",
    6: "Y2",
    7: "Y3",
    8: "Y4",
    9: "Y5",
    10: "GND",
    11: "VDD",
    12: "Y6",
    13: "Y7",
    14: "Y8",
    15: "GND",
    16: "VDD",
    17: "Y9",
    18: "Y10",
    19: "Y11",
    20: "GND",
    21: "VDD",
    22: "VDD",
    23: "NC",
    24: "NC",
}

BOARD_W, BOARD_H = 70.0, 30.0
MIC_X = [15.0, 27.0, 39.0, 51.0]
MIC_Y = 18.0
U1_POS = (10.0, 7.5)
J1_POS = (64.0, 15.0)  # 2x5 2.54 mm header


# --- Footprint emitters ------------------------------------------------------------
def _fp_text(kind: str, text: str, x: float, y: float, layer: str, hide: bool = False) -> str:
    h = "\n\t\t(hide yes)" if hide else ""
    return (
        f'\t(fp_text {kind} "{text}" (at {x} {y} 0) (layer "{layer}"){h}\n'
        '\t\t(effects (font (size 1.0 1.0) (thickness 0.15)))\n\t\t(uuid "' + uid() + '")\n\t)'
    )


def _annulus_polys(r_out: float, r_in: float, seg: int = 16) -> list[list[tuple[float, float]]]:
    import math as _m

    polys = []
    for half in range(2):
        a0 = _m.pi * half
        outer = [
            (r_out * _m.cos(a0 + _m.pi * i / seg), r_out * _m.sin(a0 + _m.pi * i / seg))
            for i in range(seg + 1)
        ]
        inner = [
            (
                r_in * _m.cos(a0 + _m.pi - _m.pi * i / seg),
                r_in * _m.sin(a0 + _m.pi - _m.pi * i / seg),
            )
            for i in range(seg + 1)
        ]
        polys.append(outer + inner)
    return polys


def emit_mic_footprint(spec: dict) -> str:
    lines = [
        f'(footprint "{spec["name"]}"\n\t(layer "F.Cu")\n\t(uuid "{uid()}")',
        f'\t(descr "{spec["mpn"]} bottom-port PDM mic, T-016 coupon. {spec["port_note"]}")',
        "\t(attr smd)",
        _fp_text("reference", "REF**", 0, -2.6, "F.SilkS"),
        _fp_text("value", spec["name"], 0, -3.6, "F.Fab"),
    ]
    for num, role, x, y, w, h in spec["pads"]:
        lines.append(
            f'\t(pad "{num}" smd rect (at {x} {y}) (size {w} {h}) '
            f'(layers "F.Cu" "F.Paste" "F.Mask") (uuid "{uid()}"))'
        )
    # Pad 3: annular GND ring (custom copper), paste pulled back, plus four small
    # bridge pads so the zone/thermal connection lands on copper outside the ring.
    ro, ri = spec["ring_outer"] / 2, spec["ring_inner"] / 2
    polys = _annulus_polys(ro, ri)
    prim = []
    for poly in polys:
        pts = " ".join(f"(xy {px:.4f} {py:.4f})" for px, py in poly)
        prim.append(f"\t\t(gr_poly (pts {pts}) (stroke (width 0) (type solid)) (fill yes))")
    lines.append(
        f'\t(pad "3" smd custom (at 0 0) (size {ro * 2:.3f} {ro * 2:.3f}) '
        f'(layers "F.Cu" "F.Paste" "F.Mask")\n'
        "\t\t(options (clearance outline) (anchor circle))\n"
        f"\t\t(primitives\n" + "\n".join(prim) + f')\n\t\t(uuid "{uid()}"))'
    )
    # 0.50 mm non-plated acoustic hole, mask opened, no copper annulus.
    lines.append(
        '\t(pad "" np_thru_hole circle (at 0 0) (size 0.5 0.5) (drill 0.5) '
        f'(layers "*.Cu" "*.Mask") (uuid "{uid()}"))'
    )
    # Fab body + courtyard + silk outline; pin-1 dot near pad 1.
    bw, bh, (bcx, bcy) = spec["body"]
    x0, y0 = bcx - bw / 2, bcy - bh / 2
    x1, y1 = bcx + bw / 2, bcy + bh / 2
    lines.append(
        f"\t(fp_rect (start {x0:.3f} {y0:.3f}) (end {x1:.3f} {y1:.3f}) "
        f'(stroke (width 0.05) (type solid)) (fill no) (layer "F.Fab") (uuid "{uid()}"))'
    )
    cw, ch, (ccx, ccy) = spec["courtyard"]
    lines.append(
        f"\t(fp_rect (start {ccx - cw / 2:.3f} {ccy - ch / 2:.3f}) (end {ccx + cw / 2:.3f} {ccy + ch / 2:.3f}) "
        f'(stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{uid()}"))'
    )
    lines.append(
        f"\t(fp_rect (start {x0 - 0.12:.3f} {y0 - 0.12:.3f}) (end {x1 + 0.12:.3f} {y1 + 0.12:.3f}) "
        f'(stroke (width 0.12) (type solid)) (fill no) (layer "F.SilkS") (uuid "{uid()}"))'
    )
    p1 = spec["pads"][0]
    lines.append(
        f"\t(fp_circle (center {p1[2]:.3f} {p1[3] + 0.65:.3f}) (end {p1[2] + 0.2:.3f} {p1[3] + 0.65:.3f}) "
        f'(stroke (width 0.15) (type solid)) (fill yes) (layer "F.SilkS") (uuid "{uid()}"))'
    )
    lines.append(
        '\t(fp_text user "NO COPPER/MASK/PASTE IN PORT" (at 0 -4.8 0) (layer "User.2")\n'
        '\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))\n\t\t(uuid "' + uid() + '")\n\t)'
    )
    lines.append(")")
    return "\n".join(lines) + "\n"


def emit_smd0603(tag: str) -> str:
    pads = []
    for n, x in ((1, -0.5), (2, 0.5)):
        pads.append(
            f'\t(pad "{n}" smd roundrect (at {x} 0) (size 0.9 1.0) (layers "F.Cu" "F.Paste" "F.Mask") '
            f'(roundrect_rratio 0.25) (uuid "{uid()}"))'
        )
    return (
        f'(footprint "{tag}"\n\t(layer "F.Cu")\n\t(uuid "{uid()}")\n\t(descr "0603 SMD (T-016 coupon)")\n\t(attr smd)\n'
        + _fp_text("reference", "REF**", 0, -1.2, "F.SilkS")
        + _fp_text("value", tag, 0, 1.2, "F.Fab")
        + "\n"
        + "\n".join(pads)
        + f'\n\t(fp_rect (start -0.8 -0.4) (end 0.8 0.4) (stroke (width 0.05) (type solid)) (fill no) (layer "F.Fab") (uuid "{uid()}"))'
        + f'\n\t(fp_rect (start -1.0 -0.75) (end 1.0 0.75) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{uid()}"))\n)\n'
    )


def emit_tssop24() -> str:
    pads = []
    for i in range(12):
        x = -3.575 + i * 0.65
        pads.append(
            f'\t(pad "{i + 1}" smd rect (at {x:.3f} 2.8) (size 0.4 1.5) (layers "F.Cu" "F.Paste" "F.Mask") (uuid "{uid()}"))'
        )
        pads.append(
            f'\t(pad "{24 - i}" smd rect (at {x:.3f} -2.8) (size 0.4 1.5) (layers "F.Cu" "F.Paste" "F.Mask") (uuid "{uid()}"))'
        )
    return (
        f'(footprint "TSSOP-24_4.4x7.8mm_P0.65mm_T016"\n\t(layer "F.Cu")\n\t(uuid "{uid()}")'
        '\n\t(descr "TSSOP-24, 4.4x7.8mm body, 0.65mm pitch (generic; CDCLVC1112PWR pin map UNVERIFIED)")\n\t(attr smd)\n'
        + _fp_text("reference", "REF**", 0, -4.2, "F.SilkS")
        + _fp_text("value", "TSSOP-24_4.4x7.8mm_P0.65mm_T016", 0, 4.2, "F.Fab")
        + "\n"
        + "\n".join(pads)
        + f'\n\t(fp_rect (start -3.9 -2.2) (end 3.9 2.2) (stroke (width 0.05) (type solid)) (fill no) (layer "F.Fab") (uuid "{uid()}"))'
        + f'\n\t(fp_rect (start -4.35 -3.75) (end 4.35 3.75) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{uid()}"))'
        + f'\n\t(fp_circle (center -4.15 3.1) (end -3.95 3.1) (stroke (width 0.15) (type solid)) (fill yes) (layer "F.SilkS") (uuid "{uid()}"))\n)\n'
    )


def emit_pinheader(rows: int, cols: int, tag: str) -> str:
    pads = []
    for c in range(cols):
        for r in range(rows):
            n = r * cols + c + 1
            x, y = c * 2.54, -r * 2.54
            pads.append(
                f'\t(pad "{n}" thru_hole circle (at {x:.2f} {y:.2f}) (size 1.7 1.7) (drill 0.9) '
                f'(layers "*.Cu" "*.Mask") (uuid "{uid()}"))'
            )
    w = (cols - 1) * 2.54
    h = -(rows - 1) * 2.54
    return (
        f'(footprint "{tag}"\n\t(layer "F.Cu")\n\t(uuid "{uid()}")\n\t(descr "2.54 mm pin header (T-016 coupon)")\n\t(attr through_hole)\n'
        + _fp_text("reference", "REF**", 0, 2.0, "F.SilkS")
        + _fp_text("value", tag, 0, h - 2.0, "F.Fab")
        + "\n"
        + "\n".join(pads)
        + f'\n\t(fp_rect (start -1.27 1.27) (end {w + 1.27:.2f} {h - 1.27:.2f}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.Fab") (uuid "{uid()}"))\n)\n'
    )


def emit_testpoint() -> str:
    return (
        f'(footprint "TP_1.5mm_T016"\n\t(layer "F.Cu")\n\t(uuid "{uid()}")\n\t(descr "SMD test point pad 1.5 mm")\n\t(attr smd)\n'
        + _fp_text("reference", "REF**", 0, -1.5, "F.SilkS")
        + _fp_text("value", "TP_1.5mm_T016", 0, 1.5, "F.Fab")
        + f'\n\t(pad "1" smd circle (at 0 0) (size 1.5 1.5) (layers "F.Cu" "F.Mask") (uuid "{uid()}"))'
        + f'\n\t(fp_circle (center 0 0) (end 1.1 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{uid()}"))\n)\n'
    )


def emit_mounting_hole() -> str:
    return (
        f'(footprint "MountingHole_2.2mm_T016"\n\t(layer "F.Cu")\n\t(uuid "{uid()}")\n\t(descr "M2 mounting hole, NPTH, no copper")\n\t(attr exclude_from_pos_files)\n'
        + _fp_text("reference", "REF**", 0, -1.8, "F.SilkS", hide=True)
        + _fp_text("value", "MountingHole_2.2mm_T016", 0, 1.8, "F.Fab", hide=True)
        + f'\n\t(pad "" np_thru_hole circle (at 0 0) (size 2.2 2.2) (drill 2.2) (layers "*.Cu" "*.Mask") (uuid "{uid()}"))'
        + f'\n\t(fp_circle (center 0 0) (end 1.75 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{uid()}"))\n)\n'
    )


# --- Symbol library ----------------------------------------------------------------
def sym_def(
    name: str,
    ref: str,
    pins: list[tuple[str, str, float, float, float, str]],
    w: float,
    h: float,
    prefix: str = "",
) -> str:
    """pins: (number, pname, rel_x, rel_y, angle_deg, etype). Box centred at 0."""
    lines = [
        f'\t\t(symbol "{prefix}{name}"',
        "\t\t\t(pin_numbers (hide no)) (pin_names (offset 0.508) (hide no))",
        "\t\t\t(exclude_from_sim no) (in_bom yes) (on_board yes)",
        f'\t\t\t(property "Reference" "{ref}" (at 0 {-h / 2 - 2} 0) (effects (font (size 1.27 1.27))))',
        f'\t\t\t(property "Value" "{name}" (at 0 {h / 2 + 2} 0) (effects (font (size 1.27 1.27))))',
        '\t\t\t(property "Footprint" "" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))',
        '\t\t\t(property "Datasheet" "" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))',
        '\t\t\t(property "Description" "" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))',
        f'\t\t\t(symbol "{name}_0_1"',
        f"\t\t\t\t(rectangle (start {-w / 2} {h / 2}) (end {w / 2} {-h / 2})",
        "\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background)))",
        "\t\t\t)",
        f'\t\t\t(symbol "{name}_1_1"',
    ]
    for num, pname, x, y, ang, etype in pins:
        lines.append(
            f"\t\t\t\t(pin {etype} line (at {x} {y} {ang}) (length 2.54)"
            f' (name "{pname}" (effects (font (size 1.0 1.0))))'
            f' (number "{num}" (effects (font (size 1.0 1.0)))))'
        )
    lines += ["\t\t\t)", "\t\t)"]
    return "\n".join(lines) + "\n"


def mic_sym_pins() -> list[tuple[str, str, float, float, float, str]]:
    # left side: CLK, SELECT, GND; right side: VDD, DATA
    return [
        ("4", "CLK", -6.35, 2.54, 0, "input"),
        ("2", "SELECT", -6.35, 0.0, 0, "input"),
        ("3", "GND", -6.35, -2.54, 0, "power_in"),
        ("5", "VDD", 6.35, 2.54, 180, "power_in"),
        ("1", "DATA", 6.35, 0.0, 180, "output"),
    ]


def buffer_sym_pins() -> list[tuple[str, str, float, float, float, str]]:
    pins = []
    for n in range(1, 25):
        name = BUFFER_PIN_MAP[n]
        etype = {
            "CLKIN": "input",
            "1G": "input",
            "GND": "power_in",
            "VDD": "power_in",
            "NC": "no_connect",
        }.get(name, "output")
        if n <= 12:  # left column, top to bottom
            pins.append((str(n), name, -12.7, 15.24 - (n - 1) * 2.54, 0, etype))
        else:  # right column, bottom to top
            pins.append((str(n), name, 12.7, -15.24 + (n - 13) * 2.54, 180, etype))
    return pins


def rc_sym(name: str, ref: str) -> str:
    return sym_def(
        name,
        ref,
        [("1", "1", -2.54, 0.0, 0, "passive"), ("2", "2", 2.54, 0.0, 180, "passive")],
        3.0,
        1.6,
    )


SYMBOL_DEFS = {
    "MIC": ("PDM_MIC_T016", "M", mic_sym_pins(), 12.7, 7.62),
    "BUF": ("CDCLVC1112PWR_T016", "U", buffer_sym_pins(), 25.4, 33.02),
    "R": ("R_T016", "R", []),
    "C": ("C_T016", "C", []),
    "TP": ("TP_T016", "TP", [("1", "1", 0.0, 0.0, 0, "passive")]),
    "JP": (
        "JUMPER_T016",
        "JP",
        [("1", "1", -2.54, 0.0, 0, "passive"), ("2", "2", 2.54, 0.0, 180, "passive")],
    ),
    "J1": (
        "CONN_2X05_T016",
        "J",
        [
            (
                str(c * 5 + r + 1),
                f"P{c * 5 + r + 1}",
                -6.35 if c == 0 else 6.35,
                5.08 - r * 2.54,
                0 if c == 0 else 180,
                "passive",
            )
            for c in range(2)
            for r in range(5)
        ],
    ),
}


# --- Schematic emitter ---------------------------------------------------------------
SYM_META = {
    "MIC": ("PDM_MIC_T016", "M", mic_sym_pins(), 12.7, 7.62),
    "BUF": ("CDCLVC1112PWR_T016", "U", buffer_sym_pins(), 25.4, 33.02),
    "R": (
        "R_T016",
        "R",
        [("1", "1", -2.54, 0.0, 0, "passive"), ("2", "2", 2.54, 0.0, 180, "passive")],
        3.0,
        1.6,
    ),
    "C": (
        "C_T016",
        "C",
        [("1", "1", -2.54, 0.0, 0, "passive"), ("2", "2", 2.54, 0.0, 180, "passive")],
        3.0,
        1.6,
    ),
    "TP": ("TP_T016", "TP", [("1", "1", -2.54, 0.0, 0, "passive")], 2.0, 2.0),
    "JP": (
        "JUMPER_T016",
        "JP",
        [("1", "1", -2.54, 0.0, 0, "passive"), ("2", "2", 2.54, 0.0, 180, "passive")],
        3.0,
        1.6,
    ),
    "J1": (
        "CONN_2X05_T016",
        "J",
        [
            (
                str(n),
                f"P{n}",
                -6.35 if n % 2 == 1 else 6.35,
                5.08 - ((n - 1) // 2) * 2.54,
                0 if n % 2 == 1 else 180,
                "passive",
            )
            for n in range(1, 11)
        ],
        12.7,
        12.7,
    ),
}


def g(v: float) -> float:
    """Snap to the 1.27 mm schematic grid (ERC endpoint_off_grid hygiene)."""
    return round(v / 1.27) * 1.27


class Schematic:
    def __init__(self) -> None:
        self.items: list[str] = []
        self.project = ""
        self.root_uuid = uid()

    def place(
        self, kind: str, ref: str, value: str, footprint: str, x: float, y: float
    ) -> dict[str, tuple[float, float]]:
        name, _, pins, _, _ = SYM_META[kind]
        # KiCad symbol-lib coordinates have +y UP; schematic coordinates +y DOWN.
        pin_xy = {num: (x + dx, y - dy) for num, _, dx, dy, _, _ in pins}
        props = [
            ("Reference", ref, 0, -3, False),
            ("Value", value, 0, 3, False),
            ("Footprint", footprint, 0, 0, True),
            ("Datasheet", "", 0, 0, True),
            ("Description", "", 0, 0, True),
        ]
        lines = [
            "\t(symbol",
            f'\t\t(lib_id "coupon-symbols:{name}")',
            f"\t\t(at {x} {y} 0)",
            "\t\t(unit 1) (body_style 1)",
            "\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (in_pos_files yes) (dnp no)",
            "\t\t(fields_autoplaced yes)",
            f'\t\t(uuid "{uid()}")',
        ]
        for pname, pval, pdx, pdy, hide in props:
            h = "\n\t\t\t\t(hide yes)" if hide else ""
            lines.append(
                f'\t\t\t(property "{pname}" "{pval}" (at {x + pdx} {y + pdy} 0){h}\n'
                "\t\t\t\t(effects (font (size 1.27 1.27)))\n\t\t\t)"
            )
        for num in pin_xy:
            lines.append(f'\t\t\t(pin "{num}" (uuid "{uid()}"))')
        lines.append(
            f'\t\t\t(instances (project "{self.project}" (path "/{self.root_uuid}" (reference "{ref}") (unit 1))))'
        )
        lines.append("\t)")
        self.items.append("\n".join(lines))
        return pin_xy

    def stub_label(self, x: float, y: float, outward: tuple[float, float], net: str) -> None:
        ex, ey = x + outward[0] * 2.54, y + outward[1] * 2.54
        ang = 0 if outward[0] >= 0 else 180
        justify = "left bottom" if outward[0] >= 0 else "right bottom"
        self.items.append(
            f"\t(wire (pts (xy {x:.2f} {y:.2f}) (xy {ex:.2f} {ey:.2f}))\n"
            '\t\t(stroke (width 0) (type default)) (uuid "' + uid() + '"))'
        )
        self.items.append(
            f'\t(label "{net}" (at {ex:.2f} {ey:.2f} {ang}) (effects (font (size 1.27 1.27)) (justify {justify}))\n'
            '\t\t(uuid "' + uid() + '"))'
        )

    def no_connect(self, x: float, y: float) -> None:
        self.items.append(f'\t(no_connect (at {x:.2f} {y:.2f}) (uuid "{uid()}"))')

    def text(self, x: float, y: float, body: str) -> None:
        self.items.append(
            f'\t(text "{body}" (at {x} {y} 0) (effects (font (size 1.5 1.5)))\n\t\t(uuid "{uid()}"))'
        )


def build_schematic(variant: str, project: str) -> str:
    spec = MIC_FOOTPRINTS[variant]
    sch = Schematic()
    sch.project = project
    mic_fp = f"coupon:{spec['name']}"

    # Mic instances: M1/M3 SELECT low (even channels), M2/M4 SELECT high.
    mic_nets = []
    for i, x in enumerate((50.8, 81.28, 111.76, 142.24)):
        pins = sch.place("MIC", f"M{i + 1}", spec["mpn"], mic_fp, x, 60.96)
        sel = "GND" if i % 2 == 0 else "+3V3_MIC"
        data = "D0M" if i < 2 else "D1M"
        nets = {"4": "CLK_ST", "2": sel, "3": "GND", "5": "+3V3_MIC", "1": data}
        mic_nets.append(nets)
        for num, net in nets.items():
            px, py = pins[num]
            outward = (-1.0, 0.0) if px < x else (1.0, 0.0)
            sch.stub_label(px, py, outward, net)
        cpins = sch.place(
            "C",
            f"C{i + 1}",
            "100nF X7R 0603",
            "coupon:C_0603_T016",
            g(x + 15.24),
            60.96,
        )
        sch.stub_label(*cpins["1"], (-1.0, 0.0), "+3V3_MIC")
        sch.stub_label(*cpins["2"], (1.0, 0.0), "GND")

    upins = sch.place(
        "BUF",
        "U1",
        "CDCLVC1112PWR (PIN MAP UNVERIFIED)",
        "coupon:TSSOP-24_4.4x7.8mm_P0.65mm_T016",
        69.85,
        129.54,
    )
    for n in range(1, 25):
        px, py = upins[str(n)]
        outward = (-1.0, 0.0) if n <= 12 else (1.0, 0.0)
        name = BUFFER_PIN_MAP[n]
        if name in ("Y2", "Y3", "Y4", "Y5", "Y6", "Y7", "Y8", "Y9", "Y10", "Y11", "NC"):
            sch.no_connect(px, py)
        else:
            net = {
                "CLKIN": "CLK_IN",
                "1G": "CLK_EN",
                "Y0": "CLK_Y0",
                "Y1": "CLK_FBR",
                "GND": "GND",
                "VDD": "+3V3_MIC",
            }[name]
            sch.stub_label(px, py, outward, net)

    discretes = [
        ("R", "R0", "10R 0603", 38.1, 137.16, "CLK_Y0", "CLK_ST"),
        ("R", "R1", "10R 0603", 38.1, 134.62, "CLK_FBR", "CLK_FB"),
        ("R", "R12", "100k 0603", 38.1, 142.24, "CLK_EN", "GND"),
        ("R", "R13", "0R 0603", 60.96, 100.33, "D0M", "D0"),
        ("R", "R14", "0R 0603", 60.96, 105.41, "D1M", "D1"),
        ("C", "C5", "100nF X7R 0603", 95.25, 120.65, "+3V3_MIC", "GND"),
        ("C", "C6", "100nF X7R 0603", 95.25, 125.73, "+3V3_MIC", "GND"),
        ("C", "C7", "100nF X7R 0603", 95.25, 129.54, "+3V3_MIC", "GND"),
        ("C", "C8", "100nF X7R 0603", 95.25, 135.89, "+3V3_MIC", "GND"),
        ("C", "C9", "1uF 0603", 95.25, 139.7, "+3V3_MIC", "GND"),
        ("C", "C10", "10uF 0603", 95.25, 144.78, "+3V3_MIC", "GND"),
        ("JP", "JP1", "JUMPER (current break)", 120.65, 120.65, "+3V3_MIC", "+3V3_IN"),
    ]
    for kind, ref, val, x, y, n1, n2 in discretes:
        pins = sch.place(
            kind,
            ref,
            val,
            f"coupon:{'C' if kind == 'C' else 'R'}_0603_T016"
            if kind in "RC"
            else "coupon:PINHEADER_1X02_T016",
            x,
            y,
        )
        sch.stub_label(*pins["1"], (-1.0, 0.0), n1)
        sch.stub_label(*pins["2"], (1.0, 0.0), n2)

    j1 = sch.place(
        "J1",
        "J1",
        "Conn_02x05 bench header",
        "coupon:PINHEADER_2X05_T016",
        160.02,
        129.54,
    )
    j1_nets = {
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
    for num, net in j1_nets.items():
        px, py = j1[num]
        outward = (-1.0, 0.0) if int(num) % 2 == 1 else (1.0, 0.0)
        sch.stub_label(px, py, outward, net)

    tp_defs = [
        ("TP1", "+3V3_MIC", 120.65, 105.41),
        ("TP2", "CLK_ST", 120.65, 110.49),
        ("TP3", "CLK_ST", 120.65, 115.57),
        ("TP4", "D0", 135.89, 100.33),
        ("TP5", "D1", 135.89, 105.41),
        ("TP6", "CLK_FB", 135.89, 110.49),
    ]
    for ref, net, x, y in tp_defs:
        pins = sch.place("TP", ref, f"TP {net}", "coupon:TP_1.5mm_T016", x, y)
        sch.stub_label(*pins["1"], (-1.0, 0.0), net)

    sch.text(
        30,
        40,
        f"T-016 PDM mic bake-off coupon, variant {variant} ({spec['mpn']}). "
        "Four mics on one CDCLVC1112PWR output = worst-case four-load branch. "
        "No pulls on D0/D1. 0.50 mm NPTH acoustic ports. Buffer pin map UNVERIFIED - see README.",
    )

    lib_syms = "\n".join(
        sym_def(meta[0], meta[1], meta[2], meta[3], meta[4], prefix="coupon-symbols:")
        for meta in SYM_META.values()
    )
    body = "\n".join(sch.items)
    return (
        '(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n'
        f'\t(uuid "{sch.root_uuid}")\n\t(paper "A4")\n'
        "\t(lib_symbols\n" + lib_syms + "\n\t)\n" + body + "\n"
        '\t(sheet_instances (path "/" (page "1")))\n\t(embedded_fonts no)\n)\n'
    )


# --- PCB emitter ---------------------------------------------------------------------
NETS = [
    "",
    "GND",
    "+3V3_IN",
    "+3V3_MIC",
    "CLK_IN",
    "CLK_EN",
    "CLK_Y0",
    "CLK_ST",
    "CLK_FBR",
    "CLK_FB",
    "D0M",
    "D0",
    "D1M",
    "D1",
]
NET_ID = {name: i for i, name in enumerate(NETS)}


class Pcb:
    def __init__(self) -> None:
        self.items: list[str] = []

    def seg(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        net: str,
        layer: str = "F.Cu",
        w: float = 0.2,
    ) -> None:
        self.items.append(
            f"\t(segment (start {x0:.3f} {y0:.3f}) (end {x1:.3f} {y1:.3f}) (width {w}) "
            f'(layer "{layer}") (net {NET_ID[net]}) (uuid "{uid()}"))'
        )

    def path(
        self,
        pts: list[tuple[float, float]],
        net: str,
        layer: str = "F.Cu",
        w: float = 0.2,
    ) -> None:
        for a, b in zip(pts, pts[1:]):
            self.seg(a[0], a[1], b[0], b[1], net, layer, w)

    def via(self, x: float, y: float, net: str, size: float = 0.6, drill: float = 0.3) -> None:
        self.items.append(
            f'\t(via (at {x:.3f} {y:.3f}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") '
            f'(net {NET_ID[net]}) (uuid "{uid()}"))'
        )

    def zone(self, net: str, layer: str) -> None:
        self.items.append(
            f'\t(zone (net {NET_ID[net]}) (net_name "{net}") (layer "{layer}") (uuid "{uid()}") (hatch full 0.508)\n'
            "\t\t(connect_pads (clearance 0.15)) (min_thickness 0.2) (filled_areas_thickness no)\n"
            "\t\t(fill (thermal_gap 0.3) (thermal_bridge_width 0.3))\n"
            f"\t\t(polygon (pts (xy 0.5 0.5) (xy {BOARD_W - 0.5} 0.5) (xy {BOARD_W - 0.5} {BOARD_H - 0.5}) (xy 0.5 {BOARD_H - 0.5})))\n\t)"
        )

    def fp_0603(self, ref: str, value: str, x: float, y: float, rot: int, n1: str, n2: str) -> None:
        pads = []
        for num, (dx, dy), net in ((1, (-0.5, 0.0), n1), (2, (0.5, 0.0), n2)):
            w, h = 0.9, 1.0
            pads.append(
                f'\t\t(pad "{num}" smd roundrect (at {dx} {dy}) (size {w} {h}) (layers "F.Cu" "F.Paste" "F.Mask") '
                f'(roundrect_rratio 0.25) (net {NET_ID[net]} "{net}") (uuid "{uid()}"))'
            )
        self.items.append(
            f'\t(footprint "coupon:C_0603_T016" (layer "F.Cu") (uuid "{uid()}")\n'
            f"\t\t(at {x} {y} {rot})\n"
            + _fp_text("reference", ref, 0, -1.2, "F.SilkS")
            + _fp_text("value", value, 0, 1.2, "F.Fab")
            + "\n"
            + "\n".join(pads)
            + f'\n\t\t(fp_rect (start -0.8 -0.4) (end 0.8 0.4) (stroke (width 0.05) (type solid)) (fill no) (layer "F.Fab") (uuid "{uid()}"))'
            + f'\n\t\t(fp_rect (start -1.0 -0.75) (end 1.0 0.75) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{uid()}"))\n\t)'
        )

    def fp_mic(self, spec: dict, ref: str, x: float, y: float, nets: dict[int, str]) -> None:
        lines = [
            f'\t(footprint "coupon:{spec["name"]}" (layer "F.Cu") (uuid "{uid()}")',
            f"\t\t(at {x} {y} 0)",
            f'\t\t(descr "{spec["mpn"]} bottom-port PDM mic, T-016 coupon")',
            "\t\t(attr smd)",
            _fp_text("reference", ref, 0, -2.6, "F.SilkS"),
            _fp_text("value", spec["mpn"], 0, -3.6, "F.Fab"),
        ]
        for num, role, px, py, w, h in spec["pads"]:
            net = nets[num]
            lines.append(
                f'\t\t(pad "{num}" smd rect (at {px} {py}) (size {w} {h}) '
                f'(layers "F.Cu" "F.Paste" "F.Mask") (net {NET_ID[net]} "{net}") (uuid "{uid()}"))'
            )
        ro, ri = spec["ring_outer"] / 2, spec["ring_inner"] / 2
        prim = []
        for poly in _annulus_polys(ro, ri):
            pts = " ".join(f"(xy {px:.4f} {py:.4f})" for px, py in poly)
            prim.append(f"\t\t\t(gr_poly (pts {pts}) (stroke (width 0) (type solid)) (fill yes))")
        lines.append(
            f'\t\t(pad "3" smd custom (at 0 0) (size {ro * 2:.3f} {ro * 2:.3f}) (layers "F.Cu" "F.Paste" "F.Mask")\n'
            f'\t\t\t(net {NET_ID["GND"]} "GND")\n'
            "\t\t\t(options (clearance outline) (anchor circle))\n"
            "\t\t\t(primitives\n" + "\n".join(prim) + f'\n\t\t\t) (uuid "{uid()}"))'
        )
        lines.append(
            '\t\t(pad "" np_thru_hole circle (at 0 0) (size 0.5 0.5) (drill 0.5) (layers "*.Cu" "*.Mask") '
            f'(uuid "{uid()}"))'
        )
        bw, bh, (bcx, bcy) = spec["body"]
        x0, y0, x1, y1 = bcx - bw / 2, bcy - bh / 2, bcx + bw / 2, bcy + bh / 2
        lines.append(
            f'\t\t(fp_rect (start {x0:.3f} {y0:.3f}) (end {x1:.3f} {y1:.3f}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.Fab") (uuid "{uid()}"))'
        )
        cw, ch, (ccx, ccy) = spec["courtyard"]
        lines.append(
            f"\t\t(fp_rect (start {ccx - cw / 2:.3f} {ccy - ch / 2:.3f}) (end {ccx + cw / 2:.3f} {ccy + ch / 2:.3f}) "
            f'(stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{uid()}"))'
        )
        p1 = spec["pads"][0]
        lines.append(
            f"\t\t(fp_circle (center {p1[2]:.3f} {p1[3] + 0.65:.3f}) (end {p1[2] + 0.2:.3f} {p1[3] + 0.65:.3f}) "
            f'(stroke (width 0.15) (type solid)) (fill yes) (layer "F.SilkS") (uuid "{uid()}"))'
        )
        lines.append("\t)")
        self.items.append("\n".join(lines))

    def fp_tssop24(self, x: float, y: float, nets: dict[int, str]) -> None:
        pads = []
        for i in range(12):
            px = -3.575 + i * 0.65
            for num, py in ((i + 1, 2.8), (24 - i, -2.8)):
                net = nets.get(num, "")
                netattr = f'(net {NET_ID[net]} "{net}")' if net else ""
                pads.append(
                    f'\t\t(pad "{num}" smd rect (at {px:.3f} {py}) (size 0.4 1.5) '
                    f'(layers "F.Cu" "F.Paste" "F.Mask") {netattr} (uuid "{uid()}"))'
                )
        self.items.append(
            f'\t(footprint "coupon:TSSOP-24_4.4x7.8mm_P0.65mm_T016" (layer "F.Cu") (uuid "{uid()}")\n'
            f"\t\t(at {x} {y} 0)\n"
            + _fp_text("reference", "U1", 0, -4.2, "F.SilkS")
            + _fp_text("value", "CDCLVC1112PWR", 0, 4.2, "F.Fab")
            + "\n"
            + "\n".join(pads)
            + f'\n\t\t(fp_rect (start -3.9 -2.2) (end 3.9 2.2) (stroke (width 0.05) (type solid)) (fill no) (layer "F.Fab") (uuid "{uid()}"))'
            + f'\n\t\t(fp_rect (start -4.35 -3.75) (end 4.35 3.75) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{uid()}"))'
            + f'\n\t\t(fp_circle (center -4.15 3.1) (end -3.95 3.1) (stroke (width 0.15) (type solid)) (fill yes) (layer "F.SilkS") (uuid "{uid()}"))\n\t)'
        )

    def fp_header(
        self,
        ref: str,
        value: str,
        x: float,
        y: float,
        rows: int,
        cols: int,
        nets: dict[int, str],
    ) -> None:
        pads = []
        for c in range(cols):
            for r in range(rows):
                n = r * cols + c + 1
                net = nets[n]
                pads.append(
                    f'\t\t(pad "{n}" thru_hole circle (at {c * 2.54:.2f} {-r * 2.54:.2f}) (size 1.7 1.7) (drill 0.9) '
                    f'(layers "*.Cu" "*.Mask") (net {NET_ID[net]} "{net}") (uuid "{uid()}"))'
                )
        self.items.append(
            f'\t(footprint "coupon:PINHEADER_{cols}X{rows:02d}_T016" (layer "F.Cu") (uuid "{uid()}")\n'
            f"\t\t(at {x} {y} 0)\n"
            + _fp_text("reference", ref, 0, 2.0, "F.SilkS")
            + _fp_text("value", value, 0, -(rows - 1) * 2.54 - 2.0, "F.Fab")
            + "\n"
            + "\n".join(pads)
            + "\n\t)"
        )

    def fp_tp(self, ref: str, x: float, y: float, net: str, bottom: bool = False) -> None:
        cu = "B.Cu" if bottom else "F.Cu"
        mask = "B.Mask" if bottom else "F.Mask"
        silk = "B.SilkS" if bottom else "F.SilkS"
        self.items.append(
            f'\t(footprint "coupon:TP_1.5mm_T016" (layer "{cu}") (uuid "{uid()}")\n'
            f"\t\t(at {x} {y} 0)\n"
            + _fp_text("reference", ref, 0, -1.5, silk)
            + _fp_text("value", net, 0, 1.5, "F.Fab")
            + f'\n\t\t(pad "1" smd circle (at 0 0) (size 1.5 1.5) (layers "{cu}" "{mask}") (net {NET_ID[net]} "{net}") (uuid "{uid()}"))\n\t)'
        )

    def fp_hole(self, x: float, y: float) -> None:
        self.items.append(
            f'\t(footprint "coupon:MountingHole_2.2mm_T016" (layer "F.Cu") (uuid "{uid()}")\n'
            f"\t\t(at {x} {y} 0)\n"
            + _fp_text("reference", "H", 0, -1.8, "F.SilkS", hide=True)
            + _fp_text("value", "M2", 0, 1.8, "F.Fab", hide=True)
            + f'\n\t\t(pad "" np_thru_hole circle (at 0 0) (size 2.2 2.2) (drill 2.2) (layers "*.Cu" "*.Mask") (uuid "{uid()}"))\n\t)'
        )

    def silk_text(self, x: float, y: float, body: str, layer: str = "F.SilkS") -> None:
        self.items.append(
            f'\t(gr_text "{body}" (at {x} {y}) (layer "{layer}") (uuid "{uid()}")\n'
            "\t\t(effects (font (size 1.2 1.2) (thickness 0.2))))"
        )


def build_pcb(variant: str) -> str:
    spec = MIC_FOOTPRINTS[variant]
    pcb = Pcb()
    TRUNK_Y = 12.6

    # --- Mics + per-mic routing. M1/M3 SELECT low, M2/M4 SELECT high. ---
    for i, mx in enumerate(MIC_X):
        sel_net = "GND" if i % 2 == 0 else "+3V3_MIC"
        data_net = "D0M" if i < 2 else "D1M"
        pcb.fp_mic(
            spec,
            f"M{i + 1}",
            mx,
            MIC_Y,
            {1: data_net, 2: sel_net, 3: "GND", 4: "CLK_ST", 5: "+3V3_MIC"},
        )
        r_merge_x = 20.0 if i < 2 else 44.0
        pad1_x = r_merge_x - 0.5
        if variant == "SPH":
            # CLK: vertical right of the GND ring, 45-degree entry into pad 4 bottom.
            pcb.path(
                [
                    (mx + 1.4, TRUNK_Y),
                    (mx + 1.4, 18.9),
                    (mx + 0.9, 19.15),
                    (mx + 0.9, 19.32),
                ],
                "CLK_ST",
            )
            pcb.path([(mx + 1.15, 20.335), (mx + 1.8, 20.335)], "+3V3_MIC")
            pcb.via(mx + 1.8, 20.335, "+3V3_MIC")
            pcb.path([(mx - 1.15, 19.513), (mx - 1.8, 19.513)], sel_net)
            pcb.via(mx - 1.8, 19.513, sel_net)
            pcb.via(mx - 1.4, 17.5, "GND")
            pcb.via(mx - 1.4, 18.5, "GND")
            # Hard-tie the annular GND ring to a stitch via (do not rely on pour contact).
            pcb.path([(mx - 0.56, 17.58), (mx - 0.55, 16.5)], "GND", w=0.3)
            pcb.fp_0603(f"C{i + 1}", "100nF X7R", mx + 3.6, 18.0, 270, "+3V3_MIC", "GND")
            pcb.path([(mx + 3.6, 17.05), (mx + 3.6, 16.6)], "+3V3_MIC")
            pcb.via(mx + 3.6, 16.5, "+3V3_MIC")
            data_x = mx - 0.8375
            if i % 2 == 0:
                pcb.path(
                    [(data_x, 20.55), (data_x, 22.3), (pad1_x, 22.3), (pad1_x, 22.55)],
                    data_net,
                )
            else:
                pcb.path(
                    [(data_x, 20.55), (data_x, 23.8), (pad1_x, 23.8), (pad1_x, 23.45)],
                    data_net,
                )
        else:  # ICS
            # CLK: around the left of the GND ring, entry into pad 4 from the left.
            pcb.path([(mx - 1.4, TRUNK_Y), (mx - 1.4, 19.15), (mx + 1.05, 19.15)], "CLK_ST")
            pcb.path([(mx + 1.252, 16.85), (mx + 1.252, 16.1)], "+3V3_MIC")
            pcb.via(mx + 1.252, 16.1, "+3V3_MIC")
            pcb.path([(mx + 2.28, 18.837), (mx + 2.9, 18.837)], sel_net)
            pcb.via(mx + 2.9, 18.837, sel_net)
            pcb.via(mx - 2.1, 17.5, "GND")
            pcb.via(mx - 0.55, 16.5, "GND")
            # Hard-tie the annular GND ring to a stitch via (do not rely on pour contact).
            pcb.path([(mx - 0.56, 17.58), (mx - 0.55, 16.5)], "GND", w=0.3)
            pcb.via(mx + 0.55, 16.35, "GND")
            pcb.fp_0603(f"C{i + 1}", "100nF X7R", mx - 2.5, 18.0, 270, "+3V3_MIC", "GND")
            pcb.path([(mx - 2.5, 17.05), (mx - 2.5, 16.6)], "+3V3_MIC")
            pcb.via(mx - 2.5, 16.5, "+3V3_MIC")
            data_x = mx + 2.074
            ex_x = mx + 3.55
            if i % 2 == 0:
                pcb.path(
                    [
                        (data_x + 0.23, 17.162),
                        (ex_x, 17.162),
                        (ex_x, 22.3),
                        (pad1_x, 22.3),
                        (pad1_x, 22.55),
                    ],
                    data_net,
                )
            else:
                pcb.path(
                    [
                        (data_x + 0.23, 17.162),
                        (ex_x, 17.162),
                        (ex_x, 23.8),
                        (pad1_x, 23.8),
                        (pad1_x, 23.45),
                    ],
                    data_net,
                )

    # Inter-mic GND stitching vias keep the mid-row pour stitched to In1/B.Cu.
    for vx in (21.0, 33.0, 45.0):
        pcb.via(vx, 15.5, "GND")

    # --- Clock buffer area ---
    pcb.fp_tssop24(
        *U1_POS,
        {
            1: "CLK_IN",
            2: "CLK_EN",
            3: "GND",
            4: "CLK_Y0",
            5: "CLK_FBR",
            10: "GND",
            11: "+3V3_MIC",
            15: "GND",
            16: "+3V3_MIC",
            20: "GND",
            21: "+3V3_MIC",
            22: "+3V3_MIC",
        },
    )
    # Y0 source resistor, then the clock trunk with stubs to all four mics.
    pcb.fp_0603("R0", "10R", 16.5, 11.8, 0, "CLK_Y0", "CLK_ST")
    pcb.path([(8.375, 11.0), (8.375, 11.8), (15.55, 11.8)], "CLK_Y0")
    trunk_end = 52.4 if variant == "SPH" else 51.4
    trunk_start = 16.4 if variant == "SPH" else 13.6  # first mic's stub x
    pcb.path([(17.45, 11.8), (17.9, 11.8), (17.9, TRUNK_Y)], "CLK_ST", w=0.25)
    pcb.seg(trunk_start, TRUNK_Y, trunk_end, TRUNK_Y, "CLK_ST", w=0.25)
    # Y1 returned clock via R1 to J1 pin 9.
    pcb.fp_0603("R1", "10R", 9.025, 8.3, 270, "CLK_FB", "CLK_FBR")
    pcb.seg(9.025, 9.5, 9.025, 9.3, "CLK_FBR")
    pcb.fp_tp("TP6", 11.0, 8.8, "CLK_FBR")
    pcb.seg(9.525, 8.8, 11.0, 8.8, "CLK_FBR")
    pcb.seg(9.025, 7.35, 9.025, 6.8, "CLK_FB")
    pcb.via(9.025, 6.8, "CLK_FB")
    pcb.path([(9.025, 6.8), (62.73, 6.8), (62.73, 9.92)], "CLK_FB", layer="B.Cu")
    # 1G pulldown + enable from header (B.Cu run).
    pcb.fp_0603("R12", "100k", 9.5, 13.6, 0, "CLK_EN", "GND")
    pcb.seg(7.075, 9.5, 7.075, 12.46, "CLK_EN")
    pcb.via(7.075, 12.46, "CLK_EN")
    pcb.path([(62.73, 12.46), (7.075, 12.46)], "CLK_EN", layer="B.Cu")
    pcb.path([(8.4, 12.46), (8.4, 13.6)], "CLK_EN", layer="B.Cu")
    pcb.via(8.4, 13.6, "CLK_EN")
    pcb.path([(10.4, 13.6), (11.3, 13.6), (11.3, 15.3)], "GND")
    pcb.via(11.3, 15.3, "GND")
    # U1 VDD pin 11 via (top row) and bottom-row VDD vias.
    pcb.seg(12.925, 11.0, 12.925, 11.3, "+3V3_MIC")
    pcb.via(12.925, 11.3, "+3V3_MIC", size=0.5, drill=0.25)
    for vx in (11.625, 8.375, 7.725):
        pcb.seg(vx, 4.0, vx, 3.3, "+3V3_MIC")
        pcb.via(vx, 3.0, "+3V3_MIC")
    # Clock trunk test points: near (source end) and far (last load).
    pcb.path([(18.4, TRUNK_Y), (18.4, 14.0)], "CLK_ST")
    pcb.fp_tp("TP2", 18.4, 14.0, "CLK_ST")
    pcb.seg(trunk_end, TRUNK_Y, 53.5, TRUNK_Y, "CLK_ST")
    pcb.fp_tp("TP3", 53.5, TRUNK_Y, "CLK_ST")

    # --- U1 decoupling + bulk caps; VDD via below each cap, GND into the pour ---
    for cx, ref, val in (
        (6.5, "C5", "100nF X7R"),
        (8.9, "C6", "100nF X7R"),
        (11.3, "C7", "100nF X7R"),
        (13.7, "C8", "100nF X7R"),
        (16.1, "C9", "1uF"),
        (18.5, "C10", "10uF"),
    ):
        pcb.fp_0603(ref, val, cx, 2.0, 0, "+3V3_MIC", "GND")
        pcb.seg(cx - 0.5, 2.45, cx - 0.5, 2.9, "+3V3_MIC")
        pcb.via(cx - 0.5, 3.2, "+3V3_MIC")

    # --- Data merge jumpers + B.Cu connector runs + test points ---
    pcb.fp_0603("R13", "0R", 20.0, 23.0, 0, "D0M", "D0")
    pcb.fp_0603("R14", "0R", 44.0, 23.0, 0, "D1M", "D1")
    pcb.path([(20.95, 23.0), (21.5, 23.0), (21.5, 22.2)], "D0")
    pcb.via(21.5, 22.2, "D0")
    pcb.path([(21.5, 22.2), (60.5, 22.2), (60.5, 17.54)], "D0", layer="B.Cu")
    pcb.fp_tp("TP4", 30.0, 22.2, "D0", bottom=True)
    pcb.via(60.5, 17.54, "D0")
    pcb.seg(60.5, 17.54, 62.73, 17.54, "D0")
    pcb.seg(44.95, 23.0, 46.6, 23.0, "D1")
    pcb.via(46.6, 23.0, "D1")
    pcb.path(
        [(46.6, 23.0), (46.6, 24.2), (66.5, 24.2), (66.5, 16.1), (63.9, 16.1)],
        "D1",
        layer="B.Cu",
    )
    pcb.fp_tp("TP5", 50.0, 24.2, "D1", bottom=True)
    pcb.via(63.9, 16.1, "D1")
    pcb.path([(63.9, 16.1), (65.27, 16.1), (65.27, 17.54)], "D1")

    # --- Bench header, current-break jumper, rail test point ---
    pcb.fp_header(
        "J1",
        "Bench 2x05",
        62.73,
        20.08,
        5,
        2,
        {
            1: "+3V3_IN",
            2: "GND",
            3: "D0",
            4: "D1",
            5: "GND",
            6: "CLK_IN",
            7: "CLK_EN",
            8: "GND",
            9: "CLK_FB",
            10: "GND",
        },
    )
    pcb.fp_header("JP1", "JUMPER", 58.73, 25.5, 1, 2, {1: "+3V3_MIC", 2: "+3V3_IN"})
    pcb.path([(62.73, 20.08), (62.73, 25.5), (61.27, 25.5)], "+3V3_IN")
    pcb.seg(57.88, 25.5, 56.9, 25.5, "+3V3_MIC")
    pcb.fp_tp("TP1", 56.9, 25.5, "+3V3_MIC")

    # --- Clock input from header via bottom layer ---
    pcb.path(
        [
            (65.27, 15.0),
            (65.27, 13.7),
            (14.2, 13.7),
            (14.2, 14.6),
            (6.0, 14.6),
            (6.0, 12.6),
        ],
        "CLK_IN",
        layer="B.Cu",
    )
    pcb.via(6.0, 12.6, "CLK_IN")
    pcb.path([(6.0, 12.6), (6.0, 10.3), (6.3, 10.3)], "CLK_IN")

    for hx, hy in ((4, 4), (66, 4), (4, 26), (66, 26)):
        pcb.fp_hole(hx, hy)

    pcb.silk_text(35, 27.5, f"T-016 {spec['mpn']} coupon  rev A")
    pcb.silk_text(35, 25.9, "no wash; ports stay bare", layer="F.SilkS")
    pcb.silk_text(
        35,
        4.0,
        "4L 1.6mm JLC04161H-7628 intent; 4x 0.50mm NPTH ports: no plate/cu/mask/paste; ENIG",
        layer="Cmts.User",
    )

    pcb.items.append(
        '\t(gr_rect (start 0 0) (end 70 30) (stroke (width 0.05) (type solid)) (fill no) (layer "Edge.Cuts") '
        f'(uuid "{uid()}"))'
    )
    pcb.zone("GND", "F.Cu")
    pcb.zone("GND", "In1.Cu")
    pcb.zone("+3V3_MIC", "In2.Cu")
    pcb.zone("GND", "B.Cu")

    layers = "\n".join(
        [
            '\t\t(0 "F.Cu" signal)',
            '\t\t(1 "In1.Cu" signal)',
            '\t\t(2 "In2.Cu" signal)',
            '\t\t(31 "B.Cu" signal)',
            '\t\t(32 "B.Adhes" user "B.Adhes")',
            '\t\t(33 "F.Adhes" user "F.Adhes")',
            '\t\t(34 "B.Paste" user "B.Paste")',
            '\t\t(35 "F.Paste" user "F.Paste")',
            '\t\t(36 "B.SilkS" user "B.Silkscreen")',
            '\t\t(37 "F.SilkS" user "F.Silkscreen")',
            '\t\t(38 "B.Mask" user "B.Mask")',
            '\t\t(39 "F.Mask" user "F.Mask")',
            '\t\t(40 "Dwgs.User" user "User.Drawings")',
            '\t\t(41 "Cmts.User" user "User.Comments")',
            '\t\t(42 "Eco1.User" user "User.Eco1")',
            '\t\t(43 "Eco2.User" user "User.Eco2")',
            '\t\t(44 "Edge.Cuts" user)',
            '\t\t(45 "Margin" user)',
            '\t\t(46 "B.CrtYd" user "B.Courtyard")',
            '\t\t(47 "F.CrtYd" user "F.Courtyard")',
            '\t\t(48 "B.Fab" user "B.Fab")',
            '\t\t(49 "F.Fab" user "F.Fab")',
            '\t\t(50 "User.1" user)',
            '\t\t(51 "User.2" user)',
        ]
    )
    netdefs = "\n".join(f'\t(net {i} "{n}")' for i, n in enumerate(NETS))
    items = "\n".join(pcb.items)
    return (
        '(kicad_pcb (version 20260206) (generator "pcbnew") (generator_version "10.0")\n'
        '\t(general (thickness 1.6) (legacy_teardrops no))\n\t(paper "A4")\n'
        "\t(layers\n" + layers + "\n\t)\n"
        "\t(setup\n\t\t(pad_to_mask_clearance 0)\n\t)\n" + netdefs + "\n" + items + "\n)\n"
    )


FP_LIB_TABLE = """(fp_lib_table
  (version 7)
  (lib (name "coupon") (type "KiCad") (uri "${KIPRJMOD}/libs/coupon.pretty") (options "") (descr "T-016 coupon footprints"))
)
"""

SYM_LIB_TABLE = """(sym_lib_table
  (version 7)
  (lib (name "coupon-symbols") (type "KiCad") (uri "${KIPRJMOD}/coupon-symbols.kicad_sym") (options "") (descr "T-016 coupon symbols"))
)
"""


def _kicad_pro(name: str) -> str:
    # Template from a known-good KiCad 10 project file; a from-scratch minimal
    # project crashed kicad-cli pcb drc (missing sections).
    import json

    ref = json.loads(
        (Path(__file__).resolve().parents[2] / "rx_amp_sim" / "rx_amp_sim.kicad_pro").read_text()
    )
    ref["meta"]["filename"] = f"{name}.kicad_pro"
    return json.dumps(ref, indent=2) + "\n"


def write_variant(variant: str) -> Path:
    spec = MIC_FOOTPRINTS[variant]
    name = f"{variant.lower()}-coupon"
    d = OUT / name
    (d / "libs" / "coupon.pretty").mkdir(parents=True, exist_ok=True)
    (d / f"{name}.kicad_pro").write_text(_kicad_pro(name), encoding="utf-8")
    (d / f"{name}.kicad_sch").write_text(build_schematic(variant, name), encoding="utf-8")
    (d / f"{name}.kicad_pcb").write_text(build_pcb(variant), encoding="utf-8")
    (d / "fp-lib-table").write_text(FP_LIB_TABLE, encoding="utf-8")
    (d / "sym-lib-table").write_text(SYM_LIB_TABLE, encoding="utf-8")

    pretty = d / "libs" / "coupon.pretty"
    (pretty / f"{spec['name']}.kicad_mod").write_text(emit_mic_footprint(spec), encoding="utf-8")
    (pretty / "C_0603_T016.kicad_mod").write_text(emit_smd0603("C_0603_T016"), encoding="utf-8")
    (pretty / "R_0603_T016.kicad_mod").write_text(emit_smd0603("R_0603_T016"), encoding="utf-8")
    (pretty / "TSSOP-24_4.4x7.8mm_P0.65mm_T016.kicad_mod").write_text(
        emit_tssop24(), encoding="utf-8"
    )
    (pretty / "PINHEADER_2X05_T016.kicad_mod").write_text(
        emit_pinheader(5, 2, "PINHEADER_2X05_T016"), encoding="utf-8"
    )
    (pretty / "PINHEADER_1X02_T016.kicad_mod").write_text(
        emit_pinheader(1, 2, "PINHEADER_1X02_T016"), encoding="utf-8"
    )
    (pretty / "TP_1.5mm_T016.kicad_mod").write_text(emit_testpoint(), encoding="utf-8")
    (pretty / "MountingHole_2.2mm_T016.kicad_mod").write_text(
        emit_mounting_hole(), encoding="utf-8"
    )

    sym_defs = "\n".join(
        sym_def(meta[0], meta[1], meta[2], meta[3], meta[4]) for meta in SYM_META.values()
    )
    (d / "coupon-symbols.kicad_sym").write_text(
        '(kicad_symbol_lib (version 20231120) (generator "t016-coupon-generator") (generator_version "1.0")\n'
        + sym_defs
        + ")\n",
        encoding="utf-8",
    )
    return d


def main() -> None:
    for variant in ("SPH", "ICS"):
        d = write_variant(variant)
        print(f"wrote {d}")


if __name__ == "__main__":
    main()
