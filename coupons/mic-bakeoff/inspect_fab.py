#!/usr/bin/env python3
"""Check actual drill/placement/BOM exports; optionally render Gerbers themselves.

Run after check_coupons.sh. For visual inspection (also needs rsvg-convert):
  uv run --with gerbonara==1.6.3 python coupons/mic-bakeoff/inspect_fab.py --render
Rendering is independent of KiCad's board SVG output. These are inspection
artifacts, not a fabricator's DFM approval or an assembly rotation conversion.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "build/t016"


def drill_hits(path):
    text = path.read_text()
    assert "METRIC" in text and "G90" in text, path
    tools = {n: float(size) for n, size in re.findall(r"^T(\d+)C([\d.]+)$", text, re.M)}
    selected = None
    hits = []
    for line in text.splitlines():
        if re.fullmatch(r"T\d+", line):
            selected = line[1:]
        elif match := re.fullmatch(r"X(-?[\d.]+)Y(-?[\d.]+)", line):
            hits.append((tools[selected], *map(float, match.groups())))
    return hits


def inspect(variant, render):
    name = f"{variant}-coupon"
    outdir = BUILD / f"{name}-fab"
    gerb = outdir / "gerbers"
    npth = gerb / f"{name}-NPTH.drl"
    pth = gerb / f"{name}-PTH.drl"
    assert not (gerb / f"{name}.drl").exists(), "Obsolete mixed drill file present"
    assert "NonPlated" in npth.read_text() and "MixedPlating" not in npth.read_text()
    assert "NonPlated" not in pth.read_text()
    expected_ports = {(0.5, x, -18.0) for x in (15.0, 27.0, 39.0, 51.0)}
    holes = drill_hits(npth)
    assert len(holes) == 8 and {h for h in holes if h[0] == 0.5} == expected_ports
    assert sum(h[0] == 2.2 for h in holes) == 4
    assert all(h[0] in (0.25, 0.3, 0.9) for h in drill_hits(pth))
    print(f"PASS {variant}: actual drill files separate PTH/NPTH; four exact acoustic ports")

    with (outdir / f"{name}-pos.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    by_ref = {r["Ref"]: r for r in rows}
    expected_smd = {f"C{i}" for i in range(1, 12)} | {f"M{i}" for i in range(1, 5)}
    expected_smd |= {"U1", "R0", "R1", "R12", "R13", "R14"}
    assert len(rows) == len(by_ref) == 21 and by_ref.keys() == expected_smd
    assert all(r["Side"] == "top" for r in rows)
    with (outdir / f"{name}-origin-pos.csv").open() as stream:
        origins = {r["Ref"]: r for r in csv.DictReader(stream)}
    # Independent body-centre offsets from the two manufacturer drawings.
    dx, dy = (0, -0.971) if variant == "sph" else (0.710, 0)
    for i, x in enumerate((15, 27, 39, 51), 1):
        row = by_ref[f"M{i}"]
        assert (float(row["PosX"]), float(row["PosY"]), float(row["Rot"])) == (x + dx, -18 + dy, 0)
        origin = origins[f"M{i}"]
        assert (float(origin["PosX"]), float(origin["PosY"])) == (x, -18)
    assert float(by_ref["U1"]["PosX"]) == 10 and float(by_ref["U1"]["PosY"]) == -7.5
    for ref in ("C1", "C2", "C3", "C4", "C7", "C8", "R1"):
        assert float(by_ref[ref]["Rot"]) == -90, ref
    assert float(by_ref["C11"]["Rot"]) == 90
    with (BUILD / f"{variant}-bom.csv").open() as stream:
        bom = list(csv.DictReader(stream))
    assert {r["Refs"] for r in bom} == expected_smd | {"J1", "JP1"}
    print(
        f"PASS {variant}: metric centroid CSV, 21 SMD placements, 23 BOM components; no bare pads"
    )

    if render:
        from gerbonara.rs274x import GerberFile

        for suffix in (
            "F_Cu.gtl",
            "In1_Cu.g1",
            "In2_Cu.g2",
            "B_Cu.gbl",
            "F_Paste.gtp",
            "F_Mask.gts",
        ):
            source = gerb / f"{name}-{suffix}"
            svg = outdir / f"gerber-{suffix}.svg"
            svg.write_text(str(GerberFile.open(source).to_svg(force_bounds=((0, -30), (70, 0)))))
            subprocess.run(
                [
                    "rsvg-convert",
                    "--background-color",
                    "white",
                    "-w",
                    "2100",
                    "-o",
                    str(svg.with_suffix(".png")),
                    str(svg),
                ],
                check=True,
            )
        print(f"PASS {variant}: six actual Gerber layers rendered independently for visual review")

    sources = [
        p
        for p in (ROOT / f"coupons/mic-bakeoff/{name}").rglob("*")
        if p.suffix in (".kicad_pcb", ".kicad_sch", ".kicad_pro", ".kicad_sym", ".kicad_mod")
        or p.name in ("fp-lib-table", "sym-lib-table")
    ]
    artifacts = list(gerb.glob("*")) + [
        outdir / f"{name}-pos.csv",
        outdir / f"{name}-origin-pos.csv",
        BUILD / f"{variant}-bom.csv",
    ]
    manifest = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(sources + artifacts)
        if p.is_file()
    }
    (outdir / "SHA256.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()
    for variant in ("sph", "ics"):
        inspect(variant, args.render)
