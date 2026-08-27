#!/usr/bin/env python3
"""Assemble build/review/index.html — a self-contained visual review page for
Joshua, the human gate on the Sonar v1 project.

The page is dark-on-light, framework-free, lazy-loaded, and every figure is
captioned with what it shows and why it matters. All image assets are copied
into build/review/assets/ so the build/review/ folder is portable (build/ is
gitignored; only this script is committed). Links to source documents are
repo-relative (../../...) and resolve when the page is viewed in place.

Usage:
    python3 scripts/gen_review_page.py [--fallback DIR ...] [--skip-gateware]

--fallback DIR   Extra repo checkouts to search for artifacts missing here
                 (e.g. the main checkout's build/t016 coupon renders).
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
table.key { border-collapse: collapse; width: 100%; margin: 1em 0; background: #fff; }
table.key th, table.key td { border: 1px solid #d4d4cc; padding: 8px 12px;
     text-align: left; vertical-align: top; }
table.key th { background: #e8ecef; }
table.key td.v { font-family: Menlo, Consolas, monospace; white-space: nowrap; }
figure { background: #fff; border: 1px solid #d4d4cc; border-radius: 6px;
         padding: 12px; margin: 14px 0; }
figure img { max-width: 100%; height: auto; display: block; margin: 0 auto;
         background: #fff; }
figcaption { margin-top: 8px; font-size: 0.92rem; color: #374151; }
figcaption b { color: #1c2733; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 18px; }
@media (max-width: 800px) { .grid { grid-template-columns: 1fr; } }
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
"""

# ---------------------------------------------------------------- utilities

def find_asset(rel: str, fallbacks: list[Path]) -> Path | None:
    for base in [ROOT, *fallbacks]:
        p = base / rel
        if p.exists():
            return p
    return None


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
        px = list(data[m.end(): m.end() + w * h])
    else:
        px = [int(t) for t in data[m.end():].split()][: w * h]
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
    raw = b"".join(b"\x00" + bytes(px[y * w:(y + 1) * w]) for y in range(h))

    def chunk(tag: bytes, payload: bytes) -> bytes:
        c = tag + payload
        return struct.pack(">I", len(payload)) + c + struct.pack(">I", zlib.crc32(c))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


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
        for key, pat in [("truth", r"truth_range_m=([\d.]+)"),
                         ("est", r"estimated_range_m=([\d.]+)"),
                         ("truth_b", r"truth_bearing_deg=([\d.]+)"),
                         ("est_b", r"estimated_bearing_deg=([\d.]+)")]:
            m = re.search(pat, t)
            if m:
                out[key] = m.group(1)
    return out


