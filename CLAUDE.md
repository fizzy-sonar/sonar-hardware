# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A KiCad hardware monorepo for the Sonar ultrasonic project. There is **no software build/test pipeline** — work is done in KiCad GUIs against `.kicad_sch` / `.kicad_pcb` / `.kicad_sym` / `.kicad_mod` files. The only executable is the library setup script.

## Repo layout

| Directory          | Role                                                                  |
| ------------------ | --------------------------------------------------------------------- |
| `sonar-library/`   | Shared KiCad symbol + footprint + 3D-model + SPICE library            |
| `sonar-v1-pcb/`    | Main board: power tree, 8-element transducer array, TX h-bridge, RX amp |
| `tx-rx-dev-board/` | Earlier dev board for prototyping TX/RX circuitry (`src/`)            |
| `rx_amp_sim/`      | Standalone KiCad project used for SPICE-simulating the RX amp         |

## Setup

To register the shared library with the local KiCad install:

```bash
./sonar-library/setup-kicad.py            # default: KiCad 10.0 config dir
./sonar-library/setup-kicad.py --kicad-version 9.0
./sonar-library/setup-kicad.py --config-dir /path/to/kicad/config
```

Requires `uv` (the script has an inline PEP 723 header — `uv run` resolves `psutil` automatically). The legacy `setup-kicad.sh` does the same job in pure bash.

What it writes to KiCad's user config:
- Adds a `sonar-library` entry to the global `sym-lib-table` and `fp-lib-table`
- Sets path variables in `kicad_common.json`:
  - `SONAR_SYMBOL_DIR` → `sonar-library/`
  - `SONAR_FOOTPRINT_DIR` → `sonar-library/`
  - `SONAR_SPICE_DIR` → `sonar-library/spice-models/`

The script refuses to run while KiCad is open — KiCad rewrites `kicad_common.json` on exit and would clobber the path vars. The top-level `README.md` tells you to run `./setup-kicad.sh` from the repo root, but the script lives in `sonar-library/`; run it from there.

## How library resolution works (important)

Two layers, and both are in use:

1. **Global / shared** (`sonar-library`) — referenced via the `SONAR_SYMBOL_DIR` / `SONAR_FOOTPRINT_DIR` env vars that `setup-kicad.py` plants in `kicad_common.json`. Any project on this machine can `${SONAR_SYMBOL_DIR}/sonar-library.kicad_sym`.
2. **Project-local** — each PCB project also has its own `sym-lib-table` / `fp-lib-table` next to the `.kicad_pro`. For `sonar-v1-pcb/`:
   - `sym-lib-table` registers `sonar_lib` → `${KIPRJMOD}/sonar_lib.kicad_sym` (project-only symbols)
   - `fp-lib-table` registers `Sonar` → `${KIPRJMOD}/libs/Sonar.pretty` (project-only footprints) **and** re-registers `sonar-library` via a relative path `${KIPRJMOD}/../sonar-library/sonar-library.pretty`

When adding a part: prefer the shared `sonar-library` if the part is reusable; only put it in the per-project `sonar_lib.kicad_sym` / `libs/Sonar.pretty` if it's truly board-specific.

## sonar-v1-pcb structure

`sonar.kicad_sch` is the top-level sheet; the rest are hierarchical sub-sheets pulled in from it. Roughly grouped:

- **Power tree**: `power_supply.kicad_sch`, `5_to_10_boost.kicad_sch`, `5v_to_12v_boost.kicad_sch`, `inverting_buck_boost.kicad_sch` (active; `_OLD` is the prior revision kept around), `-10v_negative_ldo.kicad_sch`, `2.75V_ldo.kicad_sch`, `12v_to_10v_ldo.kicad_sch`, `5V_in_adjustable_buck.kicad_sch`, `ideal_diode.kicad_sch`, `power_mux.kicad_sch`
- **TX**: `20kHz-h-bridge.kicad_sch` (driver) → `eight_transducer_array.kicad_sch` / `tx_transducer.kicad_sch`
- **RX**: `rx_amp.kicad_sch`

`rx_amp_sim/` mirrors the RX amp into a separate `.kicad_pro` so it can be SPICE-simulated against models in `sonar-library/spice-models/` without dragging the rest of the schematic in.

## Working conventions

- Don't edit auto-generated artifacts under `*-backups/`, `.history/`, `*.bak`, `sonar_lib.bak`, etc. They're either KiCad's autosaves or VS Code Local History.
- KiCad's `*.kicad_prl` files are user-local and gitignored — don't commit them.
- When you hand-edit `.kicad_sch` / `.kicad_pcb` (e.g. mass property changes), close KiCad first; KiCad will silently overwrite on save otherwise.
- Footprints live in `sonar-library/sonar-library.pretty/` (reusable) and `sonar-v1-pcb/libs/Sonar.pretty/` (project-only). 3D `.step` files for shared parts go in `sonar-library/3d-models/`.
- License is GPL v3.0 for the whole repo.
