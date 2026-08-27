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

## Addendum — unsandboxed harness run (host side)

`./scripts/check.sh` run unsandboxed on merged main (2026-08-26 ~15:52 PDT): all
commands completed; `kicad-cli pcb drc` works fine outside the agent sandbox (the
SIGABRT/exit-134 was environmental). sonar ERC = 347 messages (matches T-013's
post-fix count — integration consistent); sonar DRC = 175 violations, identical to
the T-006 baseline (the .kicad_pcb predates the v2 schematic rework; layout is a
later phase). Reports in `build/sonar-erc.rpt`, `build/sonar-drc.rpt`.

## Addendum — T-011 live gate FAILED and is being repaired

The live Digilent fetch (orchestrator, networked) disproved the offline pinmap
transcription: master XDC GPIO labels skip pio15/16/24/25; reference manual §8:
44 digital + pins 15/16 analog (XADC divider) + pin 24=VU, pin 25=GND (no DIP 3V3).
Every pinmap row from position 15 up was on the wrong DIP position; the current
sheet would have put FT_D2/FT_D3 on VU/GND. codex/sol-t011 is regenerating the
sheet/pinmap/XDC from the corrected generator table. Evidence: /tmp XDC + Wayback
manual; a reproducible check script lands under scripts/ with the fix.

## Addendum 2 — T-011 done, T-005 done (evening)

- T-011 repair merged (c609520 + closeouts): pinmap/digital sheet/XDC regenerated
  with true DIP positions; `scripts/check_pinmap_vs_xdc.py` PASS 44/44 vs the live
  master XDC (orchestrator re-ran independently). True CC set matches T-008's
  original list; contract doc restored. T-011 → done.
- T-005 spike merged and closed NO-GO: host-side `pcb build` fails exactly at the
  hand-written-IC boundary (quad_opamp.zen), confirming the sandbox finding —
  the tool needs its network registry or hand-authored IC modules; KiCad + JLC
  turnkey stand per D008/D009.
- State: all non-human-gated tickets complete. Remaining path is Joshua-gated:
  T-007 purchases/host → T-020 bitstream; CP-BM coupon order + bench → T-010 →
  T-014 → T-015 (cross-family review; use Claude budget) → CP-C → CP-D.

## Addendum 3 — T-020 SRAM snapshot controller (late evening)

codex/sol-t020 implemented the remaining agent-doable T-020 item: the 512 KiB
on-module SRAM (IS61WV5128BLL-10BLI, dedicated bank-14 pins, no DIP collision —
verified against the live master XDC at /tmp/cmod-a7-master.xdc and refman §3 at
/tmp/cmod-refman.html) snapshot controller with a behavioral SRAM TB enforcing
real timing. Orchestrator independently re-ran `make clean && make test`:
11/11 PASS incl. full 512 KiB window (524,334 bytes bit-exact) and back-to-back
captures. XDC gained the 30 SRAM pins + uart_rxd_out verbatim from the live
master XDC. Merged (b1aafec + closeout 76c13eb). T-020 stays in-progress on:
Vivado host (T-007), sonar_top<->XDC port-name reconciliation (flagged),
ISSI timing constants live-PDF re-check, hardware demo.
