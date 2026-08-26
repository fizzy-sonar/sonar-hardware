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
  label=$1; kind=$2; expected=$3; output=$4; shift 4
  echo "== $label"
  "$@" >"$BUILD/$label.stdout" 2>"$BUILD/$label.stderr"
  rc=$?
  echo "exit=$rc"
  if [ "$rc" -eq 0 ]; then
    [ -e "$output" ] || { echo "HARNESS_ERROR: missing output $output"; failures=$((failures + 1)); }
  elif [ "$kind" = baseline ] && [ "$rc" -eq "$expected" ]; then
    echo "baseline violation exit accepted: $rc"
  else
    echo "HARNESS_ERROR: unexpected $kind exit $rc"
    failures=$((failures + 1))
  fi
}

# Top-level sheets are sufficient: KiCad follows hierarchical sheet references.
for pair in \
  "sonar sonar-v1-pcb/sonar.kicad_sch" \
  "rx_amp_sim rx_amp_sim/rx_amp_sim.kicad_sch" \
  "txrx_dev tx-rx-dev-board/src/tx-rx-dev-board.kicad_sch"; do
  name=${pair%% *}; sheet=${pair#* }
  [ -f "$ROOT/$sheet" ] || continue
  run "${name}_erc" baseline 5 "$BUILD/${name}-erc.rpt" "$CLI" sch erc --severity-all --exit-code-violations -o "$BUILD/${name}-erc.rpt" "$ROOT/$sheet"
  run "${name}_netlist" export 0 "$BUILD/${name}.net" "$CLI" sch export netlist -o "$BUILD/${name}.net" "$ROOT/$sheet"
  run "${name}_pdf" export 0 "$BUILD/${name}.pdf" "$CLI" sch export pdf -o "$BUILD/${name}.pdf" "$ROOT/$sheet"
  run "${name}_svg" export 0 "$BUILD/${name}-svg" "$CLI" sch export svg -o "$BUILD/${name}-svg" "$ROOT/$sheet"
  run "${name}_bom" export 0 "$BUILD/${name}-bom.csv" "$CLI" sch export bom -o "$BUILD/${name}-bom.csv" "$ROOT/$sheet"
done

for pair in \
  "sonar sonar-v1-pcb/sonar.kicad_pcb" \
  "rx_amp_sim rx_amp_sim/rx_amp_sim.kicad_pcb" \
  "txrx_dev tx-rx-dev-board/src/tx-rx-dev-board.kicad_pcb"; do
  name=${pair%% *}; pcb=${pair#* }
  [ -f "$ROOT/$pcb" ] || continue
  run "${name}_drc" baseline 5 "$BUILD/${name}-drc.rpt" "$CLI" pcb drc --severity-all --exit-code-violations -o "$BUILD/${name}-drc.rpt" "$ROOT/$pcb"
done

if [ "$failures" -gt 0 ]; then
  echo "SUMMARY: $failures harness/tool failures; baseline ERC/DRC violations were soft-accepted."
  exit 1
fi
echo "SUMMARY: all invoked KiCad commands completed successfully."
exit 0
