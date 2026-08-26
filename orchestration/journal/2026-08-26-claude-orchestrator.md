# 2026-08-26 — claude/orchestrator: multi-subagent session (Fireworks kimi workers)

## Session model

User directive: lean orchestrator context; subagents do the work. Budgets: $40 Claude
(untouched — reserved for T-015 cross-family review), $500 open-weight via Fireworks.
All workers were `codex exec` on the Fireworks provider (kimi-latest; medium effort
for mid-tier tickets, high for top-tier), each in its own git worktree, each told to
leave changes uncommitted (their sandbox cannot write the shared .git). The
orchestrator (this agent) claimed tickets on main, created worktrees, committed/
landed worker output (bundles or uncommitted trees), resolved STATUS.md merge
conflicts (union semantics), and merged each branch to main with --no-ff.

## Landed on main today (in order)

1. T-009 → done (branch agent/T-009-pico-snapshot-fw; close-out 82e4bd2).
2. T-021 → done (bundle-landed 5eed699; closeout patch/bundle artifacts dropped).
3. T-020 → in-progress; simulator milestone landed (bundle d138d5c, 5 commits);
   gates: Vivado host (T-007 item 7), final XDC (was T-011), hardware demo,
   512 KiB SRAM controller, T-013 TX limits (tx-limits.md now exists).
4. T-016 → review (scratch-clone branch landed b5be9e8, 4 commits); CP-BM human gate.
5. T-011 → in-progress, merged (commits 086a32a, 9bcb3f8, e41b3fa, audit 49602c0);
   only gate to done: Joshua's ~60-s live Digilent master-XDC diff (top of pinmap.md).
6. T-012 → done (8a36180 + closeout b6666a1); six legacy power sheets deleted.
7. T-013 → done (df283c7 + closeout 9aa1796); tx-limits.md feeds T-020; C6 dup-ref
   fixed (netlist deterministic again).

## Environment notes for future orchestrators

- `codex exec` must run escalated (it needs ~/.codex + network); inside its sandbox
  it CANNOT write the repo's .git (worktree gitdirs live in the main .git) and
  kicad-cli `pcb drc` SIGABRTs (exit 134) even on pristine projects — ERC is the
  agent-side gate; re-run DRC unsandboxed. Workers ship bundles or uncommitted trees.
- Fireworks burn for ~7 worker sessions (incl. 2 long ones at 9M/34M mostly-cached
  tokens) is on the order of tens of dollars, well within budget.
- All worktrees remain under /private/tmp/sonar-tNNN; all agent branches merged.

## Next agent

Nothing is `ready` and unblocked except optional T-005 (non-gating). Wait for
Joshua: CP-BM (T-016 order package), T-007 purchases, T-011 live XDC diff, CP-B.
