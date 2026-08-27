---
id: T-018
title: Guided visual review page for Joshua
status: in-progress
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
