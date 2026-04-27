"""
FreeSSM CSV log analyzer — engine v2.

Pipeline:
    1. Parse FreeSSM CSV (cp1252 / `;` delimiter, prefix-based sensor headers).
    2. Classify each row into one of 8 engine phases (state machine).
    3. Compute per-phase statistics + RPM x Load maps.
    4. Detect events (knock, fuel trim drift, EVAP, misfire) — DFCO-aware.
    5. Run declarative diagnostic Checks (Tier 1 fuel system).
    6. Emit human-readable Markdown report and compact JSON summary.

Usage:
    python tools/log-analyzer/analyze.py logs/FreeSSM_log2.csv --fuel lpg

Design notes:
    - Stdlib-only (no pandas / numpy). Runs anywhere with Python 3.10+.
    - Checks live in a Python list of `Check` dataclasses (declarative-ish).
      A YAML/JSON loader can be bolted on later without changing the engine.
    - Phase classifier uses hysteresis-by-min-duration to suppress flicker.
    - DFCO is an explicit phase => downstream checks know to ignore lambda
      excursions and fuel-trim noise during fuel cut.

Sensor naming convention is the prefix-based scheme committed in
v1.3.0-ms.7 (e.g. `Fuel Trim - LTFT B1 [%]`). The KEY_SENSORS dict maps
logical names to header-substring patterns — single source of truth.

See `docs/analyzer_design_panel.md` for the full design rationale.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# ============================================================================
# Section 1 — Sensor mapping (prefix-based scheme, v1.3.0-ms.7+)
# ============================================================================

KEY_SENSORS: dict[str, list[str]] = {
    # logical_name : list of substrings ALL of which must appear (case-insensitive)
    # --- Core engine state ---
    "rpm":         ["engine", "speed [rpm]"],
    "load":        ["engine", "load [%]"],
    "vss":         ["vehicle speed"],
    "ect":         ["coolant temperature"],
    "oil_temp":    ["oil temperature"],
    "iat":         ["intake temperature"],
    # --- Air path ---
    "map":         ["manifold absolute pressure"],
    "map_rel":     ["manifold relative pressure"],
    "atm_p":       ["atmospheric pressure"],
    "maf_gs":      ["mass flow", "[g/s]"],
    "maf_v":       ["maf sensor voltage"],
    "tps":         ["throttle position"],
    "tps_main_v":  ["throttle sensor main voltage"],
    "tps_sub_v":   ["throttle sensor sub voltage"],
    "throttle_motor_duty": ["throttle motor duty"],
    "throttle_motor_v":    ["throttle motor voltage"],
    "pedal":       ["pedal position"],
    "pedal_main_v":["pedal sensor main voltage"],
    "pedal_sub_v": ["pedal sensor sub voltage"],
    # --- Ignition ---
    "ign_tim":     ["ignition", "timing [deg]"],
    "knock":       ["knock correction"],
    # --- Fuel system ---
    "ltft_b1":     ["ltft b1"],
    "ltft_b3":     ["ltft b3"],
    "stft_b1":     ["stft b1"],
    "stft_b3":     ["stft b3"],
    "lambda":      ["pre-cat", "lambda"],
    "o2_pre_i":    ["pre-cat", "current"],
    "o2_pre_r":    ["pre-cat", "resistance"],
    "o2_post":     ["post-cat voltage"],
    "fuel_tank_p": ["tank pressure (evap)"],
    "fuel_temp":   ["fuel", "temperature"],
    "fuel_level_v":["fuel", "level", "voltage"],
    "fuel_level_r":["fuel", "level", "resistance"],
    "cpc_duty":    ["cpc valve duty"],
    "inj_pulse":   ["injection pulse"],
    # --- VVT / variable cam ---
    "vvt_duty_l":  ["osv duty left"],
    "vvt_duty_r":  ["osv duty right"],
    "vvt_curr_l":  ["osv current left"],
    "vvt_curr_r":  ["osv current right"],
    # --- EGR ---
    "egr_steps":   ["egr", "steps"],
    # --- Electrical ---
    "battery":     ["battery voltage"],
}

# Boolean (switch) sensors we care about — used for phase detection / event flags.
KEY_SWITCHES: dict[str, list[str]] = {
    "idle_switch":   ["idle switch"],
    "brake_switch":  ["brake switch"],
    "clutch_switch": ["clutch switch"],
    "neutral":       ["neutral position"],
    "starter":       ["starter switch"],
    "ac_compressor": ["air conditioning compressor"],
    "ac_switch":     ["air conditioning switch"],
    "o2_post_rich":  ["rear o2 sensor rich signal"],
    "knock_signal":  ["knocking signal"],
    "oil_pressure_1":["engine oil pressure switch #1"],
    "fuel_pump":     ["fuel pump relay"],
    "radiator_fan_1":["radiator fan relay #1"],
    "pcv_solenoid":  ["pcv", "solenoid"],
    "vent_solenoid": ["ventilation solenoid"],
}


# ============================================================================
# Section 2 — CSV parsing
# ============================================================================

def _parse_float(s: str) -> float | None:
    if s is None:
        return None
    s = s.strip().replace(",", ".")
    if s == "" or s.lower() in ("nan", "n/a"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _is_bool_value(s: str) -> bool:
    return s.strip() in ("On", "Off", "ON", "OFF", "0", "1")


def _find_col(header: list[str], patterns: list[str]) -> int | None:
    for i, name in enumerate(header):
        low = name.lower()
        if all(p.lower() in low for p in patterns):
            return i
    return None


@dataclass
class ParsedLog:
    path: str
    header: list[str]
    time: list[float]
    numeric: dict[int, list[float | None]]
    boolean: dict[int, list[bool | None]]
    key_idx: dict[str, int | None] = field(default_factory=dict)
    switch_idx: dict[str, int | None] = field(default_factory=dict)
    rows: int = 0
    duration_s: float = 0.0

    def col(self, key: str) -> list[float | None] | None:
        idx = self.key_idx.get(key)
        if idx is None or idx not in self.numeric:
            return None
        return self.numeric[idx]

    def bool_col(self, key: str) -> list[bool | None] | None:
        idx = self.switch_idx.get(key)
        if idx is None or idx not in self.boolean:
            return None
        return self.boolean[idx]


def load_csv(path: Path) -> ParsedLog:
    raw = path.read_bytes()
    text = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "cp1250", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise RuntimeError("Cannot decode CSV with common encodings")

    reader = csv.reader(text.splitlines(), delimiter=";")
    rows = list(reader)
    if not rows:
        raise RuntimeError("Empty CSV")
    header = [h.strip() for h in rows[0]]
    body = rows[1:]

    sample = body[: min(50, len(body))]
    types: list[str] = []  # "num" | "bool" | "skip"
    for ci in range(len(header)):
        col_vals = [r[ci] if ci < len(r) else "" for r in sample]
        non_empty = [v for v in col_vals if v.strip() != ""]
        if not non_empty:
            types.append("skip")
            continue
        bool_count = sum(1 for v in non_empty if _is_bool_value(v))
        num_count = sum(1 for v in non_empty if _parse_float(v) is not None)
        if bool_count >= 0.8 * len(non_empty):
            types.append("bool")
        elif num_count >= 0.8 * len(non_empty):
            types.append("num")
        else:
            types.append("skip")

    time_col = 0
    time_vals: list[float] = []
    numeric: dict[int, list[float | None]] = {ci: [] for ci, t in enumerate(types) if t == "num"}
    boolean: dict[int, list[bool | None]] = {ci: [] for ci, t in enumerate(types) if t == "bool"}

    for r in body:
        if not r or len(r) < 2:
            continue
        t = _parse_float(r[time_col]) if time_col < len(r) else None
        if t is None:
            continue
        time_vals.append(t)
        for ci in numeric:
            numeric[ci].append(_parse_float(r[ci]) if ci < len(r) else None)
        for ci in boolean:
            raw_v = r[ci] if ci < len(r) else ""
            s = raw_v.strip().lower()
            if s in ("on", "1"):
                boolean[ci].append(True)
            elif s in ("off", "0"):
                boolean[ci].append(False)
            else:
                boolean[ci].append(None)

    log = ParsedLog(
        path=str(path),
        header=header,
        time=time_vals,
        numeric=numeric,
        boolean=boolean,
        rows=len(time_vals),
        duration_s=(time_vals[-1] - time_vals[0]) if time_vals else 0.0,
    )
    log.key_idx = {k: _find_col(header, pats) for k, pats in KEY_SENSORS.items()}
    log.switch_idx = {k: _find_col(header, pats) for k, pats in KEY_SWITCHES.items()}
    return log


# ============================================================================
# Section 3 — Phase classifier (8 phases, hysteresis-suppressed)
# ============================================================================

# Phase semantics (see docs/analyzer_design_panel.md):
#   COLD_START   ECT < 40 °C
#   WARMUP       40 <= ECT < 70 °C
#   IDLE         warm + RPM < 950 + load < 22 + vss < 3 + tps < 5
#   OVERRUN_DFCO warm + tps < 3 + rpm > 1300 + (vss > 5 OR load very low)
#                => ECU likely in DFCO; lambda/STFT meaningless here
#   CRUISE       warm + steady (load 15-45) + vss > 10
#   PART_LOAD    warm + load 30-75
#   WOT          warm + tps > 75 OR load > 80
#   TRANSITION   short bursts of load change |dload| > 12 (tip-in / tip-out)
PHASE_COLD_START   = "COLD_START"
PHASE_WARMUP       = "WARMUP"
PHASE_IDLE         = "IDLE"
PHASE_OVERRUN_DFCO = "OVERRUN_DFCO"
PHASE_CRUISE       = "CRUISE"
PHASE_PART_LOAD    = "PART_LOAD"
PHASE_WOT          = "WOT"
PHASE_TRANSITION   = "TRANSITION"
PHASE_OFF          = "OFF"
PHASE_UNKNOWN      = "UNKNOWN"

PHASE_ORDER = [
    PHASE_COLD_START, PHASE_WARMUP, PHASE_IDLE, PHASE_CRUISE,
    PHASE_PART_LOAD, PHASE_WOT, PHASE_OVERRUN_DFCO, PHASE_TRANSITION,
    PHASE_OFF, PHASE_UNKNOWN,
]

COLD_START_ECT = 40.0
WARMUP_ECT = 70.0


def classify_phases(log: ParsedLog) -> list[str]:
    """Per-row phase. Then a smoothing pass merges sub-second flicker."""
    rpm = log.col("rpm") or [None] * log.rows
    load = log.col("load") or [None] * log.rows
    ect = log.col("ect") or [None] * log.rows
    vss = log.col("vss") or [None] * log.rows
    tps = log.col("tps") or [None] * log.rows
    lam = log.col("lambda") or [None] * log.rows
    # Idle Switch is a definitive marker: ECU itself decided "throttle plate
    # is at mechanical idle stop". Trust it over geometry when available.
    idle_sw = log.bool_col("idle_switch") or [None] * log.rows

    raw: list[str] = []
    prev_load = None
    for i in range(log.rows):
        r, l, e, v, t, lm = rpm[i], load[i], ect[i], vss[i], tps[i], lam[i]
        isw = idle_sw[i] if i < len(idle_sw) else None

        # Engine off — RPM ~ 0
        if r is not None and r < 200:
            raw.append(PHASE_OFF)
            prev_load = l if l is not None else prev_load
            continue

        if r is None or l is None:
            raw.append(PHASE_UNKNOWN)
            continue

        # Temperature gating
        if e is not None and e < COLD_START_ECT:
            raw.append(PHASE_COLD_START)
            prev_load = l
            continue
        if e is not None and e < WARMUP_ECT:
            raw.append(PHASE_WARMUP)
            prev_load = l
            continue

        # DFCO: throttle closed at speed/RPM. Two triggers:
        #   (a) Geometry: TPS<3 AND rpm>1300 AND moving (vss>5 or unknown)
        #   (b) Direct evidence: lambda > 1.20 means O2 sees pure air =>
        #       fuel must be cut, regardless of what TPS / VSS report.
        is_dfco_geom = (t is not None and t < 3.0 and r > 1300
                        and (v is None or v > 5))
        is_dfco_lam = (lm is not None and lm > 1.20)
        if is_dfco_geom or is_dfco_lam:
            raw.append(PHASE_OVERRUN_DFCO)
            prev_load = l
            continue

        # WOT
        if (t is not None and t > 75) or l > 80:
            raw.append(PHASE_WOT)
            prev_load = l
            continue

        # Idle. Two equivalent triggers:
        #   (a) Idle Switch ON + vehicle stationary => definitive idle.
        #   (b) Geometry fallback when switch column absent / wrong.
        is_idle_sw = (isw is True and (v is None or v < 3) and r < 1000
                      and l < 30 and (t is None or t < 8))
        is_idle_geom = (r < 950 and l < 22 and (v is None or v < 3)
                        and (t is None or t < 5))
        if is_idle_sw or is_idle_geom:
            raw.append(PHASE_IDLE)
            prev_load = l
            continue

        # Tip-in / tip-out (transition)
        if prev_load is not None:
            dl = l - prev_load
            if abs(dl) > 12:
                raw.append(PHASE_TRANSITION)
                prev_load = l
                continue

        # Part load vs cruise
        if l < 30 and (v is None or v > 10):
            raw.append(PHASE_CRUISE)
        else:
            raw.append(PHASE_PART_LOAD)
        prev_load = l

    return _smooth_phases(raw, log.time, min_duration_s=0.6)


def _smooth_phases(phases: list[str], times: list[float], min_duration_s: float) -> list[str]:
    """Merge phase runs shorter than `min_duration_s` into the previous run.

    Suppresses one-sample flicker (e.g. a single sample of TRANSITION
    inside CRUISE). Pure phases like COLD_START / OFF are not absorbed
    into other phases (they're hard boundaries).
    """
    if not phases:
        return phases
    out = list(phases)
    n = len(out)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and out[j + 1] == out[i]:
            j += 1
        run_dur = (times[j] - times[i]) if j > i else 0.0
        # Hard-boundary phases are never absorbed into neighbours:
        # - COLD_START / WARMUP / OFF / UNKNOWN: thermal/electrical state.
        # - OVERRUN_DFCO: triggered by direct evidence (lambda > 1.20). Even a
        #   single-sample fuel-cut event must survive smoothing, otherwise the
        #   absorbed sample contaminates downstream lambda/STFT statistics.
        if (run_dur < min_duration_s and i > 0
                and out[i] not in (PHASE_COLD_START, PHASE_WARMUP, PHASE_OFF,
                                   PHASE_UNKNOWN, PHASE_OVERRUN_DFCO)):
            replacement = out[i - 1]
            for k in range(i, j + 1):
                out[k] = replacement
        i = j + 1
    return out


# ============================================================================
# Section 4 — Aggregations
# ============================================================================

def _stats(xs: list[float]) -> dict[str, float] | None:
    if not xs:
        return None
    n = len(xs)
    xs_sorted = sorted(xs)

    def pct(p: float) -> float:
        if n == 1:
            return xs_sorted[0]
        k = (n - 1) * p
        f = math.floor(k); c = math.ceil(k)
        if f == c:
            return xs_sorted[int(k)]
        return xs_sorted[f] + (xs_sorted[c] - xs_sorted[f]) * (k - f)

    return {
        "n": n,
        "min": round(xs_sorted[0], 2),
        "p05": round(pct(0.05), 2),
        "median": round(pct(0.50), 2),
        "mean": round(statistics.fmean(xs_sorted), 2),
        "p95": round(pct(0.95), 2),
        "max": round(xs_sorted[-1], 2),
        "std": round(statistics.pstdev(xs_sorted) if n > 1 else 0.0, 2),
    }


KEYS_FOR_STATS = ["rpm", "load", "vss", "ect", "oil_temp", "iat",
                  "atm_p", "map", "map_rel", "maf_gs", "maf_v", "tps",
                  "tps_main_v", "tps_sub_v", "throttle_motor_duty",
                  "pedal", "pedal_main_v", "pedal_sub_v",
                  "ltft_b1", "stft_b1", "lambda", "o2_pre_i", "o2_pre_r", "o2_post",
                  "knock", "ign_tim", "inj_pulse",
                  "vvt_duty_l", "vvt_duty_r", "vvt_curr_l", "vvt_curr_r",
                  "egr_steps", "fuel_tank_p", "fuel_temp", "battery"]


def per_phase_stats(log: ParsedLog, phases: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    counter = Counter(phases)
    for phase, n in counter.items():
        if n < 5:
            continue
        out[phase] = {"samples": n, "share_pct": round(100 * n / log.rows, 1)}
        for k in KEYS_FOR_STATS:
            vals = log.col(k)
            if vals is None:
                continue
            xs = [vals[i] for i in range(log.rows)
                  if phases[i] == phase and vals[i] is not None]
            s = _stats(xs)
            if s is not None:
                out[phase][k] = s
    return out


def rpm_load_map(log: ParsedLog, sensor_key: str,
                 exclude_phases: tuple[str, ...] = ()) -> dict[str, dict]:
    rpm = log.col("rpm")
    load = log.col("load")
    target = log.col(sensor_key)
    if rpm is None or load is None or target is None:
        return {}
    rpm_bins = [(0, 1100, "idle"), (1100, 2500, "low"),
                (2500, 4500, "mid"), (4500, 9000, "high")]
    load_bins = [(0, 25, "low"), (25, 60, "mid"), (60, 200, "high")]
    grid: dict[str, list[float]] = defaultdict(list)
    for i in range(log.rows):
        r, l, t = rpm[i], load[i], target[i]
        if r is None or l is None or t is None:
            continue
        rb = next((nm for lo, hi, nm in rpm_bins if lo <= r < hi), None)
        lb = next((nm for lo, hi, nm in load_bins if lo <= l < hi), None)
        if rb and lb:
            grid[f"{rb}_rpm/{lb}_load"].append(t)
    return {k: {"mean": round(statistics.fmean(v), 2),
                "median": round(statistics.median(v), 2),
                "n": len(v)} for k, v in grid.items() if len(v) >= 3}


def fuel_trim_drift(log: ParsedLog) -> dict[str, dict]:
    """Compare fuel trim mean over first 20% vs last 20% of the log."""
    out: dict[str, dict] = {}
    for k in ("ltft_b1", "ltft_b3", "stft_b1", "stft_b3"):
        v = log.col(k)
        if v is None:
            continue
        clean = [x for x in v if x is not None]
        if len(clean) < 20:
            continue
        nq = max(5, len(clean) // 5)
        head = clean[:nq]
        tail = clean[-nq:]
        out[k] = {
            "head_mean": round(statistics.fmean(head), 2),
            "tail_mean": round(statistics.fmean(tail), 2),
            "drift": round(statistics.fmean(tail) - statistics.fmean(head), 2),
        }
    return out


def boolean_summary(log: ParsedLog) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for ci, vals in log.boolean.items():
        on_count = sum(1 for v in vals if v is True)
        off_count = sum(1 for v in vals if v is False)
        total = on_count + off_count
        if total < 5:
            continue
        on_pct = round(100 * on_count / total, 1)
        cls = "constant" if on_pct in (0.0, 100.0) else "toggling"
        out[log.header[ci]] = {
            "on_pct": on_pct,
            "transitions": sum(1 for i in range(1, len(vals))
                               if vals[i] is not None and vals[i - 1] is not None
                               and vals[i] != vals[i - 1]),
            "class": cls,
        }
    return out


# ============================================================================
# Section 5 — Event detection (DFCO-aware)
# ============================================================================

def detect_events(log: ParsedLog, phases: list[str]) -> list[dict]:
    events: list[dict] = []

    def append_runs(name: str, mask: list[bool], min_run: int,
                    extra: dict[str, Any] | None = None) -> None:
        i = 0
        while i < len(mask):
            if mask[i]:
                j = i
                while j + 1 < len(mask) and mask[j + 1]:
                    j += 1
                if j - i + 1 >= min_run:
                    ev: dict[str, Any] = {
                        "type": name,
                        "t_start": round(log.time[i], 2),
                        "t_end": round(log.time[j], 2),
                        "duration_s": round(log.time[j] - log.time[i], 2),
                        "samples": j - i + 1,
                        "phase": phases[i],
                    }
                    if extra:
                        ev.update(extra)
                    events.append(ev)
                i = j + 1
            else:
                i += 1

    # Knock retard (always meaningful)
    knock = log.col("knock")
    if knock:
        append_runs("knock_retard", [(v is not None and v <= -1.0) for v in knock], min_run=2)

    # LTFT outside warn band — meaningful only in warm closed-loop phases
    cl_phases = (PHASE_IDLE, PHASE_CRUISE, PHASE_PART_LOAD)
    for k in ("ltft_b1", "ltft_b3"):
        v = log.col(k)
        if v:
            mask = [(v[i] is not None and abs(v[i]) > 10.0 and phases[i] in cl_phases)
                    for i in range(log.rows)]
            append_runs(f"{k}_drift", mask, min_run=5)

    # STFT volatility — exclude transitions and DFCO (where swing is normal)
    for k in ("stft_b1", "stft_b3"):
        v = log.col(k)
        if v:
            mask = [(v[i] is not None and abs(v[i]) > 15.0
                     and phases[i] in cl_phases)
                    for i in range(log.rows)]
            append_runs(f"{k}_excursion", mask, min_run=3)

    # Lambda excursion — DFCO-aware (excludes overrun)
    lam = log.col("lambda")
    if lam:
        mask = [(lam[i] is not None and (lam[i] < 0.90 or lam[i] > 1.10)
                 and phases[i] not in (PHASE_OVERRUN_DFCO, PHASE_TRANSITION,
                                        PHASE_COLD_START, PHASE_WARMUP, PHASE_OFF))
                for i in range(log.rows)]
        append_runs("lambda_excursion", mask, min_run=3)

    # EVAP tank pressure spike
    ftp = log.col("fuel_tank_p")
    if ftp:
        mask = [(x is not None and abs(x) > 2.0) for x in ftp]
        append_runs("evap_tank_pressure", mask, min_run=2)

    # Misfire counters increasing
    for ci, name in enumerate(log.header):
        if "misfire monitor cyl" in name.lower() and ci in log.numeric:
            v = log.numeric[ci]
            last_val = 0.0
            spikes = 0
            for x in v:
                if x is None:
                    continue
                if x > last_val:
                    spikes += 1
                last_val = max(last_val, x)
            if spikes:
                events.append({"type": "misfire_counter_increment",
                               "cylinder": name, "increments": spikes})

    return events


# ============================================================================
# Section 6 — Diagnostic checks (Tier 1: fuel system)
# ============================================================================

@dataclass
class Finding:
    check_id: str
    title: str
    severity: str               # "pass" | "info" | "warn" | "alarm" | "skipped"
    value: float | str | None
    explanation: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class Check:
    id: str
    title: str
    tier: int
    fuel_types: tuple[str, ...]    # ("petrol",), ("lpg",), or ("petrol","lpg")
    fn: Callable[["CheckCtx"], Finding]


@dataclass
class CheckCtx:
    log: ParsedLog
    phases: list[str]
    summary: dict[str, Any]
    fuel_type: str             # "petrol" | "lpg" | "unknown"


def _phase_median(ctx: CheckCtx, phase: str, key: str) -> float | None:
    p = ctx.summary["per_phase"].get(phase)
    if p is None:
        return None
    s = p.get(key)
    return s["median"] if s else None


def _phase_samples(ctx: CheckCtx, phase: str) -> int:
    return ctx.summary["per_phase"].get(phase, {}).get("samples", 0)


def _band(value: float | None, pass_lo: float, pass_hi: float,
          warn_lo: float, warn_hi: float) -> str:
    if value is None:
        return "skipped"
    if pass_lo <= value <= pass_hi:
        return "pass"
    if warn_lo <= value <= warn_hi:
        return "warn"
    return "alarm"


# ----- Check implementations -----

def chk_idle_ltft_static(ctx: CheckCtx) -> Finding:
    n = _phase_samples(ctx, PHASE_IDLE)
    val = _phase_median(ctx, PHASE_IDLE, "ltft_b1")
    if n < 30 or val is None:
        return Finding("idle_ltft_static", "Idle LTFT (warm)", "skipped", val,
                       f"Insufficient warm-idle data ({n} samples, need 30+).")
    if ctx.fuel_type == "lpg":
        sev = _band(val, -8, 8, -12, 12)
        rich_msg = (
            f"LTFT median {val:+.1f}% at LPG idle — ECU is removing fuel. "
            "On LPG this often means LPG injector seepage (warm-soak), "
            "reducer overfeed, or sticky LPG injector (clattering noise = wear). "
            "Cross-check with petrol idle log for the same vehicle."
        )
        lean_msg = (
            f"LTFT median {val:+.1f}% at LPG idle — ECU adding fuel. "
            "Possible: LPG injectors clogging, low gas pressure (reducer), "
            "vacuum leak (intake/PCV/brake booster), MAF drift."
        )
    else:  # petrol or unknown
        sev = _band(val, -5, 5, -8, 8)
        rich_msg = (
            f"LTFT median {val:+.1f}% at idle — ECU removing fuel. Possible: "
            "leaking petrol injector(s), high fuel pressure (FPR vacuum hose off), "
            "cracked exhaust before O2, dirty MAF (under-reading). "
            "If dual-fuel: LPG injector seepage even when on petrol is possible."
        )
        lean_msg = (
            f"LTFT median {val:+.1f}% at idle — ECU adding fuel. Possible: "
            "vacuum leak (intake / PCV / brake booster / FPR), weak fuel pressure, "
            "dirty MAF, exhaust leak before O2."
        )
    if sev == "pass":
        msg = f"LTFT median {val:+.1f}% at idle — within healthy band."
    elif val < 0:
        msg = rich_msg
    else:
        msg = lean_msg
    return Finding("idle_ltft_static", "Idle LTFT (warm)", sev, val, msg,
                   evidence={"phase": PHASE_IDLE, "samples": n})


def chk_cruise_ltft_static(ctx: CheckCtx) -> Finding:
    n = _phase_samples(ctx, PHASE_CRUISE)
    val = _phase_median(ctx, PHASE_CRUISE, "ltft_b1")
    if n < 60 or val is None:
        return Finding("cruise_ltft_static", "Cruise LTFT (warm)", "skipped", val,
                       f"Insufficient cruise data ({n} samples, need 60+).")
    if ctx.fuel_type == "lpg":
        sev = _band(val, -7, 7, -12, 12)
    else:
        sev = _band(val, -5, 5, -8, 8)
    msg = f"LTFT median {val:+.1f}% in CRUISE — "
    if sev == "pass":
        msg += "within healthy band."
    elif val < 0:
        msg += ("ECU removing fuel under part-throttle cruise. Often points to "
                "MAF over-reading, leaking injectors, or — on LPG — to a rich "
                "LPG mixture map (reducer setting / injector size mismatch).")
    else:
        msg += ("ECU adding fuel under part-throttle cruise. Often points to "
                "MAF under-reading (dirt), partial vacuum leak, weak fuel pressure, "
                "or — on LPG — undersized LPG injectors / low gas pressure.")
    return Finding("cruise_ltft_static", "Cruise LTFT (warm)", sev, val, msg,
                   evidence={"phase": PHASE_CRUISE, "samples": n})


def chk_ltft_load_dependency(ctx: CheckCtx) -> Finding:
    """If LTFT moves strongly with load -> vacuum-leak signature (rich at idle, neutral at load)."""
    idle_v = _phase_median(ctx, PHASE_IDLE, "ltft_b1")
    cruise_v = _phase_median(ctx, PHASE_CRUISE, "ltft_b1")
    if idle_v is None or cruise_v is None:
        return Finding("ltft_load_dependency", "LTFT load dependency",
                       "skipped", None,
                       "Need both IDLE and CRUISE LTFT medians.")
    delta = cruise_v - idle_v
    if abs(delta) < 5:
        sev = "pass"
        msg = f"LTFT IDLE vs CRUISE delta = {delta:+.1f}% — flat. No clear load dependency."
    elif delta > 5:
        sev = "warn"
        msg = (f"LTFT rises with load (idle {idle_v:+.1f}% -> cruise {cruise_v:+.1f}%, "
               f"delta {delta:+.1f}%). Two main signatures match this shape: "
               "(1) idle is too rich (leaking injector / FPR / -- on LPG -- LPG injector seepage), "
               "so ECU subtracts at idle and the trim relaxes back near zero under load; "
               "(2) load-side enleanment from a clogged secondary fuel path / dirty injector at higher demand.")
    else:
        sev = "warn"
        msg = (f"LTFT falls with load (idle {idle_v:+.1f}% -> cruise {cruise_v:+.1f}%, "
               f"delta {delta:+.1f}%). Classic vacuum-leak signature on petrol: "
               "leak air dominates at idle -> ECU adds fuel (idle LTFT high), then leak becomes "
               "negligible at load (LTFT relaxes). On LPG, can also indicate the LPG load map "
               "being too rich while idle is correct.")
    return Finding("ltft_load_dependency", "LTFT load dependency", sev, delta, msg,
                   evidence={"idle_median": idle_v, "cruise_median": cruise_v})


def chk_stft_volatility(ctx: CheckCtx) -> Finding:
    p = ctx.summary["per_phase"].get(PHASE_CRUISE)
    if not p or "stft_b1" not in p:
        return Finding("stft_volatility", "STFT volatility (cruise)",
                       "skipped", None, "No STFT data in CRUISE.")
    std = p["stft_b1"]["std"]
    sev = _band(std, 0, 4, 0, 7)
    msg = f"STFT std in CRUISE = {std:.1f}%. "
    if sev == "pass":
        msg += "Closed-loop control is stable."
    elif sev == "warn":
        msg += "Closed-loop is twitchy. Possible: O2 sensor lazy/aging, intermittent vacuum leak, "
        msg += "fuel pressure ripple, mixed fuels."
    else:
        msg += "Closed-loop is wildly oscillating. Inspect O2 sensor wiring and fuel delivery first."
    return Finding("stft_volatility", "STFT volatility (cruise)", sev, std, msg,
                   evidence={"phase": PHASE_CRUISE, "std_pct": std})


def chk_lambda_stoich_tracking(ctx: CheckCtx) -> Finding:
    lam = ctx.log.col("lambda")
    if lam is None:
        return Finding("lambda_stoich_tracking", "Lambda CL tracking",
                       "skipped", None, "No lambda channel.")
    cl = (PHASE_IDLE, PHASE_CRUISE, PHASE_PART_LOAD)
    samples = [lam[i] for i in range(ctx.log.rows)
               if ctx.phases[i] in cl and lam[i] is not None]
    if len(samples) < 100:
        return Finding("lambda_stoich_tracking", "Lambda CL tracking",
                       "skipped", None,
                       f"Only {len(samples)} CL samples, need 100+.")
    # Stoich-tracking tolerance: petrol ECUs sit within +-0.02 of stoich in
    # closed loop. LPG installs add reducer + LPG-injector latency, so cycle
    # amplitude widens to ~+-0.05. Use a wider tolerance and looser pass band.
    if ctx.fuel_type == "lpg":
        threshold = 0.05
        pass_pct, warn_pct = 35, 60
    else:
        threshold = 0.02
        pass_pct, warn_pct = 25, 50
    off_stoich = sum(1 for x in samples if abs(x - 1.0) > threshold)
    pct = round(100 * off_stoich / len(samples), 1)
    if pct <= pass_pct:
        sev = "pass"
    elif pct <= warn_pct:
        sev = "warn"
    else:
        sev = "alarm"
    msg = (f"{pct}% of warm closed-loop samples have |lambda - 1.00| > "
           f"{threshold:.2f} (fuel={ctx.fuel_type}). ")
    if sev == "pass":
        msg += "Lambda tracks stoich within expected band for this fuel."
    elif sev == "warn":
        msg += ("Tracking is loose. On petrol: lazy O2 sensor likely. "
                "On LPG: typically reducer pressure ripple or LPG injector "
                "timing slightly off; check Stag map first.")
    else:
        msg += ("Tracking is poor. Either the wideband sensor is failing, "
                "trims have hit limits, or (LPG) the LPG fuelling is "
                "materially mis-scaled and ECU cannot keep up.")
    return Finding("lambda_stoich_tracking", "Lambda CL tracking",
                   sev, pct, msg, evidence={"samples": len(samples)})


def chk_power_enrichment(ctx: CheckCtx) -> Finding:
    n = _phase_samples(ctx, PHASE_WOT)
    if n < 10:
        return Finding("power_enrichment", "Power enrichment (WOT)",
                       "skipped", None, f"Only {n} WOT samples — no WOT pulls.")
    val = _phase_median(ctx, PHASE_WOT, "lambda")
    if val is None:
        return Finding("power_enrichment", "Power enrichment (WOT)",
                       "skipped", None, "No lambda in WOT phase.")
    # Healthy WOT lambda 0.80-0.88 for NA/EJ on petrol.
    # On LPG, PE is often disabled or much milder (higher octane, less knock
    # margin needed) so lambda staying near 1.0 at WOT is NOT necessarily a fault.
    if ctx.fuel_type == "lpg":
        # Treat 0.85-1.00 as acceptable; only flag if leaner than 1.00 OR very rich.
        if val < 0.78:
            sev = "warn"
        elif val > 1.02:
            sev = "alarm"
        else:
            sev = "pass"
    else:
        sev = _band(val, 0.80, 0.88, 0.75, 0.95)
    msg = f"Lambda median at WOT = {val:.2f}. "
    if sev == "pass":
        if ctx.fuel_type == "lpg":
            msg += ("On LPG, PE is often calibration-disabled or mild; lambda staying "
                    "near stoich at full load is normal as long as no knock retard is logged.")
        else:
            msg += "Healthy power enrichment."
    elif val > 1.00:
        msg += ("Mixture is lean at WOT. On petrol this risks detonation. "
                "On LPG, check that knock retard is absent during the same pulls; "
                "if knock is also present, LPG injectors / pressure are likely undersized for full load.")
    elif val > 0.95:
        msg += ("Mixture is lean for WOT (close to stoich). On petrol this is risky for sustained "
                "full load. On LPG it is often acceptable if no knock retard is logged.")
    elif val < 0.78:
        msg += "Mixture is very rich at WOT — wasted fuel, possible cat damage with prolonged WOT."
    else:
        msg += "Slightly off the ideal band; not critical for short pulls."
    return Finding("power_enrichment", "Power enrichment (WOT)", sev, val, msg,
                   evidence={"samples": n})


def chk_dfco_present(ctx: CheckCtx) -> Finding:
    n = _phase_samples(ctx, PHASE_OVERRUN_DFCO)
    pct = round(100 * n / max(ctx.log.rows, 1), 1)
    if n < 5:
        sev = "info"
        msg = ("No DFCO (deceleration fuel cut-off) detected. Either the log "
               "contains no overrun events or DFCO is disabled in the calibration.")
    else:
        sev = "pass"
        msg = (f"DFCO active in {n} samples ({pct}% of log). "
               "Lambda excursions in this phase are expected and excluded from fuel-system checks.")
    return Finding("dfco_present", "DFCO detection", sev, n, msg,
                   evidence={"samples": n, "share_pct": pct})


def chk_idle_rpm_stability(ctx: CheckCtx) -> Finding:
    p = ctx.summary["per_phase"].get(PHASE_IDLE)
    if not p or "rpm" not in p:
        return Finding("idle_rpm_stability", "Idle RPM stability",
                       "skipped", None, "No IDLE samples.")
    std = p["rpm"]["std"]
    sev = _band(std, 0, 25, 0, 60)
    msg = f"Idle RPM std = {std:.1f} rpm. "
    if sev == "pass":
        msg += "Idle is stable."
    elif sev == "warn":
        msg += "Idle is rough. Possible: dirty IACV / throttle plate, ignition coil/plug, vacuum leak, LPG injector wear (clatter)."
    else:
        msg += "Idle is hunting. Same root causes; severity is high — diagnose before next drive."
    return Finding("idle_rpm_stability", "Idle RPM stability", sev, std, msg,
                   evidence={"samples": p["samples"]})


# ---------- Tier 1 (extra): WOT fuel delivery (lean + STFT-pegged signature) ----------

def chk_wot_fuel_delivery(ctx: CheckCtx) -> Finding:
    """Detect insufficient fuel supply under load.

    Signature: at WOT lambda lean (>= 1.00) AND STFT pegged high (>= +15%
    p95). Means ECU is asking for fuel, injectors / pump cannot keep up.
    Classic clogged fuel filter / weak pump / dirty injector pattern.
    """
    p = ctx.summary["per_phase"].get(PHASE_WOT)
    if not p or "lambda" not in p or "stft_b1" not in p:
        return Finding("wot_fuel_delivery", "WOT fuel delivery",
                       "skipped", None, f"Only {p.get('samples', 0) if p else 0} WOT samples.")
    lam_med = p["lambda"]["median"]
    stft_p95 = p["stft_b1"]["p95"]
    stft_mean = p["stft_b1"]["mean"]
    stft_std = p["stft_b1"]["std"]
    samples = p["samples"]

    # Two-axis decision:
    #   A) lambda lean (>1.00) under WOT is itself a flag (we expect 0.85-0.92).
    #   B) STFT clinging to +15% or higher means the ECU is working at the
    #      authority limit (typical ECU clamp = +25%). High std confirms it
    #      is not a single transient but sustained struggle.
    lean = lam_med >= 1.00
    stft_high = stft_p95 >= 15.0 or stft_mean >= 8.0
    stft_volatile = stft_std >= 6.0

    if lean and stft_high:
        sev = "alarm"
        msg = (f"Lambda median {lam_med:.2f} at WOT (lean) AND STFT p95 {stft_p95:+.1f}% "
               f"(mean {stft_mean:+.1f}%, std {stft_std:.1f}%) \u2014 ECU is at fuel-correction limit. "
               "Strong signature of insufficient fuel supply under load. Check, in order: "
               "(1) fuel filter (replace if > 50k km), "
               "(2) fuel rail pressure under WOT (norm: ~3.4 bar held under load), "
               "(3) injector flow (clogged / aged injectors).")
    elif stft_high or stft_volatile:
        sev = "warn"
        msg = (f"STFT struggling at WOT (p95 {stft_p95:+.1f}%, std {stft_std:.1f}%). "
               f"Lambda {lam_med:.2f}. Marginal fuel delivery; worth inspecting filter and rail pressure.")
    elif lean and ctx.fuel_type != "lpg":
        sev = "warn"
        msg = (f"Lambda {lam_med:.2f} at WOT is lean for petrol (expected 0.80-0.88). "
               f"STFT not pegged (p95 {stft_p95:+.1f}%) so fuel delivery may be marginal rather than failed.")
    else:
        sev = "pass"
        msg = (f"Lambda {lam_med:.2f}, STFT p95 {stft_p95:+.1f}% at WOT \u2014 ECU keeps up "
               "with fuel demand under full load.")
    return Finding("wot_fuel_delivery", "WOT fuel delivery", sev, stft_p95, msg,
                   evidence={"samples": samples, "lambda_median": lam_med,
                             "stft_p95": stft_p95, "stft_mean": stft_mean,
                             "stft_std": stft_std})


# ---------- Tier 2 (air system) ----------

def chk_maf_idle_value(ctx: CheckCtx) -> Finding:
    p = ctx.summary["per_phase"].get(PHASE_IDLE)
    if not p or "maf_gs" not in p:
        return Finding("maf_idle_value", "MAF at warm idle",
                       "skipped", None, "No warm idle samples.")
    val = p["maf_gs"]["median"]
    # EJ253 (2.5 L NA) at warm idle ~700 rpm: expect 2.5-3.5 g/s.
    sev = _band(val, 2.5, 3.6, 2.0, 4.5)
    msg = f"MAF median {val:.2f} g/s at warm idle (~700 rpm). "
    if sev == "pass":
        msg += "Within expected band for EJ253 at idle."
    elif val > 3.6:
        msg += ("Higher than expected. Possible: vacuum leak (intake / brake booster / FPR / PCV), "
                "high idle, MAF over-reading after replacement.")
    else:
        msg += ("Lower than expected. Possible: dirty MAF (under-reading), partial intake restriction, "
                "intake leak after the MAF (false air bypassing the meter).")
    return Finding("maf_idle_value", "MAF at warm idle", sev, val, msg,
                   evidence={"samples": p["samples"]})


def chk_map_rel_idle(ctx: CheckCtx) -> Finding:
    """At warm idle a healthy NA engine pulls ~25 kPa absolute => ~-65 kPa relative.

    A weak vacuum (MAP idle high or relative pressure too small in magnitude)
    indicates a vacuum leak, leaking valve seal, or a stuck-open PCV path.
    """
    p = ctx.summary["per_phase"].get(PHASE_IDLE)
    if not p:
        return Finding("vacuum_at_idle", "Manifold vacuum at idle",
                       "skipped", None, "No warm idle samples.")
    if "map" in p:
        val = p["map"]["median"]
        sev = _band(val, 22, 30, 18, 40)
        msg = f"MAP {val:.1f} kPa abs at warm idle. "
        if sev == "pass":
            msg += "Healthy manifold vacuum (~ -75 kPa rel)."
        elif val > 30:
            msg += "Weak manifold vacuum. Suspect vacuum leak, sticking throttle plate, late ignition, or major valve issue."
        else:
            msg += "Unusually high vacuum at idle. Possibly partial intake restriction (filter / TB plate)."
        return Finding("vacuum_at_idle", "Manifold vacuum at idle", sev, val, msg,
                       evidence={"samples": p["samples"]})
    return Finding("vacuum_at_idle", "Manifold vacuum at idle",
                   "skipped", None, "MAP channel missing.")


def chk_iat_plausibility(ctx: CheckCtx) -> Finding:
    """IAT must respond to driving. After a warm cruise it should track ambient.
    A frozen / unplausible IAT (constant value) usually means a bad sensor
    or stuck-open thermostat in the airbox area.
    """
    iat = ctx.log.col("iat")
    if iat is None:
        return Finding("iat_plausibility", "IAT plausibility",
                       "skipped", None, "No IAT channel.")
    samples = [x for x in iat if x is not None]
    if len(samples) < 100:
        return Finding("iat_plausibility", "IAT plausibility",
                       "skipped", None, "Too few IAT samples.")
    rng = max(samples) - min(samples)
    sev = "pass" if rng >= 2 else "warn"
    msg = (f"IAT range {min(samples):.0f}-{max(samples):.0f} °C (\u0394 {rng:.0f} °C). "
           + ("Sensor responds to driving conditions." if sev == "pass" else
              "Sensor is essentially frozen \u2014 likely stuck reading or wiring issue."))
    return Finding("iat_plausibility", "IAT plausibility", sev, rng, msg)


def chk_maf_map_correlation(ctx: CheckCtx) -> Finding:
    """Both MAF and MAP must rise together with load. If correlation drops,
    one of the sensors is drifting. We compute Pearson r in PART_LOAD+CRUISE.
    """
    maf = ctx.log.col("maf_gs")
    mp = ctx.log.col("map")
    if maf is None or mp is None:
        return Finding("maf_map_correlation", "MAF / MAP correlation",
                       "skipped", None, "MAF or MAP channel missing.")
    cl = (PHASE_CRUISE, PHASE_PART_LOAD, PHASE_WOT)
    pairs = [(maf[i], mp[i]) for i in range(ctx.log.rows)
             if ctx.phases[i] in cl and maf[i] is not None and mp[i] is not None]
    if len(pairs) < 100:
        return Finding("maf_map_correlation", "MAF / MAP correlation",
                       "skipped", None, f"Only {len(pairs)} usable pairs.")
    xs = [a for a, _ in pairs]
    ys = [b for _, b in pairs]
    mx = statistics.fmean(xs); my = statistics.fmean(ys)
    num = sum((x - mx) * (y - my) for x, y in pairs)
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    r = (num / den) if den > 0 else 0.0
    if r >= 0.85:
        sev = "pass"
    elif r >= 0.70:
        sev = "warn"
    else:
        sev = "alarm"
    msg = (f"MAF vs MAP Pearson r = {r:.2f} across {len(pairs)} loaded samples. "
           + {"pass": "Both sensors agree on engine load \u2014 air-path metrology is consistent.",
              "warn": "Mild disagreement \u2014 one sensor may be drifting (often dirty MAF).",
              "alarm": "Strong disagreement \u2014 inspect MAF and MAP wiring + signal."}[sev])
    return Finding("maf_map_correlation", "MAF / MAP correlation", sev, r, msg)


# ---------- Tier 3 (ignition) ----------

def chk_knock_active_retard(ctx: CheckCtx) -> Finding:
    """In Subaru SSM2, "Knock Correction" is the algebraic in-the-moment
    correction. Positive values are usually long-term FKL applied as advance
    when no knock is sensed. The interesting signal is **negative transients**:
    short dips of -1.4° or worse mean the knock sensor fired right now.
    """
    knock = ctx.log.col("knock")
    if knock is None:
        return Finding("knock_active_retard", "Active knock retard events",
                       "skipped", None, "No knock channel.")
    # Count samples with retard <= -1.4 in real working phases
    work = (PHASE_CRUISE, PHASE_PART_LOAD, PHASE_WOT, PHASE_TRANSITION)
    work_samples = [knock[i] for i in range(ctx.log.rows)
                    if ctx.phases[i] in work and knock[i] is not None]
    if len(work_samples) < 50:
        return Finding("knock_active_retard", "Active knock retard events",
                       "skipped", None, "Too few loaded samples.")
    minus_14 = sum(1 for x in work_samples if x <= -1.4)
    minus_28 = sum(1 for x in work_samples if x <= -2.8)
    minus_50 = sum(1 for x in work_samples if x <= -5.0)
    worst = min(work_samples)
    if minus_50 > 0:
        sev = "alarm"
    elif minus_28 > 5 or minus_14 > 30:
        sev = "warn"
    elif minus_14 > 0:
        sev = "info"
    else:
        sev = "pass"
    msg = (f"Worst knock correction in load = {worst:+.2f}°. "
           f"Counts: {minus_14} \u2264 -1.4°, {minus_28} \u2264 -2.8°, {minus_50} \u2264 -5.0°. ")
    if sev == "pass":
        msg += "No active knock retard worth flagging."
    elif sev == "info":
        msg += "Sporadic mild retard \u2014 normal for any street engine."
    elif sev == "warn":
        msg += ("Repeated retard at \u2264 -2.8°. Check fuel octane, ignition timing learning, "
                "carbon buildup, or (LPG) reducer / mixture timing.")
    else:
        msg += ("Severe retard observed (\u2264 -5°). Bearing-damage risk territory \u2014 "
                "diagnose before further full-load driving.")
    return Finding("knock_active_retard", "Active knock retard events",
                   sev, minus_14, msg,
                   evidence={"worst_deg": worst, "n_minus_1_4": minus_14,
                             "n_minus_2_8": minus_28, "n_minus_5_0": minus_50})


def chk_knock_learn_advance(ctx: CheckCtx) -> Finding:
    """High persistent positive values in WOT / PART_LOAD = ECU learned that
    no knock occurs and added timing. On LPG that's healthy. On petrol 95
    after switching from LPG, that learned advance is risky until ECU re-learns.
    """
    knock = ctx.log.col("knock")
    if knock is None:
        return Finding("knock_learn_advance", "Learned knock advance",
                       "skipped", None, "No knock channel.")
    work = (PHASE_PART_LOAD, PHASE_WOT)
    samples = [knock[i] for i in range(ctx.log.rows)
               if ctx.phases[i] in work and knock[i] is not None]
    if len(samples) < 30:
        return Finding("knock_learn_advance", "Learned knock advance",
                       "skipped", None, "Too few loaded samples.")
    p95 = sorted(samples)[int(0.95 * (len(samples) - 1))]
    median = statistics.median(samples)
    if p95 >= 5.0 and ctx.fuel_type == "petrol":
        sev = "warn"
        msg = (f"Learned advance p95 = {p95:+.1f}° on petrol. If this advance was learned on "
               "LPG (95+ ON) and ECU has not yet re-learned on petrol 95, detonation risk is real "
               "until knock retard re-trains the FKL table. Drive gently for 1-2 tankfuls.")
    elif p95 >= 4.0:
        sev = "info"
        msg = f"Learned advance p95 = {p95:+.1f}°. ECU has built up advance margin in the working cells."
    else:
        sev = "pass"
        msg = f"Learned advance modest (p95 {p95:+.1f}°)."
    return Finding("knock_learn_advance", "Learned knock advance",
                   sev, p95, msg,
                   evidence={"median": median, "p95": p95, "samples": len(samples)})


def chk_timing_warmup(ctx: CheckCtx) -> Finding:
    """During WARMUP (cold catalyst protection) ignition is normally retarded.
    Excessively high timing in WARMUP indicates the cold-start map is wrong
    or the ECU thinks the engine is warm when it isn't.
    """
    p = ctx.summary["per_phase"].get(PHASE_WARMUP)
    if not p or "ign_tim" not in p:
        return Finding("timing_warmup", "Ignition timing during warmup",
                       "skipped", None, "No WARMUP samples with ignition data.")
    median = p["ign_tim"]["median"]
    p95 = p["ign_tim"]["p95"]
    if median > 25 or p95 > 35:
        sev = "warn"
        msg = (f"WARMUP ignition median {median:+.1f}° / p95 {p95:+.1f}°. Higher than typical "
               "cold-cat protection map. Verify ECT sensor reads cold values correctly.")
    else:
        sev = "pass"
        msg = f"WARMUP ignition median {median:+.1f}° \u2014 normal cold-start retard."
    return Finding("timing_warmup", "Ignition timing during warmup",
                   sev, median, msg, evidence={"median": median, "p95": p95})


# ---------- Tier 4 (temperatures & cooling) ----------

def chk_coolant_warmup_rate(ctx: CheckCtx) -> Finding:
    """Healthy thermostat: ECT goes from <40°C to >75°C in 4-10 minutes
    of driving. Faster = thermostat stuck open (long warm-up never reached).
    Slower = thermostat broken open or coolant too cold.
    """
    ect = ctx.log.col("ect")
    if ect is None:
        return Finding("coolant_warmup_rate", "Coolant warmup rate",
                       "skipped", None, "No ECT channel.")
    # Find first sample <= 40°C and first sample where ECT first reaches >= 75°C
    t_cold = None
    t_warm = None
    for i in range(ctx.log.rows):
        if ect[i] is None:
            continue
        if t_cold is None and ect[i] <= 40:
            t_cold = ctx.log.time[i]
        if t_cold is not None and ect[i] >= 75:
            t_warm = ctx.log.time[i]
            break
    if t_cold is None or t_warm is None:
        return Finding("coolant_warmup_rate", "Coolant warmup rate",
                       "skipped", None, "Log does not span cold->warm transition.")
    minutes = (t_warm - t_cold) / 60
    if minutes < 2:
        sev = "warn"
        msg = f"Warmup in {minutes:.1f} min \u2014 unusually fast. Could be ECT sensor fast-jumping."
    elif minutes <= 10:
        sev = "pass"
        msg = f"Warmup in {minutes:.1f} min \u2014 thermostat is healthy."
    elif minutes <= 15:
        sev = "info"
        msg = f"Warmup in {minutes:.1f} min \u2014 slowish but acceptable in cold ambient."
    else:
        sev = "warn"
        msg = (f"Warmup in {minutes:.1f} min. Thermostat may be stuck open, coolant level low, "
               "or load too light to heat the engine.")
    return Finding("coolant_warmup_rate", "Coolant warmup rate",
                   sev, minutes, msg, evidence={"minutes": minutes})


def chk_oil_temp_lag(ctx: CheckCtx) -> Finding:
    """Oil temp should climb behind coolant with a lag of ~5-15 °C. Identical
    means no oil flow / sensor fault; very large lag means low oil level or
    sensor fault.
    """
    ect = ctx.log.col("ect")
    oil = ctx.log.col("oil_temp")
    if ect is None or oil is None:
        return Finding("oil_temp_lag", "Oil vs coolant lag",
                       "skipped", None, "Need both ECT and oil-temp channels.")
    # Compare medians in the last quarter of the log (assume warmed up there)
    n = ctx.log.rows
    quarter = max(50, n // 4)
    e_tail = [ect[i] for i in range(n - quarter, n) if ect[i] is not None]
    o_tail = [oil[i] for i in range(n - quarter, n) if oil[i] is not None]
    if len(e_tail) < 30 or len(o_tail) < 30:
        return Finding("oil_temp_lag", "Oil vs coolant lag",
                       "skipped", None, "Too little tail data.")
    e_med = statistics.median(e_tail)
    o_med = statistics.median(o_tail)
    lag = e_med - o_med
    if abs(lag) <= 5 and e_med > 70:
        # On a warm engine oil should be a few degrees BELOW coolant.
        sev = "pass"
        msg = f"ECT median {e_med:.0f} °C, oil {o_med:.0f} °C (\u0394 {lag:+.1f}). Healthy."
    elif lag > 25:
        sev = "warn"
        msg = (f"Oil running cold vs coolant (\u0394 {lag:+.1f} °C). "
               "Could be low oil level, sensor in a poor location, or sensor failure.")
    elif lag < -10:
        sev = "warn"
        msg = (f"Oil hotter than coolant (\u0394 {lag:+.1f} °C). Suspect failing thermostat, "
               "coolant flow problem, or wrong sensor wiring.")
    else:
        sev = "pass"
        msg = f"ECT median {e_med:.0f} °C, oil {o_med:.0f} °C (\u0394 {lag:+.1f})."
    return Finding("oil_temp_lag", "Oil vs coolant lag",
                   sev, lag, msg, evidence={"ect": e_med, "oil": o_med})


# ---------- Tier 5 (sensor sanity / voltage redundancy) ----------

def _track_voltages(a: list[float | None], b: list[float | None]) -> tuple[float, float] | None:
    """Return (Pearson r, mean abs delta) over rows where both are present."""
    pairs = [(a[i], b[i]) for i in range(min(len(a), len(b)))
             if a[i] is not None and b[i] is not None]
    if len(pairs) < 100:
        return None
    xs = [x for x, _ in pairs]; ys = [y for _, y in pairs]
    mx = statistics.fmean(xs); my = statistics.fmean(ys)
    num = sum((x - mx) * (y - my) for x, y in pairs)
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    r = (num / den) if den > 0 else 0.0
    delta = statistics.fmean(abs(x - y) for x, y in pairs)
    return r, delta


def chk_tps_voltage_redundancy(ctx: CheckCtx) -> Finding:
    """Drive-by-wire ECU has two TPS tracks (main + sub). They must
    track each other (physical redundancy) \u2014 if not, ECU goes into
    limp mode. We measure correlation r and absolute delta.
    """
    a = ctx.log.col("tps_main_v")
    b = ctx.log.col("tps_sub_v")
    if a is None or b is None:
        return Finding("tps_voltage_redundancy", "TPS dual-track sanity",
                       "skipped", None, "TPS main/sub voltages not in log.")
    res = _track_voltages(a, b)
    if res is None:
        return Finding("tps_voltage_redundancy", "TPS dual-track sanity",
                       "skipped", None, "Insufficient overlap.")
    r, _ = res
    if r >= 0.98:
        sev = "pass"; msg = f"TPS main/sub r = {r:.3f} \u2014 perfectly redundant."
    elif r >= 0.90:
        sev = "warn"; msg = f"TPS main/sub r = {r:.3f} \u2014 some divergence; clean / check connector."
    else:
        sev = "alarm"; msg = f"TPS main/sub r = {r:.3f} \u2014 redundancy broken; ECU limp risk."
    return Finding("tps_voltage_redundancy", "TPS dual-track sanity",
                   sev, r, msg)


def chk_pedal_voltage_redundancy(ctx: CheckCtx) -> Finding:
    """Same logic for the accelerator pedal sensor pair."""
    a = ctx.log.col("pedal_main_v")
    b = ctx.log.col("pedal_sub_v")
    if a is None or b is None:
        return Finding("pedal_voltage_redundancy", "Pedal dual-track sanity",
                       "skipped", None, "Pedal main/sub voltages not in log.")
    res = _track_voltages(a, b)
    if res is None:
        return Finding("pedal_voltage_redundancy", "Pedal dual-track sanity",
                       "skipped", None, "Insufficient overlap.")
    r, _ = res
    if r >= 0.98:
        sev = "pass"; msg = f"Pedal main/sub r = {r:.3f} \u2014 redundant."
    elif r >= 0.90:
        sev = "warn"; msg = f"Pedal main/sub r = {r:.3f} \u2014 mild divergence."
    else:
        sev = "alarm"; msg = f"Pedal main/sub r = {r:.3f} \u2014 redundancy broken; expect P2138 family."
    return Finding("pedal_voltage_redundancy", "Pedal dual-track sanity",
                   sev, r, msg)


def chk_maf_voltage_consistency(ctx: CheckCtx) -> Finding:
    """MAF sensor voltage and MAF g/s come from the same physical sensor; the
    ECU just applies a transfer table. Their correlation should be ~1.0; if
    not, one of the channels is being computed incorrectly (firmware quirk
    or table mismatch). Useful as a sanity probe.
    """
    a = ctx.log.col("maf_v")
    b = ctx.log.col("maf_gs")
    if a is None or b is None:
        return Finding("maf_voltage_consistency", "MAF voltage / mass agreement",
                       "skipped", None, "MAF voltage or mass channel missing.")
    res = _track_voltages(a, b)
    if res is None:
        return Finding("maf_voltage_consistency", "MAF voltage / mass agreement",
                       "skipped", None, "Insufficient overlap.")
    r, _ = res
    if r >= 0.95:
        sev = "pass"; msg = f"MAF V vs MAF g/s r = {r:.3f} \u2014 consistent."
    else:
        sev = "warn"
        msg = (f"MAF voltage and MAF g/s correlate r = {r:.3f}. "
               "Either firmware filter divergence or sensor scaling issue.")
    return Finding("maf_voltage_consistency", "MAF voltage / mass agreement",
                   sev, r, msg)


def chk_o2_pre_health(ctx: CheckCtx) -> Finding:
    """Pre-cat wideband sensor: in cruise the heater current should be steady
    (around mid-range) and resistance reasonable. Drift here precedes lambda
    oscillation. We just check that they exist and are not pegged.
    """
    cur = ctx.log.col("o2_pre_i")
    res = ctx.log.col("o2_pre_r")
    if cur is None or res is None:
        return Finding("o2_pre_health", "Pre-cat O2 health",
                       "skipped", None, "Pre-cat current/resistance not in log.")
    cur_vals = [x for x in cur if x is not None]
    res_vals = [x for x in res if x is not None]
    if len(cur_vals) < 100 or len(res_vals) < 100:
        return Finding("o2_pre_health", "Pre-cat O2 health",
                       "skipped", None, "Too few samples.")
    cur_med = statistics.median(cur_vals)
    res_med = statistics.median(res_vals)
    cur_std = statistics.pstdev(cur_vals)
    # No hard EJ253 spec available; use plausibility bands.
    sev = "pass"
    notes = []
    if cur_std > abs(cur_med) * 0.6 and abs(cur_med) > 0.05:
        sev = "warn"; notes.append("heater current is volatile")
    if res_med > 30:
        sev = "warn"; notes.append(f"resistance high ({res_med:.0f} Ω) \u2014 sensor aging?")
    msg = (f"Pre-cat O2: current median {cur_med:.2f} mA (std {cur_std:.2f}), "
           f"resistance median {res_med:.1f} Ω. " + ("; ".join(notes) if notes else "Looks healthy."))
    return Finding("o2_pre_health", "Pre-cat O2 health", sev, res_med, msg,
                   evidence={"cur_med": cur_med, "cur_std": cur_std, "res_med": res_med})


def chk_battery_charging(ctx: CheckCtx) -> Finding:
    """Alternator should hold 13.8-14.6 V under driving. Below 13.5 V sustained
    => alternator weak / drive belt slipping / regulator issue.
    """
    bat = ctx.log.col("battery")
    if bat is None:
        return Finding("battery_charging", "Battery / alternator",
                       "skipped", None, "No battery channel.")
    drive_phases = (PHASE_CRUISE, PHASE_PART_LOAD, PHASE_WOT)
    samples = [bat[i] for i in range(ctx.log.rows)
               if ctx.phases[i] in drive_phases and bat[i] is not None]
    if len(samples) < 100:
        return Finding("battery_charging", "Battery / alternator",
                       "skipped", None, "Too few loaded samples.")
    median = statistics.median(samples)
    minimum = min(samples)
    if median >= 13.8 and minimum >= 13.0:
        sev = "pass"
        msg = f"Battery median {median:.2f} V (min {minimum:.2f}) under load \u2014 charging system OK."
    elif median >= 13.3:
        sev = "warn"
        msg = f"Battery median {median:.2f} V \u2014 alternator output is low; check belt and regulator."
    else:
        sev = "alarm"
        msg = f"Battery median {median:.2f} V under load \u2014 charging system not keeping up."
    return Finding("battery_charging", "Battery / alternator",
                   sev, median, msg, evidence={"median": median, "min": minimum})


# ---------- Tier 6 (EVAP / emissions) ----------

def chk_evap_pressure_event(ctx: CheckCtx) -> Finding:
    """Was an EVAP pressure deflection captured? Useful to know whether a
    P0457-class fault could have manifested in this log window.
    """
    ftp = ctx.log.col("fuel_tank_p")
    if ftp is None:
        return Finding("evap_pressure_event", "EVAP pressure event",
                       "skipped", None, "No EVAP tank pressure channel.")
    samples = [x for x in ftp if x is not None]
    if not samples:
        return Finding("evap_pressure_event", "EVAP pressure event",
                       "skipped", None, "No EVAP samples.")
    excursion_lo = sum(1 for x in samples if x < -1.5)
    excursion_hi = sum(1 for x in samples if x > 1.5)
    rng = max(samples) - min(samples)
    if excursion_lo + excursion_hi == 0:
        sev = "info"
        msg = (f"FTPS quiet (range {rng:.2f} kPa). No EVAP pressure event captured. "
               "If P0457 occurs intermittently, log a longer highway run including the alarm.")
    elif excursion_lo > 5 or excursion_hi > 5:
        sev = "warn"
        msg = (f"FTPS shows {excursion_lo} samples < -1.5 kPa and {excursion_hi} > +1.5 kPa. "
               "Possible EVAP leak, stuck purge valve, or vibration affecting the sensor.")
    else:
        sev = "info"
        msg = f"FTPS minor excursions ({excursion_lo} low + {excursion_hi} high), within tolerance."
    return Finding("evap_pressure_event", "EVAP pressure event",
                   sev, rng, msg, evidence={"range_kpa": rng,
                                            "low_excursions": excursion_lo,
                                            "high_excursions": excursion_hi})


def chk_post_cat_o2(ctx: CheckCtx) -> Finding:
    """Post-cat O2 sensor (narrowband or rich/lean signal). For a healthy cat,
    it should oscillate slowly (<<1 Hz) and stay near the lean side of stoich
    most of the time.
    """
    sw = ctx.log.bool_col("o2_post_rich")
    v = ctx.log.col("o2_post")
    if sw is None and v is None:
        return Finding("post_cat_o2", "Post-cat O2 / cat efficiency",
                       "skipped", None, "No post-cat O2 channel.")
    if sw is not None:
        on = sum(1 for x in sw if x is True)
        off = sum(1 for x in sw if x is False)
        total = on + off
        if total < 50:
            return Finding("post_cat_o2", "Post-cat O2 / cat efficiency",
                           "skipped", None, "Too few post-cat samples.")
        on_pct = round(100 * on / total, 1)
        if 5 <= on_pct <= 50:
            sev = "pass"
            msg = f"Post-cat rich signal active {on_pct}% \u2014 catalyst working."
        elif on_pct > 70:
            sev = "warn"
            msg = f"Post-cat rich signal active {on_pct}% \u2014 catalyst may be saturating (degraded)."
        else:
            sev = "info"
            msg = f"Post-cat rich signal active {on_pct}% \u2014 lean-leaning, often normal."
        return Finding("post_cat_o2", "Post-cat O2 / cat efficiency",
                       sev, on_pct, msg, evidence={"on_pct": on_pct})
    return Finding("post_cat_o2", "Post-cat O2 / cat efficiency",
                   "skipped", None, "Only narrowband voltage available; need richer analysis.")


CHECKS_TIER1: list[Check] = [
    Check("idle_ltft_static",     "Idle LTFT (warm)",         1, ("petrol", "lpg"), chk_idle_ltft_static),
    Check("cruise_ltft_static",   "Cruise LTFT (warm)",       1, ("petrol", "lpg"), chk_cruise_ltft_static),
    Check("ltft_load_dependency", "LTFT load dependency",     1, ("petrol", "lpg"), chk_ltft_load_dependency),
    Check("stft_volatility",      "STFT volatility (cruise)", 1, ("petrol", "lpg"), chk_stft_volatility),
    Check("lambda_stoich_tracking","Lambda CL tracking",      1, ("petrol", "lpg"), chk_lambda_stoich_tracking),
    Check("power_enrichment",     "Power enrichment (WOT)",   1, ("petrol", "lpg"), chk_power_enrichment),
    Check("wot_fuel_delivery",    "WOT fuel delivery",        1, ("petrol", "lpg"), chk_wot_fuel_delivery),
    Check("dfco_present",         "DFCO detection",           1, ("petrol", "lpg"), chk_dfco_present),
    Check("idle_rpm_stability",   "Idle RPM stability",       1, ("petrol", "lpg"), chk_idle_rpm_stability),
]

CHECKS_TIER2: list[Check] = [
    Check("maf_idle_value",       "MAF at warm idle",         2, ("petrol", "lpg"), chk_maf_idle_value),
    Check("vacuum_at_idle",       "Manifold vacuum at idle",  2, ("petrol", "lpg"), chk_map_rel_idle),
    Check("iat_plausibility",     "IAT plausibility",         2, ("petrol", "lpg"), chk_iat_plausibility),
    Check("maf_map_correlation",  "MAF / MAP correlation",    2, ("petrol", "lpg"), chk_maf_map_correlation),
]

CHECKS_TIER3: list[Check] = [
    Check("knock_active_retard",  "Active knock retard",      3, ("petrol", "lpg"), chk_knock_active_retard),
    Check("knock_learn_advance",  "Learned knock advance",    3, ("petrol", "lpg"), chk_knock_learn_advance),
    Check("timing_warmup",        "Timing during warmup",     3, ("petrol", "lpg"), chk_timing_warmup),
]

CHECKS_TIER4: list[Check] = [
    Check("coolant_warmup_rate",  "Coolant warmup rate",      4, ("petrol", "lpg"), chk_coolant_warmup_rate),
    Check("oil_temp_lag",         "Oil vs coolant lag",       4, ("petrol", "lpg"), chk_oil_temp_lag),
]

CHECKS_TIER5: list[Check] = [
    Check("tps_voltage_redundancy",   "TPS dual-track sanity",   5, ("petrol", "lpg"), chk_tps_voltage_redundancy),
    Check("pedal_voltage_redundancy", "Pedal dual-track sanity", 5, ("petrol", "lpg"), chk_pedal_voltage_redundancy),
    Check("maf_voltage_consistency",  "MAF V/g/s agreement",     5, ("petrol", "lpg"), chk_maf_voltage_consistency),
    Check("o2_pre_health",            "Pre-cat O2 health",       5, ("petrol", "lpg"), chk_o2_pre_health),
    Check("battery_charging",         "Battery / alternator",    5, ("petrol", "lpg"), chk_battery_charging),
]

CHECKS_TIER6: list[Check] = [
    Check("evap_pressure_event", "EVAP pressure event",      6, ("petrol", "lpg"), chk_evap_pressure_event),
    Check("post_cat_o2",         "Post-cat O2",              6, ("petrol", "lpg"), chk_post_cat_o2),
]

ALL_CHECKS: list[Check] = (CHECKS_TIER1 + CHECKS_TIER2 + CHECKS_TIER3
                           + CHECKS_TIER4 + CHECKS_TIER5 + CHECKS_TIER6)


def run_checks(log: ParsedLog, phases: list[str], summary: dict[str, Any],
               fuel_type: str) -> list[Finding]:
    ctx = CheckCtx(log=log, phases=phases, summary=summary, fuel_type=fuel_type)
    out: list[Finding] = []
    for chk in ALL_CHECKS:
        if fuel_type != "unknown" and fuel_type not in chk.fuel_types:
            continue
        try:
            f = chk.fn(ctx)
        except Exception as exc:  # noqa: BLE001 - never let one check kill the run
            f = Finding(chk.id, chk.title, "skipped", None,
                        f"Check failed: {exc!r}")
        # Tag with tier so the report can group findings by section.
        f.evidence.setdefault("tier", chk.tier)
        out.append(f)
    return out


# ============================================================================
# Section 7 — Top-level summary builder
# ============================================================================

def summarize(log: ParsedLog, fuel_type: str) -> dict[str, Any]:
    phases = classify_phases(log)
    summary: dict[str, Any] = {
        "file": log.path,
        "fuel_type": fuel_type,
        "duration_s": round(log.duration_s, 1),
        "duration_min": round(log.duration_s / 60, 2),
        "samples": log.rows,
        "sample_rate_hz": round(log.rows / log.duration_s, 2) if log.duration_s > 0 else 0,
        "missing_key_sensors": [k for k, v in log.key_idx.items() if v is None],
        "phase_distribution": dict(Counter(phases)),
        "per_phase": per_phase_stats(log, phases),
        "rpm_load_map": {
            "ltft_b1": rpm_load_map(log, "ltft_b1", exclude_phases=(PHASE_OVERRUN_DFCO,)),
            "stft_b1": rpm_load_map(log, "stft_b1", exclude_phases=(PHASE_OVERRUN_DFCO,)),
            "lambda":  rpm_load_map(log, "lambda",  exclude_phases=(PHASE_OVERRUN_DFCO,)),
            "knock":   rpm_load_map(log, "knock"),
            "maf_gs":  rpm_load_map(log, "maf_gs"),
        },
        "fuel_trim_drift": fuel_trim_drift(log),
        "events": detect_events(log, phases),
        "boolean_switches": boolean_summary(log),
    }
    findings = run_checks(log, phases, summary, fuel_type)
    summary["findings"] = [
        {"check_id": f.check_id, "title": f.title, "severity": f.severity,
         "value": f.value, "explanation": f.explanation, "evidence": f.evidence}
        for f in findings
    ]
    sev_rank = {"alarm": 0, "warn": 1, "info": 2, "pass": 3, "skipped": 4}
    summary["health_score"] = _health_score(findings)
    summary["findings"].sort(key=lambda x: sev_rank.get(x["severity"], 5))
    return summary


def _health_score(findings: list[Finding]) -> int:
    """0..100. Each alarm -25, each warn -10, each info -2."""
    score = 100
    for f in findings:
        if f.severity == "alarm":
            score -= 25
        elif f.severity == "warn":
            score -= 10
        elif f.severity == "info":
            score -= 2
    return max(0, score)


# ============================================================================
# Section 8 — Report formatting
# ============================================================================

SEV_BADGE = {"alarm": "[ALARM]", "warn": "[WARN]", "info": "[INFO]",
             "pass": "[PASS]", "skipped": "[SKIP]"}


def format_md(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    a = lines.append

    a("# FreeSSM Log Analysis Report")
    a("")
    a(f"**File:** `{summary['file']}`  ")
    a(f"**Fuel type:** {summary['fuel_type']}  ")
    a(f"**Duration:** {summary['duration_min']} min "
      f"({summary['samples']} samples @ {summary['sample_rate_hz']} Hz)  ")
    a(f"**Health score:** **{summary['health_score']}/100**")
    a("")

    if summary["missing_key_sensors"]:
        a("> Missing/unmapped sensors: " + ", ".join(summary["missing_key_sensors"]))
        a("")

    # Findings grouped by tier; within each tier sorted by severity.
    a("## Findings")
    sev_rank = {"alarm": 0, "warn": 1, "info": 2, "pass": 3, "skipped": 4}
    tier_titles = {
        1: "Tier 1 — Fuel trims & lambda",
        2: "Tier 2 — Air system",
        3: "Tier 3 — Ignition & knock",
        4: "Tier 4 — Cooling & temperatures",
        5: "Tier 5 — Sensor sanity & redundancy",
        6: "Tier 6 — EVAP & emissions",
    }
    by_tier: dict[int, list[dict[str, Any]]] = {}
    for f in summary["findings"]:
        t = (f.get("evidence") or {}).get("tier", 1)
        by_tier.setdefault(t, []).append(f)
    for t in sorted(by_tier):
        a(f"### {tier_titles.get(t, f'Tier {t}')}")
        a("| Severity | Check | Value | Explanation |")
        a("|---|---|---:|---|")
        rows = sorted(by_tier[t], key=lambda x: sev_rank.get(x["severity"], 5))
        for f in rows:
            sev = SEV_BADGE.get(f["severity"], f["severity"])
            v = f["value"]
            v_str = f"{v:+.2f}" if isinstance(v, float) else (str(v) if v is not None else "-")
            line = f["explanation"].replace("\n", " ").strip()
            a(f"| {sev} | {f['title']} | {v_str} | {line} |")
        a("")

    # Phase distribution
    a("## Engine phase distribution")
    a("| Phase | Samples | Share |")
    a("|---|---:|---:|")
    total = summary["samples"]
    for phase in PHASE_ORDER:
        n = summary["phase_distribution"].get(phase, 0)
        if n == 0:
            continue
        a(f"| {phase} | {n} | {100*n/total:.1f}% |")
    a("")

    # Per-phase stats
    a("## Per-phase statistics (key sensors)")
    for phase in PHASE_ORDER:
        p = summary["per_phase"].get(phase)
        if not p or phase in (PHASE_OFF, PHASE_UNKNOWN):
            continue
        a(f"### {phase} ({p.get('share_pct', 0)}% — {p.get('samples', 0)} samples)")
        a("| Sensor | min | p05 | median | mean | p95 | max | std |")
        a("|---|---:|---:|---:|---:|---:|---:|---:|")
        for k, v in p.items():
            if not isinstance(v, dict):
                continue
            a(f"| {k} | {v['min']} | {v['p05']} | {v['median']} | {v['mean']} | "
              f"{v['p95']} | {v['max']} | {v['std']} |")
        a("")

    # Fuel trim drift
    a("## Fuel trim drift (head vs tail)")
    a("| Sensor | head mean | tail mean | drift |")
    a("|---|---:|---:|---:|")
    for k, v in summary["fuel_trim_drift"].items():
        a(f"| {k} | {v['head_mean']} | {v['tail_mean']} | {v['drift']:+} |")
    a("")

    # RPM x Load maps
    for label, key in [("LTFT B1", "ltft_b1"), ("Lambda", "lambda"),
                       ("Knock correction", "knock")]:
        m = summary["rpm_load_map"].get(key, {})
        if not m:
            continue
        a(f"## RPM x Load map ({label})")
        a("| Cell | mean | median | n |")
        a("|---|---:|---:|---:|")
        for cell, v in m.items():
            a(f"| {cell} | {v['mean']} | {v['median']} | {v['n']} |")
        a("")

    # Events
    events = summary["events"]
    a(f"## Events ({len(events)})")
    if not events:
        a("No flagged events.")
    else:
        for ev in events[:50]:
            t = ev.get("type")
            if "t_start" in ev:
                a(f"- **{t}** @ {ev['t_start']}-{ev['t_end']}s "
                  f"({ev.get('duration_s', 0)}s, {ev.get('samples', 0)} smp, "
                  f"phase={ev.get('phase', '?')})")
            else:
                extras = " ".join(f"{k}={v}" for k, v in ev.items() if k != "type")
                a(f"- **{t}** {extras}")
        if len(events) > 50:
            a(f"- ... and {len(events) - 50} more")
    a("")

    # Toggling switches
    toggling = {n: v for n, v in summary["boolean_switches"].items()
                if v["class"] == "toggling"}
    if toggling:
        a("## Toggling switches")
        a("| Switch | On % | Transitions |")
        a("|---|---:|---:|")
        for name, v in sorted(toggling.items(), key=lambda x: -x[1]["transitions"]):
            a(f"| {name} | {v['on_pct']} | {v['transitions']} |")
        a("")

    return "\n".join(lines)


# ============================================================================
# Section 9 — CLI
# ============================================================================

def main(argv: list[str]) -> int:
    # Force UTF-8 stdout so we can print Greek letters and arrows on Windows.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    p = argparse.ArgumentParser(description="FreeSSM CSV log analyzer")
    p.add_argument("csv", type=Path, help="Path to FreeSSM CSV log")
    p.add_argument("--fuel", choices=["petrol", "lpg", "unknown"],
                   default="unknown",
                   help="Fuel type during the recorded run (default: unknown)")
    p.add_argument("--out-dir", type=Path, default=None,
                   help="Output directory (default: same as input file)")
    args = p.parse_args(argv[1:])

    if not args.csv.exists():
        print(f"File not found: {args.csv}", file=sys.stderr)
        return 1

    log = load_csv(args.csv)
    summary = summarize(log, fuel_type=args.fuel)

    out_dir = args.out_dir if args.out_dir else args.csv.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.csv.stem

    md_path = out_dir / f"{stem}.report.md"
    json_path = out_dir / f"{stem}.summary.json"

    md_path.write_text(format_md(summary), encoding="utf-8")
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                         encoding="utf-8")

    print(f"Wrote {md_path}")
    print(f"Wrote {json_path}")
    print(f"Health score: {summary['health_score']}/100")

    # Console summary
    findings = summary["findings"]
    alarms = [f for f in findings if f["severity"] == "alarm"]
    warns = [f for f in findings if f["severity"] == "warn"]
    print(f"Findings: {len(alarms)} alarm, {len(warns)} warn, "
          f"{len([f for f in findings if f['severity'] == 'pass'])} pass, "
          f"{len([f for f in findings if f['severity'] == 'skipped'])} skipped")
    for f in alarms + warns:
        print(f"  {SEV_BADGE.get(f['severity'])} {f['title']}: "
              f"{f['explanation'].splitlines()[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
