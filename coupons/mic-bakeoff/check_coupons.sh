#!/usr/bin/env bash
# T-016 coupon verification runner. kicad-cli pcb drc cannot run sandboxed
# (SIGABRT on any board); the pcbnew-based verify_coupon.py substitutes here.
set -u -o pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$ROOT"
export XDG_CACHE_HOME="$ROOT/build/xdg-cache"
if [ -z "${HOME_OK:-}" ]; then export HOME="$ROOT/build/home"; fi
mkdir -p "$XDG_CACHE_HOME/fontconfig" "$ROOT/build/t016"

CLI=$(command -v kicad-cli || echo /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli)
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9
failures=0
note() { echo "== $*"; }

note "regenerate coupons (idempotent)"
python3 coupons/mic-bakeoff/generate_coupon.py
git -C "$ROOT" diff --quiet -- coupons/mic-bakeoff/sph-coupon coupons/mic-bakeoff/ics-coupon \
  && echo "regen: no diff (deterministic)" || { echo "regen produced a diff"; }

for v in sph ics; do
  note "$v ERC"
  "$CLI" sch erc --severity-all -o "build/t016/$v-erc.rpt" \
    "coupons/mic-bakeoff/$v-coupon/$v-coupon.kicad_sch" >/dev/null 2>&1
  # Reviewed waivers only: 2x pin_to_pin (SELECT-paired DATA), 2x power_pin_not_driven.
  count=$(grep -c "^\[" "build/t016/$v-erc.rpt" || true)
  echo "erc messages: $count (expected 4 reviewed waivers)"
  [ "$count" -eq 4 ] || failures=$((failures + 1))
  note "$v BOM"
  "$CLI" sch export bom -o "build/t016/$v-bom.csv" \
    "coupons/mic-bakeoff/$v-coupon/$v-coupon.kicad_sch" >/dev/null 2>&1
done

note "geometric verification (pcbnew: fill, connectivity, clearance, structure)"
"$KPY" coupons/mic-bakeoff/verify_coupon.py || failures=$((failures + 1))

note "fab export (gerbers/drill/pos, zones filled)"
"$KPY" coupons/mic-bakeoff/fab_export.py || failures=$((failures + 1))

note "analysis selftest + normative block byte-identity"
python3 analysis/pdm_bakeoff.py --selftest || failures=$((failures + 1))

note "lint"
ruff check analysis/pdm_bakeoff.py coupons/mic-bakeoff/ || failures=$((failures + 1))
ruff format --check analysis/pdm_bakeoff.py coupons/mic-bakeoff/ || failures=$((failures + 1))
git -C "$ROOT" diff --check || failures=$((failures + 1))

if [ "$failures" -gt 0 ]; then echo "SUMMARY: $failures failing steps"; exit 1; fi
echo "SUMMARY: coupon package checks passed"