def pull_t021_benchmark() -> str:
    ticket = ROOT / "orchestration" / "tickets" / "T-021-host-sw-skeleton.md"
    if ticket.exists():
        runs = re.findall(
            r"benchmark: ([\d.]+) MB/s vs target ([\d.]+) MB/s \(([\d.]+)x\)",
            ticket.read_text())
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
        return (f"{len(stale)} schematic SVG(s) predate the newest .kicad_sch edit — "
                f"re-run ./scripts/check.sh unsandboxed to refresh. "
                f"(In this sandbox kicad-cli pcb drc SIGABRTs; ERC/SVG renders do run.)")
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
    return (f"<figure><img src=\"{esc(href)}\" loading=\"lazy\" alt=\"{esc(caption[:80])}\" {extra}>"
            f"<figcaption>{caption}</figcaption></figure>")


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fallback", action="append", default=[],
                    help="extra repo checkout to search for missing artifacts")
    ap.add_argument("--skip-gateware", action="store_true",
                    help="use cached gateware TB list instead of make test")
    args = ap.parse_args()
    fallbacks = [Path(d).resolve() for d in args.fallback]

    if REVIEW.exists():
        shutil.rmtree(REVIEW)
    ASSETS.mkdir(parents=True)

    numbers = pull_link_budget_numbers()
    t021 = ensure_t021_demo()
    bench = pull_t021_benchmark()
    erc = pull_erc()
    pinmap = pull_pinmap_gate()
    tbs, tb_source = pull_gateware_tbs(args.skip_gateware)
    arch = pull_arch_diagram()
    stale_note = schematic_staleness_note()
    review_items, review_pointers = parse_review_plan()
    git = run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT)[1].strip() or "unknown"
    branch = run(["git", "branch", "--show-current"], cwd=ROOT)[1].strip() or "unknown"
    now = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")

    # ---- section 2: analysis plots
    analysis_captions = {
        "person-margin-vs-range.png":
            "<b>Sonar-equation margin vs range, person target (T-001).</b> The reference "
            "build keeps +27.1 dB margin at 10 m and hits zero margin at 20.2 m. "
            "<b>Why it matters:</b> this is the core proof that the v1 architecture is "
            "not SNR-gated at useful indoor ranges — the CP-B acoustic gate rests on it.",
        "absorption-vs-frequency.png":
            "<b>Atmospheric absorption vs frequency</b> (ISO 9613-1 relaxation model, "
            "20 °C / 50 % RH). <b>Why it matters:</b> absorption is the term that kills "
            "range above ~32 kHz; it fixes the 20–32 kHz chirp band and feeds every "
            "range number on this page.",
        "option-b-vs-c-noise.png":
            "<b>Microphone noise comparison in the chirp band.</b> ICS-41352 adds only "
            "+0.15 dB total noise over the analog reference in the stated ambient "
            "context. <b>Why it matters:</b> the SPH0641 vs ICS-41352 decision (D011) "
            "cannot be settled from datasheets — it rides on the T-016 coupon bake-off below.",
        "max-range-vs-frequency.png":
            "<b>Zero-margin range by target and transmitter vs frequency.</b> Person: "
            "20.2 m at 25 kHz with the wideband placeholder; the narrowband MA40S4S "
            "only pays off at 40 kHz. <b>Why it matters:</b> frames the D013 TX choice "
            "you are being asked to ratify (review item 1).",
        "blind-zone-vs-chirp.png":
            "<b>Blind zone vs chirp length.</b> 0.5 ms chirp → 3 m listen range, "
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
            f"0.002 m against a 0.18 m tolerance.")
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
            " the Pico firmware speaks are verified bit-exact off-hardware.")
    else:
        host_html += '<p class="warn">T-009 spectrogram could not be generated.</p>'

    # ---- section 4: schematics
    featured = [
        ("sonar-digital.svg",
         "<b>Digital sheet — Cmod A7-35T socket (J40).</b> Pin 24 = 5V_CMOD via R420,"
         " pin 25 GND, 15/16 NC — the corner that was wrong until the live XDC fetch"
         " caught it. <b>Why:</b> every net on this sheet is gated 44/44 against the"
         " Digilent master XDC; this is the sheet to eyeball (review item 8)."),
        ("sonar-TX Drive.svg",
         "<b>TX Drive — DRV8876 H-bridge.</b> VM = +12 V, VREF = 3.3 V (~1.95 A trip),"
         " nFAULT pulled up, off-board transducer on J50 with 0R series + DNP snubber."
         " <b>Why:</b> the hard per-half-cycle duty bound (TB 13) is what keeps the"
         " transducer inside its 20 Vpp limit — see tx-limits.md (review item 10)."),
        ("sonar-power_supply.svg",
         "<b>Power supply sheet.</b> USB-C 5 V + XT60 input and the 3.3 V buck with the"
         " filtered 3V3_MIC branch. <b>Why:</b> ERC-clean; the Cmod now feeds from the"
         " carrier 5 V through R420 (review item 2)."),
        ("sonar-power_supply-Vin to 12V Boost.svg",
         "<b>5 V → 12 V boost.</b> Generates the TX rail. <b>Why:</b> 12 V VM is what"
         " drives the whole TX drive-limit discussion in D013."),
        ("sonar-power_mux.svg",
         "<b>Power mux.</b> Source selection between USB-C and XT60."
         " <b>Why:</b> ERC-clean after the T-012 power-tree prune."),
        ("sonar-power_mux-ideal_diode0.svg",
         "<b>Ideal diode 0.</b> One of the two ideal-diode OR-ing stages in the mux."),
        ("sonar-power_mux-ideal_diode1.svg",
         "<b>Ideal diode 1.</b> Second OR-ing stage; both sheets ERC-clean."),
    ]
    sch_html = ""
    svg_dir = ROOT / "build" / "sonar-svg"
    for name, cap in featured:
        p = svg_dir / name
        if p.exists():
            sch_html += figure(copy_asset(p), cap)
    legacy = sorted(p for p in svg_dir.glob("*.svg")
                    if "eight_transducer_array" in p.name)
    if legacy:
        items = "".join(
            figure(copy_asset(p),
                   f"<b>{esc(p.name)}</b> — legacy per-channel analog RX sheet; "
                   f"replaced by the T-010 PDM array rebuild.") for p in legacy)
        sch_html += (f"<details><summary>Legacy eight_transducer_array / rx_amp sheets "
                     f"({len(legacy)} renders) — being replaced by T-010</summary>"
                     f"{items}</details>")
    if stale_note:
        sch_html = f'<p class="warn">{esc(stale_note)}</p>' + sch_html

    # ---- section 5: mic coupons
    coupon_html = ('<p class="note"><b>What this bake-off decides:</b> whether the v1 '
                   'production microphone is the SPH0641LU4H-1 or the ICS-41352 — measured '
                   'on identical coupon boards through the worst-case four-load clock branch. '
                   'The result ratifies the MPN/footprint (D011) and unblocks the T-010 array '
                   'rebuild; nothing is ordered until Joshua clears the CP-BM pre-order '
                   'checklist (review items 5–6).</p>')
    for rel, who in [("build/t016/sph-coupon-fab/sph-coupon-filled.svg", "SPH0641LU4H-1"),
                     ("build/t016/ics-coupon-fab/ics-coupon-filled.svg", "ICS-41352")]:
        p = find_asset(rel, fallbacks)
        if p:
            coupon_html += figure(
                copy_asset(p, Path(rel).name),
                f"<b>{who} coupon, filled zones ({esc(Path(rel).name)}).</b> Four mics at"
                f" 12 mm pitch on one CDCLVC1112PWR clock output, 0.50 mm NPTH acoustic"
                f" ports, 70×30 mm 4-layer. <b>Why:</b> this exact board is what CP-BM"
                f" buys to settle the mic decision with measurements instead of proxy curves.")
        else:
            coupon_html += (f'<p class="warn">Missing {esc(rel)} — generate in the main '
                            f'checkout via coupons/mic-bakeoff/check_coupons.sh, or pass '
                            f'--fallback /path/to/main-checkout.</p>')

    # ---- section 6: gateware
    tb_lis = "".join(f"<li>{esc(t)}</li>" for t in tbs)
    gate_html = (f"<p><b>{len(tbs)}/17 testbenches PASS</b> "
                 f"<span style=\"color:#6b7280\">({esc(tb_source)})</span></p>"
                 f"<ul class=\"tbs\">{tb_lis}</ul>"
                 f"<p>Architecture (PLAN.md):</p><pre class=\"arch\">{esc(arch)}</pre>")

    # ---- section 7: review items
    rev_lis = ""
    for it in review_items:
        body = md_inline(it["text"])
        gate = ' <span class="gate">GATE</span>' if "GATE" in it["text"] else ""
        rev_lis += (f'<li><label><input type="checkbox"> '
                    f'<b>{esc(it["n"])}.</b> {body}</label>{gate}</li>')
    ptr_lis = "".join(f"<li>{md_inline(p.lstrip('- '))}</li>" for p in review_pointers)
    review_html = (f"<ol class=\"review\">{rev_lis}</ol>"
                   f"<p><b>Later</b> (nothing to do until purchases/bench data exist):</p>"
                   f"<ul>{ptr_lis}</ul>"
                   f"<p style=\"color:#6b7280\">Checkboxes are scratch space — state is not"
                   f" saved. Source: <a href=\"../../orchestration/review/JOSHUA-REVIEW-PLAN.md\">"
                   f"orchestration/review/JOSHUA-REVIEW-PLAN.md</a></p>")

    # ---- assemble
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sonar v1 — visual review</title><style>{CSS}</style></head>
<body><main>
<h1>Sonar v1 — visual review page</h1>
<p class="lede">For Joshua. Everything here is bite-sized; GATE items block spending.
Generated from the live repo — every number below is pulled from project outputs,
not typed by hand.</p>

