# FreeSSM — Aktualna lista nazw sensorów MB (Measured Blocks)

Źródło: `src/SSMFlagbyteDefinitions_en.cpp`  
Łącznie: 218 unikalnych tytułów (+ kilka duplikatów o tej samej nazwie, różnym adresie/formule — oznaczone ⚠️)

Legenda kolumny **ECU**: `ENG`=Engine, `AT`=Automat, `AWD`=Napęd 4x4, `DSL`=Diesel, `ALL`=wszystkie

---

## 1. SILNIK — parametry główne

| # | Obecna nazwa | Jednostka | ECU | Uwagi |
|---|---|---|---|---|
| 1 | Engine Speed | rpm | ALL | |
| 2 | Coolant Temperature | °C | ENG | |
| 3 | Engine Load | % | ENG | |
| 4 | Ignition Timing | deg | ENG | |
| 5 | Knocking Correction | deg | ENG | ⚠️ DUPLIKAT — flaga 3 (formula -128/2) I flaga 48 (formula -128/4) — różna skala! |
| 6 | Learned Ignition Timing | deg | ENG | |
| 7 | Learned Ignition Timing Correction | deg | ENG | Flaga 48 — alias Fine Knock Learning |
| 8 | Battery Voltage | V | ALL | |
| 9 | Battery Current | A | ENG | |
| 10 | Battery Temperature | °C | ENG | |
| 11 | Alternator Duty | % | ENG | |
| 12 | Alternator Control Mode | — | ENG | Tryb: High/ExHigh/Low/Mid |
| 13 | Atmosphere Pressure | kPa | ENG | Barometr wbudowany w ECU |
| 14 | Gear Position | gear | ALL | |
| 15 | SI-Drive Mode | — | ENG | Tryb S/S#/I (STI/Legacy 3.0) |
| 16 | Roughness Monitor Cylinder #1 | — | ENG | Wskaźnik chropowatości biegu cyl. 1 |
| 17 | Roughness Monitor Cylinder #2 | — | ENG | |
| 18 | Roughness Monitor Cylinder #3 | — | ENG | |
| 19 | Roughness Monitor Cylinder #4 | — | ENG | |
| 20 | Roughness Monitor Cylinder #5 | — | ENG | 6-cyl. |
| 21 | Roughness Monitor Cylinder #6 | — | ENG | 6-cyl. |
| 22 | Target Engine Speed | rpm | DSL | Diesel — docelowe RPM |

---

## 2. PRZEPUSTNICA / DOLOT

| # | Obecna nazwa | Jednostka | ECU | Uwagi |
|---|---|---|---|---|
| 23 | Throttle Opening Angle | % | ENG | Kąt otwarcia przepustnicy (z czujnika) |
| 24 | Throttle Sensor Voltage | V | ENG | ⚠️ DUPLIKAT — flaga 3 (ENG, /50) I flaga 9 (AT, /45) — różne skale i systemy! |
| 25 | Throttle Sensor Closed Voltage | V | ENG | Napięcie przy zamkniętej przepustnicy |
| 26 | Throttle Motor Voltage | V | ENG | Silnik ETC (elektroniczna przepustnica) |
| 27 | Throttle Motor Duty | % | ENG | Wypełnienie PWM silnika ETC |
| 28 | Accelerator Pedal Travel | % | ENG | Pozycja pedału gazu |
| 29 | Main-Accelerator Sensor Voltage | V | ENG | Główny czujnik pedału gazu |
| 30 | Sub-Accelerator Sensor Voltage | V | ENG | Zapasowy czujnik pedału gazu |
| 31 | Main-Throttle Sensor Voltage | V | ENG | Główny czujnik przepustnicy |
| 32 | Sub-Throttle Sensor Voltage | V | ENG | Zapasowy czujnik przepustnicy |
| 33 | Mass Air Flow | g/s | ENG | MAF — przepływomierz |
| 34 | Air Flow Sensor Voltage | V | ENG | Napięcie z MAF (raw) |
| 35 | Manifold Absolute Pressure | kPa | ENG | MAP — ciśnienie bezwzględne w kolektorze |
| 36 | Manifold Relative Pressure | kPa | ENG | MAP — ciśnienie względne |
| 37 | Manifold Pressure Sensor Voltage | V | AT | Napięcie z czujnika MAP (AT) |
| 38 | Intake Air Temperature | °C | ENG | IAT — temperatura powietrza dolotowego |
| 39 | Intake Air Temperature (combined) | °C | DSL | IAT kombinowana (diesel) |
| 40 | Air Mass | mg/cyl | DSL | Masa powietrza na cykl (diesel) |
| 41 | Target Intake Air Amount | mg/cyl | DSL | Docelowa masa powietrza (diesel) |
| 42 | Target Intake Manifold Pressure | kPa | DSL | Docelowe ciśnienie w kolektorze (diesel) |
| 43 | Differential Pressure Sensor Voltage | V | ENG | Czujnik różnicy ciśnień — filtr powietrza |
| 44 | Pressure Differential Sensor | kPa | ENG | Wartość z czujnika różnicy ciśnień (kPa) |
| 45 | Secondary Air Flow | g/s | ENG | System wtórnego powietrza |
| 46 | Secondary Air Piping Pressure | kPa | ENG | Ciśnienie w rurze wtórnego powietrza |

