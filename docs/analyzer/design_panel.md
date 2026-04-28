# FreeSSM Analyzer — Expert Panel Design Discussion

**Date:** 2026-04-26
**Status:** Reference document — captured 1:1 from expert panel discussion.
**Scope:** Design and architecture of the post-FreeSSM CSV log analyzer
(working name: `freessm-analyzer`, project nickname: "FreeSSM Reboot").

This document is the source-of-truth for the analyzer's analytical engine.
While the production app will eventually live in a separate repository
with a Docker/React/FastAPI stack, the analytical core is being prototyped
in this repository (`tools/log-analyzer/`) using the user's real driving
data as the test bench.

---

## Panel composition

| Persona | Role | Specialization |
|---|---|---|
| **Coda** | Lead Systems Engineer & ML Architect | Architecture, code, infra |
| **Dr Marek Kowalski** | Engine Calibration & OBD Specialist | 12y Bosch Motorsport + 8y Subaru/Mitsubishi tuning UK. SSM1/SSM2/OBD-II, EJ20/EJ25/FA20 maps, fuel trim diagnostics, misfire root-cause. Philosophy: *"data without context lies"* — sensors only mean something within a defined operating regime. |
| **Inż. Tomasz Wawrzyniak** | LPG / Dual-Fuel Systems Engineer | 15y LPG workshop (Lovato, BRC, Stag), AC AutoGas certified. Hundreds of dual-fuel diagnoses. Philosophy: *"LPG always lies to the ECU — the question is how much and how"*. |
| **Lux** | Brand & UX Architect | UI, visualization, charting, branding, accessibility. |
| **Michał** | Product Owner | Domain expert, billing background, owner of the test vehicle. |

Prof. Watts (energy markets) — not relevant for this discussion.

---

## Part 1 — Application architecture (Coda)

### Stack — final recommendation

| Layer | Technology | Rationale |
|---|---|---|
| Backend | **Python 3.11 + FastAPI** | Async, OpenAPI auto-gen, ecosystem (pandas/numpy/scipy/scikit) |
| Workers | **Celery + Redis** or **RQ** | Analysis of large CSVs (50k+ rows) cannot block the request |
| DB | **PostgreSQL + TimescaleDB** | Same as `energy-costs-platform` — known infra. Logs are time-series. |
| ORM | **SQLAlchemy 2.0** + Alembic | Standard. |
| Frontend | **React 18 + TypeScript + Vite** | Vite for speed over CRA. |
| Charting | **Apache ECharts** | Native brushing/zoom/sync, good for 50k+ points |
| Styling | **Tailwind + shadcn/ui** | Convention with other Michał projects |
| LLM | **OpenAI API + Anthropic API** with fallback | User picks provider in settings |
| Auth | **OAuth (Google/GitHub)** + local session | Free tier anonymous-limited, signed-in = full |
| Deploy | **Docker Compose + Portainer** | Same as homelab |
| Storage CSV | **MinIO** (S3 compatible) or volume | Raw CSVs not worth pushing into PG |

### Does the DB make sense?

**YES, but not for raw CSV samples.** DB stores:

- Upload metadata (who, when, vehicle, fuel, length, hash)
- Analysis results (aggregate tables: fuel trim maps, event timelines)
- User accounts + tier (free/coffee/pro)
- History for comparisons (log A vs log B — idle LTFT before/after repair)
- LLM prompt cache ($ savings)

**Raw CSV → MinIO. Down-sampled series → TSDB.** Pushing 1772 rows × 90 cols × 100 logs = 16M rows. TSDB is built for this.

### Container topology

```
┌─────────────────────────────────────────┐
│  Frontend (React/Nginx)  :3000          │
└────────────┬────────────────────────────┘
             │ /api
┌────────────▼────────────────────────────┐
│  Backend (FastAPI)       :8000          │
└──┬──────┬──────┬───────────────────────┘
   │      │      │
   ▼      ▼      ▼
┌────┐ ┌─────┐ ┌──────────────┐
│PG  │ │Redis│ │MinIO (S3)    │
│TSDB│ │     │ │raw CSV files │
└────┘ └──┬──┘ └──────────────┘
          │
   ┌──────▼────────┐
   │  Worker       │
   │  (Celery/RQ)  │ → analyzer engine
   └───────────────┘
```

### Folder structure (target repo)

