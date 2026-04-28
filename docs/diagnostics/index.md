# docs/diagnostics — indeks

Dokumenty dotyczące diagnostyki **Subaru EJ253** (2.5L H4 NA, SOHC, AVCS, DBW).  
Pojazd: JDM/EDM, ~200k km, LPG + benzyna (dual-fuel Stag).  
Logi: `logs/FreeSSM_log_cleared_memory_cold_start_gasoline_only.csv` (petrol),  
      `logs/FreeSSM_log2.csv` (LPG).  
Raporty v4: `reports/v4_compare/` — autorytatywne (ms.11).

---

## Diagnoza — aktualny stan (2026-04-28)

### ✅ Definitywnie potwierdzone

| Fakt | Dowód | Data |
|---|---|---|
| **WOT na benzynie: mieszanka uboga** (lambda 1.02, STFT p95 +24%) | Analizator ms.11, `reports/v4_compare/` | 2026-04-27 |
| **WOT na LPG: mieszanka prawidłowa** (lambda 0.99, STFT p95 +2.3%) | Analizator ms.11, ten sam silnik | 2026-04-27 |
| **Ciśnienie paliwa benzyna: 50 PSI / 3.4 bar, stabilne niezależnie od obrotów** | Pomiar manometrem (Michał) | **2026-04-28** |
| **Idle ciepłe: stabilne** (RPM std 37, mediana 651, p10-p90 swing 39 RPM) | Analizator ms.11 po korekcie filtra | 2026-04-27 |
| **Sonda O2 słaba** (lambda crossings 0.19 Hz, norma ≥0.3 Hz) | Analizator ms.11 `chk_o2_dynamic_response` | 2026-04-27 |
| **Brak vacuum leak** (3-pillar fingerprint: wszystkie ujemne) | Analizator ms.11 `chk_ltft_load_dependency` | 2026-04-27 |

### ❌ Wykluczone (z dowodem)

| Hipoteza | Dlaczego wykluczona |
|---|---|
| Vacuum leak | 3-filary: LTFT idle –6.3% (lean → MINUS, nie PLUS), MAP 33 kPa (OK), gradient ujemny |
| Słaba pompa paliwa | Ciśnienie 50 PSI stabilne we wszystkich RPM (zmierzone 2026-04-28) |
| Zatkany filtr paliwa | Ciśnienie stabilne — nie ma spadku pod obciążeniem |
| Regulator ciśnienia uszkodzony | Ciśnienie stabilne — reguluje poprawnie |
| Mechanika silnika | Ten sam silnik działa zdrowo na LPG — mechanika OK |
| Zapłon / AVCS | Knock correction ≈ 0, brak retardu w WOT pulls |

### 🎯 Wniosek diagnostyczny (finalny)

> **Zużyte wtryskiwacze benzynowe.**  
> Sygnatura cross-load (ALARM `chk_injector_health`):  
> — Idle (mały czas otwarcia): wyciek końcówki → mieszanka **bogata** → LTFT –6.3%  
> — WOT (długi czas otwarcia): zatkany atomizer → mieszanka **uboga** → STFT +24%  
>
> Ciśnienie paliwa potwierdzone prawidłowe (50 PSI) → problem leży w przepływie wtryskiwacza, nie w dostawie paliwa z pompy/filtra.

### 🔧 Zalecane działania (kolejność ROI)

1. **Off-car test wtryskiwaczy** (~200 PLN komplet) — pomiar przepływu, wzorzec rozpylenia, test szczelności. Rozstrzyga sprawę.
2. **Wymiana sondy O2** (LSU 4.9 / Denso UEGO, ~300–600 PLN) — przy serwisie. Ważne: po wymianie re-run pełnej analizy dla nowego baseline.
3. Jeśli test wtryskiwaczy pokaże zużycie ≥15% → wymiana na Denso/Bosch OEM lub ultrasoniczne czyszczenie.
4. Smoke test dolotu — niski koszt (100 PLN), finalnie wyklucza vacuum leak.

---

## Sprostowania historyczne (wycofane diagnozy)

| Błędna diagnoza | Kiedy | Dlaczego błędna | Sprostowanie |
|---|---|---|---|
| Bank 2 fizycznie istnieje (EJ253 NA) | ms.9 i wcześniej | EJ253 NA ma jedną sondę przedkatalityczną → jeden bank sterujący | Kanały B3 to placeholder; ECU raportuje B1 = całość silnika |
| Vacuum leak (MAF 3.89 g/s, MAP 33 kPa "za wysoko") | ms.9 | Błędne zakresy referencyjne (ze STI), odwrócona logika LTFT | Szczegóły: [EJ253_full_pl.md](EJ253_full_pl.md) SPROSTOWANIE (top) |
| Idle hunting (std 367 RPM) | ms.9 | Artefakt klasyfikatora wciągającego tip-iny i coast-down do IDLE | Realny std = 37 RPM po filtrze 550–850 RPM + ciągłe okno ≥3s |

---

## Pliki w tym folderze

| Plik | Zawartość | Status |
|---|---|---|
| [EJ253_full_pl.md](EJ253_full_pl.md) | Pełna analiza silnika: AVCS, układ dolotowy, paliwowy, anatomia vacuum leak, sprostowania | Aktualny — top errata block (ms.10) |
| [panel_review_pl.md](panel_review_pl.md) | Panel 3 ekspertów + metodologia + finalne werdykty | Aktualny — sekcja 1.1 i 6 poprawione (ms.10) |

---

## Parametry referencyjne EJ253 NA (zweryfikowane)

| Sensor | Norma (ciepły idle ~700 rpm) | Twoje dane | Ocena |
|---|---|---|---|
| MAP | 27–37 kPa abs | 33.0 kPa | ✅ OK |
| MAF | 2.5–4.5 g/s | 3.84 g/s | ✅ OK |
| LTFT idle | –5% do +5% | –6.3% | ⚠️ Bogato |
| RPM std | <30 rpm | 37 rpm | ⚠️ Lekkie wahania |
| Lambda CL | ±0.02 od 1.0 | 62% poza pasmem | ❌ Sonda lazy |
| WOT lambda | 0.80–0.88 | 1.02 | ❌ Ubogo |
| Ciśnienie paliwa | ~44–50 PSI | **50 PSI** | ✅ OK |
| O2 crossings | ≥0.3 Hz | 0.19 Hz | ⚠️ Sonda słaba |
