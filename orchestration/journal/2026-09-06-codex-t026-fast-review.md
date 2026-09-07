# T-026 — read-only review with one immediate human question

Joshua requested an independent, low-effort review, cheaper subagents, clearer
artifacts and candid FPGA risks. Three Luna/medium artifact agents supplied:
fresh tests/probes, a short brief and two SVGs. Root owned engineering judgement
and the website. T-026 claim `7f6afab`, implementation `15eb055`, branch
`agent/T-026-fast-review`. No HDL/hardware fixes in this ticket.

## Delivered

- `./scripts/open_review.sh` opens the new local fast review without EDA rebuild.
- `--full` opens the original visual appendix, now labeled historical/reference;
  `--live` also reruns gateware for that appendix.
- Decision-first HTML: verdict, FPGA risks, proof ladder, expandable evidence,
  one immediate hardware-access question. Responsive and printable CSS.
- Joshua explicitly said he does not want to copy anything. Removed the new
  forms, JavaScript and export workflow entirely. Answers stay in chat.
- Source: `orchestration/review/fast-review.html`, `FAST-REVIEW-BRIEF.md`,
  `fast-review-assets/`; builder/checker under `scripts/`.

## Verification and limits

- Gateware 17/17 PASS, host 5/5 PASS on Python3.14.2/NumPy2.3.2 via local UV cache.
- Known starvation probe: taps before=9 / after=9; host probe reproduces idle
  EOF and chunk-decimator mismatch. Passing suites do not cover these failures.
- `python3 scripts/check_fast_review.py`: 20 local refs, one question, missing/
  stale evidence negative tests PASS. Portable: 19 refs PASS. No forms/scripts.
- Full generator/checker: 8 steps / 11 historical items / 71 images / 158 local
  references / 18 required assets PASS. Current fast page overrides old checklist.
- Ruff lint/format, bash syntax, diff whitespace, SVG XML all PASS.
- `bash scripts/check.sh` outside sandbox exits0 accepting existing ERC/DRC
  baselines. This is not a clean-main-PCB claim. Raw logs are under
  `orchestration/review/evidence-2026-09-06-t026/`.
- SHA256SUMS covers current gateware/host/test sources, constraints, build scripts,
  probes and Python dependency files, unchanged since tests. Generated page flags
  changed/missing files instead of presenting historical tests as a fresh run.
- No browser visual QA was requested/performed. No Vivado build or physical
  readout proof. Existing main KiCad project edit remains untouched.

## Optional hosting stopped at authorization boundary

Sites guidance was used for the plain static review. A new owner-only Site was
registered once; its persistent registry is `review/site/.openai/hosting.json`.
Only a 116 KiB curated static review/excerpts bundle was prepared in the isolated
ignored `build/sonar-fast-site/` source checkout, not the full Sonar repository.
Sandbox push failed DNS; escalated push was explicitly denied by permission
review because user authorization did not cover payload/destination. No bypass,
no upload, no version save, no deployment. User informed; explicit approval
requested asynchronously. Keep local unless authorization is given. Reuse the
existing project ID if later approved; never create another Site as a workaround.
The short-lived source credential was not persisted. No Sonar remote push.

## Next work, not performed here

T-023 (top): independent snapshot, commanded TX/control/timestamp, top-level
fault/absence/restart tests. T-024 (mid): live transport and chunk-invariant DSP.
T-020 Vivado constraints/resource/timing/CDC work early in parallel when a host
is available. Then physical counter-pattern transport, four-channel coherence,
and the T-025 proposed saved 1–3m reflector demo. No architecture ratification,
production microphone choice, purchase approval or 10m claim was made.

Human question: what Cmod A7, FT232H and Vivado host access exists now? Do not
ask Joshua to read HDL or copy notes to resolve the engineering proof obligations.
