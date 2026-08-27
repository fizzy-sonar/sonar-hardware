#!/usr/bin/env python3
"""T-016 coupon fabrication export: fill zones with pcbnew, save a build copy,
then export gerbers/drill/position files with kicad-cli.

kicad-cli pcb drc cannot run in this sandbox (SIGABRT even on known-good
boards; see T-006 harness notes) so zone filling is done here via pcbnew and
verification lives in verify_coupon.py. Run from the repo root:
    KiCad python: /Applications/KiCad/.../python3.9 coupons/mic-bakeoff/fab_export.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pcbnew

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
            [cli, "pcb", "export", "drill", "-o", str(gerb), str(filled)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                cli,
                "pcb",
                "export",
                "pos",
                "--side",
                "front",
                "-o",
                str(outdir / f"{name}-pos.csv"),
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
