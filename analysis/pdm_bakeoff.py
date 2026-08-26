#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy>=1.26,<3"]
# ///
"""Deterministic T-016 PDM microphone coupon bake-off analysis.

Implements the exact normative v1 screening estimator, every quantitative gate,
and the explicit selection rule from
``orchestration/tickets/T-016-pdm-mic-coupon-bakeoff.md``. The normative
estimator text is NOT duplicated here: this module locates the canonical
``T016-U95-ESTIMATOR`` block in ``docs/pdm-rx-design.md`` and the T-016 ticket,
verifies the two copies are byte-identical, and prints their hash so the
report is anchored to the reviewed text.

Usage:
    python3 analysis/pdm_bakeoff.py --selftest
    python3 analysis/pdm_bakeoff.py --dataset path/to/dataset.json \\
        --report-json out.json --report-md out.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
NORMATIVE_BEGIN = "<!-- T016-U95-ESTIMATOR-BEGIN -->"
NORMATIVE_END = "<!-- T016-U95-ESTIMATOR-END -->"
NORMATIVE_SOURCES = (
    REPO_ROOT / "docs" / "pdm-rx-design.md",
    REPO_ROOT / "orchestration" / "tickets" / "T-016-pdm-mic-coupon-bakeoff.md",
)

# --- Normative thresholds (T-016 ticket / docs/pdm-rx-design.md) ---------------
CANDIDATES = ("SPH0641LU4H-1", "ICS-41352")
SPH, ICS = CANDIDATES
N_COUPONS, N_SITES, N_RESEATS = 3, 4, 3
MIN_VALID_UNITS = 12
DECISION_BIN_EDGES_KHZ = [(20.0 + k, 21.0 + k) for k in range(12)]
BAND_HZ = (20_000.0, 32_000.0)
U_FIXTURE_K2_MAX_DB = 1.0
DRIFT_MAX_DB = 0.5
DRIFT_MAX_DEG = 5.0
T001_MARGIN_10M_MIN_DB = 24.09
T001_RANGE_25KHZ_MIN_M = 18.91
T001_SMALL_TARGET_MIN_DB = 4.1
TIE_LOSS_DB = 3.0
HARD_LOSS_DB = 6.0
SPREAD_MAX_DB = 3.0
BIN_OUTLIER_MAX_DB = 6.0
REL_SPREAD_MAX_DB = 1.0
RESEAT_RMS_MAG_MAX_DB = 0.5
RESEAT_RMS_PHASE_MAX_DEG = 5.0
RESEAT_BIN_MAG_MAX_DB = 1.0
RESEAT_BIN_PHASE_MAX_DEG = 10.0
AOP_MIN_DB_SPL = 117.0
AOP_REL_MAX_DB = 3.0
RECOVERY_PASS_S = 250e-6
RECOVERY_REVIEW_S = 1e-3
RAIL_ALLOC_MA = 100.0
RAIL_STEADY_EST_MAX_MA = 80.0  # >=25% reserve on the 100 mA allocation
BOARD_SKEW_MAX_NS = 0.500

# Four-load SPH branch limits (T-008 / T-016). ICS limits are dataset-supplied
# from the primary datasheet revision used at the bench.
SPH_ELECTRICAL_LIMITS = {
    "duty_pct": (48.0, 52.0),
    "rise_ns": (None, 3.0),
    "fall_ns": (None, 3.0),
    "tdd_ns": (None, 40.0),
    "tdz_ns": (3.0, None),
    "skew_ns": (None, BOARD_SKEW_MAX_NS),
}


def normative_block(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    begin = text.index(NORMATIVE_BEGIN)
    end = text.index(NORMATIVE_END) + len(NORMATIVE_END)
    return text[begin:end]


def check_normative_identity() -> str:
    """Verify the two canonical estimator blocks are byte-identical."""
    blocks = [normative_block(p) for p in NORMATIVE_SOURCES]
    digest = hashlib.sha256(blocks[0].encode()).hexdigest()
    for path, block in zip(NORMATIVE_SOURCES, blocks, strict=True):
        if block != blocks[0]:
            raise ValueError(f"normative estimator block diverged in {path}")
    return digest


# --- Exact v1 screening estimator ---------------------------------------------
# The hierarchy below is the executable form of the canonical T016-U95-ESTIMATOR
# block (byte-identity of the text checked above; semantics mirrored 1:1):
#   m_unit[q,u] = median_r(x[q,u,r]);  m_coupon[q] = median_u(m_unit[q,u]);
#   m = median_q(m_coupon[q]);  R/V/C worst observed deviations;
#   U95 = U_fixture_k2 + R + V + C  (linear sum, no RSS).


@dataclass(frozen=True)
class GuardResult:
    m: float
    r_term: float
    v_term: float
    c_term: float
    u_fixture_k2: float
    u95: float
    guarded: float
    complete: bool


def _is_missing(x: Any) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x))


def hierarchical_guard(
    x: list[list[list[float | None]]], u_fixture_k2: float
) -> GuardResult:
    """x[q][u][r] scalar dB screen metric over coupon/site/reseat."""
    if u_fixture_k2 > U_FIXTURE_K2_MAX_DB:
        raise ValueError(
            f"U_fixture_k2={u_fixture_k2:.3f} dB exceeds the {U_FIXTURE_K2_MAX_DB} dB "
            "fixture gate; comparison is fixture-invalid, not a microphone result"
        )
    complete = True
    m_unit: list[list[float]] = []
    for q in range(len(x)):
        row = []
        for u in range(len(x[q])):
            vals = [v for v in x[q][u] if not _is_missing(v)]
            if len(vals) < N_RESEATS:
                complete = False
            if not vals:
                row.append(math.nan)
                continue
            row.append(statistics.median(vals))
        m_unit.append(row)
    m_coupon = []
    for q in range(len(x)):
        vals = [v for v in m_unit[q] if not math.isnan(v)]
        if len(vals) < N_SITES:
            complete = False
        m_coupon.append(statistics.median(vals) if vals else math.nan)
    valid_coupons = [v for v in m_coupon if not math.isnan(v)]
    if len(valid_coupons) < N_COUPONS:
        complete = False
    m = statistics.median(valid_coupons) if valid_coupons else math.nan

    r_term = 0.0
    for q in range(len(x)):
        for u in range(len(x[q])):
            if math.isnan(m_unit[q][u]):
                continue
            for v in x[q][u]:
                if not _is_missing(v):
                    r_term = max(r_term, abs(v - m_unit[q][u]))
    v_term = 0.0
    for q in range(len(x)):
        if math.isnan(m_coupon[q]):
            continue
        for u in range(len(x[q])):
            if not math.isnan(m_unit[q][u]):
                v_term = max(v_term, abs(m_unit[q][u] - m_coupon[q]))
    c_term = 0.0
    if not math.isnan(m):
        for q in range(len(m_coupon)):
            if not math.isnan(m_coupon[q]):
                c_term = max(c_term, abs(m_coupon[q] - m))

    u95 = u_fixture_k2 + r_term + v_term + c_term
    guarded = m + u95 if not math.isnan(m) else math.nan
    return GuardResult(
        m=m,
        r_term=r_term,
        v_term=v_term,
        c_term=c_term,
        u_fixture_k2=u_fixture_k2,
        u95=u95,
        guarded=guarded,
        complete=complete,
    )


# --- Dataset model --------------------------------------------------------------
@dataclass
class CandidateData:
    name: str
    clock_hz: float
    # records[(q,u,r)] = {"snr_bin_db": [12], "snr_band_db": float,
    #                     "noise_bin_db_spl": [12], "noise_band_db_spl": float,
    #                     "resp_mag_db": [12], "resp_phase_deg": [12]}
    records: dict[tuple[int, int, int], dict[str, Any]] = field(default_factory=dict)
    valid_units: set[tuple[int, int]] = field(default_factory=set)
    installed_units: int = 0
    assembly_failures: int = 0
    sourceable: bool = True


def load_dataset(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "pdm-bakeoff-dataset/1":
        raise ValueError("dataset schema must be 'pdm-bakeoff-dataset/1'")
    return data


def parse_candidate(name: str, block: dict[str, Any]) -> CandidateData:
    cand = CandidateData(
        name=name,
        clock_hz=float(block["clock_hz"]),
        installed_units=int(block.get("installed_units", 0)),
        assembly_failures=int(block.get("assembly_failures", 0)),
        sourceable=bool(block.get("sourceable", True)),
    )
    for rec in block["records"]:
        key = (int(rec["coupon"]), int(rec["site"]), int(rec["reseat"]))
        cand.records[key] = rec
    for unit in block.get("valid_units", []):
        cand.valid_units.add((int(unit["coupon"]), int(unit["site"])))
    return cand


def _grid(
    records: dict[tuple[int, int, int], dict[str, Any]],
    field_name: str,
    index: int | None = None,
) -> list[list[list[float | None]]]:
    grid: list[list[list[float | None]]] = [
        [[None for _ in range(N_RESEATS)] for _ in range(N_SITES)]
        for _ in range(N_COUPONS)
    ]
    for (q, u, r), rec in records.items():
        if not (1 <= q <= N_COUPONS and 1 <= u <= N_SITES and 1 <= r <= N_RESEATS):
            raise ValueError(f"record index {(q, u, r)} out of range")
        value = rec[field_name]
        if index is not None:
            value = value[index]
        grid[q - 1][u - 1][r - 1] = None if value is None else float(value)
    return grid


# --- T-001 link gate -------------------------------------------------------------
def t001_link_gate(n_screen_bin_db_spl: list[float]) -> dict[str, float | bool]:
    """Rerun T-001's fixed reference case with the guarded N_screen curve.

    Uses analysis/link_budget.py's own reference-scenario defaults
    (20 deg C, 50% RH, 101.325 kPa, 30 dB SPL ambient, 10.8 Vrms wideband
    piezo, 12 kHz bandwidth, 6.6 ms chirp, person target) so the result is
    directly comparable with T-001's 27.09 dB / 20.18 m reference. The ambient
    term is added by the T-001 model exactly once, per the ticket.
    """
    sys.path.insert(0, str(REPO_ROOT / "analysis"))
    import link_budget as lb

    centers_hz = [1e3 * (lo + hi) / 2.0 for lo, hi in DECISION_BIN_EDGES_KHZ]
    curve = lb.AcousticNoiseCurve(
        name="T-016 N_screen",
        frequencies_hz=tuple(centers_hz),
        levels_db_spl=tuple(float(v) for v in n_screen_bin_db_spl),
        reference_bandwidth_hz=1_000.0,
        uncertainty_db=0.0,  # guard band already carried in N_screen itself
        basis="T-016 guarded screen curve (m + U95 per 1 kHz decision bin)",
    )
    frequency_hz = lb.DEFAULT_CENTER_FREQUENCY_HZ
    absorption = float(lb.atmospheric_absorption_db_per_m(frequency_hz, 20.0, 50.0))
    noise = float(
        lb.total_noise_db_spl(
            frequency_hz,
            curve,
            lb.DEFAULT_AMBIENT_NOISE_DB_SPL,
            lb.DEFAULT_BANDWIDTH_HZ,
        )
    )
    processing_gain = lb._processing_gain_db(
        lb.DEFAULT_BANDWIDTH_HZ, lb.DEFAULT_CHIRP_DURATION_S
    )
    source_level = float(
        lb.WIDEBAND_PIEZO_TARGET.source_level_db_spl(
            frequency_hz, lb.DEFAULT_DRIVE_V_RMS
        )
    )
    margin_10m = float(
        lb.sonar_margin_db(
            10.0,
            source_level,
            lb.TARGET_STRENGTH_DB["person"],
            absorption,
            noise,
            processing_gain,
        )
    )
    max_range = lb.max_detectable_range_m(
        source_level,
        lb.TARGET_STRENGTH_DB["person"],
        absorption,
        noise,
        processing_gain,
    )
    small_margin_10m = float(
        lb.sonar_margin_db(
            10.0,
            source_level,
            lb.TARGET_STRENGTH_DB["small object"],
            absorption,
            noise,
            processing_gain,
        )
    )
    return {
        "margin_10m_db": margin_10m,
        "range_25khz_m": max_range,
        "small_target_margin_10m_db": small_margin_10m,
        "total_noise_25khz_db_spl": noise,
        "pass": (
            margin_10m >= T001_MARGIN_10M_MIN_DB
            and max_range >= T001_RANGE_25KHZ_MIN_M
            and small_margin_10m >= T001_SMALL_TARGET_MIN_DB
        ),
    }


# --- Gates ------------------------------------------------------------------------
@dataclass
class Gate:
    name: str
    status: str  # "pass" | "fail" | "unverified" | "inconclusive"
    detail: str
    hard: bool = True


def _fixture_block(dataset: dict[str, Any]) -> dict[str, Any]:
    return dataset["fixture"]


def fixture_validity(dataset: dict[str, Any]) -> Gate:
    fx = _fixture_block(dataset)
    drift_mag = abs(float(fx["reference_drift"]["magnitude_db"]))
    drift_phase = abs(float(fx["reference_drift"]["phase_deg"]))
    problems = []
    if drift_mag > DRIFT_MAX_DB:
        problems.append(f"reference drift {drift_mag:.3f} dB > {DRIFT_MAX_DB} dB")
    if drift_phase > DRIFT_MAX_DEG:
        problems.append(f"reference drift {drift_phase:.2f} deg > {DRIFT_MAX_DEG} deg")
    for key, terms in fx["u_fixture_k2_db"].items():
        values = terms if isinstance(terms, list) else [terms]
        for i, v in enumerate(values):
            if float(v) > U_FIXTURE_K2_MAX_DB:
                problems.append(f"U_fixture_k2[{key}][{i}]={float(v):.3f} > 1.0 dB")
    if problems:
        return Gate("fixture-validity", "fail", "; ".join(problems))
    return Gate(
        "fixture-validity",
        "pass",
        f"drift {drift_mag:.3f} dB / {drift_phase:.2f} deg; all U_fixture_k2 <= 1.0 dB",
    )


def population_gate(cand: CandidateData) -> Gate:
    coupons = {q for q, _ in cand.valid_units}
    n = len(cand.valid_units)
    if n >= MIN_VALID_UNITS and len(coupons) >= N_COUPONS:
        for q, u in sorted(cand.valid_units):
            for r in range(1, N_RESEATS + 1):
                if (q, u, r) not in cand.records:
                    return Gate(
                        f"population/{cand.name}",
                        "inconclusive",
                        f"unit (coupon {q}, site {u}) missing reseat {r}",
                    )
        return Gate(
            f"population/{cand.name}",
            "pass",
            f"{n} valid units across {len(coupons)} coupons; "
            f"{cand.installed_units} installed, {cand.assembly_failures} assembly failures",
        )
    return Gate(
        f"population/{cand.name}",
        "inconclusive",
        f"only {n} valid units across {len(coupons)} coupons "
        f"(need {MIN_VALID_UNITS} across {N_COUPONS}); inconclusive unless Joshua "
        "ratifies a documented D011 waiver",
    )


def noise_screen_gate(
    cand: CandidateData, dataset: dict[str, Any]
) -> tuple[Gate, dict[str, Any]]:
    fx = _fixture_block(dataset)["u_fixture_k2_db"]
    per_bin = []
    for b in range(len(DECISION_BIN_EDGES_KHZ)):
        grid = _grid(cand.records, "noise_bin_db_spl", b)
        g = hierarchical_guard(grid, float(fx["noise_bin"][b]))
        per_bin.append(g)
    n_screen = [g.guarded for g in per_bin]
    band_grid = _grid(cand.records, "noise_band_db_spl")
    band_guard = hierarchical_guard(band_grid, float(fx["noise_band"]))
    link = t001_link_gate(n_screen)
    ok = all(g.complete for g in per_bin) and band_guard.complete and bool(link["pass"])
    detail = {
        "n_screen_bin_db_spl": n_screen,
        "per_bin": [vars(g) for g in per_bin],
        "band": vars(band_guard),
        "t001_link": link,
    }
    return (
        Gate(
            f"noise-screen/{cand.name}",
            "pass" if ok else "fail",
            f"margin@10m={link['margin_10m_db']:.2f} dB (>= {T001_MARGIN_10M_MIN_DB}), "
            f"range={link['range_25khz_m']:.2f} m (>= {T001_RANGE_25KHZ_MIN_M}), "
            f"small-target={link['small_target_margin_10m_db']:.2f} dB "
            f"(>= {T001_SMALL_TARGET_MIN_DB})",
        ),
        detail,
    )


def spread_gates(cand: CandidateData, dataset: dict[str, Any]) -> list[Gate]:
    gates: list[Gate] = []
    fx = _fixture_block(dataset)["u_fixture_k2_db"]
    # Gain normalization: one scalar per unit is applied by the bench pipeline and
    # stored in the record; analysis consumes the normalized three-reseat median.
    unit_band: dict[tuple[int, int], float] = {}
    for q, u in sorted(cand.valid_units):
        vals = [
            float(cand.records[(q, u, r)]["snr_band_db"])
            for r in range(1, N_RESEATS + 1)
            if (q, u, r) in cand.records
        ]
        if vals:
            unit_band[(q, u)] = statistics.median(vals)
    if unit_band:
        spread = max(unit_band.values()) - min(unit_band.values())
        gates.append(
            Gate(
                f"spread-band/{cand.name}",
                "pass" if spread <= SPREAD_MAX_DB else "fail",
                f"max-min band-integrated spread {spread:.3f} dB (<= {SPREAD_MAX_DB} dB)",
            )
        )
    bin_grid_median: dict[int, GuardResult] = {}
    for b in range(len(DECISION_BIN_EDGES_KHZ)):
        g = hierarchical_guard(
            _grid(cand.records, "snr_bin_db", b), float(fx["snr_bin"][b])
        )
        bin_grid_median[b] = g
    worst = 0.0
    worst_desc = ""
    for (q, u), _ in unit_band.items():
        for b in range(len(DECISION_BIN_EDGES_KHZ)):
            vals = [
                float(cand.records[(q, u, r)]["snr_bin_db"][b])
                for r in range(1, N_RESEATS + 1)
                if (q, u, r) in cand.records
            ]
            if not vals:
                continue
            deficit = bin_grid_median[b].m - statistics.median(vals)
            if deficit > worst:
                worst = deficit
                worst_desc = f"unit (q{q},u{u}) bin {b}: {deficit:.3f} dB below median"
    gates.append(
        Gate(
            f"spread-bin/{cand.name}",
            "pass" if worst <= BIN_OUTLIER_MAX_DB else "fail",
            f"worst unit/bin deficit {worst:.3f} dB (<= {BIN_OUTLIER_MAX_DB} dB); {worst_desc}",
        )
    )
    # Reseat repeatability on complex response after gain normalization.
    worst_rms_mag = worst_rms_phase = worst_bin_mag = worst_bin_phase = 0.0
    for q, u in sorted(cand.valid_units):
        mags, phases = [], []
        for r in range(1, N_RESEATS + 1):
            rec = cand.records.get((q, u, r))
            if rec is None:
                continue
            mags.append([float(v) for v in rec["resp_mag_db"]])
            phases.append([float(v) for v in rec["resp_phase_deg"]])
        if len(mags) < 2:
            continue
        med_mag = [statistics.median(col) for col in zip(*mags)]
        med_phase = [statistics.median(col) for col in zip(*phases)]
        for m_row, p_row in zip(mags, phases):
            dm = [a - b for a, b in zip(m_row, med_mag)]
            dp = [a - b for a, b in zip(p_row, med_phase)]
            rms_m = math.sqrt(sum(v * v for v in dm) / len(dm))
            rms_p = math.sqrt(sum(v * v for v in dp) / len(dp))
            worst_rms_mag = max(worst_rms_mag, rms_m)
            worst_rms_phase = max(worst_rms_phase, rms_p)
            worst_bin_mag = max(worst_bin_mag, max(abs(v) for v in dm))
            worst_bin_phase = max(worst_bin_phase, max(abs(v) for v in dp))
    ok = (
        worst_rms_mag <= RESEAT_RMS_MAG_MAX_DB
        and worst_rms_phase <= RESEAT_RMS_PHASE_MAX_DEG
        and worst_bin_mag <= RESEAT_BIN_MAG_MAX_DB
        and worst_bin_phase <= RESEAT_BIN_PHASE_MAX_DEG
    )
    gates.append(
        Gate(
            f"reseat-repeatability/{cand.name}",
            "pass" if ok else "fail",
            f"worst reseat RMS {worst_rms_mag:.3f} dB / {worst_rms_phase:.2f} deg; "
            f"worst bin {worst_bin_mag:.3f} dB / {worst_bin_phase:.2f} deg",
        )
    )
    return gates


def relative_spread_gate(
    spread_by_candidate: dict[str, float],
) -> Gate:
    if len(spread_by_candidate) < 2:
        return Gate("relative-spread", "inconclusive", "need both candidates")
    diff = abs(spread_by_candidate[SPH] - spread_by_candidate[ICS])
    return Gate(
        "relative-spread",
        "pass" if diff <= REL_SPREAD_MAX_DB else "fail",
        f"|spread_SPH - spread_ICS| = {diff:.3f} dB (<= {REL_SPREAD_MAX_DB} dB)",
    )


def paired_loss_gate(
    sph: CandidateData, ics: CandidateData, dataset: dict[str, Any]
) -> tuple[Gate, dict[str, Any]]:
    """Predeclared (q,u,r) identity pairing: d = SNR_ICS - SNR_SPH, positive = SPH worse."""
    fx = _fixture_block(dataset)["u_fixture_k2_db"]
    d_bin: list[list[list[list[float | None]]]] = [
        [
            [[None for _ in range(N_RESEATS)] for _ in range(N_SITES)]
            for _ in range(N_COUPONS)
        ]
        for _ in range(len(DECISION_BIN_EDGES_KHZ))
    ]
    d_band: list[list[list[float | None]]] = [
        [[None for _ in range(N_RESEATS)] for _ in range(N_SITES)]
        for _ in range(N_COUPONS)
    ]
    incomplete = []
    for q in range(1, N_COUPONS + 1):
        for u in range(1, N_SITES + 1):
            for r in range(1, N_RESEATS + 1):
                rs, ri = sph.records.get((q, u, r)), ics.records.get((q, u, r))
                if rs is None or ri is None:
                    incomplete.append((q, u, r))
                    continue
                for b in range(len(DECISION_BIN_EDGES_KHZ)):
                    d_bin[b][q - 1][u - 1][r - 1] = float(ri["snr_bin_db"][b]) - float(
                        rs["snr_bin_db"][b]
                    )
                d_band[q - 1][u - 1][r - 1] = float(ri["snr_band_db"]) - float(
                    rs["snr_band_db"]
                )
    bin_results = [
        hierarchical_guard(d_bin[b], float(fx["loss_bin"][b]))
        for b in range(len(DECISION_BIN_EDGES_KHZ))
    ]
    band_result = hierarchical_guard(d_band, float(fx["loss_band"]))
    hole_fail = [b for b, g in enumerate(bin_results) if g.guarded > HARD_LOSS_DB]
    detail = {
        "paired_loss_band": vars(band_result),
        "paired_loss_bins": [vars(g) for g in bin_results],
        "incomplete_blocks": incomplete,
        "spectral_hole_bins": hole_fail,
    }
    if incomplete:
        return Gate(
            "paired-loss",
            "inconclusive",
            f"{len(incomplete)} incomplete paired blocks, e.g. {incomplete[:3]}",
        ), detail
    ok_band = band_result.guarded <= HARD_LOSS_DB
    ok = ok_band and not hole_fail
    return Gate(
        "paired-loss",
        "pass" if ok else "fail",
        f"L_band+U95={band_result.guarded:.3f} dB (hard limit {HARD_LOSS_DB} dB, "
        f"tie {TIE_LOSS_DB} dB); spectral-hole failures in bins {hole_fail}",
    ), detail


def electrical_gate(cand: CandidateData, dataset: dict[str, Any]) -> Gate:
    e = dataset["electrical"][cand.name]
    problems = []
    if not e["all_units_started"]:
        problems.append("not all 12 units started/entered ultrasonic mode")
    if not e["both_select_polarities"]:
        problems.append("SELECT polarity coverage incomplete")
    if int(e["startup_cycles"]) < 10 or not e["startup_cycles_clean"]:
        problems.append("startup/mode-switch cycles show contention or stuck channel")
    if e.get("data_pulls_present", False):
        problems.append("DATA pull present (prohibited)")
    limits = (
        SPH_ELECTRICAL_LIMITS
        if cand.name == SPH
        else {k: tuple(v) for k, v in e["datasheet_limits"].items()}
    )
    for key, (lo, hi) in limits.items():
        m = e["measurements"][key]
        value, unc = float(m["value"]), abs(float(m["uncertainty"]))
        if lo is not None and value - unc < lo:
            problems.append(f"{key}: {value}+/-{unc} below limit {lo}")
        if hi is not None and value + unc > hi:
            problems.append(f"{key}: {value}+/-{unc} above limit {hi}")
    if problems:
        return Gate(f"electrical/{cand.name}", "fail", "; ".join(problems))
    return Gate(
        f"electrical/{cand.name}", "pass", "all readings plus uncertainty inside limits"
    )


def power_gate(cand: CandidateData, dataset: dict[str, Any]) -> Gate:
    p = dataset["power"][cand.name]
    steady = float(p["extrapolated_24mic_steady_ma"])
    peak = float(p["observed_peak_ma"])
    ok = steady <= RAIL_STEADY_EST_MAX_MA and peak < RAIL_ALLOC_MA
    return Gate(
        f"power/{cand.name}",
        "pass" if ok else "fail",
        f"24-mic steady estimate {steady:.1f} mA (<= {RAIL_STEADY_EST_MAX_MA}), "
        f"observed peak {peak:.1f} mA (< {RAIL_ALLOC_MA}); characterization only, "
        "not a manufacturer maximum",
    )


def port_gate(cand: CandidateData, dataset: dict[str, Any]) -> Gate:
    p = dataset["ports"][cand.name]
    inspected = int(p["holes_inspected"])
    passed = int(p["holes_pass"])
    ok = inspected >= MIN_VALID_UNITS and passed == inspected
    return Gate(
        f"ports/{cand.name}",
        "pass" if ok else "fail",
        f"{passed}/{inspected} ports pass (0.50 mm NPTH, free of copper/mask/paste/"
        f"debris, no aperture clipping); max package-to-hole offset "
        f"{float(p['max_offset_mm']):.3f} mm recorded (no SPH tolerance inferred)",
    )


def overload_gate(cand: CandidateData, dataset: dict[str, Any]) -> Gate:
    o = dataset["overload"][cand.name]
    fixture_max = float(o["fixture_max_spl_db"])
    if fixture_max < AOP_MIN_DB_SPL:
        return Gate(
            f"overload/{cand.name}",
            "unverified",
            f"fixture reaches only {fixture_max:.1f} dB SPL < {AOP_MIN_DB_SPL}; "
            "mark unverified, not pass",
            hard=False,
        )
    thd10 = float(o["thd10_db_spl"])
    recovery = float(o["recovery_s"])
    problems = []
    if thd10 < AOP_MIN_DB_SPL:
        problems.append(f"10%-THD point {thd10:.1f} < {AOP_MIN_DB_SPL} dB SPL")
    if recovery > RECOVERY_REVIEW_S:
        problems.append(f"recovery {recovery * 1e6:.0f} us > 1 ms")
    elif recovery > RECOVERY_PASS_S:
        problems.append(
            f"recovery {recovery * 1e6:.0f} us in 250 us-1 ms: needs T-001 1 ms "
            "guard + conditional human review"
        )
    if problems:
        status = (
            "fail" if recovery > RECOVERY_REVIEW_S or thd10 < AOP_MIN_DB_SPL else "pass"
        )
        g = Gate(f"overload/{cand.name}", status, "; ".join(problems))
        g.detail += " [conditional review]" if status == "pass" else ""
        return g
    return Gate(
        f"overload/{cand.name}",
        "pass",
        f"10%-THD {thd10:.1f} dB SPL (>= {AOP_MIN_DB_SPL}), recovery "
        f"{recovery * 1e6:.0f} us (<= 250 us)",
    )


def overload_relative_gate(
    sph: CandidateData, ics: CandidateData, dataset: dict[str, Any]
) -> Gate:
    oa, ob = dataset["overload"][SPH], dataset["overload"][ICS]
    if (
        float(oa["fixture_max_spl_db"]) < AOP_MIN_DB_SPL
        or float(ob["fixture_max_spl_db"]) < AOP_MIN_DB_SPL
    ):
        return Gate(
            "overload-relative",
            "unverified",
            "fixture cannot reach 117 dB SPL",
            hard=False,
        )
    delta = float(oa["thd10_db_spl"]) - float(ob["thd10_db_spl"])  # SPH - ICS
    ok = delta >= -AOP_REL_MAX_DB
    return Gate(
        "overload-relative",
        "pass" if ok else "fail",
        f"SPH 10%-THD is {-delta:.1f} dB below ICS (allowed <= {AOP_REL_MAX_DB} dB)",
    )


# --- Selection rule (ticket "Explicit selection rule", branches 1-5) --------------
def selection_rule(report: dict[str, Any]) -> tuple[str, str]:
    gates = {g.name: g for g in report["gates"]}
    fixture = gates["fixture-validity"]
    if fixture.status != "pass":
        return (
            "fixture-invalid",
            "Fixture/calibration invalid: comparison is fixture-invalid, not a "
            "microphone failure. Repair the fixture and re-run before any release.",
        )
    pop = {c: gates[f"population/{c}"].status for c in CANDIDATES}
    if any(v != "pass" for v in pop.values()):
        return (
            "inconclusive",
            "Fewer than 12 valid units or missing reseats for at least one MPN; "
            "inconclusive unless Joshua ratifies a documented D011 waiver.",
        )
    if not (
        report["candidates"][SPH]["sourceable"]
        and report["candidates"][ICS]["sourceable"]
    ):
        return (
            "inconclusive",
            "Only one exact MPN is sourceable/testable; inconclusive under D011 "
            "(rule 4). Joshua must ratify a documented waiver before any release.",
        )

    def hard_pass(c: str) -> bool:
        return all(
            g.status == "pass"
            for g in report["gates"]
            if g.name.endswith(f"/{c}") and g.hard
        )

    sph_ok, ics_ok = hard_pass(SPH), hard_pass(ICS)
    guarded_band = report["paired_loss_detail"]["paired_loss_band"]["guarded"]

    if sph_ok and not ics_ok:
        return (
            "release-sph",
            "Rule 1: SPH passes every hard gate and ICS fails a hard gate in an "
            "otherwise valid, complete comparison. Release SPH0641LU4H-1; record "
            "the ICS failure in the release record.",
        )
    if sph_ok and ics_ok:
        if guarded_band <= TIE_LOSS_DB:
            return (
                "release-sph",
                f"Rule 2: both pass and L_band+U95_loss_band={guarded_band:.3f} dB "
                f"<= {TIE_LOSS_DB} dB; lifecycle breaks the non-material acoustic "
                "tie. Release SPH0641LU4H-1.",
            )
        if guarded_band <= HARD_LOSS_DB:
            return (
                "joshua-component-choice",
                f"Rule 2: both pass but {TIE_LOSS_DB} < L_band+U95_loss_band="
                f"{guarded_band:.3f} <= {HARD_LOSS_DB} dB; no auto-select. Joshua "
                "makes an explicit component-choice decision.",
            )
        return (
            "prepare-ics-decision",
            f"Rule 3: both pass but L_band+U95_loss_band={guarded_band:.3f} > "
            f"{HARD_LOSS_DB} dB; prepare a component-choice decision exposing "
            "ICS NRND/orderability risk. Do not silently substitute ICS.",
        )
    if not sph_ok and ics_ok:
        return (
            "prepare-ics-decision",
            "Rule 3: SPH fails and ICS passes; prepare a component-choice decision "
            "exposing ICS NRND/orderability risk. Do not silently substitute ICS "
            "or change the 3.072 MHz capture contract.",
        )
    return (
        "freeze-neither",
        "Rule 5: neither candidate passes; freeze neither footprint/BOM. Reopen "
        "the D011 candidate set via a proposed decision; T-010 stays blocked.",
    )


# --- Report -----------------------------------------------------------------------
def analyze(dataset: dict[str, Any]) -> dict[str, Any]:
    digest = check_normative_identity()
    report: dict[str, Any] = {
        "normative_block_sha256": digest,
        "gates": [],
        "candidates": {},
        "details": {},
    }
    fx_gate = fixture_validity(dataset)
    report["gates"].append(fx_gate)

    cands: dict[str, CandidateData] = {}
    spreads: dict[str, float] = {}
    for name in CANDIDATES:
        if name not in dataset["candidates"]:
            continue
        cand = parse_candidate(name, dataset["candidates"][name])
        cands[name] = cand
        report["candidates"][name] = {
            "clock_hz": cand.clock_hz,
            "sourceable": cand.sourceable,
            "valid_units": len(cand.valid_units),
        }
        report["gates"].append(population_gate(cand))
        if fx_gate.status == "pass" and report["gates"][-1].status == "pass":
            noise_gate, noise_detail = noise_screen_gate(cand, dataset)
            report["gates"].append(noise_gate)
            report["details"][f"noise/{name}"] = noise_detail
            sg = spread_gates(cand, dataset)
            report["gates"].extend(sg)
            spreads[name] = max(
                (
                    float(g.detail.split("spread ")[1].split(" dB")[0])
                    for g in sg
                    if g.name.startswith("spread-band/")
                ),
                default=math.nan,
            )
            for gfun in (electrical_gate, power_gate, port_gate, overload_gate):
                report["gates"].append(gfun(cand, dataset))

    if len(cands) == 2 and fx_gate.status == "pass":
        report["gates"].append(relative_spread_gate(spreads))
        paired_gate, paired_detail = paired_loss_gate(cands[SPH], cands[ICS], dataset)
        report["gates"].append(paired_gate)
        report["paired_loss_detail"] = paired_detail
        report["gates"].append(overload_relative_gate(cands[SPH], cands[ICS], dataset))

    if "paired_loss_detail" not in report:
        report["paired_loss_detail"] = {"paired_loss_band": {"guarded": math.nan}}
    outcome, rationale = selection_rule(report)
    report["selection"] = {"outcome": outcome, "rationale": rationale}
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# T-016 bake-off release analysis report",
        "",
        f"Normative estimator block sha256: `{report['normative_block_sha256']}`",
        "",
        "## Gates",
        "",
        "| Gate | Status | Detail |",
        "|---|---|---|",
    ]
    for g in report["gates"]:
        lines.append(f"| {g.name} | **{g.status}** | {g.detail} |")
    lines += [
        "",
        "## Selection",
        "",
        f"**{report['selection']['outcome']}** — {report['selection']['rationale']}",
        "",
    ]
    return "\n".join(lines)


# --- Synthetic self-tests -----------------------------------------------------------
def _synth_records(
    snr_bin: float, noise_bin: float, *, spread: float = 0.0, jitter: float = 0.1
) -> dict[tuple[int, int, int], dict[str, Any]]:
    """Deterministic 3x4x3 record grid; no RNG so results are reproducible."""
    records: dict[tuple[int, int, int], dict[str, Any]] = {}
    for q in range(1, N_COUPONS + 1):
        for u in range(1, N_SITES + 1):
            for r in range(1, N_RESEATS + 1):
                unit_off = spread * ((u - 2.5) / 1.5) + 0.2 * (q - 2)
                reseat_off = jitter * (r - 2)
                snr_b = [
                    snr_bin + unit_off + reseat_off + 0.05 * (b - 5.5)
                    for b in range(12)
                ]
                noise_b = [
                    noise_bin - unit_off - reseat_off + 0.1 * (b - 5.5)
                    for b in range(12)
                ]
                # Integrated-band values from linear-power sums (per the estimator).
                snr_band = (
                    10.0 * math.log10(sum(10.0 ** (v / 10.0) for v in snr_b) / 1.0)
                    - 10.0 * math.log10(12.0) * 0
                )  # bins are SNRs; band is power-sum ratio
                noise_band = 10.0 * math.log10(
                    sum(10.0 ** (v / 10.0) for v in noise_b)
                ) + 10.0 * math.log10(1.0)  # 12 x 1 kHz bins integrated
                records[(q, u, r)] = {
                    "coupon": q,
                    "site": u,
                    "reseat": r,
                    "snr_bin_db": snr_b,
                    "snr_band_db": snr_band,
                    "noise_bin_db_spl": noise_b,
                    "noise_band_db_spl": noise_band,
                    "resp_mag_db": [unit_off + reseat_off] * 12,
                    "resp_phase_deg": [2.0 * unit_off + reseat_off] * 12,
                }
    return records


def _synth_dataset(
    *,
    sph_noise: float = 19.5,
    ics_noise: float = 19.0,
    ics_snr_advantage: float = 1.0,
    sph_snr: float = 45.0,
    sph_valid: bool = True,
    ics_valid: bool = True,
    sph_sourceable: bool = True,
    ics_sourceable: bool = True,
    u_fixture: float = 0.6,
    drift_db: float = 0.2,
    drift_deg: float = 2.0,
    sph_electrical_ok: bool = True,
    ics_electrical_ok: bool = True,
    sph_steady_ma: float = 55.0,
    ics_steady_ma: float = 40.0,
    sph_ports_ok: bool = True,
    ics_ports_ok: bool = True,
    fixture_max_spl: float = 120.0,
    sph_thd10: float = 118.5,
    ics_thd10: float = 119.0,
    recovery_s: float = 150e-6,
) -> dict[str, Any]:
    def cand_block(
        name: str, clock: float, noise: float, snr: float, valid: bool, sourceable: bool
    ) -> dict[str, Any]:
        records = _synth_records(snr, noise)
        units = [
            {"coupon": q, "site": u}
            for q in range(1, N_COUPONS + 1)
            for u in range(1, N_SITES + 1)
        ]
        if not valid:
            records = {
                k: v for k, v in records.items() if not (k[0] == 3 and k[1] == 4)
            }
            units = units[:-1]
        return {
            "clock_hz": clock,
            "installed_units": 12,
            "assembly_failures": 0,
            "sourceable": sourceable,
            "valid_units": units,
            "records": list(records.values()),
        }

    sph_meas = {
        "duty_pct": {"value": 50.2, "uncertainty": 0.2},
        "rise_ns": {"value": 2.0, "uncertainty": 0.3},
        "fall_ns": {"value": 2.1, "uncertainty": 0.3},
        "tdd_ns": {"value": 30.0, "uncertainty": 2.0},
        "tdz_ns": {"value": 8.0, "uncertainty": 1.0},
        "skew_ns": {"value": 0.30, "uncertainty": 0.05},
    }
    if not sph_electrical_ok:
        sph_meas["tdd_ns"] = {"value": 44.0, "uncertainty": 2.0}
    ics_meas = {
        "enable_ns": {"value": 40.0, "uncertainty": 3.0},
        "disable_ns": {"value": 20.0, "uncertainty": 3.0},
        "skew_ns": {"value": 0.30, "uncertainty": 0.05},
    }
    if not ics_electrical_ok:
        ics_meas["enable_ns"] = {"value": 60.0, "uncertainty": 3.0}
    return {
        "schema": "pdm-bakeoff-dataset/1",
        "fixture": {
            "u_fixture_k2_db": {
                "noise_bin": [u_fixture] * 12,
                "noise_band": u_fixture,
                "snr_bin": [u_fixture] * 12,
                "loss_bin": [u_fixture] * 12,
                "loss_band": u_fixture,
            },
            "reference_drift": {"magnitude_db": drift_db, "phase_deg": drift_deg},
            "calibration_provenance": "synthetic self-test fixture",
        },
        "candidates": {
            SPH: cand_block(
                SPH, 3_072_000, sph_noise, sph_snr, sph_valid, sph_sourceable
            ),
            ICS: cand_block(
                ICS,
                4_800_000,
                ics_noise,
                sph_snr + ics_snr_advantage,
                ics_valid,
                ics_sourceable,
            ),
        },
        "electrical": {
            SPH: {
                "all_units_started": sph_electrical_ok,
                "both_select_polarities": True,
                "startup_cycles": 10,
                "startup_cycles_clean": sph_electrical_ok,
                "data_pulls_present": False,
                "measurements": sph_meas,
            },
            ICS: {
                "all_units_started": ics_electrical_ok,
                "both_select_polarities": True,
                "startup_cycles": 10,
                "startup_cycles_clean": ics_electrical_ok,
                "data_pulls_present": False,
                "datasheet_limits": {
                    "enable_ns": [None, 50.0],
                    "disable_ns": [5.0, 40.0],
                    "skew_ns": [None, BOARD_SKEW_MAX_NS],
                },
                "measurements": ics_meas,
            },
        },
        "power": {
            SPH: {
                "extrapolated_24mic_steady_ma": sph_steady_ma,
                "observed_peak_ma": 70.0,
            },
            ICS: {
                "extrapolated_24mic_steady_ma": ics_steady_ma,
                "observed_peak_ma": 55.0,
            },
        },
        "ports": {
            SPH: {
                "holes_inspected": 12,
                "holes_pass": 12 if sph_ports_ok else 11,
                "max_offset_mm": 0.08,
            },
            ICS: {
                "holes_inspected": 12,
                "holes_pass": 12 if ics_ports_ok else 11,
                "max_offset_mm": 0.07,
            },
        },
        "overload": {
            SPH: {
                "fixture_max_spl_db": fixture_max_spl,
                "thd10_db_spl": sph_thd10,
                "recovery_s": recovery_s,
            },
            ICS: {
                "fixture_max_spl_db": fixture_max_spl,
                "thd10_db_spl": ics_thd10,
                "recovery_s": recovery_s,
            },
        },
    }


def _outcome(dataset: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    report = analyze(dataset)
    return report["selection"]["outcome"], report


def run_selftest() -> None:
    digest = check_normative_identity()
    print(f"normative estimator block sha256: {digest}")
    print("normative estimator blocks byte-identical: OK")

    # Worked estimator example, hand-computed:
    # x[q][u][r]: coupon q constant offset, unit offsets, reseat offsets.
    x = [
        [[10.0 + q + u * 0.5 + r * 0.1 for r in range(3)] for u in range(4)]
        for q in range(3)
    ]
    g = hierarchical_guard(x, 0.6)
    # m_unit[q][u] = 10+q+0.5u+0.1 ; m_coupon[q] = median_u = 10+q+0.85
    # m = median_q = 11.85 ; R = 0.1 ; V = |0.1? ... compute: unit offsets
    # u*0.5 around median 0.75 -> V = max |0.5u-0.75| = 0.75 ; C = 1.0
    assert abs(g.m - 11.85) < 1e-9, g.m
    assert abs(g.r_term - 0.1) < 1e-9
    assert abs(g.v_term - 0.75) < 1e-9
    assert abs(g.c_term - 1.0) < 1e-9
    assert abs(g.u95 - (0.6 + 0.1 + 0.75 + 1.0)) < 1e-9
    assert g.complete
    print("estimator worked example (m=11.85, R=0.1, V=0.75, C=1.0, U95=2.45): OK")

    try:
        hierarchical_guard(x, 1.2)
        raise AssertionError("U_fixture_k2 > 1.0 dB must raise")
    except ValueError:
        print("U_fixture_k2 > 1.0 dB raises fixture-invalid: OK")

    # T-001 wiring check: reproduce the reference case through the link gate.
    sys.path.insert(0, str(REPO_ROOT / "analysis"))
    import link_budget as lb

    ref = t001_link_gate(
        [
            float(lb.OPTION_C_PDM.self_noise_db_spl(1e3 * (lo + hi) / 2.0, 1_000.0))
            for lo, hi in DECISION_BIN_EDGES_KHZ
        ]
    )
    assert abs(ref["margin_10m_db"] - 27.09) < 0.05, ref
    assert abs(ref["range_25khz_m"] - 20.18) < 0.05, ref
    assert abs(ref["small_target_margin_10m_db"] - 7.1) < 0.05, ref
    print(
        f"T-001 reference wiring: margin={ref['margin_10m_db']:.2f} dB, "
        f"range={ref['range_25khz_m']:.2f} m, small={ref['small_target_margin_10m_db']:.2f} dB: OK"
    )

    # Selection branches 1-5 plus inconclusive/fixture-invalid.
    o, _ = _outcome(_synth_dataset(ics_electrical_ok=False))
    assert o == "release-sph", o
    print("branch 1 (SPH pass, ICS hard fail -> release SPH): OK")

    o, _ = _outcome(_synth_dataset(ics_snr_advantage=1.0))
    assert o == "release-sph", o
    print("branch 2 tie (L+U95 <= 3 dB -> release SPH): OK")

    o, _ = _outcome(_synth_dataset(ics_snr_advantage=4.5))
    assert o == "joshua-component-choice", o
    print("branch 2b (3 < L+U95 <= 6 dB -> Joshua component choice): OK")

    o, _ = _outcome(_synth_dataset(ics_snr_advantage=7.0))
    assert o == "prepare-ics-decision", o
    print("branch 3a (both pass, L+U95 > 6 dB -> ICS decision): OK")

    o, _ = _outcome(_synth_dataset(sph_electrical_ok=False))
    assert o == "prepare-ics-decision", o
    print("branch 3b (SPH fail, ICS pass -> ICS decision): OK")

    o, _ = _outcome(_synth_dataset(ics_sourceable=False))
    assert o == "inconclusive", o
    print("branch 4 (one MPN unsourceable -> inconclusive/waiver): OK")

    o, _ = _outcome(_synth_dataset(sph_electrical_ok=False, ics_electrical_ok=False))
    assert o == "freeze-neither", o
    print("branch 5 (both fail -> freeze neither): OK")

    o, _ = _outcome(_synth_dataset(u_fixture=1.4))
    assert o == "fixture-invalid", o
    print("fixture-invalid (U_fixture_k2 > 1.0 dB): OK")

    o, _ = _outcome(_synth_dataset(drift_db=0.7))
    assert o == "fixture-invalid", o
    print("fixture-invalid (reference drift > 0.5 dB): OK")

    o, _ = _outcome(_synth_dataset(sph_valid=False))
    assert o == "inconclusive", o
    print("incomplete population -> inconclusive: OK")

    # Individual gate checks.
    _, rep = _outcome(_synth_dataset(sph_steady_ma=90.0))
    g = next(g for g in rep["gates"] if g.name == f"power/{SPH}")
    assert g.status == "fail", g
    print("power gate fails 90 mA steady estimate (> 80 mA): OK")

    _, rep = _outcome(_synth_dataset(fixture_max_spl=112.0))
    g = next(g for g in rep["gates"] if g.name == f"overload/{SPH}")
    assert g.status == "unverified", g
    print("overload unverified below 117 dB SPL fixture capability: OK")

    _, rep = _outcome(_synth_dataset(sph_ports_ok=False))
    g = next(g for g in rep["gates"] if g.name == f"ports/{SPH}")
    assert g.status == "fail", g
    print("port gate fails on a bad drilled port: OK")

    # Noisy SPH that must fail the T-001 link gate.
    _, rep = _outcome(_synth_dataset(sph_noise=48.0))
    g = next(g for g in rep["gates"] if g.name == f"noise-screen/{SPH}")
    assert g.status == "fail", (g, rep["details"][f"noise/{SPH}"]["t001_link"])
    print("noise screen fails a +10 dB-noise SPH population via T-001 gate: OK")

    print("SELFTEST: all synthetic threshold and selection-branch checks passed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--report-md", type=Path)
    args = parser.parse_args()
    if args.selftest:
        run_selftest()
        return
    if not args.dataset:
        parser.error("provide --dataset or --selftest")
    dataset = load_dataset(args.dataset)
    report = analyze(dataset)
    printable = json.dumps(report, indent=2, default=lambda o: vars(o))
    if args.report_json:
        args.report_json.write_text(printable + "\n", encoding="utf-8")
    if args.report_md:
        args.report_md.write_text(render_markdown(report), encoding="utf-8")
    if not (args.report_json or args.report_md):
        print(printable)


if __name__ == "__main__":
    main()