```
fssm-analyzer/                # separate repo (later)
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── core/             # config, auth, deps
│   │   ├── analyzer/         # ❶ THE BRAIN (built in current repo first)
│   │   │   ├── parsers/      # CSV → canonical schema
│   │   │   ├── phases/       # state classifier
│   │   │   ├── checks/       # diagnostic checks (rules, YAML/JSON-driven)
│   │   │   ├── reports/      # build report JSON
│   │   │   └── llm/          # prompt assembly + provider abstraction
│   │   ├── db/
│   │   ├── workers/
│   │   └── main.py
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── charts/
│   │   └── api/
│   └── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
└── README.md
```

**Decision:** Production lives in separate repo `fssm-analyzer`. Analytical
core is prototyped in `freessm/tools/log-analyzer/` against Michał's real
data, then migrated when stable. Reasons: different stack, different
lifecycle, different contributor pool.

---

## Part 2 — What and when to analyse (Marek + Tomasz)

### Cardinal principle (Marek)

> *Data without context lies.* Every log decomposes into **operational
> phases** and **each sensor only makes sense in some of them**. This is
> the essence of "context-aware analysis".

### Canonical engine phase state machine

```
┌───────────┐      ┌─────────┐      ┌───────────┐
│COLD_START │──────│WARMUP   │──────│CLOSED_LOOP│
│ ECT<40°C  │      │40-75°C  │      │  ECT≥75°C │
└───────────┘      └─────────┘      └─────┬─────┘
                                          │
                ┌─────────────────────────┼─────────────────────────┐
                │                         │                         │
           ┌────▼────┐  ┌────────┐  ┌────▼─────┐  ┌────────┐  ┌────▼────┐
           │  IDLE   │  │CRUISE  │  │PART_LOAD │  │WOT     │  │OVERRUN  │
           │RPM<1100 │  │stable  │  │30-70%    │  │tps>80% │  │tps<3    │
           │load<20  │  │vss>10  │  │load      │  │load>80 │  │rpm>1500 │
           └─────────┘  └────────┘  └──────────┘  └────────┘  └─────────┘
                                          │
                                    ┌────▼────────┐
                                    │TRANSITIONS  │
                                    │• ACCEL_TIP-IN│
                                    │• DECEL_TIP-OUT│
                                    │• DFCO entry/exit│
                                    │• PE entry (power enrich)│
                                    └─────────────┘

Special: KEY_ON_ENGINE_OFF, CRANKING, STALL_RECOVERY
```

