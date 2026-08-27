#!/usr/bin/env python3
"""Structural and asset checks for build/review/index.html."""

from __future__ import annotations

import shutil
import struct
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "build" / "review" / "index.html"


class ReviewParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.refs: list[tuple[str, str]] = []
        self.images: list[str] = []
        self.guide_steps: list[str] = []
        self.review_ids: list[str] = []
        self.scripts: list[str] = []
        self._in_script = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if values.get("id"):
            self.ids.append(values["id"])
        for attr in ("src", "href"):
            if values.get(attr):
                self.refs.append((attr, values[attr]))
        if tag == "img" and values.get("src"):
            self.images.append(values["src"])
        classes = set(values.get("class", "").split())
        if tag == "section" and "guide-step" in classes:
            self.guide_steps.append(values.get("id", ""))
        if values.get("data-review-id"):
            self.review_ids.append(values["data-review-id"])
        if tag == "script":
            self._in_script = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._in_script = False

    def handle_data(self, data: str) -> None:
        if self._in_script:
            self.scripts.append(data)


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("invalid PNG signature")
    return struct.unpack(">II", data[16:24])


def main() -> int:
    failures: list[str] = []
    if not PAGE.exists():
        print(f"FAIL: missing {PAGE.relative_to(ROOT)}")
        return 1

    text = PAGE.read_text()
    parser = ReviewParser()
    parser.feed(text)

    duplicates = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
    if duplicates:
        failures.append(f"duplicate HTML ids: {duplicates}")
    expected_steps = [f"step-{number}" for number in range(1, 9)]
    if parser.guide_steps != expected_steps:
        failures.append(f"guide steps {parser.guide_steps}, expected {expected_steps}")
    expected_review_ids = [str(number) for number in range(1, 12)]
    if parser.review_ids != expected_review_ids:
        failures.append(f"review ids {parser.review_ids}, expected {expected_review_ids}")

    required_text = [
        "Main-board layout is not a CP-C deliverable yet",
        "NOT FOR APPROVAL",
        "Progress stays only in this browser",
        "Build summary",
        "Copy summary",
        "localStorage",
    ]
    for needle in required_text:
        if needle not in text:
            failures.append(f"missing required page text: {needle!r}")

    local_refs = 0
    for attr, ref in parser.refs:
        if ref.startswith(("http://", "https://", "mailto:", "#")):
            continue
        local_refs += 1
        if not (PAGE.parent / ref).resolve().exists():
            failures.append(f"broken {attr}: {ref}")

    required_assets = [
        "main-board-top-3d.png",
        "main-board-bottom-3d.png",
        "main-board-top-2d.svg",
        "main-board-bottom-2d.svg",
        "sph-coupon-top-3d.png",
        "sph-coupon-bottom-3d.png",
        "sph-coupon-top-2d.svg",
        "sph-coupon-bottom-2d.svg",
        "ics-coupon-top-3d.png",
        "ics-coupon-bottom-3d.png",
        "ics-coupon-top-2d.svg",
        "ics-coupon-bottom-2d.svg",
        "sonar.svg",
        "sonar-digital.svg",
        "sonar-TX_Drive.svg",
        "sph-sph-coupon.svg",
        "ics-ics-coupon.svg",
        "sonar-schematics.pdf",
    ]
    assets = PAGE.parent / "assets"
    for name in required_assets:
        path = assets / name
        if not path.exists() or path.stat().st_size < 100:
            failures.append(f"missing/empty required asset: {name}")

    for name in required_assets:
        path = assets / name
        if not path.exists():
            continue
        if path.suffix == ".png":
            try:
                width, height = png_dimensions(path)
                if width < 1200 or height < 700:
                    failures.append(f"board render too small {name}: {width}x{height}")
            except ValueError as exc:
                failures.append(f"{name}: {exc}")
        elif path.suffix == ".svg":
            header = path.read_text(errors="replace")[:4096]
            if "<svg" not in header or "viewBox=" not in header:
                failures.append(f"invalid/unscalable SVG: {name}")
        elif path.suffix == ".pdf" and not path.read_bytes().startswith(b"%PDF-"):
            failures.append(f"invalid PDF signature: {name}")

    javascript = "\n".join(parser.scripts).strip()
    if not javascript:
        failures.append("no inline JavaScript found")
    elif shutil.which("node"):
        check = subprocess.run(
            ["node", "--check", "-"],
            input=javascript,
            text=True,
            capture_output=True,
            check=False,
        )
        if check.returncode:
            failures.append(f"JavaScript syntax: {check.stderr.strip()}")

    print(
        f"review page: {len(parser.guide_steps)} steps, "
        f"{len(parser.review_ids)} review items, {len(parser.images)} images, "
        f"{local_refs} local references"
    )
    print(
        f"required assets: {len(required_assets) - len([f for f in failures if 'asset' in f])}/{len(required_assets)} present"
    )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("review page checks: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
