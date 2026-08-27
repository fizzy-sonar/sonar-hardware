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

---

# Deep port (T-017) — VERDICT: GO-WITH-CONDITIONS for v2 authoring

**VERDICT: GO-WITH-CONDITIONS.** With network + host access, `pcb build`
works and is genuinely good: three real Sonar v1 blocks (power sheet, RX
preamp tile, TX drive) build clean, emit a KiCad netlist that is
node-for-node identical to the originals, and produce a live-priced BOM.
Conditions: (1) the registry is **account-gated, not just network-gated** —
all ICs were hand-written; (2) the KiCad importer is still useless on our
design (empty stub on host, see below), so adoption means re-authoring, not
migration; (3) multi-unit symbols need a documented workaround. D008 (KiCad
for v1) stands regardless — this informs v2 only.

Date: 2026-08-27 · Agent: codex/terra-t017 · Tool: `pcbc 0.4.38`
(auto-upgraded from 0.4.36 at first run) on the host (no sandbox).

## What the registry actually offers (the T-005 unknown, now measured)

| Probe | Result |
|---|---|
| `git ls-remote https://code.diode.computer/diode/registry` | **401 Unauthorized** (Basic/Bearer); anonymous clone 403 |
| `pcb component search AP63301` | `Error: Not authenticated. Run pcb auth login` |
| `pcb search --mode kicad:components TLV2474` | `Error: Authentication required` |
| `pcb add code.diode.computer/diode/registry@latest` | fails (SSH fallback, host key) |
| `~/.pcb/cache/index_v4.sqlite` | exists but EMPTY (0 rows) |
| `pcb bom` stock/price data | **works anonymously** (live Digikey-style stock + LCSC columns) |
| Bundled stdlib (toolchain `lib/std/`) | works offline; generics + bundled KiCad footprints/symbols |
| Public GitHub (diodeinc/example, demolib, kicad_lib) | clonable; `demolib` empty, `example` is the format reference used here |

**So: without a diode account (prohibited by project rules), the component
registry contributes nothing. Every IC must be hand-written.** T-005's
supply-chain concern is now sharper: it is account-gated SaaS, not merely
network-gated.

## What was built (all under `spikes/eda-zener/deep-port/sonar_v1_deep_port/`)

- `components/AP63301.zen` — from Diodes DS42002 Rev.3 PDF (fetched live);
  pin names match `sonar_lib.kicad_sym`; vendored symbol + TSOT-23-6
  footprint from the repo. ~15 min.
- `components/OPA4171.zen` — **part choice correction**: the KiCad tile runs
  on ±5 V rails (`5V_OP_AMP_HIGH`/`-5V_OP_AMP_LOW`), so the ticket-suggested
  TLV2474 (6 V max) is unusable; chose OPA4171 (36 V RRIO quad, SOIC-14) and
  verified the pinout against TI SBOS516H Table 4-2 (fetched live). The
  KiCad tile itself names NO MPN (generic `Device:Opamp_Quad`, no
  footprint). ~20 min incl. the multi-unit papercut below.
- `components/DRV8876.zen` — from TI SLVSEY0 (drv8876.pdf, fetched live),
  PWP/HTSSOP-16 pinout; symbol vendored from `sonar_lib.kicad_sym`,
  footprint from KiCad system lib. ~10 min (pattern was known by then).
- `modules/power_supply.zen` — net-for-net port of `power_supply.kicad_sch`
  (U61 buck + FB2 3V3_MIC branch; TP81/+12V excluded — it lives on the boost
  subsheet). FB2 instantiated as the rails.md-reviewed BLM18KG121TN1D ferrite
  (KiCad currently fits 0R — documented delta).
- `modules/rx_preamp_tile.zen` — completes the T-005 hand-port. Channel
  topology corrected against the real netlist: the 4.7 nF is a shunt AFTER
  the 49.9 Ω series output (T-005 guessed feedback cap); `${R_GAIN_*}`
  textvars → one `config()` param. One module × 4 channels vs 4 KiCad sheet
  instances + textvar substitution — the hierarchy win is real.
- `modules/tx_drive.zen` — DRV8876 block net-for-net (stretch target, done).
- Build outputs: `layout/default.net` (KiCad netlist, 46 nets),
  `layout/layout.kicad_pcb` (67 footprints), `deep-port/bom.txt|json`.

## Parity spot-check (KiCad netlist via `kicad-cli sch export netlist` vs `layout/default.net`)

