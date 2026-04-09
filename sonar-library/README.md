# Sonar Library

KiCad symbol and footprint library for the Sonar project.

## Setup

Run the setup script to register the library with KiCad:

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

This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for details.
