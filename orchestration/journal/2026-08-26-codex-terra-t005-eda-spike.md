# 2026-08-26 — codex/terra-t005 — T-005 EDA spike (diodeinc/pcb "Zener")

Session: orient → work → close-out on branch `agent/T-005-eda-spike` (worktree
`/private/tmp/sonar-t005`). Ticket was pre-claimed for me; tier mid, I am mid —
no mismatch. Per launch instructions: **no commits, no push, no merge** (sandbox
blocks worktree `.git` writes); everything left uncommitted for the orchestrator.

## What happened

- `pcb` (pcbc 0.4.36) already installed at `~/.local/bin/pcb` — no install cost.
- Network fully blocked (DNS resolution fails). No registry cache on the machine.
- Ran the importer on all three relevant inputs; ran/attempted build/info/bom/test/
  sync/search/doc/new/fmt. Real outputs are tabulated in `spikes/eda-zener/REPORT.md`.

## Key findings (details + command table in the REPORT)

1. **Importer is the decisive failure** (not sandbox-related): power_supply sheet →
   silent empty stub (9-line `Board()`, zero components) + part-group error;
   quad_rx_pre_amp tile → hard error, multi-instance hierarchical sheets produce
   "Ambiguous KiCad component identities"; full project → hard error because
   `pcb import` shells out to `kicad-cli pcb drc` (SIGABRTs in this sandbox —
   the same known issue from T-012/T-016, exit 134).
2. **`pcb build`-family EPERM root-caused**: this seatbelt profile denies
   hardlinks (`ln` → "Operation not permitted") and writes to
   `~/Library/Application Support/pcb/`; pcbc vendors workspace deps via
   hardlinks → every workspace-opening command dies `os error 1`, even from a
   `.git`-less `/tmp` copy with pre-copied `.pcb/stdlib` and `vendor = []`.
   Escalation denied (approval policy Never). Sandbox limitation, honestly
   reported — no runtime evidence claimed for build/layout/BOM/ERC-run.
3. **Stdlib is bundled offline** (`…/pcb/toolchains/0.4.36/…/lib/std`): generics
   R/C/L/FB/crystal/LED/TVS/… but no ICs; BOM matcher uses hardcoded house-MPN
   tables (Yageo/Murata/onsemi/Vishay…), not JLC (relevant to D009).
   OperationalAmplifier generic is deprecated, Single/SOIC8 only.
4. **Language reviewability is genuinely good** — Starlark + typed units; the
   power fragment port is ~90 readable lines; hierarchy kills the 4-sheet
   textvar pattern. `pcb fmt` accepts all three hand-port files (syntax only).

## Verdict

**NO-GO for v1** — D008 stands, no superseding decision drafted. Ticket set to
`review` (not `done`): build/layout/BOM were never executable here, so per
"unverified work is not done" the orchestrator should run the 30-min
unsandboxed confirmation (`cd spikes/eda-zener/hand-port && pcb build .` on a
networked host) and close. The NO-GO itself rests on offline-decisive evidence
(importer behavior + registry architecture), not on the sandbox gaps.

## Gotchas for the next agent

- `pcb import` requires a working `kicad-cli` — in this sandbox that's the
  SIGABRT one, so full-project import can never succeed here even unsandboxed-
  network-wise.
- The importer `git init`s inside each output dir — nested `.git/` dirs under
  `spikes/eda-zener/*_import/` are tool-created; fine to delete on cleanup.
- `pcb fmt <file>` works offline and is a free syntax check for `.zen` edits.
- Hand-port files are **reading material, not design data** — never evaluated.
- The 4-mic AFE tile the ticket names is the legacy analog tile
  (`quad_rx_pre_amp.kicad_sch`); the v1 array is digital PDM per D011.
