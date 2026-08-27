#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"

review_args=(--skip-gateware)
if [[ "${1:-}" == "--live" ]]; then
  review_args=()
fi

python3 scripts/gen_review_page.py "${review_args[@]}"
python3 scripts/check_review_page.py
open build/review/index.html
