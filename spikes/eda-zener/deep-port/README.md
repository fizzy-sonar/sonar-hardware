# T-017 deep port (2026-08-27, codex/terra-t017)

`sonar_v1_deep_port/` is a self-contained Zener workspace (pcbc 0.4.38):

- `components/` — hand-written IC modules from live-fetched datasheets:
  AP63301 (Diodes DS42002), OPA4171 (TI SBOS516H), DRV8876 (TI SLVSEY0).
- `modules/` — net-for-net ports of power_supply.kicad_sch,
  quad_rx_pre_amp.kicad_sch (one 4-ch tile), 20kHz-h-bridge.kicad_sch.
- `symbols/`, `footprints/` — vendored KiCad symbol/footprint copies
  (provenance noted in each component header). Opamp_Quad pin names were
  renamed per-unit (OUTA/-INA/...) — Zener keys pins by name and KiCad's
  per-unit `+`/`-` duplicates are unusable otherwise; Sim.* stripped.
- `bom.txt`, `bom.json`, `netlist.net` — captured build artifacts
  (`netlist.net` == `layout/default.net`).

Rebuild: `cd sonar_v1_deep_port && pcb build . && pcb layout --no-open
sonar_v1_deep_port.zen && pcb bom sonar_v1_deep_port.zen`

See ../REPORT.md "Deep port (T-017)" for the verdict and papercuts.