---

## 3. KOREKTY MIESZANKI (Fuel Trim)

> **Uwaga**: "Air/Fuel Correction" = STFT (krótkoterminowa), "Air/Fuel Learning" = LTFT (długoterminowa). Obie wyświetlane jako "Air/Fuel..." i obie w tej samej grupie litery "A" — wymieszane ze sobą i z sensorami O2.

| # | Obecna nazwa | Jednostka | ECU | Uwagi |
|---|---|---|---|---|
| 47 | Air/Fuel Correction #1 | % | ENG | STFT bank 1 |
| 48 | Air/Fuel Correction #2 | % | ENG | STFT bank 2 |
| 49 | Air/Fuel Correction #3 | % | ENG | STFT bank 3 (6-cyl.) |
| 50 | Air/Fuel Correction #4 | % | ENG | STFT bank 4 (6-cyl.) |
| 51 | Air/Fuel Learning #1 | % | ENG | LTFT bank 1 |
| 52 | Air/Fuel Learning #2 | % | ENG | LTFT bank 2 |
| 53 | Air/Fuel Learning #3 | % | ENG | LTFT bank 3 (6-cyl.) |
| 54 | Air/Fuel Learning #4 | % | ENG | LTFT bank 4 (6-cyl.) |
| 55 | Air/Fuel Lean Correction | % | ENG | Długoterminowa korekta "lean" |
| 56 | Air/Fuel Heater Duty | % | ENG | Wypełnienie grzałki sondy (sterowanie) |
| 57 | Air/Fuel Adjust Voltage | V | ENG | Napięcie korekcji A/F |
| 58 | CO Adjustment Voltage | V | ENG | Napięcie potencjometru CO (starsze ECU) |

---

## 4. SONDY LAMBDA — WIDEBAND (A/F Sensor)

> Szerokopasmowe sondy A/F (Denso), stosowane w nowszych EJ z AVCS. Pracują na prądzie mA, nie na napięciu.

| # | Obecna nazwa | Jednostka | ECU | Uwagi |
|---|---|---|---|---|
| 59 | Air/Fuel Sensor #1 Current | mA | ENG | Prąd sondy wideband #1 |
| 60 | Air/Fuel Sensor #2 Current | mA | ENG | Prąd sondy wideband #2 |
| 61 | Air/Fuel Sensor #1 Lambda | — | ENG | Lambda obliczona (raw/128, 1.0=stoich) |
| 62 | Air/Fuel Sensor #2 Lambda | — | ENG | |
| 63 | Air/Fuel Sensor #1 Resistance | ohms | ENG | Rezystancja elementu sondy |
| 64 | Air/Fuel Sensor #2 Resistance | ohms | ENG | |
| 65 | Air/Fuel Sensor #1 Heater Current | A | ENG | ⚠️ MYLĄCE — to NIE jest to samo co poz. 71! Inny adres, formuła /10 |
| 66 | Air/Fuel Sensor #2 Heater Current | A | ENG | |

---

## 5. SONDY LAMBDA — NARROWBAND (O2 Sensor)

> Wąskopasmowe sondy cyrkonowe, stosowane w starszych EJ. Pracują na napięciu 0–1V.

