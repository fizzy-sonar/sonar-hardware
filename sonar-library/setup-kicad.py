#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "psutil>=7.2",
# ]
# ///
"""Set up sonar-library in KiCad.

Adds the sonar-library symbol and footprint libraries to KiCad's global
library tables and sets SONAR_SYMBOL_DIR / SONAR_FOOTPRINT_DIR /
SONAR_SPICE_DIR in kicad_common.json. Safe to re-run; existing entries
are replaced.
"""

import argparse
import json
import os
import platform
import re
import shutil
import sys
from pathlib import Path
from typing import Final

import psutil

KICAD_DEFAULT_VERSION: Final = "10.0"
LIB_NAME: Final = "sonar-library"
SYMBOL_DESCR: Final = "Sonar project symbol library"
FOOTPRINT_DESCR: Final = "Sonar project footprint library"
SYMBOL_URI: Final = "${SONAR_SYMBOL_DIR}/sonar-library.kicad_sym"
FOOTPRINT_URI: Final = "${SONAR_FOOTPRINT_DIR}/sonar-library.pretty"


def kicad_is_running() -> bool:
    for proc in psutil.process_iter(["name"]):
        name = (proc.info.get("name") or "").lower()
        if "kicad" in name:
            return True
    return False


def default_config_dir(version: str) -> Path:
    home = Path.home()
    system = platform.system()
    if system == "Darwin":
        return home / "Library" / "Preferences" / "kicad" / version
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else home / "AppData" / "Roaming"
        return base / "kicad" / version
    return home / ".config" / "kicad" / version


def escape_kicad_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_lib_entry(name: str, uri: str, descr: str) -> str:
    return (
        f'  (lib (name "{escape_kicad_string(name)}")'
        f'(type "KiCad")'
        f'(uri "{escape_kicad_string(uri)}")'
        f'(options "")'
        f'(descr "{escape_kicad_string(descr)}"))'
    )


def backup_path(path: Path) -> Path:
    return path.parent / f"{path.name}.bak"


def ensure_table_file(table_file: Path, header: str) -> None:
    table_file.parent.mkdir(parents=True, exist_ok=True)
    if not table_file.exists():
        table_file.write_text(f"{header}\n)\n", encoding="utf-8")


def upsert_lib_entry(table_file: Path, name: str, uri: str, descr: str) -> None:
    lines = table_file.read_text(encoding="utf-8").splitlines()
    if not lines or lines[-1].strip() != ")":
        raise RuntimeError(f"Unexpected KiCad table format in {table_file}")

    name_pattern = re.compile(rf'\(name\s+"{re.escape(name)}"\)')
    body = [line for line in lines[:-1] if not name_pattern.search(line)]
    body.append(build_lib_entry(name, uri, descr))
    body.append(")")
    table_file.write_text("\n".join(body) + "\n", encoding="utf-8")
    print(f"Configured: {name}")


def update_env_vars(
    common_json: Path,
    symbol_dir: Path,
    footprint_dir: Path,
    spice_dir: Path,
) -> None:
    common_json.parent.mkdir(parents=True, exist_ok=True)

    data: dict = {}
    if common_json.exists():
        try:
            loaded = json.loads(common_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            loaded = {}
        if isinstance(loaded, dict):
            data = loaded

    environment = data.get("environment")
    if not isinstance(environment, dict):
        environment = {}
    vars_obj = environment.get("vars")
    if not isinstance(vars_obj, dict):
        vars_obj = {}

    vars_obj["SONAR_SYMBOL_DIR"] = str(symbol_dir)
    vars_obj["SONAR_FOOTPRINT_DIR"] = str(footprint_dir)
    vars_obj["SONAR_SPICE_DIR"] = str(spice_dir)
    environment["vars"] = vars_obj
    data["environment"] = environment

    common_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("Set KiCad path variables:")
    print(f"  SONAR_SYMBOL_DIR={symbol_dir}")
    print(f"  SONAR_FOOTPRINT_DIR={footprint_dir}")
    print(f"  SONAR_SPICE_DIR={spice_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Set up sonar-library in KiCad: adds symbol and footprint library "
            "entries to the global tables and sets SONAR_SYMBOL_DIR / "
            "SONAR_FOOTPRINT_DIR in kicad_common.json."
        )
    )
    parser.add_argument(
        "--kicad-version",
        default=KICAD_DEFAULT_VERSION,
        help="KiCad version directory (default: %(default)s)",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        help="Override KiCad config directory (default: OS-specific)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if kicad_is_running():
        print(
            "Error: KiCad appears to be running. Close KiCad before running "
            "this script, otherwise it will overwrite the path assignments "
            "with empty values on exit.",
            file=sys.stderr,
        )
        return 1

    config_dir: Path = args.config_dir or default_config_dir(args.kicad_version)
    repo_root = Path(__file__).resolve().parent
    spice_dir = repo_root / "spice-models"
    spice_dir.mkdir(parents=True, exist_ok=True)

    sym_table = config_dir / "sym-lib-table"
    fp_table = config_dir / "fp-lib-table"
    common_json = config_dir / "kicad_common.json"

    for table, header in ((sym_table, "(sym_lib_table"), (fp_table, "(fp_lib_table")):
        ensure_table_file(table, header)
        backup = backup_path(table)
        if not backup.exists():
            shutil.copy2(table, backup)

    upsert_lib_entry(sym_table, LIB_NAME, SYMBOL_URI, SYMBOL_DESCR)
    upsert_lib_entry(fp_table, LIB_NAME, FOOTPRINT_URI, FOOTPRINT_DESCR)
    update_env_vars(common_json, repo_root, repo_root, spice_dir)

    print()
    print("Setup complete.")
    print(f"KiCad config dir: {config_dir}")
    print(f"Symbol table: {sym_table}")
    print(f"Footprint table: {fp_table}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
