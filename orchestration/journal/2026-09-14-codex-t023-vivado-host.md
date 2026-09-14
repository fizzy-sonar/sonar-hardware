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

## Dedalus / pricing follow-up

Joshua asked whether Dedalus Machines and credits could help, then asked for
pricing with reasonable project assumptions. Added `docs/cloud-compute-pricing.md`
and linked it from the run card. Modeled one 4-vCPU/8-GiB job, 100 GiB retained
disk, 20 compute hours, with 72-hour and 730-hour retention. Live primary pricing
and Python arithmetic give Linode $5.18/$48; Daytona $7.36/$14.11 before trial
credits; Modal Sandbox $9.52 usage covered by its $30 recurring credit; Dedalus
Pro $20.72/$27.30 if storage is outside the included compute credit. Storage
credit ambiguity and Dedalus's contradictory header/FAQ rate are explicit.
Daytona's $25 tier-unlock top-up is prepaid balance, not a recurring fee.

Captured Modal Function/Daytona archive cost reductions as conditional options,
Azure's student credit without inventing a VM quote, and E2B's disk/session
limits. Dedalus architecture and actual Vivado compatibility remain unknown;
current docs say sleep drops processes/memory even though marketing suggests
runtime preservation. Requested admission/larger storage/$100 credit in a local
email draft only. No message, account, provider deployment or spend occurred.
No provider SDK or installer was downloaded/executed. Docs-only changes stay on
main per protocol; source-identified gateware handoff remains valid at 464ba6a.

Verification: exact Decimal arithmetic checks PASS for both scenarios, credit
and subscription calculations, and Modal CPU normalization. New local Markdown
link resolves; `git diff --check` passes. The earlier source manifest still
matches 44/44 and the user's KiCad project hash is unchanged. No simulation or
physical check was repeated for this documentation-only follow-up.

## Timeline and confirmed human constraints

Joshua requested the forward plan, timeline and required inputs. Confirmed via
chat: home desk only; US$250 for cloud/dev modules/cables/adapters, excluding
coupons/instruments; 2–4 hands-on hours/week. Added docs/next-steps.md, linked
ROADMAP/run card and updated T-025. Initial dev purchase follows initial fit,
pin review and a programming plan; complete implementation and host reliability
checks can proceed during delivery. Target desk capture by early October and
first echo Oct 12–25, explicitly conditional on assembled coupon/source and
temporary measurement access. No full-array date or acoustic proof is promised.

Primary openFPGALoader board docs explicitly list cmoda7_35t; install docs show
macOS Homebrew support. This narrows the local-programming unknown to an actual
installation/USB/board test. No program was installed or hardware tested. No
school lab, free assembly or home soldering is assumed. Budget envelopes sum
to US$250; a separate actual delivered basket needs shipping destination.

Verification: local plan links 3/3; budget sum check PASS; prior source evidence
44/44 hashes unchanged; user KiCad hash unchanged; git diff --check PASS. An
initial multi-file patch failed its final context check and was atomic (git
status confirmed no partial application); corrected patch then applied. Work
is documentation on main. No account, spend, upload, message, gate ratification
or background execution. Next inputs are x86 SSH access, AMD installer/license
access and shipping country/postal code; local T-023 engineering can continue.
