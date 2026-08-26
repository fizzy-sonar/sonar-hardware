# 2026-08-26 — codex/terra-t021 — T-021 host software resume & close-out

## Session shape
Resume of a killed mid-budget session (4 commits already on `agent/T-021-host-software`,
clean worktree). Tier check: T-021 is `tier: mid`, Terra-class is the mid tier — correct
routing, no hand-back. Total session well under budget; the prior sessions left the
ticket/journal/STATUS in good enough shape that almost no context had to be re-derived.

## What I found (audit vs Definition of Done)
- `host/sonar_host/`: strict SNP1/SNR1 parsers with typed errors, buffered ingest,
  pyftdi transport boundary (D012 scope update), 24-ch CIC+FIR decimation,
  calibration, chirp/matched filter/geometry-aware delay-and-sum — all present.
- `tests/test_host.py`: 5 unittest-style tests (pytest-collectable) covering packet
  round-trip/CRC rejection, chunked SNR1 streaming, sticky-overflow surfacing, and
  end-to-end synthetic point-target recovery (0.18 m / 2.0° tolerances).
- `docs/packet-format.md`: SNP1/SNR1 contract versioned v1.
- Demo + synthetic ingest benchmark present; artifacts git-ignored.

## What was missing / done this session
- Only gap: the literal `pytest` run. It is genuinely impossible here — sandbox has
  no network (`pip install pytest` fails on DNS, escalation policy is Never), no
  local interpreter (3.13 framework / 3.11 / 3.12 user) has pytest, pip cache empty.
  The ticket's Verification section explicitly sanctions the `unittest` fallback,
  which I re-ran fresh: **5/5 OK in 0.742 s**. Demo recovers the synthetic target
  (range 4.202 m vs 4.200 truth; bearing 10.0° vs 12.0° truth, on a 2° grid);
  benchmark 3888 MB/s vs the 9.216 MB/s contract. Full output pasted in the ticket Log.
- No code changes were needed; the prior agent's repair was real and complete.

## Left for next time
- Literal pytest-green record needs any networked host: `pip install pytest &&
  python3 -m pytest -q` (tests will collect unchanged).
- Physical FT232H/libusb capture still untested — first hardware bring-up task.
- Benchmark is in-memory/synthetic by design; it does not measure USB behavior.

## Sandbox git-write blocker (IMPORTANT for orchestrator)
This sandbox has read-only access to the real `.git` directory and escalation is
policy-denied, so `git commit` cannot run here. The close-out commit was built via
`commit-tree` into a temp object dir and shipped two ways, both in the worktree root:
- `t021-closeout.bundle` (verified) — integrate with:
  `git fetch /private/tmp/sonar-t021/t021-closeout.bundle closeout && git merge --ff-only FETCH_HEAD`
  (run from `agent/T-021-host-software`; the commit's parent is `9dfb60e`.)
- `0001-T-021-close-out-fresh-verification-journal-STATUS-up.patch` — equivalent
  `git am` fallback.
Commit message: "T-021 close-out: fresh verification, journal, STATUS update";
exact SHA is in `git bundle verify t021-closeout.bundle` (self-reference would be
circular).
Delete the bundle/patch after integrating.
