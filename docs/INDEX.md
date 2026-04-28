# FreeSSM — Master Knowledge Index

**Repo:** `https://github.com/mstepuch/FreeSSM.git`  
**Gałąź robocza:** `feature/simulation-mode`  
**Wersja bieżąca:** `v1.3.0-ms.11`  
**Ostatnia aktualizacja:** 2026-04-28  

> **Dla Copilota — przeczytaj na starcie sesji:**  
> Ten plik to punkt wejścia do całego kontekstu projektu.  
> Przed pracą sprawdź odpowiedni folder `index.md` poniżej.

---

## Projekty w tym repo

| Projekt | Zakres | Status | Index |
|---|---|---|---|
| **FreeSSM Logger** (C++/Qt5) | Fork loggera SSM2 dla Subaru. Wybór sensorów, logging CSV, build Windows | ✅ Zakończony v1.3.0-ms.11 | [freessm-logger/index.md](freessm-logger/index.md) |
| **FreeSSM Analyzer** (Python) | Engine analityczny CSV: 6 tierów, 29 checków, cross-fuel comparison | ✅ Engine gotowy, GUI planowane | [analyzer/index.md](analyzer/index.md) |
| **Diagnostyka EJ253** (dane) | Diagnoza Subaru EJ253 NA + LPG użytkownika. Logi, raporty, wnioski. | 🎯 Finalna diagnoza: wtryskiwacze | [diagnostics/index.md](diagnostics/index.md) |

---

## Kluczowe ścieżki (quick-reference)

```
src/main.cpp                   ← FSSM_VERSION — tu bump wersji
tools/log-analyzer/analyze.py  ← silnik analizatora (~2400 linii)
logs/                          ← referencyjne CSV (petrol + LPG)
reports/v4_compare/            ← autorytatywne raporty ms.11
.github/copilot-instructions.md ← build/deploy procedura
```

---

## Aktualny stan diagnozy pojazdu (EJ253)

**Finalny werdykt (2026-04-28):** Zużyte wtryskiwacze benzynowe.  

Kluczowe pomiary:

| Dowód | Wartość | Wniosek |
|---|---|---|
| Ciśnienie paliwa (benzyna) | **50 PSI / 3.4 bar, stabilne w każdych RPM** (zmierzone 2026-04-28) | Pompa/filtr/regulator OK — wykluczono |
| WOT lambda (benzyna) | 1.02 (ubogo, norma 0.80–0.88) | ECU nie nadąża z paliwem |
| WOT STFT p95 (benzyna) | +24% (ECU na granicy authority) | Wtryskiwacz nie daje wymaganego przepływu |
| Idle LTFT (benzyna) | –6.3% (bogato) | Wyciek końcówki przy małym pulse width |
| WOT lambda (LPG) | 0.99 (prawidłowo) | Mechanika silnika OK |
| Cross-load sign-flip | LTFT– na idle + STFT+ na WOT | ← textbook wtryskiwacz zdegradowany |

**Następny krok:** Off-car test wtryskiwaczy (~200 PLN).

---

## Wersje i historia zmian

| Wersja | Zakres | Data |
|---|---|---|
| ms.9 | UI fixy (MB/SW dialog), CSV logging stable | 2026-04-26 |
| ms.10 | Analyzer: dynamic TPS floor, 3-pillar vacuum leak, placeholder B3, idle filter, MAP/MAF bands | 2026-04-27 |
| ms.11 | Analyzer: +5 checków (injector signature, O2 response, voltage/STFT, thermostat, EVAP purge), cross-fuel comparison mode, `_pearson()` refactor | 2026-04-27 |

---

## Następne sesje — plan

1. **Rozdzielenie repo** → `freessm-analyzer` jako osobne repo
2. **MVP GUI Streamlit** dla analizatora (drag-drop CSV, findings, wykresy)  
3. Po wyniku testu wtryskiwaczy → ewentualne doczyszczenie checklisty diagnostycznej
