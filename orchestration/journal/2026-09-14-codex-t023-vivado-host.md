# T-023 follow-up — Vivado host and branch integration

Joshua prefers Vivado, owns a DE10-Lite and Raspberry Pi, and can arrange a
local VM or Linode. This Mac is ARM64; no Vivado is installed. Retain binding
D012/Cmod. D014 remains a recorded, unadopted alternative and T-027 must not
start. No architecture decision was ratified or changed.

Added `docs/vivado-validation.md` and linked it from gateware/readiness/buy-list
guidance. Primary AMD sources verify x86-64 Linux support, free 2026.1 BASIC
with annual renewal and limited XSIM/ILA, and XC7A35T typical/peak memory of
2/3 GB. Akamai lists 8 GB / 4 vCPU / 160 GB at $0.072/hour; recommended as a
starting single-build host, not a measured resource requirement or runtime
promise. Powered-off VMs remain billable. No VM, account, license, upload or
spend was performed. Current-source links and commands are in the run card.

Existing batch script already creates the project, so removed redundant
README invocation. Inspected its real limits: bitstream generation and a
negative-slack query do not enforce all setup/hold/unconstrained/CDC gates;
PDM/FT245/SRAM external timing constraints still need completion. No FPGA
implementation has run. The default build targets 3.072 MHz; 4.8 MHz needs
matching parameter/constraint proof. Cloud build does not solve local USB
programming/debug or physical capture. Exact Pi/open-source Cmod loader support
remains unverified rather than assumed.

Verification: current gateware/host source manifest 44/44 hashes match the
2026-09-13 test evidence; 9 local Markdown links pass; `git diff --check` passes.
No RTL/XDC was changed, so the previous 21 gateware / 5 host results remain the
verification record with their documented limitations. KiCad user project hash
before/after documentation work is
`04df7b56b637381342fafc8a0f6d74583ec9ca1415f70f45eec140bc73c7f0ac`.

Branch explanation: orchestration/README step 4 requires substantive work on
an agent ticket branch. At entry, main had zero unique commits and this branch
had two (`ee0a8f8`, `454d976`). Close-out integrates the committed checkpoint via
fast-forward onto main without including the user's KiCad project edit. No
remote push. T-023 remains in progress, not declared complete by integration.

Next: user provisions/accesses an x86 Ubuntu host and AMD installer/license;
use the source-identified handoff and batch run to obtain the first T-020
implementation evidence. Independently continue T-023 command/TX/timestamp
integration and T-024 host reliability repairs. Hold production-PCB release.
