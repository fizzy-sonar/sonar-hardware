#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"

case "${1:-}" in
  --full|--live)
    review_args=(--skip-gateware)
    if [[ "$1" == "--live" ]]; then review_args=(); fi
    python3 scripts/gen_review_page.py "${review_args[@]}"
    python3 scripts/check_review_page.py
    python3 scripts/gen_fast_review.py
    open build/review/index.html
    ;;
  "")
    python3 scripts/gen_fast_review.py
    python3 scripts/check_fast_review.py
    open build/review/fast.html
    ;;
  *) echo "Usage: $0 [--full|--live]" >&2; exit 2 ;;
esac