| # | Obecna nazwa | Jednostka | ECU | Uwagi |
|---|---|---|---|---|
| 67 | Front O2 Sensor #1 Voltage | V | ENG | Napięcie sondy narrowband #1 (bank 1) |
| 68 | Front O2 Sensor #2 Voltage | V | ENG | Napięcie sondy narrowband #2 (bank 2) |
| 69 | Rear O2 Sensor Voltage | V | ENG | Napięcie sondy za katalizatorem |
| 70 | Front O2 Sensor #1 Heater Current | A | ENG | ⚠️ MYLĄCE — to NIE jest to samo co poz. 65! Inny adres, formuła /255*10 |
| 71 | Front O2 Sensor #2 Heater Current | A | ENG | |
| 72 | Rear O2 Sensor Heater Current | A | ENG | |
| 73 | Rear O2 Sensor Heater Voltage | V | ENG | Napięcie grzałki tylnej sondy |

---

## 6. UKŁAD PALIWOWY

| # | Obecna nazwa | Jednostka | ECU | Uwagi |
|---|---|---|---|---|
| 74 | Fuel Injection #1 Pulse | ms | ENG | Czas otwarcia wtryskiwacza (cyl. 1+3 alt.) |
| 75 | Fuel Injection #2 Pulse | ms | ENG | Czas otwarcia wtryskiwacza (cyl. 2+4 alt.) |
| 76 | Fuel Tank Pressure | kPa | ENG | ⚠️ DUPLIKAT — flaga 4 (formuła -128/40) I flaga 52 (formuła -128/20) — różna skala! |
| 77 | Fuel Tank Air Presser Pressure | MPa | ENG | Literówka w oryginale! ("Presser" zamiast "Pressure") |
| 78 | Fuel Level Sensor Voltage | V | ENG | Napięcie czujnika poziomu paliwa |
| 79 | Fuel Level Sensor Resistance | ohms | ENG | Rezystancja czujnika poziomu paliwa |
| 80 | Fuel Pump Duty | % | ENG | Wypełnienie PWM pompy |
| 81 | Fuel Temperature | °C | ENG | Temperatura paliwa |
| 82 | Fuel Pressure | kPa | ENG | Ciśnienie paliwa (GDI) |
| 83 | Canister Purge Control (CPC) Valve Duty Ratio | % | ENG | Wypełnienie zaworu odgazowania |
| 84 | Memorized Cruise Speed | km/h | ENG | Zapamiętana prędkość cruise control |
| 85 | Odometer | km | ENG | Licznik przebiegu |
| 86 | Target Fuel Pump Current | mA | DSL | Docelowy prąd pompy (diesel) |
| 87 | Actual Fuel Pump Current | mA | DSL | Rzeczywisty prąd pompy (diesel) |

---

## 7. UKŁAD BIEGU JAŁOWEGO (ISC)

| # | Obecna nazwa | Jednostka | ECU | Uwagi |
|---|---|---|---|---|
| 88 | Idle Speed Control (ISC) Valve Duty Ratio | % | ENG | Wypełnienie zaworu ISC |
| 89 | Idle Speed Control (ISC) Valve Steps | steps | ENG | Pozycja krokowa zaworu ISC |

---

## 8. VVT / AVCS / AVLS

> AVCS (ciągły kąt, OCV) — silniki DOHC turbo (EJ205/EJ257). AVLS (binarne On/Off, OSV) — SOHC (EJ253).

| # | Obecna nazwa | Jednostka | ECU | Uwagi |
|---|---|---|---|---|
| 90 | Variable Valve Timing (VVT) Advance Angle Amount (Right, Intake) | deg | ENG | AVCS — kąt wyprzedzenia P wlot |
| 91 | Variable Valve Timing (VVT) Advance Angle Amount (Left, Intake) | deg | ENG | AVCS — kąt wyprzedzenia L wlot |
| 92 | Variable Valve Timing (VVT) Retard Angle (Right, Exhaust) | deg | ENG | AVCS — kąt opóźnienia P wydech |
| 93 | Variable Valve Timing (VVT) Retard Angle (Left, Exhaust) | deg | ENG | AVCS — kąt opóźnienia L wydech |
| 94 | Oil Flow Control Solenoid Valve (OCV) Current (Right, Intake) | mA | ENG | AVCS — prąd OCV P wlot |
| 95 | Oil Flow Control Solenoid Valve (OCV) Current (Left, Intake) | mA | ENG | |
| 96 | Oil Flow Control Solenoid Valve (OCV) Current (Right, Exhaust) | mA | ENG | |
| 97 | Oil Flow Control Solenoid Valve (OCV) Current (Left, Exhaust) | mA | ENG | |
| 98 | Oil Flow Control Solenoid Valve (OCV) Duty (Right, Intake) | % | ENG | AVCS — wypełnienie OCV P wlot |
| 99 | Oil Flow Control Solenoid Valve (OCV) Duty (Left, Intake) | % | ENG | |
| 100 | Oil Flow Control Solenoid Valve (OCV) Duty (Right, Exhaust) | % | ENG | |
| 101 | Oil Flow Control Solenoid Valve (OCV) Duty (Left, Exhaust) | % | ENG | |
| 102 | VVL Lift Mode | — | ENG | Tryb zmiany profilu krzywki |
| 103 | Oil Switching Solenoid Valve (OSV) Current (Right) | mA | ENG | AVLS — prąd OSV P |
| 104 | Oil Switching Solenoid Valve (OSV) Current (Left) | mA | ENG | |
| 105 | Oil Switching Solenoid Valve (OSV) Duty (Right) | % | ENG | AVLS — wypełnienie OSV P |
| 106 | Oil Switching Solenoid Valve (OSV) Duty (Left) | % | ENG | |
| 107 | Oil Temperature | °C | ENG | Temperatura oleju silnikowego |

