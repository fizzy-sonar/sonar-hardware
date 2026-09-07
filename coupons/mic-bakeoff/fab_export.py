#!/usr/bin/env python3
"""T-016 coupon fabrication export: fill zones with pcbnew, save a build copy,
then export gerbers/drill/position files with kicad-cli.

Full DRC is mandatory before exporting. If KiCad aborts in a sandbox, run
with approved host access; do not bypass this gate. Run from the repo root:
    KiCad python: /Applications/KiCad/.../python3.9 coupons/mic-bakeoff/fab_export.py
"""

from __future__ import annotations

import subprocess
import sys
import csv
from pathlib import Path

import pcbnew
from generate_coupon import MIC_FOOTPRINTS

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "build" / "t016"
CLI_CANDIDATES = [
    "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
    "/Applications/KiCad.app/Contents/MacOS/kicad-cli",
    "kicad-cli",
]
LAYERS = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts"


def find_cli() -> str:
    for c in CLI_CANDIDATES:
        if Path(c).exists():
            return c
    return "kicad-cli"


def main() -> None:
    cli = find_cli()
    for variant in ("sph", "ics"):
        name = f"{variant}-coupon"
        src = ROOT / "coupons" / "mic-bakeoff" / name / f"{name}.kicad_pcb"
        outdir = BUILD / f"{name}-fab"
        outdir.mkdir(parents=True, exist_ok=True)
        filled = outdir / f"{name}.kicad_pcb"

        board = pcbnew.LoadBoard(str(src))
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        pcbnew.SaveBoard(str(filled), board)
        # sibling project file so kicad-cli pcb commands do not crash
        (outdir / f"{name}.kicad_pro").write_text(
            (ROOT / "coupons" / "mic-bakeoff" / name / f"{name}.kicad_pro").read_text()
        )

        subprocess.run(
            [
                cli,
                "pcb",
                "drc",
                "--refill-zones",
                "--severity-all",
                "--exit-code-violations",
                "-o",
                str(outdir / f"{name}-drc.rpt"),
                str(src),
            ],
            check=True,
            capture_output=True,
        )

        gerb = outdir / "gerbers"
        gerb.mkdir(exist_ok=True)
        subprocess.run(
            [
                cli,
                "pcb",
                "export",
                "gerbers",
                "-l",
                LAYERS,
                "-o",
                str(gerb),
                str(filled),
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                cli,
                "pcb",
                "export",
                "drill",
                "--excellon-separate-th",
                "--generate-map",
                "--map-format",
                "svg",
                "--generate-report",
                "-o",
                str(gerb),
                str(filled),
            ],
            check=True,
            capture_output=True,
        )
        # Retire only this generator's obsolete mixed-plating drill output.
        # Shipping it beside the separated files would make the drill set ambiguous.
        (gerb / f"{name}.drl").unlink(missing_ok=True)
        subprocess.run(
            [
                cli,
                "pcb",
                "export",
                "pos",
                "--format",
                "csv",
                "--units",
                "mm",
                "--smd-only",
                "--side",
                "front",
                "-o",
                str(outdir / f"{name}-origin-pos.csv"),
                str(filled),
            ],
            check=True,
            capture_output=True,
        )
        # Mic footprint origins are acoustic ports, not package centroids.
        # Preserve the raw KiCad export, and provide a body-centre placement
        # file so the assembler does not shift every microphone off its port.
        with (outdir / f"{name}-origin-pos.csv").open() as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames
            positions = list(reader)
        dx, dy = MIC_FOOTPRINTS[variant.upper()]["body"][2]
        for row in positions:
            if row["Ref"] in ("M1", "M2", "M3", "M4"):
                if float(row["Rot"]) != 0 or row["Side"] != "top":
                    raise ValueError(
                        "Re-audit mic centroid transform for rotated/bottom placements"
                    )
                row["PosX"] = f"{float(row['PosX']) + dx:.6f}"
                row["PosY"] = f"{float(row['PosY']) - dy:.6f}"
        with (outdir / f"{name}-pos.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(positions)
        for layer in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu", "F.Paste", "F.Mask"):
            subprocess.run(
                [
                    cli,
                    "pcb",
                    "export",
                    "svg",
                    "--mode-single",
                    "--page-size-mode",
                    "2",
                    "-l",
                    layer + ",Edge.Cuts",
                    "-o",
                    str(outdir / f"{name}-{layer}.svg"),
                    str(filled),
                ],
                check=True,
                capture_output=True,
            )
        subprocess.run(
            [
                cli,
                "pcb",
                "export",
                "svg",
                "-l",
                "F.Cu,In1.Cu,In2.Cu,B.Cu,F.SilkS,Edge.Cuts",
                "-o",
                str(outdir / f"{name}-filled.svg"),
                str(filled),
            ],
            check=True,
            capture_output=True,
        )
        print(f"{name}: fab package written to {outdir}")


if __name__ == "__main__":
    sys.exit(main())
