# Vivado validation from this Mac — 2026-09-14

Keep the D012 Cmod A7-35T / Vivado target. Joshua owns a DE10-Lite and a
Raspberry Pi, but prefers Vivado. D014 is not adopted and T-027 must not start.
The next implementation milestone needs a supported build host, not an FPGA
attached to that host. No cloud instance or account has been created.

## Host choice

| Available option | Assessment |
|---|---|
| This ARM64 Mac | Already runs Icarus and host tests. Native Vivado is unsupported. |
| Ordinary ARM Linux VM on this Mac | Still ARM; it does not meet Vivado's x86-64 requirement. Full x86 emulation is a separate, unsupported experiment; do not make it the validation dependency. |
| Raspberry Pi | ARM, so not a supported Vivado build host. Its possible later bench role is separate from synthesis. |
| x86-64 Linux cloud VM, controlled over SSH | Recommended first implementation host. No GPU, GUI desktop or attached board required for batch synthesis/implementation. |

[AMD's supported hosts](https://docs.amd.com/r/en-US/ug973-vivado-release-notes-install-license/Supported-Operating-Systems)
for Vivado 2026.1 include x86-64 Ubuntu 22.04.5. Confirm `uname -m` reports
`x86_64` and inspect `/etc/os-release` on the actual VM; the label "Linux" alone
is insufficient.

Suggested starting configuration: **Linode shared CPU, 8 GB RAM, 4 vCPUs,
160 GB disk, Ubuntu 22.04 x86-64** (verify installed point release). The
[current pricing page](https://www.akamai.com/cloud/pricing) lists this plan at
**US$0.072/hour, US$48/month**. Ten provisioned hours are $0.72 compute-only;
this is an arithmetic example, not a build-duration estimate. Region, tax and
optional services can alter the bill. Export results before removing the VM:
[powered-off instances still accrue charges](https://techdocs.akamai.com/cloud-computing/docs/understanding-how-billing-works).

This sizing is an engineering recommendation for one build at a time. AMD's
[device memory table](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vivado/vivado-buy.html)
lists XC7A35T at 2 GB typical / 3 GB peak for a single batch run, not a guarantee
for this RTL. Observe actual RAM use; increase resources only if needed.

## Tool installation and first build

Use **Vivado 2026.1 BASIC with Artix-7 device support**, and record the precise
installed version/patch. AMD lists BASIC as free with annual renewal, supporting
Linux and all Artix-7 devices. It has limits on XSIM and ILA features; confirm
those limits against the actual simulation/debug job. Do not assume an old
"no license needed" instruction applies to 2026.1.
[Licensing and feature table](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vivado/vivado-buy.html).

Joshua handles cloud provisioning and any new AMD account/license enrollment
under the repository's purchase/account rule. Once the host and installer are
available, setup and builds can be driven over SSH from this Mac.

Use the [AMD web installer](https://www.amd.com/en/support/downloads/adaptive-socs-and-fpgas/development-tools/2026-1.html)
to select Vivado and Artix-7 only. Check its actual disk estimate before
installation; the full all-device offline image is unnecessary here. Install
the runtime libraries required by UG973. Lab Edition alone cannot synthesize
the design. AMD documents a
[batch installation flow](https://docs.amd.com/r/en-US/ug973-vivado-release-notes-install-license/Batch-Mode-Installation-Flow);
generate the configuration from the chosen installer rather than borrowing
another release's component names.

For the later Dedalus/credits question, see the [project-specific cloud cost
comparison and unsent email draft](cloud-compute-pricing.md). It compares a
three-day sprint and intermittent monthly use; no alternative provider has
been tested with Vivado or selected automatically.

Make a source handoff on this Mac after committing the intended changes:

```sh
mkdir -p build/vivado-handoff
git rev-parse HEAD > build/vivado-handoff/source-commit.txt
git archive --format=tar HEAD gateware docs/vivado-validation.md > build/vivado-handoff/gateware.tar
cd build/vivado-handoff
shasum -a 256 gateware.tar > gateware.tar.sha256
```

Transfer these three files to a new directory on the chosen host. The archive
contains committed gateware and this run card; it excludes the private Git
history, KiCad projects and uncommitted changes. No transfer is automatic.
On the host, from that directory:

```sh
sha256sum -c gateware.tar.sha256
tar -xf gateware.tar
# Source the settings64.sh at the location chosen during installation.
# Example placeholder; replace with the actual installed path:
source /absolute/installed/path/settings64.sh
vivado -version > vivado-version.txt
uname -sm > build-host.txt
cat /etc/os-release >> build-host.txt
cd gateware
vivado -mode batch -source vivado/build_bitstream.tcl
```

The build script already sources `create_project.tcl`; do not run project
creation separately. Keep the console exit status, `vivado.log`, `vivado.jou`,
`build/reports/`, synthesis/implementation run logs, checkpoints and any `.bit`
together with `source-commit.txt`, archive checksum and Vivado version. Retrieve
the evidence before deleting the host. A failed build is useful evidence too.

## What must be established before calling implementation validated

The first batch run is diagnostic. The current script requests synthesis,
implementation, a bitstream, utilization, timing and CDC reports. Its final
negative-slack check is **not a complete signoff gate**. T-020 must resolve:

1. Real primitive elaboration and resource fit; confirm large FIFOs infer block
   RAM with the current initialization/reset logic, rather than LUT/register
   storage. Check the intended MMCM/clock mux and IDDR resources.
2. Complete clock and I/O timing constraints. The current pin XDC lacks the
   final PDM both-edge input delays, FT245 external timing and SRAM interface
   budgets. Package-pin coverage does not establish setup/hold closure.
3. Review setup **and hold**, pulse widths, unconstrained paths, clock
   interactions, exceptions, implementation DRC and every relevant CDC/reset
   crossing. Do not silence findings with broad false paths or global waivers.
4. Vendor UNISIM/xsim checks for the primitive behavior exercised by our
   functional Icarus models, within the installed license's limits.
5. Both microphone modes if both remain candidates. The default target/XDC is
   3.072 MHz; a 4.8 MHz simulation pass does not mean a 4.8 MHz implementation
   was built or timed. Its RTL parameters and constraints must agree.

Use the first failure to drive repairs and retain an auditable report set for
each tested configuration. No Vivado build has run as of this document.

## What still requires hardware

Cloud implementation cannot prove FT232H EEPROM configuration, cables/pin
connections, USB/OS stall tolerance, electrical PDM margins or acoustics. After
digital implementation review, bring up the Cmod with counter patterns, prove
UART snapshot recovery with USB absent/stalled, then test the FT232H stream for
integrity at both intended rates before attaching microphones. Host idle-EOF
and chunked-DSP defects (T-024) and commanded TX/metadata (T-023) remain open.

A cloud machine also cannot directly see a Cmod plugged into this Mac. Before
the physical bench session, establish and test a local programming/debug path
or an appropriate remote cable connection. Follow-up source review confirms
openFPGALoader lists Cmod A7-35T and documents macOS installation; see
[`next-steps.md`](next-steps.md). Actual USB access/programming remains untested.
Do not assume Vivado's hardware server runs on ARM or that the DE10-Lite's
USB-Blaster programs Cmod.

The immediate order is: **x86 Vivado diagnostic build → repair/review the
implementation evidence → development-board counter tests → microphone coupon
measurements**. Production-PCB release stays gated by the readiness review.