---

## 9. TURBO / BOOST

| # | Obecna nazwa | Jednostka | ECU | Uwagi |
|---|---|---|---|---|
| 108 | Primary Wastegate Duty Cycle | % | ENG | Wypełnienie głównego zaworu wastegate |
| 109 | Secondary Wastegate Duty Cycle | % | ENG | Wypełnienie wtórnego zaworu wastegate |
| 110 | Boost Pressure Feedback | % | DSL | Korekta ciśnienia doładowania (diesel) |
| 111 | Tumble Generator Valve (TGV) Position Sensor (Right) | V | ENG | Pozycja zaworu TGV P |
| 112 | Tumble Generator Valve (TGV) Position Sensor (Left) | V | ENG | |

---

## 10. EGR (Recyrkulacja spalin)

| # | Obecna nazwa | Jednostka | ECU | Uwagi |
|---|---|---|---|---|
| 113 | Number of Exhaust Gas Recirculation (EGR) Steps | steps | ENG | Pozycja krokowa zaworu EGR |
| 114 | Exhaust Gas Recirculation (EGR) Valve Opening Angle | deg | DSL | Kąt otwarcia zaworu EGR |
| 115 | Exhaust Gas Recirculation (EGR) Target Valve Opening Angle | deg | DSL | |
| 116 | Exhaust Gas Recirculation (EGR) Duty | % | DSL | Wypełnienie EGR (diesel) |

---

## 11. TEMPERATURA SPALIN

| # | Obecna nazwa | Jednostka | ECU | Uwagi |
|---|---|---|---|---|
| 117 | Exhaust Gas Temperature | °C | ENG | Temperatura spalin #1 |
| 118 | Exhaust Gas Temperature 2 | °C | ENG | Temperatura spalin #2 |

---

## 12. UKŁAD ELEKTRYCZNY / RADIATOR / KLIMATYZACJA

| # | Obecna nazwa | Jednostka | ECU | Uwagi |
|---|---|---|---|---|
| 119 | Radiator Fan Control | % | ENG | Sterowanie wentylatorem chłodnicy |
| 120 | Electric Power Steering Current | A | ENG | Prąd wspomagania kierownicy |
| 121 | Vehicle Speed | km/h | ALL | |
| 122 | Interior Heater | Steps | DSL | Podgrzewacz kabiny (diesel) |

---

## 13. SKRZYNIA BIEGÓW (AT)

| # | Obecna nazwa | Jednostka | ECU | Uwagi |
|---|---|---|---|---|
| 123 | Turbine Revolution Speed | rpm | AT | Prędkość turbiny momentu |
| 124 | ATF Temperature | °C | AT | ⚠️ DUPLIKAT — flaga 9 (tabela lookup) I flaga 10 (formuła -50) — różna skala! |
| 125 | ATF Temperature 2 | °C | AT | Drugi czujnik temp. oleju AT |
| 126 | Transfer Duty Ratio | % | AT | Wypełnienie sprzęgła transferowego |
| 127 | Lock Up Duty Ratio | % | AT | Wypełnienie sprzęgła L/U |
| 128 | Line Pressure Duty Ratio | % | AT | Wypełnienie zaworu ciśnienia liniowego |
| 129 | High Clutch Duty | % | AT | Wypełnienie sprzęgła H/C |
| 130 | Low Clutch Duty | % | AT | Wypełnienie sprzęgła L/C |
| 131 | Brake Clutch Duty Ratio | % | AT | Wypełnienie hamulca |
| 132 | Low & Reverse Brake (L&R B) Duty | % | AT | Wypełnienie hamulca L&R |
| 133 | AT Turbine Speed 1 | rpm | AT | Prędkość turbiny AT #1 |
| 134 | AT Turbine Speed 2 | rpm | AT | Prędkość turbiny AT #2 |
| 135 | Throttle Sensor Voltage (AT) | V | AT | ⚠️ Ten sam tytuł co poz. 24 ale inny adres/skala! |

