#!/usr/bin/env python3
"""Non-browser structural, link, source-staleness and JavaScript checks."""

from __future__ import annotations

import argparse
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

import gen_fast_review as build


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.refs: list[str] = []
        self.notes: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if data.get("id"):
            self.ids.append(data["id"])
        for key in ("href", "src"):
            if data.get(key):
                self.refs.append(data[key])
        if "data-question" in data:
            self.notes.append(data["data-question"])
        if tag in ("form", "textarea", "input", "script"):
            self.errors.append("Review must stay read-only with no copy workflow")
        if tag == "img" and not data.get("alt"):
            self.errors.append("Image lacks alternate text")


def check(path: Path) -> None:
    text = path.read_text()
    page = Page()
    page.feed(text)
    assert len(page.ids) == len(set(page.ids)), "duplicate IDs"
    assert page.notes == ["hardware"], page.notes
    assert not page.errors, page.errors
    assert "@@" not in text and 'href="repo:' not in text, "unexpanded template"
    for required in (
        "NOT PRODUCT-READY",
        "17 / 17",
        "~5.33 ms",
        "not a new test run",
        "@media print",
        "No purchase",
        "Vivado",
        "1–3 m",
    ):
        assert required in text, required
    for ref in page.refs:
        if ref.startswith("#"):
            assert ref[1:] in page.ids, ref
        elif not ref.startswith(("https://", "http://")):
            assert (path.parent / ref).is_file(), ref
    print(f"PASS {path}: {len(page.notes)} human questions, {len(page.refs)} valid links/assets")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("page", type=Path, nargs="?", default=build.ROOT / "build/review/fast.html")
    args = parser.parse_args()
    check(args.page)
    with tempfile.TemporaryDirectory(prefix="sonar-review-check-") as scratch:
        root = Path(scratch)
        # Exercise stale and missing manifests without touching real sources.
        with patch.object(build, "EVIDENCE", root):
            assert build.evidence_status()[0] == "stale"
            (root / "SHA256SUMS").write_text("0" * 64 + "  gateware/rtl/sonar_top.sv\n")
            assert "changed" in build.evidence_status()[1]
    print("PASS missing/stale evidence detection; no browser testing performed")


if __name__ == "__main__":
    main()