The previous analyzer prototype used 5 states (idle/cruise/accel/decel/off).
**This is too primitive** — diagnostically the difference between WARMUP and
CLOSED_LOOP is critical (fuel trims aren't active in WARMUP).

### Check schema (YAML/JSON declarative)

Each diagnostic check is **configured by phase + required sensors + rule + result**:

```yaml
# checks/idle_ltft_negative.yaml
id: idle_ltft_negative
name: "Negative LTFT at idle"
applies_to:
  phases: [IDLE]
  min_phase_duration_s: 30
  min_samples: 50
required_sensors: [rpm, load, ect, ltft_b1]
preconditions:
  ect_min: 75
  vss_max: 5
rule:
  metric: median(ltft_b1)
  threshold:
    pass: [-5, +5]
    warn: [-8, -5] U [+5, +8]
    alarm: [-Inf, -8] U [+8, +Inf]
explanation:
  alarm_low: |
    LTFT median {value}% at idle indicates the ECU constantly
    subtracts fuel. Common causes: leaking injectors, high fuel
    pressure (vacuum hose off FPR), LPG injector seepage in dual-fuel.
  alarm_high: |
    LTFT median {value}% at idle indicates ECU adds fuel. Common
    causes: vacuum leak (intake/PCV/brake booster), weak fuel
    pressure, dirty MAF, exhaust leak before O2.
```

**Each check is a file, not code.** Checks are user-contributable.

### Check inventory v1 (priority-ordered)

**Tier 1 — Fuel system (most diagnostic):**

| ID | Description |
|---|---|
| `idle_ltft_static` | LTFT median in IDLE warm |
| `cruise_ltft_static` | LTFT median in CRUISE warm |
| `ltft_load_dependency` | LTFT vs Load slope (vacuum-leak diagnostic) |
| `ltft_rpm_dependency` | LTFT vs RPM slope (injector vs MAF differentiation) |
| `stft_volatility` | std(STFT) per phase (closed-loop control quality) |
| `lambda_stoich_tracking` | % time |λ−1.00| > 0.02 in CL warm |
| `power_enrichment_check` | λ at WOT (target 0.80–0.88) |
| `dfco_detection` | proper DFCO entry+exit |

**Tier 2 — Air system:**

| ID | Description |
|---|---|
| `maf_idle_value` | MAF g/s at warm idle vs expected (e.g. 2.5–3.5 for H4 2.5L) |
| `maf_vs_map_correlation` | sanity check (both should track load) |
| `iat_plausibility` | IAT within ambient + heat soak budget |
| `idle_air_control` | RPM stability during idle (std RPM) |

**Tier 3 — Ignition:**

| ID | Description |
|---|---|
| `knock_retard_events` | sustained negative knock correction |
| `knock_learn_positive` | high learned advance (octane indicator, LPG signal) |
| `timing_under_load` | ignition timing curve vs RPM/Load expected window |

**Tier 4 — Temperatures & cooling:**

| ID | Description |
|---|---|
| `coolant_warmup_rate` | °C/min during warmup phase |
| `coolant_steady_temp` | ECT median in CRUISE |
| `oil_temp_lag` | oil follows coolant with proper lag |

**Tier 5 — EVAP & emissions:**

| ID | Description |
|---|---|
| `evap_pressure_test_seen` | was a pressure event detected during the log |
| `evap_purge_active_periods` | time CPC duty > 0 |
| `post_cat_o2_static` | post-cat oscillation amplitude (cat efficiency proxy) |

**Tier 6 — Electrical:**

| ID | Description |
|---|---|
| `battery_voltage_idle` | vbat at idle (alternator load sanity) |
| `battery_voltage_cranking` | voltage drop on cranking |

**Tier 7 — Transients (hardest, but unique selling point):**

| ID | Description |
|---|---|
| `tip_in_enrichment` | STFT response on accel tip-in |
| `tip_out_recovery` | STFT/lambda recovery after decel |
| `dfco_restoration_quality` | overshoot magnitude when fuel restored |

Total: **26 checks**. v1 ships Tier 1+2+3 (15 checks); Tier 4–7 added iteratively.

### LPG-specific layer (Tomasz)

LPG is an **overlay on the petrol ECU** — 90% of diagnostics are identical,
but key differences exist.

**How does the ECU know it's running LPG?** Short answer: **it doesn't.**
Aftermarket installs (Stag, BRC, Lovato) make the ECU see:

- its own petrol injectors closed (LPG controller intercepts the signal)
- its own lambda sensor — and if the lambda emulator doesn't substitute
  the signal, the ECU sees the real lambda from LPG combustion
- its own MAF — unchanged

Effect: ECU adapts LTFT based on **real AFR measured on the lambda sensor
during LPG operation**. So LTFT on LPG reflects **drift of the LPG reducer
/ injectors**, not the engine.

### LPG-Tier checks (require fuel_type marker)

| ID | What it checks | Why it matters |
|---|---|---|
| `lpg_ltft_offset_vs_petrol` | Δ median(LTFT) between LPG and petrol phases in same log | Scale of LPG-map inaccuracy |
| `lpg_idle_drift` | LTFT idle on LPG (standalone) | Reducer seepage, slightly leaking injectors |
| `lpg_load_response` | LTFT vs load **on LPG** | Is the LPG map correct under load? |
| `lpg_to_petrol_transition` | First 30s after switch to petrol — STFT swing | Petrol map "infected" by LPG adaptation? |
| `petrol_to_lpg_transition` | First 30s after switch to LPG — STFT swing | Reducer cold/warm response? |
| `lpg_knock_advance` | Knock learn on LPG (expect positive) | Lack = no octane benefit from LPG |
| `lpg_fuel_temp_warmup` | Fuel temp (if reducer reports it) | Reducer warmed by coolant? |

### Critical LPG facts the analyzer must know

1. **LPG installs typically have a "petrol-only zone"** — first N seconds after
   start always petrol (cold reducer). User reports "starts on petrol" is
   normal, not a problem.
2. **"LTFT infected by LPG"** — classic case. ECU has one LTFT table. Drive 6h
   on LPG, LTFT learns to add +12%. Switch to petrol — LTFT stays +12% for
   another quarter hour, engine floods on petrol. **This is exactly Michał's
   reported symptom of "petrol runs poorly before LPG kicks in".**
3. **P0457 + LPG**: LPG installs sometimes route around the fuel-cap path,
   but **vibration from the reducer and LPG pumps** can recalibrate the
   tank-pressure sensor. Unlikely but on the "uncommon causes" list.
4. **For diagnostics** we need not just `fuel_type ∈ {petrol, lpg}` marker
   but **events from the LPG system**: `lpg_active`, `transition_started`,
   `reducer_temp` (if controller exposes it). Out of scope for v1 — manual
   marker on upload is sufficient.

### Operational consequence for Coda

**Every check parameterized by fuel_type:**

```yaml
applies_to:
  phases: [IDLE]
  fuel_types: [petrol]   # or [lpg], or [petrol, lpg]
```

And there must be **paired checks**: `idle_ltft_static_petrol` and
`idle_ltft_static_lpg` separately, because thresholds differ. Petrol idle
LTFT ±5%, LPG idle LTFT ±10% is normal.

---

## Part 3 — UX / charts / data presentation (Lux)

### 3-second comprehension principle

User uploads CSV → first screen after analysis must show:

```
┌─────────────────────────────────────────────────────────────┐
│  Subaru Forester • LPG run • 17.8 min • 2026-04-12          │
│                                                             │
│  HEALTH SCORE: 78/100   ●●●●●●●○○○                         │
│                                                             │
│  ▼ 2 ALARMS    ▼ 5 WARNINGS    ✓ 18 PASSED                  │
│                                                             │
│  Top finding:                                               │
│  → Negative LTFT at idle (-6.3%, alarm).                    │
│    Likely: leaking LPG injector, FPR vacuum hose,           │
│             or warm-fuel injector seepage.                  │
│                                                             │
│  [View detailed report]  [Ask AI about this]  [Compare]     │
└─────────────────────────────────────────────────────────────┘
```

NOT a 26-row table of numbers. **3 seconds to understand the car's state.**

### Layout (5 views)

1. **Dashboard** — landing post-upload. Health score, top 3 findings,
   sparklines of key sensors (RPM/LTFT/Lambda).
2. **Phase Timeline** — *the strength of the app*. Audacity-style timeline:

   ```
   ────█████ COLD_START ████ WARMUP ███████████████ CLOSED_LOOP ████████
        0:00    2:30           5:15                                17:48
   ```

   Below: synchronized charts (brushing) — RPM, Load, LTFT, Lambda, ECT.
   Click on a phase → shows that phase's stats. **ECharts has this built-in
   (`dataZoom`).**
3. **Diagnostic Report** — all 26 checks grouped (Fuel/Air/Ignition/...),
   each with color (green/yellow/red), expand → shows `explanation` text +
   relevant chart fragment.
4. **RPM × Load Maps** — heatmaps. One per LTFT, lambda, knock, ignition
   timing. Cells with few samples shaded (confidence indicator).
5. **Compare** — two logs side-by-side. "Before/after repair", "LPG/petrol".
   Diff health scores, diff LTFT maps.
6. **AI Insights** (separate view) — "Ask AI" button, but the **prompt is
   curated**: we don't send raw CSV, we send summary JSON + user question.
   User receives structured response.

### Charts — chosen library

**ECharts > Recharts > Plotly for our case:**

- **ECharts**: brushing, sync, 100k points smooth, native time-axis, events
  (markline/markarea for phases). Apache 2.0.
- **Plotly**: pretty but heavy, weak with 50k+ realtime points.
- **Recharts**: simpler but no native brushing.

**Key:** brush + zoom + multi-pane sync. User must be able to highlight 30s
on the time axis and see how all sensors behaved in that window. ECharts
gives this for free.

### Branding

- Working name: **OBDLens** / **SubaruScope** / **DriveDiag** — Michał decides.
  *(Update from Michał: working name is `freessm-analyzer`, project
  nicknamed "FreeSSM Reboot".)*
- Palette: dark mode + signal colors (red alarm / amber warn / emerald pass).
  Automotive professional, not corporate startup.
- Logo: simple wordmark, monogram in a hexagon (automotive vibe, not kitsch).
- Typography: Inter (UI) + JetBrains Mono (sensor values, log timestamps).

### Monetization UX

**Free tier:**
- Upload up to 3 logs / month, 7-day retention
- All checks (Tier 1–3, 15 checks)
- No AI insights
- No compare

**Coffee tier (€3/mo or €15/yr one-off via Buy-Me-a-Coffee membership):**
- Unlimited uploads, 90-day retention
- All checks (Tier 1–7)
- AI insights — 20/mo (OpenAI cap)
- Compare logs

**Pro tier (€10/mo):**
- 365-day retention
- AI insights unlimited (rate-limited)
- PDF report export
- Garage profile (multiple vehicles, history per vehicle)

**Hard rule:** OpenAI/Anthropic per-request cost. AI insights need a
**budget**. One insight = max 4k tokens of context (curated summary, not raw
data) + 1k tokens response. ~$0.05/request at GPT-4o. Coffee tier
20×$0.05 = $1, OK margin at €3. **This must be designed in from the start.**

---

## Part 4 — LLM integration (Coda)

### LLM prompt assembly pipeline

```
analysis_results (JSON, ~5kB)
        ↓
  context_filter()   ← user asks something specific, e.g. "idle LTFT"
        ↓
  promptlet_builder()  → picks fragments: relevant checks + relevant phase stats +
                         relevant timeseries snippet + reference ranges
        ↓
  prompt template
        ↓
  LLM (GPT-4o / Claude Sonnet 4.5)
        ↓
  structured response (JSON: {summary, hypotheses[], next_steps[], confidence})
        ↓
  UI rendering
```

### Prompt template (English, expert tone)

```
SYSTEM:
You are an expert ECU diagnostic engineer reviewing a Subaru SSM data log.
You have access to phase-segmented statistics, diagnostic check results,
and reference operating ranges. Provide structured analysis with hypotheses,
ranked by likelihood, with concrete next-step recommendations.

USER:
Vehicle: {make} {model} {year}, fuel: {fuel_type}
Run duration: {duration_min} min, phases: {phase_distribution}

User question: "{user_question}"

Diagnostic findings:
{filtered_checks_with_results}

Phase statistics:
{filtered_phase_stats}

Reference ranges and explanations:
{relevant_explanations}

Constraint: respond in JSON with fields:
- summary (1-2 sentences)
- hypotheses: list of {hypothesis, likelihood, evidence_from_log, contradicts}
- next_steps: list of {action, why, expected_observation}
- confidence (low/medium/high)
```

**Key:** `context_filter` runs in the Python backend, **not in the LLM**. LLM
gets a pre-filtered subset. This cuts cost 10× and improves accuracy 3×.

### Token budget per request (hard cap)

| Section | Max tokens |
|---|---:|
| System prompt | 300 |
| User context | 300 |
| Filtered checks (max 8 of 26) | 1200 |
| Filtered phase stats (max 3 of 5) | 800 |
| Reference explanations | 600 |
| User question | 200 |
| **Input total** | **~3400** |
| Response | ~1000 |
| **Total** | **~4400** |

GPT-4o: $0.01 prompt + $0.04 response = ~$0.05/insight.

### Why we don't send raw timeseries

2 samples/s × 17 min × 90 columns = 60,000 values. JSON-serialized ≈ 500kB ≈
200k tokens. That's $2/request at GPT-4o. Economically impossible.

Even if free — **the LLM cannot analyze 60k numbers**. It hallucinates.
Better not to try.

---

## Part 5 — Roadmap (target external repo timeline)

### Sprint 0 (1 week — prep)
- New repo `fssm-analyzer` on GitHub
- Branding decision (Lux delivers 3 options)
- `docker-compose.yml` (FastAPI + React stub + Postgres + Redis)
- CI/CD on GitHub Actions

### Sprint 1 (2 weeks — analyzer engine MVP) — **WE ARE HERE, in this repo**
- `analyzer/parsers/freessm_csv.py` — reads FreeSSM CSV (cp1252, `;`),
  normalizes to canonical schema
- `analyzer/phases/classifier.py` — phase state machine (8 phases)
- `analyzer/checks/` — Tier 1 (8 fuel checks)
- API endpoint `POST /api/analyses` (upload), `GET /api/analyses/{id}` (result)
- CLI `python -m analyzer logs/foo.csv` (offline use, dev)

### Sprint 2 (2 weeks — UI MVP)
- React + Vite scaffold
- Upload page → triggers analysis
- Dashboard view (health score, top findings)
- Diagnostic Report view (check list)
- Auth (Google OAuth)

### Sprint 3 (2 weeks — charts + phase timeline)
- ECharts integration
- Phase timeline view
- RPM × Load heatmap

### Sprint 4 (2 weeks — full check set + LPG)
- Tier 2–4 (air, ignition, temperature) — 13 additional checks
- LPG-Tier — 7 LPG-specific checks
- fuel_type marker — UI for user to manually mark log fragments

### Sprint 5 (2 weeks — LLM insights + monetization)
- LLM provider abstraction (OpenAI + Anthropic)
- Prompt assembly + token budgeting
- Buy-Me-a-Coffee → tier system
- Rate limiting per tier

### Sprint 6 (2 weeks — polish + launch)
- Compare logs
- PDF export
- Landing page (PL+EN)
- Forum announcements (subaruforester.org, klubsubaru.pl, NASIOC)

**Total: ~13 weeks to public MVP.**

---

## Part 6 — Decisions taken so far (Michał, 2026-04-26)

| # | Question | Decision |
|---|---|---|
| 1 | App name | **freessm-analyzer** (the broader project: "FreeSSM Reboot"); branding name TBD |
| 2 | Palette | dark default + light toggle (panel default) |
| 3 | Free tier limit | TBD — defer until monetization sprint |
| 4 | Auth provider | TBD |
| 5 | LLM provider primary | OpenAI GPT-4o (panel default) |
| 6 | Hosting | homelab → VPS later (panel default) |
| 7 | Repo public/private | TBD |
| 8 | License | TBD (panel suggests AGPL-3.0) |
| 9 | v1 supports only FreeSSM CSV? | **YES.** v2 = plug-in parsers |
| 10 | Michał's role | Product owner — Coda commits, Michał reviews |
| **A** | **fuel_type marker location** | **NOT in FreeSSM CSV. Selected at upload time in the analyzer UI.** |
| **B** | **Vehicle metadata in CSV** | **YES — add to FreeSSM CSV header (Michał approved)** |
| **C** | **Repo split timing** | **NOT NOW.** Build the analytical engine in this repo (`tools/log-analyzer/`) on Michał's real data. Migrate to separate repo when stable. |

### Critical FreeSSM side-quests (deferred)

These are **on hold** until the analytical engine matures:

1. **fuel_type marker in CSV** — *cancelled*. Will be a per-upload option in the analyzer UI.
2. **Vehicle metadata header** — *approved, deferred*.
3. **Fix icon clipping on main window** — *approved, deferred*.

### Out of scope for v1 (explicit)

- Live streaming (FreeSSM → analyzer realtime). Upload only.
- CSV editor in app.
- Native mobile app (responsive web is enough).
- Other brands (Toyota OBD-II, BMW INPA). Subaru only.
- Custom ML model (LLM-only).
- Tuning recommendations (RomRaider table values). Different product.

---

## Appendix A — Sensor naming convention (reference)

After commit `1d2ddfe (v1.3.0-ms.7) feat: rename 218 MB sensor names to
prefix-based scheme`, FreeSSM CSV headers follow a stable convention:

```
<Group> – <Specific name> [<unit>]
```

Examples:

- `Air – Mass Flow (MAF) [g/s]`
- `Engine – Speed [rpm]`
- `Fuel Trim – LTFT B1 [%]`
- `O2 – Pre-Cat B1 Lambda`
- `Fuel – Tank Pressure (EVAP) [kPa]`

The analyzer's parser must use these as the source of truth. Any rename in
FreeSSM **must** be mirrored in `analyzer/parsers/freessm_csv.py` lookup
patterns. Locked-in mapping lives in the parser.

## Appendix B — Reference: Michał's vehicle / case file

Vehicle: Subaru with EJ-series H4, dual-fuel petrol + LPG (Stag 2000
controller), wideband Denso lambda replaced ~1 month before logging.

Reported symptoms (2026-04-26):

1. Cold start on petrol — sluggish acceleration before LPG engages.
   *Initial impression*: after wideband replacement, performance was good;
   later it deteriorated.
2. Long highway runs on LPG — intermittent EVAP leak DTC (P0457). Tightening
   fuel cap (already tight) and clearing the code → sometimes returns,
   sometimes not.
3. LPG injectors are starting to rattle (LPG-side wear).

These symptoms become the empirical test bench for analyzer rule design.
The first analyzer run on `logs/FreeSSM_log2.csv` (LPG run, 17.8 min)
already produced concrete findings (idle LTFT −6.3%, no knock retard,
+9° learned advance suggesting LPG octane benefit). See devlog for
iteration history.