---

## 14. NAPĘD 4x4 / PODWOZIE (AWD)

| # | Obecna nazwa | Jednostka | ECU | Uwagi |
|---|---|---|---|---|
| 136 | Front Wheel Speed | km/h | ALL | |
| 137 | Rear Wheel Speed | km/h | AT/AWD | |
| 138 | Wheel Speed Front Left | km/h | AWD | |
| 139 | Wheel Speed Front Right | km/h | AWD | |
| 140 | Wheel Speed Rear Left | km/h | AWD | |
| 141 | Wheel Speed Rear Right | km/h | AWD | |
| 142 | Steering Angle Sensor | deg | AWD | |
| 143 | Lateral G | m/s² | AWD | Boczna siła G |
| 144 | Lateral G Sensor Voltage | V | AT | Napięcie czujnika G bocznego |
| 145 | Yaw Rate | deg/s | AWD | Prędkość kątowa odchylenia |
| 146 | Yaw Rate Sensor Voltage | V | AWD | |
| 147 | Yaw Rate & G Sensor Reference Voltage | V | AWD | Napięcie referencyjne układu IMU |
| 148 | AWD Solenoid Valve Current | A | AWD | Prąd sprzęgła AWD (VTD/DCCD) |
| 149 | AWD Solenoid Valve Pressure | kPa | AWD | Ciśnienie sprzęgła AWD |
| 150 | Center Differential Indicate Current | A | AWD | Wymagany prąd diff. centralnego |
| 151 | Center Differential Real Current | A | AWD | Rzeczywisty prąd diff. centralnego |
| 152 | Voltage Center Differential Switch | V | AWD | |
| 153 | Front-Rear Wheel Rotation Ratio | — | AWD | Stosunek obrotów przód/tył |
| 154 | Fwd/B Solenoid Valve Current | A | AWD | |
| 155 | Fwd/B Solenoid Valve Target Pressure | kPa | AWD | |
| 156 | Drivers Control Center Differential (DCCD) Mode | — | AWD | Tryb DCCD |
| 157 | Drivers Control Center Differential (DCCD) Torque Allocation | — | AWD | Podział momentu DCCD |

---

## 15. HYDRAULIKA AT (zawory sprzęgłowe)

> Nazwy skrótów: H&LR/C = High & Low-Reverse Clutch, D/C = Drive Clutch, F/B = Forward Brake, I/C = Input Clutch, P/L = Pressure Line, L/U = Lock-Up.

| # | Obecna nazwa | Jednostka | ECU | Uwagi |
|---|---|---|---|---|
| 158 | H&LR/C Solenoid Valve Current | A | AT | Prąd zaworu H&LR/C |
| 159 | D/C Solenoid Valve Current | A | AT | |
| 160 | F/B Solenoid Valve Current | A | AT | |
| 161 | I/C Solenoid Valve Current | A | AT | |
| 162 | P/L Solenoid Valve Current | A | AT | |
| 163 | L/U Solenoid Valve Current | A | AT | |
| 164 | H&LR/C Solenoid Valve Pressure | kPa | AT | Ciśnienie zaworu H&LR/C |
| 165 | D/C Solenoid Valve Pressure | kPa | AT | |
| 166 | F/B Solenoid Valve Pressure | kPa | AT | |
| 167 | I/C Solenoid Valve Pressure | kPa | AT | |
| 168 | P/L Solenoid Valve Pressure | kPa | AT | |
| 169 | L/U Solenoid Valve Pressure | kPa | AT | |

---

## 16. DIESEL — specyficzne

