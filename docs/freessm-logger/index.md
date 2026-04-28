# docs/freessm-logger — indeks

Dokumenty dotyczące aplikacji **FreeSSM** (C++/Qt5 logger, fork Comer352L/FreeSSM).
Gałąź robocza: `feature/simulation-mode`. Remote: `https://github.com/mstepuch/FreeSSM.git`

## Status aplikacji (2026-04-28)
**Zakończone i stabilne.** FreeSSM służy jako logger CSV — zakres prac ukończony.  
Wersja: `v1.3.0-ms.11`. Build: `builds/v1.3.0-ms.11/`.

### Co zrobiono (ms.1–ms.11):
- Prefix-based CSV naming scheme (ms.7) — jednoznaczne identyfikatory kolumn
- UI fixy: wybór MB/SW, przemieszczanie, resize kolumn, defaulty (ms.8–ms.9)
- Analizator CSV w `tools/log-analyzer/` (ms.7–ms.11)
- Build pipeline: `windeployqt` + `Qt5SerialPort.dll` + `definitions/` (patrz `../.github/copilot-instructions.md`)

### Co NIE zostało zrobione (świadoma decyzja):
- Zmiana nazw sensorów w UI / CSV — **celowo pominięte**. Zmiana headerów CSV zepsuje historyczne logi i analizator. Jeśli kiedyś: warstwa `display_name` w UI bez ruszania nagłówka CSV.
- Polish translation (Phase 2.2) — niski priorytet
- Simulation mode (Phase 3.x) — rusztowanie istnieje, bez implementacji

---

## Pliki w tym folderze

| Plik | Zawartość | Status |
|---|---|---|
| [modernization_plan.md](modernization_plan.md) | Pełny plan modernizacji FreeSSM (Phase 1–4+) — co zrobiono, co planowane | Aktywny plan, częściowo wykonany |
| [sensor_names_current.md](sensor_names_current.md) | Lista 218 nazw sensorów MB z `SSMFlagbyteDefinitions_en.cpp` | Archiwalny — source of truth dla CSV headerów |
| [sensor_names_proposed.md](sensor_names_proposed.md) | Proponowane nowe nazwy sensorów z prefixami tematycznymi | Odłożone — patrz uwaga wyżej |
| [subaru_protocol_research.md](subaru_protocol_research.md) | Badania protokołów Subaru: SSM1/SSM2/UDS/CAN-FD, Security Gateway, Right to Repair | Bazowy raport badawczy (2024–2026) |

---

## Szybki start budowania

```powershell
$env:PATH = "C:\Qt\5.15.2\mingw81_64\bin;C:\Qt\Tools\mingw810_64\bin;" + $env:PATH
mingw32-make -j4 release
# Potem deploy — pełna procedura w .github/copilot-instructions.md
```
