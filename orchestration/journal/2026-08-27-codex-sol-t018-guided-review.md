# 2026-08-27 — codex/sol-t018: guided visual review

## What changed

- Expanded `scripts/gen_review_page.py` into the single guided surface Joshua
  asked for: eight previous/next steps, a jump menu, “show everything” and print
  modes, full-resolution images, persistent checkbox/notes state, and a generated
  response that can be pasted back into an agent session.
- Made every visual current at generation time. The script now exports the full
  50-sheet Sonar schematic set and multipage PDF; both coupon schematics; and top/
  bottom 2D copper/mask/silkscreen plus top/bottom 3D views for the main PCB, SPH
  coupon, and ICS coupon.
- Put the physical-state boundary directly in the review: the main PCB render is
  sparse because it is the legacy pre-v2 file and P3 has not started. It is marked
  NOT FOR APPROVAL with DRC/unconnected/footprint counts pulled from the live
  report. The two coupon layouts are correctly presented as the physical designs
  currently at CP-BM review.
- Added `scripts/check_review_page.py` for required steps, decision items, unique
  IDs, local links, PNG/SVG/PDF integrity, render dimensions, required assets, and
  JavaScript syntax. Added `scripts/open_review.sh` as the one-command regenerate,
  verify, and open path; `--live` includes the full 17-test gateware run.
- Updated `orchestration/review/JOSHUA-REVIEW-PLAN.md` with the easy path.

## Verification

`python3 scripts/gen_review_page.py --skip-gateware`:

    link check: 157 local src/href attributes, 157 resolve, 0 broken
    assets copied: 72
    link check: PASS

`python3 scripts/check_review_page.py`:

    review page: 8 steps, 11 review items, 71 images, 157 local references
    required assets: 18/18 present
    review page checks: PASS

Also PASS: `ruff check`, `ruff format --check`, `bash -n scripts/open_review.sh`,
and `git diff --check`. Visual inspection covered a 1440 px page preview, all six
3D board renders, the sparse main-board 2D view, and coupon top/bottom 2D views.
The in-app browser plugin could not bootstrap because its installed runtime points
at a stale package version; Quick Look and direct image inspection provided the
visual check. The standalone page and normal browser launcher are unaffected.

## State / next step

T-018 is done. No KiCad, PCB, gateware, or user project file changed. Joshua runs
`./scripts/open_review.sh`, works through the persistent review items, builds the
summary in step 8, and pastes it back. That supplies the human decisions needed to
advance D013, T-007, CP-B, and CP-BM.
