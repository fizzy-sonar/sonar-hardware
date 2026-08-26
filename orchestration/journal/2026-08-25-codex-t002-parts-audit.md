# 2026-08-25 — codex/luna: T-002 parts and lifecycle audit

Continued the existing T-002 claim on `agent/T-002-parts-lifecycle-audit`.
Preserved the pre-existing unstaged edits in orchestration files and
`sonar-v1-pcb/sonar.kicad_pro`.

Delivered `orchestration/parts-matrix.md`. Primary D011 rows are ICS-41350,
ICS-41352, SPH0641LU4H-1, and T5838; D012 rows cover Cmod A7-35T, FT232H,
Pico 2, LAN8720, DIP-48 socket, and the rejected SODIMM-200. Analog ADC/opamp
and analog-mic rows are explicitly historical-only. Manufacturer pages and
datasheets were checked live on 2026-08-25. Findings: ICS-41350 is EOL;
ICS-41352 is production NRND with no TDK inventory; SPH0641 is the strongest
lifecycle alternate but needs clock/rail confirmation; T5838 lacks primary
public evidence. No reliable public qty-30 quote or JLC turnkey status was
available, so the matrix marks those fields for BOM-freeze verification.

Knowles AN-17 and AN24 were extracted: response can remain useful above 10 kHz,
with sensitivity decreasing and self-noise decreasing; open-mesh SiSonic family
guidance covers approximately 20–80 kHz or more, but this is not a production
tolerance for SPH0641. T-008 must perform a normalized physical bake-off.

Verification: `git diff --check` passed; all matrix rows have dated source links.
