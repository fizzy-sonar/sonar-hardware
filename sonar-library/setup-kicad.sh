#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"

KICAD_VERSION="10.0"
SONAR_SYMBOL_DIR="${REPO_ROOT}"
SONAR_FOOTPRINT_DIR="${REPO_ROOT}"

if pgrep -il "kicad" > /dev/null; then
  echo "Error: KiCad appears to be running. Please close KiCad before running this setup script." >&2
  echo "If KiCad remains open, it will overwrite the path assignments with empty variables on exit." >&2
  exit 1
fi

normalize_windows_path_to_posix() {
  local raw="$1"
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -u "$raw"
    return
  fi

  local p="${raw//\\//}"
  if [[ "$p" =~ ^([A-Za-z]):(.*)$ ]]; then
    local drive="${BASH_REMATCH[1],,}"
    local rest="${BASH_REMATCH[2]}"
    printf '/%s%s\n' "$drive" "$rest"
  else
    printf '%s\n' "$p"
  fi
}

default_config_dir_for_os() {
  local version="$1"
  local os
  os="$(uname -s)"

  case "$os" in
    Darwin)
      printf '%s/Library/Preferences/kicad/%s\n' "$HOME" "$version"
      ;;
    Linux)
      printf '%s/.config/kicad/%s\n' "$HOME" "$version"
      ;;
    CYGWIN*|MINGW*|MSYS*)
      if [[ -n "${APPDATA:-}" ]]; then
        local appdata_posix
        appdata_posix="$(normalize_windows_path_to_posix "$APPDATA")"
        printf '%s/kicad/%s\n' "$appdata_posix" "$version"
      else
        printf '%s/AppData/Roaming/kicad/%s\n' "$HOME" "$version"
      fi
      ;;
    *)
      printf '%s/.config/kicad/%s\n' "$HOME" "$version"
      ;;
  esac
}

CONFIG_DIR="$(default_config_dir_for_os "$KICAD_VERSION")"

usage() {
  cat <<USAGE
Usage: $(basename "$0") [--config-dir DIR] [--kicad-version VERSION]

Sets up sonar-library in KiCad by:
- adding the sonar-library symbol library to global sym-lib-table
- adding the sonar-library footprint library to global fp-lib-table
- setting SONAR_SYMBOL_DIR and SONAR_FOOTPRINT_DIR in kicad_common.json

Options:
  --config-dir DIR       Override KiCad config directory
                         (default: OS-specific, based on --kicad-version)
  --kicad-version VER    KiCad version directory (default: 10.0)
  -h, --help             Show this help
USAGE
}

escape_for_kicad() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  printf '%s' "$s"
}

ensure_table_file() {
  local file="$1"
  local header="$2"
  mkdir -p "$(dirname "$file")"
  if [[ ! -f "$file" ]]; then
    printf '%s\n)\n' "$header" > "$file"
  fi
}

upsert_lib_entry() {
  local table_file="$1"
  local lib_name="$2"
  local lib_uri="$3"
  local lib_descr="$4"

  local escaped_name escaped_uri escaped_descr entry tmp
  escaped_name="$(escape_for_kicad "$lib_name")"
  escaped_uri="$(escape_for_kicad "$lib_uri")"
  escaped_descr="$(escape_for_kicad "$lib_descr")"
  entry="  (lib (name \"${escaped_name}\")(type \"KiCad\")(uri \"${escaped_uri}\")(options \"\")(descr \"${escaped_descr}\"))"

  tmp="$(mktemp)"
  sed '$d' "$table_file" | grep -Fv "(name \"${lib_name}\")" > "$tmp" || true
  printf '%s\n)\n' "$entry" >> "$tmp"
  mv "$tmp" "$table_file"

  echo "Configured: ${lib_name}"
}