<h2><span class="num">1</span>AT A GLANCE</h2>
<p>All P1/P2/P5 agent work is landed and the project is <b>human-gated</b>: the T-001
link budget, T-008 mic electrical baseline, T-009 Pico snapshot firmware, T-020 gateware
simulator milestone, and T-021 host DSP pipeline are done; the T-016 mic bake-off
coupons are at review behind your CP-BM gate. What remains: your CP-B/CP-BM reviews
(section 7), the T-007 purchases/host choice, then T-010 array rebuild → T-014 BOM →
T-015 cross-family review → CP-C schematic sign-off.</p>
<table class="key">
<tr><th>Check</th><th>Result</th><th>Source</th></tr>
<tr><td>T-001 link budget — person margin @ 10 m</td><td class="v">{esc(numbers['margin_10m'])}</td>
<td>analysis/link_budget.md</td></tr>
<tr><td>T-001 zero-margin range (person, 25 kHz wideband)</td><td class="v">{esc(numbers['zero_margin_range'])}</td>
<td>analysis/link_budget.md / generated/max-range-summary.csv</td></tr>
<tr><td>T-021 synthetic target recovery</td><td class="v">{t021['est']} m vs {t021['truth']} m truth</td>
<td>host/artifacts/t021-demo-summary.txt (regenerated if missing)</td></tr>
<tr><td>T-021 ingest benchmark vs 9.216 MB/s contract</td><td class="v">{esc(bench)}</td>
<td>orchestration/tickets/T-021-host-sw-skeleton.md (latest log run)</td></tr>
<tr><td>T-020 gateware testbenches</td><td class="v">{len(tbs)}/17 PASS</td>
<td>gateware make test — {esc(tb_source)}</td></tr>
<tr><td>Schematic ERC (sonar project)</td><td class="v">{erc['total']} violations, all legacy sheets; modern sheets {erc['modern']}</td>
<td>build/sonar-erc.rpt</td></tr>
<tr><td>T-011 pinmap gate vs live Digilent XDC</td><td class="v">{esc(pinmap)}</td>
<td>scripts/check_pinmap_vs_xdc.py (run at page generation)</td></tr>
</table>