Power sheet, node-for-node (KiCad refdes.pin → Zener refdes.pin, all match):
`5V` 6/6 nodes, `+3.3V` 6/6, `3V3_MIC` 4/4, `Net-(U61-FB)` 3/3,
`Net-(U61-SW)` 3/3, `Net-(U61-BST)` 2/2, `Net-(U61-EN)` 2/2; U2 (AP63301)
6/6 pins. Preamp ch0: `U5A-+`=3/3, `U5A--`=3/3 + KiCad's alt-stuffing pair
(parameterized away), `AMP_OUT_0`=3/3; U1 (OPA4171) 14/14 pins. TX: `+12V`
4/4, `CPH/CPL/VCP/IMODE/IPROPI`/J50/snub all exact; U3 (DRV8876) 17/17 pins
incl. EP. Component counts: power 16+TP81(excluded)=17 vs KiCad 19
(TP81 + FB2-as-0R diff accounted); preamp tile 37 vs KiCad ~45 (8
alt-stuffing resistors parameterized); TX 13 vs KiCad 16 (3 power symbols /
flags not ported).

## ERC-equivalent: real, and it bites

`voltage_within` checks ran at build. Negative test (checked +3V3 against
"5V 10%"): `Error: Voltage range 3.3V 2% of +3V3 is not within 5V 10%` —
build fails. Reverted, build green.

## Importer re-test (host + network, pcbc 0.4.38)

`pcb import sonar-v1-pcb/power_supply.kicad_sch` → same empty 9-line stub,
same `Error: Part group 12V has PCB footprints but no schematic symbol
instances`. **The importer is still not viable; Zener adoption =
re-authoring.** At the measured cost (~10–20 min/IC, ~15–20 min/sheet-block)
that is affordable for v2 but rules out any "import the v1 design" path.

## Papercuts (each cost 1–3 build iterations; ~15 of the ~40 min)

1. `pins=` keys are KiCad pin NAMES (numbers only when the name is
   empty/`~`). Error message lists expected names — good.
2. **Multi-unit symbols are effectively unsupported as-is**: Opamp_Quad's
   pins are named `+`/`-` per unit (duplicates), and Zener keys nets by
   signal name → would short all units. Fix: renamed pins in the vendored
   symbol copy (OUTA/-INA/+INA/... per SBOS516H). Undocumented; worked by
   reading the pcb source (diodeinc/pcb is public, helpful).
3. Multi-symbol `.kicad_sym` needs `Symbol(library=..., name=...)`; KiCad
   nested `_0_1/_1_1` subunits are flattened as separate "symbols".
4. Symbol `Sim.*` properties auto-import a SPICE model; unresolved
   `${KICAD9_SYMBOL_DIR}` → hard build failure. Stripped `Sim.*` from the
   vendored symbol.
5. Net names reject `.` (KiCad's `RX.PRE`, `+3.3V` are illegal → `RX_PRE0`,
   `+3V3`) and duplicate `Net("x")` literals are rejected (bind to a var) —
   annoying for KiCad-faithful naming, good hygiene otherwise.
6. `properties["datasheet"]/["description"]` are hard errors; must use
   `datasheet=`/`description=` kwargs. `Part()` is prelude.
7. Generic kwargs can be aliased (FerriteBead `impedance` → pass as
   `value=`); discoverable only by reading stdlib source.
8. Any non-generic component without `part=Part(...)` fails the BOM stage.
9. stdlib `Inductor` package enum lacks 1008 → used 0402 (footprint
   mismatch vs KiCad's L_1008_2520Metric; flagged in the module).
10. `pcb new board` demands a repo URL and inits a nested git repo (deleted).
11. `pcb fmt` accepts one path; `pintype "stereo"` in emitted netlists is
    cosmetic noise.
12. Toolchain auto-upgraded 0.4.36→0.4.38 on first run — no pin/lock visible
    in pcb.toml (`pcb-version = "0.4"` semver floor only). Repro risk.

## BOM quality

17 unique parts: 12 matched with live stock+price (house MPNs:
Murata/Panasonic/Yageo — US-vendor-oriented, not JLC; D009 tension
unchanged). Unmatched: 22 µF 0603 (16 V/10 V), 10 µF 16 V, 2.2 µH 0402
inductor, **4.7 nF C0G 0603 — corroborates T-016's finding that C0G 0603 is
unbuyable**; the stdlib house tables silently agree. ICs (AP63301, DRV8876,
connector) matched by explicit MPN; AP63301 even resolved LCSC C2158003.

## Bottom line for v2

The authoring loop (write → `pcb build` → real netlist/BOM/checks) is
credible and pleasant; a full Sonar-scale board is days of authoring, not
weeks. Conditions before v2 adoption: (a) decide the account question
(registry auth) or commit to vendored components only; (b) pin the toolchain
version; (c) expect to hand-manage multi-unit symbols; (d) no importer — plan
greenfield re-authoring; (e) BOM house parts need a JLC-oriented table to
satisfy D009. For v1: KiCad per D008, unchanged.