update_env_vars_in_common_json() {
  local json_file="$1"
  local symbol_dir="$2"
  local footprint_dir="$3"
  local python_bin=""

  if command -v python3 >/dev/null 2>&1; then
    python_bin="python3"
  elif command -v python >/dev/null 2>&1; then
    python_bin="python"
  fi

  mkdir -p "$(dirname "$json_file")"
  if [[ ! -f "$json_file" ]]; then
    printf '{}\n' > "$json_file"
  fi

  if command -v jq >/dev/null 2>&1; then
    local tmp
    tmp="$(mktemp)"
    jq --arg symbol_dir "$symbol_dir" \
       --arg footprint_dir "$footprint_dir" '
      .environment |= (. // {})
      | .environment.vars |= (. // {})
      | .environment.vars.SONAR_SYMBOL_DIR = $symbol_dir
      | .environment.vars.SONAR_FOOTPRINT_DIR = $footprint_dir
    ' "$json_file" > "$tmp"
    mv "$tmp" "$json_file"
  elif [[ -n "$python_bin" ]]; then
    JSON_FILE="$json_file" \
    SONAR_SYMBOL_DIR="$symbol_dir" \
    SONAR_FOOTPRINT_DIR="$footprint_dir" \
    "$python_bin" - <<'PY'
import json
import os
from pathlib import Path

json_file = Path(os.environ["JSON_FILE"])
symbol_dir = os.environ["SONAR_SYMBOL_DIR"]
footprint_dir = os.environ["SONAR_FOOTPRINT_DIR"]

data = {}
if json_file.exists():
    try:
        data = json.loads(json_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}

if not isinstance(data, dict):
    data = {}
environment = data.get("environment")
if not isinstance(environment, dict):
    environment = {}
vars_obj = environment.get("vars")
if not isinstance(vars_obj, dict):
    vars_obj = {}

vars_obj["SONAR_SYMBOL_DIR"] = symbol_dir
vars_obj["SONAR_FOOTPRINT_DIR"] = footprint_dir
environment["vars"] = vars_obj
data["environment"] = environment

json_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY
  else
    echo "Warning: neither jq nor python is available; could not update ${json_file}."
    echo "Set this manually in KiCad -> Preferences -> Configure Paths:"
    echo "  SONAR_SYMBOL_DIR=${symbol_dir}"
    echo "  SONAR_FOOTPRINT_DIR=${footprint_dir}"
    return
  fi

  echo "Set KiCad path variables:"
  echo "  SONAR_SYMBOL_DIR=${symbol_dir}"
  echo "  SONAR_FOOTPRINT_DIR=${footprint_dir}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config-dir)
      CONFIG_DIR="$2"
      shift 2
      ;;
    --kicad-version)
      KICAD_VERSION="$2"
      CONFIG_DIR="$(default_config_dir_for_os "$KICAD_VERSION")"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

SYM_TABLE="${CONFIG_DIR}/sym-lib-table"
FP_TABLE="${CONFIG_DIR}/fp-lib-table"
COMMON_JSON="${CONFIG_DIR}/kicad_common.json"

ensure_table_file "$SYM_TABLE" "(sym_lib_table"
ensure_table_file "$FP_TABLE" "(fp_lib_table"

if [[ ! -f "${SYM_TABLE}.bak" ]]; then
  cp "$SYM_TABLE" "${SYM_TABLE}.bak"
fi
if [[ ! -f "${FP_TABLE}.bak" ]]; then
  cp "$FP_TABLE" "${FP_TABLE}.bak"
fi

upsert_lib_entry \
  "$SYM_TABLE" \
  "sonar-library" \
  "\${SONAR_SYMBOL_DIR}/sonar-library.kicad_sym" \
  "Sonar project symbol library"

upsert_lib_entry \
  "$FP_TABLE" \
  "sonar-library" \
  "\${SONAR_FOOTPRINT_DIR}/sonar-library.pretty" \
  "Sonar project footprint library"

update_env_vars_in_common_json "$COMMON_JSON" "$SONAR_SYMBOL_DIR" "$SONAR_FOOTPRINT_DIR"

echo
echo "Setup complete."
echo "KiCad config dir: ${CONFIG_DIR}"
echo "Symbol table: ${SYM_TABLE}"
echo "Footprint table: ${FP_TABLE}"
