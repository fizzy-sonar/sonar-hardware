# Sonar Library

KiCad symbol and footprint library for the Sonar project.

## Setup

Run the setup script to register the library with KiCad:

```bash
# make sure to have uv installed, you can install like so if required:
curl -LsSf https://astral.sh/uv/install.sh | sh

# then run the setup script
./setup-kicad.py
```

This will:

- Add `sonar-library` to the global symbol and footprint library tables
- Set `SONAR_SYMBOL_DIR` and `SONAR_FOOTPRINT_DIR` path variables in `kicad_common.json`

If your KiCad config is not under the default `10.0` directory:

```bash
./setup-kicad.sh --kicad-version 9.0
./setup-kicad.sh --config-dir /path/to/your/kicad/config
```

## License

This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for details.
