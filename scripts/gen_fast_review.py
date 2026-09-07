#!/usr/bin/env python3
"""Build the fast local review and a curated, portable static site; no EDA runs."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "orchestration/review"
EVIDENCE = SOURCE / "evidence-2026-09-06-t026"


def evidence_status() -> tuple[str, str]:
    manifest = EVIDENCE / "SHA256SUMS"
    if not manifest.exists():
        return "stale", "Evidence manifest missing. Treat displayed results as historical."
    changed = []
    for line in manifest.read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        path = ROOT / name.lstrip("*")
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            changed.append(name)
    if changed:
        return (
            "stale",
            f"HISTORICAL EVIDENCE: {len(changed)} tested source files changed. Rerun and review before relying on the snapshot.",
        )
    return (
        "",
        "Evidence snapshot from 06 Sep 2026 matches the tested source hashes. This page generation is not a new test run.",
    )


def generate(output: Path, portable: bool = False) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    page = (SOURCE / "fast-review.html").read_text()
    css_class, message = evidence_status()
    revision = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
    ).strip()
    values = {
        "FRESHNESS_CLASS": css_class,
        "FRESHNESS": message,
        "GENERATED": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "REVISION": revision,
    }
    for key, value in values.items():
        page = page.replace(f"@@{key}@@", html.escape(value))
    appendix = (
        "The full PCB/schematic visual appendix stays in the local repo: "
        "<code>./scripts/open_review.sh --full</code>. It is not uploaded here."
    )
    if not portable:
        appendix = (
            '<a href="index.html">Full local visual appendix · optional engineering reference</a>'
            if (output / "index.html").exists()
            else "Generate the optional visual appendix with <code>./scripts/open_review.sh --full</code>."
        )
    page = page.replace("@@APPENDIX@@", appendix)

    def source_link(match: re.Match[str]) -> str:
        name = match.group(1)
        source = (ROOT / name).resolve()
        if not source.is_relative_to(ROOT) or not source.is_file():
            raise ValueError(f"Missing or unsafe review source: {name}")
        if not portable:
            return f'href="../../{name}"'
        # Only explicitly linked review documents are uploaded, as inert text.
        target = output / "source" / (name + ".html")
        target.parent.mkdir(parents=True, exist_ok=True)
        content = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        content += f"<title>{html.escape(source.name)} · Sonar evidence</title>"
        content += "<style>body{max-width:1000px;margin:30px auto;padding:0 18px;font:16px/1.6 system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#11665f}</style>"
        content += f"<h1>{html.escape(source.name)}</h1><p>Source snapshot · 06 Sep 2026. Paths inside this document refer to the local repository.</p><pre>{html.escape(source.read_text())}</pre></html>"
        target.write_text(content)
        return f'href="source/{name}.html"'

    page = re.sub(r'href="repo:([^"]+)"', source_link, page)
    assets = output / "assets"
    assets.mkdir(exist_ok=True)
    for name in ("fpga-readout.svg", "proof-ladder.svg"):
        shutil.copyfile(SOURCE / "fast-review-assets" / name, assets / name)
    target = output / ("index.html" if portable else "fast.html")
    target.write_text(page)
    print(f"Generated {target.relative_to(ROOT) if target.is_relative_to(ROOT) else target}")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--portable", type=Path, help="Also build a curated static output directory"
    )
    args = parser.parse_args()
    generate(ROOT / "build/review")
    if args.portable:
        generate(args.portable.resolve(), portable=True)
        registry = SOURCE / "site/.openai/hosting.json"
        if registry.exists():
            metadata = args.portable.resolve().parent / ".openai"
            metadata.mkdir(exist_ok=True)
            shutil.copyfile(registry, metadata / "hosting.json")


if __name__ == "__main__":
    main()
