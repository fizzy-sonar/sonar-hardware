# 2026-08-25 — claude (fable): architecture review & orchestration setup

## What happened
- Full architecture review of the repo (see `/PLAN.md` for the result). Key finding:
  system shape sound; analog implementation (±10 V rails, 7-converter power tree,
  ADS8568 HV SAR, parallel buses) over-engineered for MEMS mics and replaced by
  decisions D001–D010 (all `proposed`, awaiting CP-A).
- Corrections during review: array geometry is 5×5 minus center-TX (not 3 rows);
  SPU0410 mic initially recommended turned out EOL — D003 keeps Joshua's
  SPV0142LR5H-1 (Syntiant, ex-Knowles) with a P1 bake-off.
- First-cut link budget (hand calc): margin ≈ 90 − 40log10(r) − r dB → ~+40 dB on a
  person at 10 m; architecture choice likely not SNR-gated. Formalized as T-001.
- EDA question (KiCad vs diodeinc/pcb vs atopile) resolved as a gate, not a decree:
  D008 + spike ticket T-005.
- Created this orchestration layer: README (agent protocol), STATUS, ROADMAP
  (P1–P6 + checkpoints CP-A…CP-E), decisions D001–D010, tickets T-001…T-021.
- Published human-readable plan: https://claude.ai/code/artifact/b752caf6-dc27-40dd-9c43-617d7e3fe5f9

## Open threads
- CP-A: Joshua to ratify D001–D010 (blocks P2, not P1/P5).
- T-007 buy list should be produced early so dev hardware ships.
- Nothing committed to git yet this session — repo also has a pre-existing
  uncommitted change to sonar-v1-pcb/sonar.kicad_pro.

## Addendum (same day): D011 — digital PDM mics adopted
Joshua: "For now, I am ok to use the digital microphones." Recorded as D011
(ratified, provisional — revisit at CP-B). D002/D003 superseded; T-003/T-004
superseded; T-008 created; T-002/T-010/T-012/T-020/T-001 rescoped. Board RX is now
24 PDM mics + clock tree + ~12 data lines into the i5; no ADCs or analog rails.

## Addendum 2: GO — CP-A cleared, platform finalized (D012 ratified)
Joshua: "ok. lets go with that." Registry now: D001/D006/D007/D008/D009/D010/D011/
D012 ratified; D002/D003 superseded by D011; D004/D005 superseded by D012. Platform:
Pico 2 snapshot v0 → Cmod A7-35T + FT232H sync-FIFO continuous raw streaming →
optional DNP Ethernet milestone. Tickets rescoped (T-007/T-011/T-020 rewritten;
T-009 created; T-005 optional non-gating; T-021/T-002/T-010 patched). PLAN.md
rewritten as v2. P1 + P5 open for agents; P2 gates on T-002 + T-008.
