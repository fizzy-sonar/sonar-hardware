---
id: T-028
title: Preserve local repository work before laptop migration
status: in-progress
phase: maintenance
tier: mid
priority: 1
assignee: codex
depends_on: []
needs_human: false
created: 2026-09-18
updated: 2026-09-18
---
## Goal
Preserve the existing user KiCad project edit and push current history to the configured origin at Joshua's explicit request. No engineering milestone or hardware signoff is implied.

## Definition of Done
Existing project edit committed; required harness run recorded; main and any local branch histories absent from remote preserved through normal pushes; live remote hashes verified.

## Verification
JSON comparison of the project edit, git diff --check, scripts/check.sh, and git ls-remote origin against local branch tips.

## Log
- 2026-09-18: Claimed migration housekeeping. The only working edit reorders the used_designators string without changing the set. Origin is the existing fizzy-sonar/sonar-hardware repository. No force pushes or design changes planned.
- 2026-09-18: Verification PASS: project JSON differs only by used_designators ordering; git diff --check clean. scripts/check.sh exited 0 with SUMMARY: all invoked KiCad commands completed successfully. Existing ERC/DRC violations are baseline-accepted, not a clean-board signoff. `git branch --no-merged main` returned no branches: pushing main preserves all ordinary local branch histories. Next: push and verify origin/main hash.
