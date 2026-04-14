# Sonar

Monorepo for the Sonar ultrasonic project — KiCad hardware designs and supporting library.

## Repository layout

| Directory | Description |
|---|---|
| `sonar-library/` | KiCad symbol and footprint library shared across boards |
| `sonar-v1-pcb/` | Main Sonar v1 PCB (transducer array, power supply, RX amp) |
| `tx-rx-dev-board/` | Development board for testing TX/RX circuitry |

## Setup

Run the setup script to register the shared library with KiCad:

```bash
./setup-kicad.sh
```

This will:

- Add `sonar-library` to the global symbol and footprint library tables
- Set `SONAR_SYMBOL_DIR` and `SONAR_FOOTPRINT_DIR` path variables in `kicad_common.json`

Restart KiCad if it was already open.

If your KiCad config is not under the default `10.0` directory:

```bash
./setup-kicad.sh --kicad-version 9.0
./setup-kicad.sh --config-dir /path/to/your/kicad/config
```

## License

Licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for details.
