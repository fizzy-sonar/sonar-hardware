# T-005 EDA spike — VERDICT: NO-GO for v1 (diodeinc/pcb "Zener"); keep KiCad per D008

**VERDICT: NO-GO for v1 (keep KiCad, per ratified D008). Re-evaluate post-v1.**
The blocker is not the sandbox: it is that (1) the KiCad importer cannot ingest
our actual design, (2) BOM coverage for our ICs depends on a network registry
that cannot be vendored, and (3) no build/layout/ERC could be executed to give
(b)(c)(d) real evidence. The language itself is genuinely good (see (e)).

Date: 2026-08-26 · Agent: codex/terra-t005 · Tool under test: `pcbc 0.4.36`
(already installed at `~/.local/bin/pcb`; no install, account, or money needed).

## What was run (real commands, real output)

| # | Command | Result |
|---|---------|--------|
| 1 | `pcb --version` | `pcbc 0.4.36` (release check fails: no network in sandbox) |
| 2 | `pcb import sonar-v1-pcb/power_supply.kicad_sch power_supply_import` | "Success" but output is an **empty stub**: 9-line `Board()` declaration, zero components/nets; stderr `Error: Part group 12V has PCB footprints but no schematic symbol instances`. Ran its own KiCad-ERC table first (12 err / 55 warn on this sheet). |
| 3 | `pcb import sonar-v1-pcb/quad_rx_pre_amp.kicad_sch preamp_import` | **HARD FAIL**: `Error: Failed to parse KiCad netlist — Ambiguous KiCad component identities: refdes C177 maps to paths /…/a401e73b…, /…/a401e73b…` (×4 repeated sheet instances, also MK33, R352, R356, TP98). The ticket's own test tile — a multi-instance hierarchical sheet — defeats the importer. |
| 4 | `pcb import sonar-v1-pcb/sonar.kicad_pro sonar_full_import` | **HARD FAIL**: `Error: KiCad DRC failed — kicad-cli execution failed`. `pcb import` shells out to `kicad-cli pcb drc`, which SIGABRTs in this sandbox (known since T-012/T-016); also means import has a hard dependency on a working kicad-cli. Output: empty stub again. |
| 5 | `pcb build --offline power_supply_import` (also from `/tmp/psi2` without `.git`, with `XDG_*` redirects, with `.pcb/stdlib` pre-vendored) | `Error: Operation not permitted (os error 1)` — see §Sandbox forensics. |
| 6 | `pcb info .`, `pcb test`, `pcb bom power_supply.zen`, `pcb sync` | same EPERM. |
| 7 | `pcb search …` | `Error: No component search index is available` (registry index is network-fetched; nothing cached on this machine). |
| 8 | `pcb doc --package @stdlib` | `Error: Failed to resolve dependencies for …/.pcb/stdlib — Operation not permitted`. |
| 9 | `pcb new board scratch_nb <url>` | Works offline; emits `pcb.toml` + 9-line `Board()` stub + git init. |
| 10 | `pcb fmt hand-port/*.zen` | `✓ ap63301.zen / ✓ power_supply.zen / ✓ rx_preamp_channel.zen` — parser accepts the hand port (syntax-only check; eval/build never ran). |

## Sandbox forensics (what exactly could not run, and why)

- Network: `curl https://api.github.com` → `Could not resolve host`. All registry /
  `pcb add|sync|update|search|component download` features are unreachable. No
  registry cache exists anywhere on this machine (`~/Library/Application
  Support/pcb/` contains only the toolchain + stdlib, no package cache).
- Evaluator EPERM: root cause identified — this seatbelt profile denies
  **hardlinks** (`ln std/units.zen x` → `Operation not permitted`) and **writes
  to the toolchain dir** (probe symlink into `~/Library/Application Support/pcb/`
  → EPERM). pcbc vendors workspace deps (hardlink-based) and writes state under
  its toolchain dir, so every command that opens/evaluates a workspace dies with
  the same bare `os error 1`. Reproduced from a `.git`-less copy in `/tmp/psi2`
  with pre-copied `.pcb/stdlib` and `vendor = []` — still EPERM. Escalated run
  denied by policy (`approval policy is Never`). This is a **sandbox limitation,
  not (necessarily) a tool defect** — but it means zero runtime evidence for
  build/layout/BOM in this session.

## Evidence per ticket question

### (a) BOM coverage for our exact parts — INSUFFICIENT without network
- Bundled stdlib generics (offline, readable): Resistor, Capacitor, Inductor,
  FerriteBead, Crystal, Led, Tvs, Zener, Rectifier, Thermistor, OpAmp
  (**deprecated, Single/SOIC8 only — no quad**), PinHeader, TestPoint, NetTie,
  Fiducial, MountingHole, SolderJumper.