| # | Obecna nazwa | Jednostka | ECU | Uwagi |
|---|---|---|---|---|
| 170 | Common Rail Pressure | MPa | DSL | |
| 171 | Common Rail Target Pressure | MPa | DSL | |
| 172 | Final Injection Amount | mm³ | DSL | |
| 173 | Main Injection Period | °CA | DSL | |
| 174 | Final Main Injection Period | ms | DSL | |
| 175 | Number of Times Injected | — | DSL | |
| 176 | Quantity Correction Cylinder #1 | ms | DSL | |
| 177 | Quantity Correction Cylinder #2 | ms | DSL | |
| 178 | Quantity Correction Cylinder #3 | ms | DSL | |
| 179 | Quantity Correction Cylinder #4 | ms | DSL | |
| 180 | Individual Pump Difference Learning Value | mA | DSL | |
| 181 | Micro-Quantity-Injection Final Learning Value 1-1 | ms | DSL | (× 20 wpisów 1-1 do 5-4) |
| … | *Micro-Quantity-Injection Final Learning Value 1-2 … 5-4* | ms | DSL | 20 wpisów łącznie |
| 182 | Mileage after Injector Replacement | km | DSL | |
| 183 | Mileage after Injector Learning | km | DSL | |
| 184 | Oil Dilution Ratio | % | DSL | |
| 185 | Soot Accumulation Ratio | % | DSL | |
| 186 | Estimated Temperature of the Diesel Particulate Filter (DPF) | °C | DSL | |
| 187 | Estimated Catalyst Temperature | °C | DSL | |
| 188 | Exhaust Gas Temperature at Diesel Particulate Filter (DPF) Inlet | °C | DSL | |
| 189 | Exhaust Gas Temperature at Catalyst Inlet | °C | DSL | |
| 190 | Pressure Difference between Diesel Particulate Filter (DPF) Inlet and Outlet | kPa | DSL | |
| 191 | Cumulative Ash Ratio | % | DSL | |
| 192 | Diesel Particulate Filter (DPF) Regeneration Count | Times | DSL | |
| 193 | Running Distance since last Diesel Particulate Filter (DPF) Regeneration | km | DSL | |
| 194 | Estimated Distance to Oil Change | km | DSL | |
| 195 | Accumulated Count of Overspeed Instances (High RPM) | Time | DSL | |
| 196 | Accumulated Count of Overspeed Instances (Very High RPM) | Time | DSL | |
| 197 | Actual Common Rail Pressure (Time Syncronized) | MPa | DSL | Literówka: "Syncronized" |

---

## Podsumowanie problemów z nazewnictwem

### 🔴 Krytyczne — powodują dezorientację

| Problem | Dotknięte sensory |
|---|---|
| **Duplikaty tej samej nazwy, różne atrybuty** | `Knocking Correction` (x2), `Fuel Tank Pressure` (x2), `ATF Temperature` (x2), `Throttle Sensor Voltage` (x2) |
| **Wideband A/F i narrowband O2 pomieszane** | `Air/Fuel Sensor #1 Heater Current` vs `Front O2 Sensor #1 Heater Current` — podobne nazwy, całkowicie różne sensory |
| **STFT i LTFT wymieszane alfabetycznie** | `Air/Fuel Correction` (STFT) i `Air/Fuel Learning` (LTFT) — rozdzielone literą alfabetu, nie logiką |
| **Literówki w oryginale** | `Fuel Tank Air Presser Pressure` (powinno być Pressure), `Actual Common Rail Pressure (Time Syncronized)` |

### 🟡 Umiarkowane — długie nazwy, skróty bez rozwinięcia

| Problem | Przykład |
|---|---|
| **Nazwy >50 znaków** | `Oil Flow Control Solenoid Valve (OCV) Current (Left, Intake)` = 55 znaków |
| **Skróty bez kontekstu** | `H&LR/C`, `D/C`, `F/B` dla zaworów AT |
| **Brak spójności numeru banku** | `#1`/`#2` dla sond — co to jest? Bank 1 = prawa strona czy lewa? |

### 🟢 Do rozważenia przy renaming

- Czy dodać prefix systemowy? `[ENG]`, `[AT]`, `[AWD]`, `[DSL]` — ułatwiłoby filtrowanie
- Czy użyć standardowych skrótów OBD2? `STFT B1`, `LTFT B1`, `MAF`, `MAP`, `IAT`, `ECT` — bardziej czytelne dla kogoś kto zna OBD2
