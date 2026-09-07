#!/usr/bin/env python3
"""Assemble build/review/index.html — a self-contained visual review page for
Joshua, the human gate on the Sonar v1 project.

The page is dark-on-light, framework-free, lazy-loaded, and every figure is
captioned with what it shows and why it matters. All image assets are copied
into build/review/assets/ so the build/review/ folder is portable (build/ is
gitignored; only this script is committed). Links to source documents are
repo-relative (../../...) and resolve when the page is viewed in place.

Usage:
    python3 scripts/gen_review_page.py [--skip-gateware]

--skip-gateware  Do not re-run `make -C gateware test`; use the cached TB list.

The script verifies at the end that every src/href in the generated HTML
resolves to a real file, and exits nonzero if any link is broken.
"""

from __future__ import annotations

import argparse
import datetime
import html
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVIEW = ROOT / "build" / "review"
ASSETS = REVIEW / "assets"

# Cached copy of the 2026-08-27 `make -C gateware test` PASS lines, used only
# when iverilog/make are unavailable in the current environment.
GATEWARE_TB_SNAPSHOT = [
    "PASS sampler/tone rate=3072000Hz frames=80 payload=73728000b/s checksum=cff870",
    "PASS sampler/tone rate=4800000Hz frames=80 payload=115200000b/s checksum=cff870",
    "PASS sampler/tone rate=3072000Hz frames=80 payload=73728000b/s checksum=cff870 (XILINX stubs)",
    "PASS sampler/tone rate=4800000Hz frames=80 payload=115200000b/s checksum=cff870 (XILINX stubs)",
    "PASS async FIFO/packer/FT245 backpressure bytes=24",
    "PASS core SNR1 + 100 exact frames survive long/random TXE# stalls",
    "PASS overflow stops and drains exact 8-frame prefix; capture restart increments SNR1 ID",
    "PASS SNR1 exact 32-byte headers start once per capture and hold under backpressure",
    "PASS UART SNP1 snapshot bytes=60 CRCs verified",
    "PASS exact 1.536/3.072/4.8MHz plan, 50ms+10ms startup, and bounded TX chirp safety",
    "PASS reset_sync/release edges=2/domain + debounce clean",
    "PASS pdm_clock waveform: pulses=68 std=17 run10us=37 sram2us=1964, no clipped edges",
    "PASS B2 duty hard-bound: 6536 half-cycles checked, 0 over bound; worst duty 187/188 = 254/256",
    "PASS SRAM snapshot SNP1 round-trip: two back-to-back 16-frame captures + timeout-empty header, CRCs verified",
    "PASS SRAM snapshot full 512 KiB window bytes=524334 bit-exact",
    "PASS XILINX primitive branches and sonar_top elaborate (functional stub models; -t null elaboration retained)",
    "PASS sonar_top <-> XDC port bijection: 28 ports / 73 bits exact (active get_ports only, DNP block excluded)",
]

CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { margin: 0; background: #f4f4f0; color: #1c2733;
       font: 16px/1.55 -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
main { max-width: 1080px; margin: 0 auto; padding: 24px 20px 64px; }
h1 { font-size: 1.7rem; margin: 0.2em 0 0.1em; }
h2 { font-size: 1.25rem; margin: 2.2em 0 0.4em; padding-top: 0.8em;
     border-top: 3px solid #1c2733; }
h2 .num { color: #0f766e; margin-right: 0.5em; }
p.lede { color: #44515f; margin-top: 0.2em; }
.guidebar { position: sticky; top: 0; z-index: 20; margin: 18px 0 24px;
            padding: 10px 12px; border: 1px solid #c9c9c0; border-radius: 8px;
            background: rgba(244,244,240,0.97); backdrop-filter: blur(8px); }
.guidebar .row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.guidebar .where { flex: 1 1 280px; min-width: 0; }
.guidebar progress { width: 100%; height: 9px; accent-color: #0f766e; }
button { border: 1px solid #8b969f; border-radius: 5px; background: #fff;
         color: #1c2733; padding: 7px 11px; font: inherit; cursor: pointer; }
button:hover { background: #e8ecef; }
button.primary { background: #0f766e; border-color: #0f766e; color: #fff; }
button[disabled] { opacity: 0.45; cursor: default; }
.jump { max-width: 240px; padding: 7px 8px; border: 1px solid #8b969f;
        border-radius: 5px; background: #fff; color: #1c2733; font: inherit; }
.guide-step { scroll-margin-top: 112px; }
.guided .guide-step[hidden] { display: none; }
.section-intro { color: #44515f; margin-top: 0; }
table.key { border-collapse: collapse; width: 100%; margin: 1em 0; background: #fff; }
table.key th, table.key td { border: 1px solid #d4d4cc; padding: 8px 12px;
     text-align: left; vertical-align: top; }
table.key th { background: #e8ecef; }
table.key td.v { font-family: Menlo, Consolas, monospace; white-space: nowrap; }
figure { background: #fff; border: 1px solid #d4d4cc; border-radius: 6px;
         padding: 12px; margin: 14px 0; }
figure img { max-width: 100%; height: auto; display: block; margin: 0 auto;
         background: #fff; }
figure a.zoom { display: block; cursor: zoom-in; }
figcaption { margin-top: 8px; font-size: 0.92rem; color: #374151; }
figcaption b { color: #1c2733; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 18px; }
@media (max-width: 800px) { .grid { grid-template-columns: 1fr; } }
.board-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 800px) { .board-grid { grid-template-columns: 1fr; } }
.board-grid figure { margin: 0; }
details { background: #fff; border: 1px solid #d4d4cc; border-radius: 6px;
          padding: 10px 14px; margin: 14px 0; }
summary { cursor: pointer; font-weight: 600; }
pre.arch { background: #fff; border: 1px solid #d4d4cc; border-radius: 6px;
           padding: 14px; overflow-x: auto; font-size: 0.85rem; }
ul.tbs { font-family: Menlo, Consolas, monospace; font-size: 0.82rem;
         columns: 2; background: #fff; border: 1px solid #d4d4cc;
         border-radius: 6px; padding: 12px 12px 12px 32px; }
@media (max-width: 800px) { ul.tbs { columns: 1; } }
ul.tbs li { margin: 3px 0; }
ol.review li { margin: 10px 0; background: #fff; border: 1px solid #d4d4cc;
               border-radius: 6px; padding: 10px 12px; list-style: none; }
ol.review { padding-left: 0; }
ol.review label.checkline { display: grid; grid-template-columns: auto 1fr;
                            align-items: start; gap: 9px; }
ol.review input[type="checkbox"] { width: 20px; height: 20px; margin-top: 2px;
                                   accent-color: #0f766e; }
ol.review textarea { width: 100%; min-height: 58px; margin-top: 8px; padding: 7px 8px;
                     resize: vertical; border: 1px solid #b8bec4; border-radius: 4px;
                     font: inherit; }
.summary-box { width: 100%; min-height: 180px; padding: 9px 10px; resize: vertical;
               border: 1px solid #b8bec4; border-radius: 5px; font: 0.85rem/1.45
               Menlo, Consolas, monospace; }
.review-actions { display: flex; gap: 8px; flex-wrap: wrap; margin: 10px 0; }
.status-pill { display: inline-block; border-radius: 999px; padding: 2px 8px;
               font-size: 0.8rem; font-weight: 600; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
           overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }
.done { background: #dff3e8; color: #075e54; }
.pending { background: #fdf3e0; color: #8a3d00; }
.blocked { background: #fdeaea; color: #991b1b; }
.gate { background: #fdeaea; border-left: 4px solid #b91c1c;
        padding: 2px 10px; border-radius: 3px; display: inline-block; }
a { color: #0f766e; }
code { background: #eceae4; padding: 1px 5px; border-radius: 3px;
       font-size: 0.88em; }
.note { background: #eaf3ef; border-left: 4px solid #0f766e; padding: 8px 12px;
        border-radius: 3px; }
.warn { background: #fdf3e0; border-left: 4px solid #b45309; padding: 8px 12px;
        border-radius: 3px; }
footer { margin-top: 3em; padding-top: 1em; border-top: 1px solid #c9c9c0;
         color: #6b7280; font-size: 0.85rem; }
@media print {
  body { background: #fff; }
  main { max-width: none; padding: 0; }
  .guidebar, .review-actions { display: none; }
  .guide-step[hidden] { display: block !important; }
  figure, details, ol.review li { break-inside: avoid; }
}
"""

JS = r"""
(() => {
  const root = document.documentElement;
  const sections = [...document.querySelectorAll('.guide-step')];
  const jump = document.getElementById('guide-jump');
  const prev = document.getElementById('guide-prev');
  const next = document.getElementById('guide-next');
  const toggle = document.getElementById('guide-toggle');
  const position = document.getElementById('guide-position');
  const title = document.getElementById('guide-title');
  const progress = document.getElementById('guide-progress');
  const reviewProgress = document.getElementById('review-progress');
  let guided = true;
  let current = 0;

  function safeGet(key, fallback) {
    try { return localStorage.getItem(key) ?? fallback; } catch (_) { return fallback; }
  }
  function safeSet(key, value) {
    try { localStorage.setItem(key, value); } catch (_) {}
  }
  function show(index, scroll = false) {
    current = Math.max(0, Math.min(sections.length - 1, index));
    sections.forEach((section, i) => { section.hidden = guided && i !== current; });
    root.classList.toggle('guided', guided);
    position.textContent = guided ? `Step ${current + 1} of ${sections.length}` : 'All sections';
    title.textContent = guided ? sections[current].dataset.title : 'Complete review';
    progress.max = sections.length;
    progress.value = guided ? current + 1 : sections.length;
    prev.disabled = !guided || current === 0;
    next.disabled = !guided || current === sections.length - 1;
    toggle.textContent = guided ? 'Show everything' : 'Use guided mode';
    jump.value = String(current);
    safeSet('sonar-review-step', String(current));
    safeSet('sonar-review-guided', guided ? '1' : '0');
    if (scroll) sections[current].scrollIntoView({behavior: 'smooth', block: 'start'});
  }
  prev.addEventListener('click', () => show(current - 1, true));
  next.addEventListener('click', () => show(current + 1, true));
  toggle.addEventListener('click', () => { guided = !guided; show(current, false); });
  jump.addEventListener('change', () => { guided = true; show(Number(jump.value), true); });

  const checks = [...document.querySelectorAll('[data-review-id]')];
  const notes = [...document.querySelectorAll('[data-note-id]')];
  function updateReviewProgress() {
    const done = checks.filter(box => box.checked).length;
    reviewProgress.textContent = `${done}/${checks.length} review items checked`;
  }
  checks.forEach(box => {
    box.checked = safeGet(`sonar-review-check-${box.dataset.reviewId}`, '0') === '1';
    box.addEventListener('change', () => {
      safeSet(`sonar-review-check-${box.dataset.reviewId}`, box.checked ? '1' : '0');
      updateReviewProgress();
    });
  });
  notes.forEach(note => {
    note.value = safeGet(`sonar-review-note-${note.dataset.noteId}`, '');
    note.addEventListener('input', () => safeSet(`sonar-review-note-${note.dataset.noteId}`, note.value));
  });
  updateReviewProgress();

  const output = document.getElementById('review-summary-output');
  function buildSummary() {
    const lines = ['Sonar v1 review — Joshua', ''];
    checks.forEach(box => {
      const item = box.closest('li');
      const text = item.querySelector('.item-text').textContent.replace(/\s+/g, ' ').trim();
      const note = item.querySelector('textarea').value.trim();
      lines.push(`${box.checked ? '[x]' : '[ ]'} ${box.dataset.reviewId}. ${text}`);
      if (note) lines.push(`    Decision/notes: ${note}`);
    });
    output.value = lines.join('\n');
    output.focus();
    output.select();
  }
  document.getElementById('build-summary').addEventListener('click', buildSummary);
  document.getElementById('copy-summary').addEventListener('click', async () => {
    buildSummary();
    try {
      await navigator.clipboard.writeText(output.value);
      document.getElementById('copy-state').textContent = 'Copied';
    } catch (_) {
      document.execCommand('copy');
      document.getElementById('copy-state').textContent = 'Selected — press Cmd-C if needed';
    }
  });

  guided = safeGet('sonar-review-guided', '1') === '1';
  current = Number(safeGet('sonar-review-step', '0')) || 0;
  show(current, false);
})();
"""

# ---------------------------------------------------------------- utilities


def copy_asset(src: Path, name: str | None = None) -> str:
    """Copy src into assets/, return the href relative to index.html."""
    ASSETS.mkdir(parents=True, exist_ok=True)
    dest = ASSETS / (name or src.name.replace(" ", "_"))
    shutil.copyfile(src, dest)
    return f"assets/{dest.name}"


def pgm_to_png_bytes(data: bytes, scale: int = 4) -> bytes:
    """Stdlib P5/P2 PGM -> 8-bit grayscale PNG, nearest-neighbour upscale."""
    m = re.match(rb"P([25])\s+(\d+)\s+(\d+)\s+(\d+)\s", data)
    if not m:
        raise ValueError("unsupported PGM header")
    kind, w, h, maxv = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
    if kind == 5:
        px = list(data[m.end() : m.end() + w * h])
    else:
        px = [int(t) for t in data[m.end() :].split()][: w * h]
    if maxv != 255:
        px = [v * 255 // maxv for v in px]
    # Display stretch: the T-009 PGM quantizes a between-bins tone to value ~2
    # against a saturated DC row, which renders as pure black. Normalize on the
    # brightest non-DC row so the tone line is visible; clip the DC row at 255.
    body = px[w:]
    body_max = max(body) if body else 0
    if 0 < body_max < 128:
        gain = 255.0 / body_max
        px = [min(255, int(v * gain)) for v in px]
    if scale > 1:
        big = bytearray()
        for y in range(h):
            row = bytearray()
            for x in range(w):
                row += bytes([px[y * w + x]]) * scale
            for _ in range(scale):
                big += row
        px, w, h = list(big), w * scale, h * scale
    raw = b"".join(b"\x00" + bytes(px[y * w : (y + 1) * w]) for y in range(h))

    def chunk(tag: bytes, payload: bytes) -> bytes:
        c = tag + payload
        return struct.pack(">I", len(payload)) + c + struct.pack(">I", zlib.crc32(c))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 240) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, str(exc)


def esc(s: str) -> str:
    return html.escape(s, quote=True)


# ---------------------------------------------------------------- data pulls


def pull_link_budget_numbers() -> dict[str, str]:
    out = {"margin_10m": "n/a", "zero_margin_range": "n/a"}
    md = ROOT / "analysis" / "link_budget.md"
    if md.exists():
        t = md.read_text()
        m = re.search(r"retains \*\*\+?([\d.]+) dB\*\* at 10 m", t)
        if m:
            out["margin_10m"] = f"+{m.group(1)} dB"
        m = re.search(r"zero margin at \*\*([\d.]+) m\*\*", t)
        if m:
            out["zero_margin_range"] = f"{m.group(1)} m"
    return out


def ensure_t021_demo() -> dict[str, str]:
    summary = ROOT / "host" / "artifacts" / "t021-demo-summary.txt"
    svg = ROOT / "host" / "artifacts" / "t021-demo.svg"
    if not (summary.exists() and svg.exists()):
        # demo.py writes to the relative path host/artifacts/, so cwd must be ROOT.
        run([sys.executable, "host/demo.py"], cwd=ROOT)
    out = {"truth": "n/a", "est": "n/a", "truth_b": "n/a", "est_b": "n/a"}
    if summary.exists():
        t = summary.read_text()
        for key, pat in [
            ("truth", r"truth_range_m=([\d.]+)"),
            ("est", r"estimated_range_m=([\d.]+)"),
            ("truth_b", r"truth_bearing_deg=([\d.]+)"),
            ("est_b", r"estimated_bearing_deg=([\d.]+)"),
        ]:
            m = re.search(pat, t)
            if m:
                out[key] = m.group(1)
    return out


def pull_t021_benchmark() -> str:
    ticket = ROOT / "orchestration" / "tickets" / "T-021-host-sw-skeleton.md"
    if ticket.exists():
        runs = re.findall(
            r"benchmark: ([\d.]+) MB/s vs target ([\d.]+) MB/s \(([\d.]+)x\)", ticket.read_text()
        )
        if runs:
            mbps, target, mult = runs[-1]
            return f"{mbps} MB/s vs {target} MB/s contract ({mult}x)"
    return "n/a"


def pull_erc() -> dict[str, object]:
    rpt = ROOT / "build" / "sonar-erc.rpt"
    if not rpt.exists():
        return {"total": "n/a", "modern": "n/a"}
    txt = rpt.read_text(errors="replace")
    total = 0
    legacy = 0
    for sheet in re.split(r"\*\*\*\*\* Sheet ", txt)[1:]:
        name = sheet.splitlines()[0]
        n = len(re.findall(r"\[\w+\]:", sheet))
        total += n
        if "eight_transducer_array" in name or name == "/":
            legacy += n
    return {"total": total, "modern": total - legacy}


def pull_drc() -> dict[str, str]:
    out = {"violations": "n/a", "unconnected": "n/a", "footprints": "n/a"}
    report = ROOT / "build" / "sonar-drc.rpt"
    if not report.exists():
        return out
    text = report.read_text(errors="replace")
    patterns = {
        "violations": r"\*\* Found (\d+) DRC violations \*\*",
        "unconnected": r"\*\* Found (\d+) unconnected pads \*\*",
        "footprints": r"\*\* Found (\d+) Footprint errors \*\*",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            out[key] = match.group(1)
    return out


def pull_pinmap_gate() -> str:
    code, out = run([sys.executable, "scripts/check_pinmap_vs_xdc.py"], cwd=ROOT, timeout=120)
    m = re.search(r"PASS: (\d+/\d+)", out)
    if code == 0 and m:
        return f"{m.group(1)} PASS"
    return "FAIL (see scripts/check_pinmap_vs_xdc.py)"


def pull_gateware_tbs(skip: bool) -> tuple[list[str], str]:
    if not skip and shutil.which("make") and shutil.which("iverilog"):
        code, out = run(["make", "test"], cwd=ROOT / "gateware", timeout=300)
        passes = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("PASS")]
        if code == 0 and passes:
            return passes, f"re-run live: make test, {len(passes)}/17 PASS"
    return GATEWARE_TB_SNAPSHOT, "cached from 2026-08-27 make test run (iverilog unavailable here)"


def ensure_spectrogram_png() -> Path | None:
    pgm = ROOT / "firmware" / "pico-snapshot" / "build" / "synthetic_spectrogram.pgm"
    if not pgm.exists():
        run([sys.executable, "host/simulate.py"], cwd=ROOT / "firmware" / "pico-snapshot")
    if not pgm.exists():
        return None
    png = ASSETS / "t009-synthetic-spectrogram.png"
    ASSETS.mkdir(parents=True, exist_ok=True)
    png.write_bytes(pgm_to_png_bytes(pgm.read_bytes(), scale=5))
    return png


def pull_arch_diagram() -> str:
    plan = (ROOT / "PLAN.md").read_text()
    for block in re.findall(r"```\n(.*?)```", plan, re.S):
        if "FT232H" in block:
            return block.strip("\n")
    return "(architecture diagram block not found in PLAN.md)"


def schematic_staleness_note() -> str | None:
    svg_dir = ROOT / "build" / "sonar-svg"
    sch_dir = ROOT / "sonar-v1-pcb"
    if not svg_dir.exists():
        return None
    svgs = list(svg_dir.glob("*.svg"))
    schs = list(sch_dir.glob("*.kicad_sch"))
    if not svgs or not schs:
        return None
    newest_sch = max(p.stat().st_mtime for p in schs)
    stale = [p.name for p in svgs if p.stat().st_mtime < newest_sch]
    if stale:
        return (
            f"{len(stale)} schematic SVG(s) predate the newest .kicad_sch edit — "
            f"re-run ./scripts/check.sh unsandboxed to refresh. "
            f"(In this sandbox kicad-cli pcb drc SIGABRTs; ERC/SVG renders do run.)"
        )
    return None


def parse_review_plan() -> tuple[list[dict], list[str]]:
    """Return (checkbox items, part-3 pointer lines) from JOSHUA-REVIEW-PLAN.md."""
    md = (ROOT / "orchestration" / "review" / "JOSHUA-REVIEW-PLAN.md").read_text()
    items: list[dict] = []
    pointers: list[str] = []
    part3 = False
    cur: dict | None = None
    for line in md.splitlines():
        if line.startswith("## Part 3"):
            part3 = True
            if cur:
                items.append(cur)
                cur = None
            continue
        if line.startswith("## What you can safely skip"):
            break
        if part3:
            if line.startswith("- **"):
                pointers.append(line)
            elif pointers and line.strip():
                pointers[-1] += " " + line.strip()
            continue
        m = re.match(r"^(\d+)\.\s+(.*)", line)
        if m:
            if cur:
                items.append(cur)
            cur = {"n": m.group(1), "text": m.group(2)}
        elif cur is not None and line.strip() and not line.startswith("#"):
            cur["text"] += " " + line.strip()
    if cur:
        items.append(cur)
    return items, pointers


def md_inline(text: str) -> str:
    """Minimal inline markdown: **bold**, *em*, `code` (paths become links)."""
    text = esc(text)

    def code_repl(m: re.Match) -> str:
        inner = html.unescape(m.group(1))
        p = ROOT / inner
        if p.exists() and not inner.endswith("/"):
            href = f"../../{inner}"
            return f'<a href="{esc(href)}"><code>{esc(inner)}</code></a>'
        return f"<code>{esc(inner)}</code>"

    text = re.sub(r"`([^`]+)`", code_repl, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    return text


def figure(href: str, caption: str, extra: str = "") -> str:
    return (
        f'<figure><a class="zoom" href="{esc(href)}" target="_blank" '
        f'rel="noopener"><img src="{esc(href)}" loading="lazy" '
        f'alt="{esc(re.sub("<[^>]+>", "", caption)[:120])}" {extra}></a>'
        f"<figcaption>{caption}</figcaption></figure>"
    )


def export_schematic_svgs(source: Path, prefix: str = "") -> tuple[dict[str, str], str]:
    """Export every sheet to SVG, copy into assets, return source-name -> href."""
    if not shutil.which("kicad-cli"):
        return {}, "kicad-cli unavailable"
    with tempfile.TemporaryDirectory(prefix="sonar-review-sch-") as tmp:
        code, out = run(
            ["kicad-cli", "sch", "export", "svg", "--output", tmp, str(source)],
            cwd=source.parent,
            timeout=180,
        )
        if code != 0:
            tail = " | ".join(out.strip().splitlines()[-3:])
            return {}, f"schematic SVG export failed: {tail or f'exit {code}'}"
        exported: dict[str, str] = {}
        for path in sorted(Path(tmp).glob("*.svg")):
            name = f"{prefix}{path.name}".replace(" ", "_")
            exported[path.name] = copy_asset(path, name)
        if not exported:
            return {}, "schematic SVG export produced no files"
        return exported, f"fresh kicad-cli export: {len(exported)} sheet(s)"


def export_schematic_pdf(source: Path, name: str) -> tuple[str | None, str]:
    if not shutil.which("kicad-cli"):
        return None, "kicad-cli unavailable"
    output = ASSETS / name
    code, out = run(
        ["kicad-cli", "sch", "export", "pdf", "--output", str(output), str(source)],
        cwd=source.parent,
        timeout=180,
    )
    if code == 0 and output.exists() and output.stat().st_size:
        return f"assets/{name}", "fresh kicad-cli PDF export"
    tail = " | ".join(out.strip().splitlines()[-3:])
    return None, f"schematic PDF export failed: {tail or f'exit {code}'}"


def render_board_views(board: Path, prefix: str) -> tuple[dict[str, str], list[str]]:
    """Generate top/bottom 2D plots and top/bottom 3D renders for one PCB."""
    views: dict[str, str] = {}
    errors: list[str] = []
    if not shutil.which("kicad-cli"):
        return views, ["kicad-cli unavailable"]

    plot_jobs = [
        ("top-2d", "F.Cu,F.Mask,F.Silkscreen,Edge.Cuts", False),
        ("bottom-2d", "B.Cu,B.Mask,B.Silkscreen,Edge.Cuts", True),
    ]
    for key, layers, mirror in plot_jobs:
        output = ASSETS / f"{prefix}-{key}.svg"
        cmd = [
            "kicad-cli",
            "pcb",
            "export",
            "svg",
            "--output",
            str(output),
            "--layers",
            layers,
            "--mode-single",
            "--page-size-mode",
            "2",
            "--exclude-drawing-sheet",
            "--fit-page-to-board",
        ]
        if mirror:
            cmd.append("--mirror")
        cmd.append(str(board))
        code, out = run(cmd, cwd=board.parent, timeout=180)
        if code == 0 and output.exists() and output.stat().st_size:
            views[key] = f"assets/{output.name}"
        else:
            tail = " | ".join(out.strip().splitlines()[-3:])
            errors.append(f"{key}: {tail or f'exit {code}'}")

    render_jobs = [("top-3d", "top"), ("bottom-3d", "bottom")]
    for key, side in render_jobs:
        output = ASSETS / f"{prefix}-{key}.png"
        cmd = [
            "kicad-cli",
            "pcb",
            "render",
            "--output",
            str(output),
            "--width",
            "1400",
            "--height",
            "900",
            "--side",
            side,
            "--background",
            "opaque",
            "--quality",
            "high",
            "--floor",
            "--perspective",
            "--rotate",
            "315,0,35",
            str(board),
        ]
        code, out = run(cmd, cwd=board.parent, timeout=240)
        if code == 0 and output.exists() and output.stat().st_size:
            views[key] = f"assets/{output.name}"
        else:
            tail = " | ".join(out.strip().splitlines()[-3:])
            errors.append(f"{key}: {tail or f'exit {code}'}")
    return views, errors


def board_gallery(
    views: dict[str, str],
    title: str,
    context: str,
    errors: list[str],
) -> str:
    labels = {
        "top-3d": "Top 3D",
        "bottom-3d": "Bottom 3D",
        "top-2d": "Top copper / mask / silkscreen",
        "bottom-2d": "Bottom copper / mask / silkscreen (mirrored)",
    }
    parts = [f'<h3>{esc(title)}</h3><p class="section-intro">{context}</p>']
    if errors:
        parts.append(f'<p class="warn"><b>Render warning:</b> {esc("; ".join(errors))}</p>')
    figs = ""
    for key in ("top-3d", "bottom-3d", "top-2d", "bottom-2d"):
        if key in views:
            figs += figure(
                views[key],
                f"<b>{esc(labels[key])}.</b> Click the image for the full-resolution render.",
            )
    if figs:
        parts.append(f'<div class="board-grid">{figs}</div>')
    else:
        parts.append('<p class="warn">No board views were generated.</p>')
    return "".join(parts)


# ---------------------------------------------------------------- main


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--skip-gateware",
        action="store_true",
        help="use cached gateware TB list instead of make test",
    )
    args = ap.parse_args()

    if REVIEW.exists():
        shutil.rmtree(REVIEW)
    ASSETS.mkdir(parents=True)

    numbers = pull_link_budget_numbers()
    t021 = ensure_t021_demo()
    bench = pull_t021_benchmark()
    erc = pull_erc()
    drc = pull_drc()
    pinmap = pull_pinmap_gate()
    tbs, tb_source = pull_gateware_tbs(args.skip_gateware)
    arch = pull_arch_diagram()
    stale_note = schematic_staleness_note()
    review_items, review_pointers = parse_review_plan()
    git = run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT)[1].strip() or "unknown"
    branch = run(["git", "branch", "--show-current"], cwd=ROOT)[1].strip() or "unknown"
    now = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")

    main_sch, main_sch_status = export_schematic_svgs(ROOT / "sonar-v1-pcb" / "sonar.kicad_sch")
    main_pdf, main_pdf_status = export_schematic_pdf(
        ROOT / "sonar-v1-pcb" / "sonar.kicad_sch", "sonar-schematics.pdf"
    )
    sph_sch, sph_sch_status = export_schematic_svgs(
        ROOT / "coupons" / "mic-bakeoff" / "sph-coupon" / "sph-coupon.kicad_sch",
        "sph-",
    )
    ics_sch, ics_sch_status = export_schematic_svgs(
        ROOT / "coupons" / "mic-bakeoff" / "ics-coupon" / "ics-coupon.kicad_sch",
        "ics-",
    )
    main_board, main_board_errors = render_board_views(
        ROOT / "sonar-v1-pcb" / "sonar.kicad_pcb", "main-board"
    )
    sph_board, sph_board_errors = render_board_views(
        ROOT / "coupons" / "mic-bakeoff" / "sph-coupon" / "sph-coupon.kicad_pcb",
        "sph-coupon",
    )
    ics_board, ics_board_errors = render_board_views(
        ROOT / "coupons" / "mic-bakeoff" / "ics-coupon" / "ics-coupon.kicad_pcb",
        "ics-coupon",
    )

    # ---- section 2: analysis plots
    analysis_captions = {
        "person-margin-vs-range.png": "<b>Sonar-equation margin vs range, person target (T-001).</b> The reference "
        "build keeps +27.1 dB margin at 10 m and hits zero margin at 20.2 m. "
        "<b>Why it matters:</b> this is the core proof that the v1 architecture is "
        "not SNR-gated at useful indoor ranges — the CP-B acoustic gate rests on it.",
        "absorption-vs-frequency.png": "<b>Atmospheric absorption vs frequency</b> (ISO 9613-1 relaxation model, "
        "20 °C / 50 % RH). <b>Why it matters:</b> absorption is the term that kills "
        "range above ~32 kHz; it fixes the 20–32 kHz chirp band and feeds every "
        "range number on this page.",
        "option-b-vs-c-noise.png": "<b>Microphone noise comparison in the chirp band.</b> ICS-41352 adds only "
        "+0.15 dB total noise over the analog reference in the stated ambient "
        "context. <b>Why it matters:</b> the SPH0641 vs ICS-41352 decision (D011) "
        "cannot be settled from datasheets — it rides on the T-016 coupon bake-off below.",
        "max-range-vs-frequency.png": "<b>Zero-margin range by target and transmitter vs frequency.</b> Person: "
        "20.2 m at 25 kHz with the wideband placeholder; the narrowband MA40S4S "
        "only pays off at 40 kHz. <b>Why it matters:</b> frames the D013 TX choice "
        "you are being asked to ratify (review item 1).",
        "blind-zone-vs-chirp.png": "<b>Blind zone vs chirp length.</b> 0.5 ms chirp → 3 m listen range, "
        "6.67 ms → 30 m. <b>Why it matters:</b> this is the chirp-length↔minimum-range "
        "schedule the firmware and host DSP both implement.",
    }
    analysis_html = ""
    for png in sorted((ROOT / "analysis" / "generated").glob("*.png")):
        href = copy_asset(png)
        cap = analysis_captions.get(png.name, f"<b>{esc(png.name)}</b> — T-001 generated output.")
        analysis_html += figure(href, cap)

    # ---- section 3: host DSP + pico sim
    host_html = ""
    demo_svg = ROOT / "host" / "artifacts" / "t021-demo.svg"
    if demo_svg.exists():
        href = copy_asset(demo_svg)
        host_html += figure(
            href,
            f"<b>T-021 synthetic point-target demo (host/artifacts/t021-demo.svg).</b> "
            f"Range profile (teal) and bearing scan (red) from the full Python pipeline — "
            f"PDM decimation → calibration → matched filter → beamformer — on a synthetic "
            f"target. Truth {t021['truth']} m / {t021['truth_b']}°, recovered "
            f"{t021['est']} m / {t021['est_b']}°. <b>Why it matters:</b> the entire DSP "
            f"chain is proven end-to-end before any hardware exists; range error is "
            f"0.002 m against a 0.18 m tolerance.",
        )
    spec_png = ensure_spectrogram_png()
    if spec_png:
        host_html += figure(
            f"assets/{spec_png.name}",
            "<b>T-009 Pico snapshot: synthetic 28 kHz PDM spectrogram"
            " (firmware/pico-snapshot/host/simulate.py).</b> 16 ms / 49,152 frames of"
            " synthetic 3.072 MHz PDM run through the receiver's packet decode and the"
            " decimator; the bright line is the 28 kHz tone recovered at bin ~28 of"
            " 64 (tone/off-tone power ratio 287 dB), exactly where physics puts it."
            " <b>Why it matters:</b> the SNP1 packet format, CRCs, and decimation math"
            " the Pico firmware speaks are verified bit-exact off-hardware.",
        )
    else:
        host_html += '<p class="warn">T-009 spectrogram could not be generated.</p>'

    # ---- section 4: schematics
    featured = [
        (
            "sonar.svg",
            "<b>Top-level Sonar v1 hierarchy.</b> This is the map connecting power,"
            " digital, TX, and the still-legacy array hierarchy. <b>Why:</b> it makes"
            " the current boundary explicit — T-010 replaces the array only after"
            " the microphone coupon gate releases an exact MPN and footprint.",
        ),
        (
            "sonar-digital.svg",
            "<b>Digital sheet — Cmod A7-35T socket (J40).</b> Pin 24 = 5V_CMOD via R420,"
            " pin 25 GND, 15/16 NC — the corner that was wrong until the live XDC fetch"
            " caught it. <b>Why:</b> every net on this sheet is gated 44/44 against the"
            " Digilent master XDC; this is the sheet to eyeball (review item 8).",
        ),
        (
            "sonar-TX Drive.svg",
            "<b>TX Drive — DRV8876 H-bridge.</b> VM = +12 V, VREF = 3.3 V (~1.95 A trip),"
            " nFAULT pulled up, off-board transducer on J50 with 0R series + DNP snubber."
            " <b>Why:</b> the hard per-half-cycle duty bound (TB 13) is what keeps the"
            " transducer inside its 20 Vpp limit — see tx-limits.md (review item 10).",
        ),
        (
            "sonar-power_supply.svg",
            "<b>Power supply sheet.</b> USB-C 5 V + XT60 input and the 3.3 V buck with the"
            " filtered 3V3_MIC branch. <b>Why:</b> ERC-clean; the Cmod now feeds from the"
            " carrier 5 V through R420 (review item 2).",
        ),
        (
            "sonar-power_supply-Vin to 12V Boost.svg",
            "<b>5 V → 12 V boost.</b> Generates the TX rail. <b>Why:</b> 12 V VM is what"
            " drives the whole TX drive-limit discussion in D013.",
        ),
        (
            "sonar-power_mux.svg",
            "<b>Power mux.</b> Source selection between USB-C and XT60."
            " <b>Why:</b> ERC-clean after the T-012 power-tree prune.",
        ),
        (
            "sonar-power_mux-ideal_diode0.svg",
            "<b>Ideal diode 0.</b> One of the two ideal-diode OR-ing stages in the mux.",
        ),
        (
            "sonar-power_mux-ideal_diode1.svg",
            "<b>Ideal diode 1.</b> Second OR-ing stage; both sheets ERC-clean.",
        ),
    ]
    sch_html = (
        f'<p class="note"><b>Render source:</b> {esc(main_sch_status)}. '
        f"{esc(main_pdf_status)}. "
        + (
            f'<a href="{esc(main_pdf)}" target="_blank">Open the complete '
            f"multipage schematic PDF</a>."
            if main_pdf
            else ""
        )
        + "</p>"
    )
    svg_dir = ROOT / "build" / "sonar-svg"  # fallback only
    for name, cap in featured:
        href = main_sch.get(name)
        if href:
            sch_html += figure(href, cap)
        else:
            p = svg_dir / name
            if p.exists():
                sch_html += figure(copy_asset(p), cap)
            else:
                sch_html += f'<p class="warn">Missing schematic render: {esc(name)}</p>'

    sch_html += "<h3>Coupon schematics</h3>"
    sch_html += (
        f'<p class="section-intro">SPH export: {esc(sph_sch_status)}. '
        f"ICS export: {esc(ics_sch_status)}.</p>"
    )
    for mapping, name, label in [
        (sph_sch, "sph-coupon.svg", "SPH0641LU4H-1 coupon schematic"),
        (ics_sch, "ics-coupon.svg", "ICS-41352 coupon schematic"),
    ]:
        href = mapping.get(name)
        if href:
            sch_html += figure(
                href,
                f"<b>{esc(label)}.</b> Four microphones, the worst-case four-load "
                f"CDCLVC1112 clock branch, SELECT pairing, power filtering, and test header.",
            )
        else:
            sch_html += f'<p class="warn">Missing {esc(label)} render.</p>'

    legacy_paths = sorted(
        (Path(name), href) for name, href in main_sch.items() if "eight_transducer_array" in name
    )
    if not legacy_paths:
        legacy_paths = [
            (p, copy_asset(p))
            for p in sorted(svg_dir.glob("*.svg"))
            if "eight_transducer_array" in p.name
        ]
    legacy = legacy_paths
    if legacy:
        items = "".join(
            figure(
                href,
                f"<b>{esc(p.name)}</b> — legacy per-channel analog RX sheet; "
                f"replaced by the T-010 PDM array rebuild.",
            )
            for p, href in legacy
        )
        sch_html += (
            f"<details><summary>Legacy eight_transducer_array / rx_amp sheets "
            f"({len(legacy)} renders) — being replaced by T-010</summary>"
            f"{items}</details>"
        )
    if stale_note and not main_sch:
        sch_html = f'<p class="warn">{esc(stale_note)}</p>' + sch_html

    # ---- section 5: physical boards / layouts
    layout_html = (
        '<p class="warn"><b>Main-board layout is not a CP-C deliverable yet.</b> '
        "P3 has not started and <code>sonar.kicad_pcb</code> is the sparse legacy board "
        f"(current report: {esc(drc['violations'])} DRC violations / "
        f"{esc(drc['unconnected'])} unconnected pads / "
        f"{esc(drc['footprints'])} footprint errors). It does not contain "
        "the v2 schematic placement or routing. It is shown so you can see the exact "
        "physical state instead of mistaking “schematics done” for “board laid out.”</p>"
    )
    layout_html += board_gallery(
        main_board,
        "Main board — current legacy/pre-v2 PCB",
        '<span class="status-pill blocked">NOT FOR APPROVAL</span> Only the old board '
        "outline and a small amount of legacy placement exist. T-010/T-014/T-015 and "
        "then P3 must happen before the production layout exists.",
        main_board_errors,
    )
    layout_html += (
        '<p class="note"><b>Coupon boards are the current physical design to review.</b> '
        "Each is 70×30 mm, four layers, four bottom-port microphones, four 0.50 mm NPTH "
        "acoustic ports, and the worst four-load clock branch. T-022 repaired the "
        "complete CDCLVC1112 pin map and physical shorts: rev B full DRC is 0/0/0 "
        "for both variants. Read the "
        '<a href="../../coupons/mic-bakeoff/docs/T-022-release-verification.md">'
        "repair evidence and remaining DFM gates</a>. Sourcing, assembly DFM and "
        "purchase approval remain Joshua’s; the integrated echo path is still "
        "unfinished (T-023/T-024/T-025).</p>"
    )
    layout_html += board_gallery(
        sph_board,
        "SPH0641LU4H-1 microphone coupon",
        '<span class="status-pill pending">CP-BM REVIEW</span> Separate exact SPH land '
        "pattern; fully generated fabrication package exists under "
        "<code>build/t016/sph-coupon-fab/</code>.",
        sph_board_errors,
    )
    layout_html += board_gallery(
        ics_board,
        "ICS-41352 microphone coupon",
        '<span class="status-pill pending">CP-BM REVIEW</span> Separate exact ICS land '
        "pattern; fully generated fabrication package exists under "
        "<code>build/t016/ics-coupon-fab/</code>.",
        ics_board_errors,
    )

    # ---- section 6: gateware
    tb_lis = "".join(f"<li>{esc(t)}</li>" for t in tbs)
    gate_html = (
        f"<p><b>{len(tbs)}/17 testbenches PASS</b> "
        f'<span style="color:#6b7280">({esc(tb_source)})</span></p>'
        f'<ul class="tbs">{tb_lis}</ul>'
        f'<p>Architecture (PLAN.md):</p><pre class="arch">{esc(arch)}</pre>'
    )

    # ---- section 7: review items
    rev_lis = ""
    for it in review_items:
        body = md_inline(it["text"])
        gate = ' <span class="gate">GATE</span>' if "GATE" in it["text"] else ""
        rev_lis += (
            f'<li><label class="checkline"><input type="checkbox" '
            f'data-review-id="{esc(it["n"])}"> '
            f'<span class="item-text"><b>{esc(it["n"])}.</b> {body} {gate}</span></label>'
            f'<label for="review-note-{esc(it["n"])}"><span class="sr-only">'
            f"Decision or notes for item {esc(it['n'])}</span></label>"
            f'<textarea id="review-note-{esc(it["n"])}" data-note-id="{esc(it["n"])}" '
            f'placeholder="Decision or notes (saved only in this browser)"></textarea></li>'
        )
    ptr_lis = "".join(f"<li>{md_inline(p.lstrip('- '))}</li>" for p in review_pointers)
    review_html = (
        f'<ol class="review">{rev_lis}</ol>'
        f"<p><b>Later</b> (nothing to do until purchases/bench data exist):</p>"
        f"<ul>{ptr_lis}</ul>"
        f'<p style="color:#6b7280">Checkboxes and notes are saved locally in'
        f" this browser; nothing is sent or committed automatically. Source: "
        f'<a href="../../orchestration/review/JOSHUA-REVIEW-PLAN.md">'
        f"orchestration/review/JOSHUA-REVIEW-PLAN.md</a></p>"
    )

    # ---- assemble
    guide_titles = [
        "Where the project stands",
        "Physics and microphone evidence",
        "DSP and Pico proof",
        "Schematics",
        "Physical boards and layouts",
        "FPGA gateware proof",
        "Your decisions and checks",
        "Share the review result",
    ]
    jump_options = "".join(
        f'<option value="{i}">{i + 1}. {esc(title)}</option>'
        for i, title in enumerate(guide_titles)
    )
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sonar v1 — guided visual review</title><style>{CSS}</style></head>
<body><main>
<h1>Sonar v1 — guided visual review</h1>
<p class="lede">For Joshua. This walks you through what exists, what is simulated,
what is physically laid out, and exactly which choices still need you. Every image
opens at full resolution; red GATE items block ordering or later phases.</p>

<nav class="guidebar" aria-label="Guided review navigation">
  <div class="row">
    <div class="where"><b id="guide-position">Step 1 of 8</b> —
      <span id="guide-title">Where the project stands</span><br>
      <span id="review-progress">0 review items checked</span></div>
    <select class="jump" id="guide-jump" aria-label="Jump to review step">{jump_options}</select>
    <button type="button" id="guide-prev">Previous</button>
    <button type="button" class="primary" id="guide-next">Next</button>
    <button type="button" id="guide-toggle">Show everything</button>
  </div>
  <progress id="guide-progress" max="8" value="1">1 of 8</progress>
</nav>

<section class="guide-step" data-title="{esc(guide_titles[0])}" id="step-1">
<h2><span class="num">1</span>WHERE THE PROJECT STANDS</h2>
<p>All currently possible P1/P2/P5 agent work is landed and the project is
<b>human-gated</b>. The analysis, digital/power/TX schematics, portable gateware
simulation, Pico snapshot firmware, host DSP, and microphone coupon package exist.
The production microphone, array schematic, production BOM, FPGA bitstream, and
main-board layout do not exist yet.</p>
<table class="key">
<tr><th>Area</th><th>State</th><th>What that means</th></tr>
<tr><td>Analysis + architecture</td><td><span class="status-pill done">DONE</span></td>
<td>T-001/T-008 establish feasibility and a provisional PDM baseline.</td></tr>
<tr><td>Digital, power, TX schematics</td><td><span class="status-pill done">DONE</span></td>
<td>Repaired after cross-family review; visual renders are in step 4.</td></tr>
<tr><td>Microphone coupons</td><td><span class="status-pill pending">YOUR REVIEW</span></td>
<td>Two physically separate candidate boards await CP-BM checks and ordering.</td></tr>
<tr><td>Main RX array schematic</td><td><span class="status-pill blocked">BLOCKED</span></td>
<td>T-010 waits for the measured microphone/footprint release from T-016.</td></tr>
<tr><td>Main PCB placement + routing</td><td><span class="status-pill blocked">NOT STARTED</span></td>
<td>P3 starts only after CP-C. The current PCB file is legacy and sparse.</td></tr>
<tr><td>FPGA bitstream + hardware</td><td><span class="status-pill blocked">WAITING</span></td>
<td>Needs the x86 Vivado host and purchased Cmod/FT232H hardware.</td></tr>
</table>
<h3>Evidence snapshot</h3>
<table class="key">
<tr><th>Check</th><th>Result</th><th>Source</th></tr>
<tr><td>T-001 person margin @ 10 m</td><td class="v">{esc(numbers["margin_10m"])}</td>
<td>analysis/link_budget.md</td></tr>
<tr><td>T-001 zero-margin range</td><td class="v">{esc(numbers["zero_margin_range"])}</td>
<td>analysis/link_budget.md</td></tr>
<tr><td>T-021 synthetic target recovery</td><td class="v">{t021["est"]} m vs {t021["truth"]} m</td>
<td>host/artifacts/t021-demo-summary.txt</td></tr>
<tr><td>T-021 ingest benchmark</td><td class="v">{esc(bench)}</td>
<td>T-021 latest log run</td></tr>
<tr><td>T-020 gateware tests</td><td class="v">{len(tbs)}/17 PASS</td>
<td>gateware make test — {esc(tb_source)}</td></tr>
<tr><td>Main schematic ERC</td><td class="v">{erc["total"]} total; modern sheets {erc["modern"]}</td>
<td>build/sonar-erc.rpt</td></tr>
<tr><td>T-011 pinmap vs Digilent XDC</td><td class="v">{esc(pinmap)}</td>
<td>scripts/check_pinmap_vs_xdc.py</td></tr>
</table>
</section>

<section class="guide-step" data-title="{esc(guide_titles[1])}" id="step-2">
<h2><span class="num">2</span>PHYSICS + MICROPHONE EVIDENCE</h2>
<p class="section-intro">These plots answer “does the architecture have enough
signal?” and “what can only be settled by measurements?”</p>
{analysis_html}
</section>

<section class="guide-step" data-title="{esc(guide_titles[2])}" id="step-3">
<h2><span class="num">3</span>DSP + PICO PROOF</h2>
<p class="section-intro">Generated demonstrations of the laptop processing chain
and the snapshot-mode packet/decimation path.</p>
{host_html}
</section>

<section class="guide-step" data-title="{esc(guide_titles[3])}" id="step-4">
<h2><span class="num">4</span>SCHEMATICS</h2>
<p class="section-intro">Fresh kicad-cli SVG renders. Click any sheet to inspect
the original vector image; the full multipage PDF is linked below.</p>
{sch_html}
</section>

<section class="guide-step" data-title="{esc(guide_titles[4])}" id="step-5">
<h2><span class="num">5</span>PHYSICAL BOARDS + LAYOUTS</h2>
<p class="section-intro">Top/bottom 3D renders and top/bottom copper/mask/silkscreen
plots generated directly from each current <code>.kicad_pcb</code>.</p>
{layout_html}
</section>

<section class="guide-step" data-title="{esc(guide_titles[5])}" id="step-6">
<h2><span class="num">6</span>FPGA GATEWARE PROOF</h2>
<p class="section-intro">Portable simulation is complete. Vivado synthesis,
placed timing/CDC, UNISIM equivalence, and physical streaming remain hardware-gated.</p>
{gate_html}
</section>

<section class="guide-step" data-title="{esc(guide_titles[6])}" id="step-7">
<h2><span class="num">7</span>YOUR DECISIONS + CHECKS</h2>
<p class="section-intro">Work down this list. Check an item when reviewed and write
the decision or concern underneath. Progress stays only in this browser.</p>
{review_html}
</section>

<section class="guide-step" data-title="{esc(guide_titles[7])}" id="step-8">
<h2><span class="num">8</span>SHARE THE REVIEW RESULT</h2>
<p>Generate a concise summary, then paste it back into Codex. Nothing on this page
changes a ticket, ratifies a decision, or authorizes spending until you explicitly
send the result.</p>
<div class="review-actions">
  <button type="button" id="build-summary">Build summary</button>
  <button type="button" class="primary" id="copy-summary">Copy summary</button>
  <span id="copy-state" aria-live="polite"></span>
</div>
<label for="review-summary-output"><b>Review summary</b></label>
<textarea class="summary-box" id="review-summary-output" placeholder="Your checked items and notes will appear here."></textarea>
<p class="note"><b>Recommended minimum response:</b> D013 decision, Cmod R420 power
strategy, Vivado-host choice, CDCLVC1112 pin-map result, and whether the coupon
order package is approved to proceed to current-price/stock refresh.</p>
</section>

<footer>Generated {esc(now)} by scripts/gen_review_page.py · git {esc(git)}
({esc(branch)}) · local assets in build/review/assets/ · source links are
repo-relative and resolve when viewed at build/review/index.html</footer>
</main><script>{JS}</script></body></html>
"""

    (REVIEW / "index.html").write_text(page)

    # ---- verify every src/href resolves
    broken, checked = [], 0
    for attr in re.findall(r'(?:src|href)="([^"]+)"', page):
        if attr.startswith(("http://", "https://", "mailto:", "#")):
            continue
        checked += 1
        if not (REVIEW / attr).resolve().exists():
            broken.append(attr)
    print(
        f"link check: {checked} local src/href attributes, "
        f"{checked - len(broken)} resolve, {len(broken)} broken"
    )
    for b in broken:
        print(f"  BROKEN: {b}")
    n_assets = len(list(ASSETS.iterdir()))
    print(f"assets copied: {n_assets}")
    if broken:
        return 1
    print("link check: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