- `stdlib/bom/match_generics.zen` assigns house MPNs from hardcoded tables
  (Yageo/Panasonic/Uniroyal/Murata/onsemi/Vishay/Abracon/ECS/Würth) — passives
  and simple discretes only, orientation toward the vendor's house stock, not
  JLC (cf. D009).
- Our non-generic parts: **AP63301WU-7** buck (×2), quad op-amp, plus upstream
  DRV8876, CDCLVC1112, FT232H, Cmod-carrier elements, SPH0641LU4H-1 — none are
  stdlib generics; each needs the network registry (`code.diode.computer`) or a
  hand-written component module. I hand-wrote `ap63301.zen` (~50 lines, 10 min)
  to gauge the cost: easy, but unverifiable offline.
- The KiCad sheet also uses textvars (`${R_GAIN_TARGET}` etc.) — no import path;
  in Zener these become `config()` params naturally (see hand port).

### (b) Generated netlist/layout quality — NOT EVALUABLE here; import fidelity NEGATIVE
- Could not run `pcb build`/`pcb layout` at all (above).
- Import fidelity evidence is bad: empty-stub output on the one sheet that
  "succeeded", hard failure on the multi-instance tile, hard failure on the
  full project. Nobody should trust a silent 9-line stub for a 30-symbol sheet.

### (c) Hand-edited placement vs `pcb layout` re-run — NOT EVALUABLE here
- Docs-level signal only: `pcb layout --sync-footprints` advertises "Reload
  managed footprint definitions from source; **preserve placement and routing**"
  and layout lives in a `layout/` path next to the .zen. Not tested.

### (d) ERC-equivalent checks — EXISTS (two layers), only partially executed
- Observed live: `pcb import` ran a schematic ERC table on our sheets
  (`pin_not_connected`, `power_pin_not_driven`, `wire_dangling`,
  `footprint_link_issues`, …) — real output in command #2/#3 above.
- In-language: `stdlib/checks.zen` (`voltage_within`, `builtin.add_electrical_check`)
  + build-time lint tiers (`-D/-W/-S`, kinds like `electrical.voltage_mismatch`).
  Never executed here; the stdlib test suite (`stdlib/test/*.zen`) couldn't run.

### (e) Reviewability for Joshua — GOOD (the one clear positive)
- `.zen` is Starlark with typed physical units: `Resistor(name="R_FB_TOP",
  value="31.6kOhm 1%", package="0603", P1=v33, P2=vfb)`. The whole
  power-tree fragment port (`hand-port/power_supply.zen`) is ~90 lines and
  readable top-to-bottom in well under 10 min; the feedback divider comment even
  shows the 0.8 V×(1+31.6/10) math where KiCad shows only "31.6k".
- Hierarchy is a real win for us: the 4-channel preamp tile is one
  parameterized module + 4 instantiations, vs 4 KiCad sheet instances with
  textvar substitution.
- Everything is diffable text in git; `pcb fmt` normalizes style.

## Verdict & rationale

**NO-GO for v1.** D008 (KiCad + kicad-cli CI) stands; no superseding decision is
drafted. Even discounting every sandbox failure as unmeasurable, the offline
evidence alone fails the gate: the importer cannot ingest our hierarchical
design (empty stubs or hard errors on 3/3 inputs), and BOM/IC coverage is gated
on a hosted registry we cannot vendor, pin offline, or audit — an unacceptable
supply-chain dependency for a solo-maintainer hardware project mid-flight.

Reconsider post-v1 if: importer handles multi-instance sheets + textvars;
registry components can be fully vendored into git; `pcb layout`'s
placement-preservation is demonstrated on a real board.

## Next step (exact)

Orchestrator/Joshua, on an unsandboxed + networked host, 30-min confirmation:
`cd spikes/eda-zener/hand-port && pcb build .` and
`pcb import ../../../sonar-v1-pcb/sonar.kicad_pro /tmp/sonar-zener-import` —
paste outputs into this report's Log section. If both still fail as above,
close T-005 as NO-GO (done); no further work.

## Layout of this spike

- `hand-port/` — hand-authored port (pcb.toml, ap63301.zen, power_supply.zen,
  rx_preamp_channel.zen). `pcb fmt`-clean; **never built/evaluated** — treat as
  reading material, not design data.
- `power_supply_import/`, `preamp_import/`, `sonar_full_import/` — raw importer
  outputs (stubs) kept as evidence. Each contains an importer-created nested
  `.git/`; ignore or delete at cleanup.
