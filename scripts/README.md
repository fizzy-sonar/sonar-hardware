# KiCad check harness

Run from the repository root with `./scripts/check.sh`. The script locates
`kicad-cli` on `PATH` or at the standard KiCad 10 macOS application path,
creates the gitignored `build/` directory, and exports ERC/DRC reports, netlists,
PDF/SVG schematics, and BOM CSVs. It is idempotent: each run overwrites the same
named outputs and does not edit design files.

Exit status 2 means the harness could not run (missing `kicad-cli`). KiCad command
failures are summarized but return status 0 so known baseline ERC/DRC violations
do not block development; inspect `build/*.stdout`, `build/*.stderr`, and reports.
Once P2 establishes a clean baseline, `--exit-code-violations` can be promoted to
a CI-failing policy. CI runners must install KiCad 10 and invoke this script.