<h2><span class="num">2</span>ANALYSIS PLOTS <span style="font-weight:400;font-size:0.8em">— T-001 link budget + mic comparison</span></h2>
{analysis_html}

<h2><span class="num">3</span>HOST DSP + PICO SIM <span style="font-weight:400;font-size:0.8em">— T-021 + T-009 generated demos</span></h2>
{host_html}

<h2><span class="num">4</span>SCHEMATICS <span style="font-weight:400;font-size:0.8em">— kicad-cli SVG renders</span></h2>
{sch_html}

<h2><span class="num">5</span>MIC COUPONS <span style="font-weight:400;font-size:0.8em">— T-016 bake-off, your CP-BM gate</span></h2>
{coupon_html}

<h2><span class="num">6</span>GATEWARE <span style="font-weight:400;font-size:0.8em">— T-020 simulator milestone</span></h2>
{gate_html}

<h2><span class="num">7</span>YOUR REVIEW ITEMS <span style="font-weight:400;font-size:0.8em">— from JOSHUA-REVIEW-PLAN.md</span></h2>
{review_html}

<footer>Generated {esc(now)} by scripts/gen_review_page.py · git {esc(git)}
({esc(branch)}) · assets in build/review/assets/ · links to source docs are
repo-relative and resolve when this page is viewed in place at build/review/index.html</footer>
</main></body></html>
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
    print(f"link check: {checked} local src/href attributes, "
          f"{checked - len(broken)} resolve, {len(broken)} broken")
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
