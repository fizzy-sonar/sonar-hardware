---
id: T-018
title: Guided visual review page for Joshua
status: done
phase: P2
tier: mid        # Python/HTML review tooling plus KiCad render orchestration
priority: 1
assignee: codex/sol-t018
depends_on: [T-011, T-012, T-013]
needs_human: false
created: 2026-08-27
updated: 2026-08-27
---

## Goal

Turn the existing generated review page into the single guided surface Joshua can
use for the current human gates. It must show the actual analysis plots, current
schematic renders, coupon schematics and layouts, gateware/host evidence, and the
existing main-board PCB state without implying that the legacy pre-P3 layout is a
finished v2 layout.

## Definition of Done

- `scripts/gen_review_page.py` produces `build/review/index.html` from a clean
  build directory and verifies every local image/document link.
- The page has a guided review mode with persistent local progress, clear previous
  and next controls, and the exact Joshua-only decision/checklist items.
- Current main schematic sheets and top sheet are visible at useful resolution.
- Main-board PCB top/bottom 2D and 3D renders are visible and loudly identified as
  legacy/pre-v2/P3-not-started; coupon schematic plus top/bottom 2D and 3D renders
  are visible for both candidates.
- Missing or failed renders degrade to an explicit warning rather than a broken
  image.
- Verification includes the generator link check, HTML structural checks, image
  dimension/format checks, and a visual inspection of the resulting page.

## Verification

```text
python3 scripts/gen_review_page.py --skip-gateware
python3 scripts/check_review_page.py
git diff --check
```

## Log

- 2026-08-27 codex/sol-t018: ticket created and claimed from Joshua's request for
  an easy guided review showing the renders, layouts, and complete evidence set.
- 2026-08-27 codex/sol-t018: completed the guided page and one-command launcher.
  `scripts/gen_review_page.py` now freshly exports the 50-sheet main schematic +
  PDF, both coupon schematics, top/bottom 2D board plots, and top/bottom 3D renders
  for the legacy main PCB and both coupon candidates. The page has eight guided
  steps, full-resolution image links, a persistent 11-item checklist with notes,
  “show everything”/print modes, and a paste-ready review-summary builder. The
  main PCB is explicitly marked NOT FOR APPROVAL with DRC counts pulled from the
  report; it cannot be confused with an unstarted production layout.
- Verification (2026-08-27, real output):

      python3 scripts/gen_review_page.py --skip-gateware
      link check: 157 local src/href attributes, 157 resolve, 0 broken
      assets copied: 72
      link check: PASS

      python3 scripts/check_review_page.py
      review page: 8 steps, 11 review items, 71 images, 157 local references
      required assets: 18/18 present
      review page checks: PASS

      ruff check scripts/gen_review_page.py scripts/check_review_page.py
      All checks passed!

  `ruff format --check`, `bash -n scripts/open_review.sh`, and `git diff --check`
  also pass. Visually inspected the 1440 px generated page preview, all six 3D
  board views, and representative main/coupon top/bottom 2D plots. The installed
  in-app-browser bridge has a stale internal package path, so Quick Look plus
  direct render inspection supplied visual QA; this does not affect the standalone
  page or `./scripts/open_review.sh`. No schematic, PCB, gateware, or user project
  file was changed.
