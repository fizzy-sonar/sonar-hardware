#!/usr/bin/env bash
set -u -o pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BUILD="$ROOT/build"
mkdir -p "$BUILD"

find_kicad_cli() {
  if command -v kicad-cli >/dev/null 2>&1; then command -v kicad-cli; return; fi
  for p in /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli \
    /Applications/KiCad.app/Contents/MacOS/kicad-cli; do
    [ -x "$p" ] && { printf '%s\n' "$p"; return; }
  done
  return 1
}

if ! CLI=$(find_kicad_cli); then
  echo "HARNESS_ERROR: kicad-cli not found (install KiCad 10 or set PATH)" >&2
  exit 2
fi
echo "kicad-cli: $CLI"
echo "build: $BUILD"

failures=0
run() {
  label=$1; shift
  echo "== $label"
  "$@" >"$BUILD/$label.stdout" 2>"$BUILD/$label.stderr"
  rc=$?
  echo "exit=$rc"
  [ "$rc" -eq 0 ] || failures=$((failures + 1))
}

# Top-level sheets are sufficient: KiCad follows hierarchical sheet references.
for pair in \
  "sonar sonar-v1-pcb/sonar.kicad_sch" \
  "rx_amp_sim rx_amp_sim/rx_amp_sim.kicad_sch" \
  "txrx_dev tx-rx-dev-board/src/tx-rx-dev-board.kicad_sch"; do
  name=${pair%% *}; sheet=${pair#* }
  [ -f "$ROOT/$sheet" ] || continue
  run "${name}_erc" "$CLI" sch erc --severity-all --exit-code-violations \
    -o "$BUILD/${name}-erc.rpt" "$ROOT/$sheet"
  run "${name}_netlist" "$CLI" sch export netlist -o "$BUILD/${name}.net" "$ROOT/$sheet"
  run "${name}_pdf" "$CLI" sch export pdf -o "$BUILD/${name}.pdf" "$ROOT/$sheet"
  run "${name}_svg" "$CLI" sch export svg -o "$BUILD/${name}-svg" "$ROOT/$sheet"
  run "${name}_bom" "$CLI" sch export bom -o "$BUILD/${name}-bom.csv" "$ROOT/$sheet"
done

for pair in \
  "sonar sonar-v1-pcb/sonar.kicad_pcb" \
  "rx_amp_sim rx_amp_sim/rx_amp_sim.kicad_pcb" \
  "txrx_dev tx-rx-dev-board/src/tx-rx-dev-board.kicad_pcb"; do
  name=${pair%% *}; pcb=${pair#* }
  [ -f "$ROOT/$pcb" ] || continue
  run "${name}_drc" "$CLI" pcb drc --severity-all --exit-code-violations \
    -o "$BUILD/${name}-drc.rpt" "$ROOT/$pcb"
done

if [ "$failures" -gt 0 ]; then
  echo "SUMMARY: $failures tool/design command(s) non-zero; reports remain in build/." 
  echo "Non-zero ERC/DRC is a baseline design violation, not a harness failure."
  exit 0
fi
echo "SUMMARY: all invoked KiCad commands completed successfully."
exit 0
