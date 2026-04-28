# docs/analyzer — indeks

Dokumenty dotyczące **FreeSSM Analyzer** — narzędzia do analizy logów CSV FreeSSM.  
Kod: `tools/log-analyzer/analyze.py` (~2400 linii, stdlib-only, Python 3.10+).  
Docelowo: **osobne repo** `freessm-analyzer` z GUI (Streamlit MVP → PySide6 faza 2).

## Status analizatora (2026-04-28)
**Gotowy engine analityczny v2.** Zakres: 6 tierów, 29 checków, cross-fuel comparison.  
Wersja: `v1.3.0-ms.11` (w ramach FreeSSM repo — przed rozdzieleniem).

### Architektura (skrót — pełne szczegóły w design_panel.md)

| Warstwa | Technologia | Stan |
|---|---|---|
| Engine analityczny | Python 3.10+ stdlib-only | ✅ gotowy, 29 checków |
| CLI | argparse, `--fuel`, `--out-dir`, `--compare-with` | ✅ gotowy |
| Raporty | Markdown + JSON | ✅ gotowy |
| Backend API | FastAPI + Celery + Redis | ❌ nie zaczęty |
| DB | PostgreSQL + TimescaleDB | ❌ nie zaczęty |
| Frontend | React 18 + TypeScript + ECharts | ❌ nie zaczęty |
| MVP GUI | Streamlit | ❌ planowany następny krok |

### Uruchomienie:
```bash
# Jeden log:
python tools/log-analyzer/analyze.py logs/moj_log.csv --fuel petrol --out-dir reports/moje/

# Cross-fuel comparison:
python tools/log-analyzer/analyze.py logs/petrol.csv --fuel petrol \
  --out-dir reports/compare/ \
  --compare-with logs/lpg.csv --compare-fuel lpg
```

### Struktura checków (tiery):
| Tier | Zakres | Checków |
|---|---|---|
| 1 | Fuel trims & lambda | 10 |
| 2 | Air system (MAF, MAP, IAT) | 4 |
| 3 | Ignition & knock + O2 response | 4 |
| 4 | Cooling & temperatures | 3 |
| 5 | Sensor sanity & redundancy + STFT/voltage | 6 |
| 6 | EVAP & emissions + purge fingerprint | 3 |

### Kluczowe decyzje architektoniczne:
- **Stdlib-only** — zero dependencies, działa wszędzie z Python 3.10+. Celowe — silnik ma być przenośny.
- **Placeholder detection** — auto-wykrywanie kanałów B3 jako constant, pomijanie w scoringu.
- **Dynamic TPS floor** — 5-ty percentyl warm TPS + 0.5 pp, zamiast hardcoded TPS < 1%.
- **3-pillar vacuum leak fingerprint** — wymaga wszystkich 3 filarów (P1 LTFT+, P2 MAP+, P3 gradient+). Jeden filar ≠ leak.
- **Cross-fuel comparison** — `compare_summaries()` + `_COMPARE_METRICS` declarative list. Dodanie metryki = 1 linia.

---

## Pliki w tym folderze

| Plik | Zawartość | Status |
|---|---|---|
| [design_panel.md](design_panel.md) | Pełna architektura aplikacji + decyzje designerskie (panel ekspercki) | Source of truth dla stack decyzji |

---

## Następne kroki (priorytet malejący)

1. **Rozdzielić repo** → `freessm-analyzer` jako osobne repo na GitHub
2. **MVP GUI Streamlit** — drag-drop CSV, findings table, wykresy time-series, RPM×Load heatmap
3. **FastAPI backend** — async processing dużych logów
4. **AVCS tracking check** (Tier 3) — commanded vs actual cam angle
5. **Fuel pressure inference** z STFT(load) ratio — wymaga modelu VE
