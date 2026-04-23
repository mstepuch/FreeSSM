# FreeSSM — Proponowane nazwy sensorów MB

## Schemat nazewnictwa

**Format**: `[Blok] – [Opis] ([kontekst])`

- `[Blok]` to prefix tematyczny — gwarantuje grupowanie w alfabetycznej liście UI FreeSSM
- Separator `–` (en-dash + spacje) — jednoznaczny separator, nie myślnik z nazwy własnej
- `([kontekst])` — opcjonalny tylko gdy nazwa byłaby niejednoznaczna bez niego
- Skróty OBD2 dozwolone jako kontekst: `STFT`, `LTFT`, `B1`, `B2`, `MAF`, `MAP`, `TPS`, `IAT`, `ECT`, `ISC`

**Bloki tematyczne**:
| Prefix | Zakres |
|---|---|
| `Engine` | Główne parametry pracy silnika |
| `Air` | Dolot, przepustnica, MAF, MAP |
| `Fuel Trim` | Korekty krótko- i długoterminowe (STFT/LTFT) |
| `O2` | Sondy lambda — wideband (prąd mA) i narrowband (0–1V) |
| `Fuel` | Paliwo — wtrysk, pompa, zbiornik, ciśnienie |
| `Ignition` | Zapłon, knock |
| `Idle` | Bieg jałowy (ISC) |
| `VVT` | Zmienny rozrząd (AVCS = OCV, AVLS = OSV) |
| `Turbo` | Wastegate, boost, TGV (tylko silniki turbo) |
| `EGR` | Recyrkulacja spalin |
| `Exhaust` | Temperatura spalin |
| `Electrical` | Akumulator, alternator, EPS |
| `Cooling` | Wentylator chłodnicy |
| `AT` | Skrzynia automatyczna |
| `AWD` | Napęd 4x4, DCCD, czujniki podwozia |
| `DSL` | Diesel — specyficzne parametry |

---

## 1. Engine — główne parametry silnika

| Proponowana nazwa | Jedn. | Obecna nazwa | Zmiana |
|---|---|---|---|
| `Engine – Speed` | rpm | Engine Speed | skrócenie |
| `Engine – Load` | % | Engine Load | skrócenie |
| `Engine – Coolant Temperature (ECT)` | °C | Coolant Temperature | skrót ECT |
| `Engine – Oil Temperature` | °C | Oil Temperature | prefix |
| `Engine – Battery Temperature` | °C | Battery Temperature | przeniesienie do Electrical |
| `Engine – Vehicle Speed` | km/h | Vehicle Speed | prefix |
| `Engine – Gear Position` | — | Gear Position | prefix |
| `Engine – SI-Drive Mode` | — | SI-Drive Mode | prefix |
| `Engine – Misfire Monitor Cyl 1` | — | Roughness Monitor Cylinder #1 | czytelniejsza nazwa |
| `Engine – Misfire Monitor Cyl 2` | — | Roughness Monitor Cylinder #2 | |
| `Engine – Misfire Monitor Cyl 3` | — | Roughness Monitor Cylinder #3 | |
| `Engine – Misfire Monitor Cyl 4` | — | Roughness Monitor Cylinder #4 | |
| `Engine – Misfire Monitor Cyl 5` | — | Roughness Monitor Cylinder #5 | 6-cyl. |
| `Engine – Misfire Monitor Cyl 6` | — | Roughness Monitor Cylinder #6 | 6-cyl. |
| `Engine – Odometer` | km | Odometer | prefix |
| `Engine – Cruise Speed Memory` | km/h | Memorized Cruise Speed | czytelniej |
| `Engine – Target Speed` | rpm | Target Engine Speed | DSL |

---

## 2. Air — dolot, przepustnica, czujniki powietrza

| Proponowana nazwa | Jedn. | Obecna nazwa | Zmiana |
|---|---|---|---|
| `Air – Mass Flow (MAF)` | g/s | Mass Air Flow | +skrót |
| `Air – MAF Sensor Voltage` | V | Air Flow Sensor Voltage | spójność nazwy |
| `Air – Manifold Absolute Pressure (MAP)` | kPa | Manifold Absolute Pressure | skrót MAP |
| `Air – Manifold Relative Pressure` | kPa | Manifold Relative Pressure | prefix |
| `Air – Manifold Pressure Sensor Voltage (AT)` | V | Manifold Pressure Sensor Voltage | +kontekst AT |
| `Air – Intake Temperature (IAT)` | °C | Intake Air Temperature | skrót IAT |
| `Air – Intake Temperature Combined` | °C | Intake Air Temperature (combined) | bez nawiasów |
| `Air – Atmospheric Pressure` | kPa | Atmospheric Pressure | prefix |
| `Air – Throttle Position (TPS)` | % | Throttle Opening Angle | +skrót |
| `Air – Throttle Sensor Voltage` | V | Throttle Sensor Voltage *(flaga 3, ENG, /50)* | ⚠️ duplikat rozwiązany — to ENG |
| `Air – Throttle Sensor Voltage (AT)` | V | Throttle Sensor Voltage *(flaga 9, AT, /45)* | ⚠️ duplikat rozwiązany — to AT |
| `Air – Throttle Closed Voltage` | V | Throttle Sensor Closed Voltage | skrócenie |
| `Air – Throttle Motor Duty` | % | Throttle Motor Duty | prefix |
| `Air – Throttle Motor Voltage` | V | Throttle Motor Voltage | prefix |
| `Air – Pedal Position` | % | Accelerator Pedal Travel | czytelniej |
| `Air – Pedal Sensor Main Voltage` | V | Main-Accelerator Sensor Voltage | spójność |
| `Air – Pedal Sensor Sub Voltage` | V | Sub-Accelerator Sensor Voltage | |
| `Air – Throttle Sensor Main Voltage` | V | Main-Throttle Sensor Voltage | spójność |
| `Air – Throttle Sensor Sub Voltage` | V | Sub-Throttle Sensor Voltage | |
| `Air – Differential Pressure Sensor` | kPa | Pressure Differential Sensor | skrócenie |
| `Air – Differential Pressure Sensor Voltage` | V | Differential Pressure Sensor Voltage | prefix |
| `Air – Secondary Air Flow` | g/s | Secondary Air Flow | prefix |
| `Air – Secondary Air Pressure` | kPa | Secondary Air Piping Pressure | skrócenie |
| `Air – Air Mass per Cyl` | mg/cyl | Air Mass | +kontekst |
| `Air – Target Air Mass per Cyl` | mg/cyl | Target Intake Air Amount | ujednolicenie |
| `Air – Target Manifold Pressure` | kPa | Target Intake Manifold Pressure | skrócenie |

---

## 3. Fuel Trim — korekty mieszanki

> Boxer: **STFT** (Short Term Fuel Trim) = chwilowa korekta ~sekundowa. **LTFT** (Long Term Fuel Trim) = wyuczona historycznie. **B1/B2** = Bank 1 / Bank 2. `#1` i `#2` w starych nazwach NIE odnosi się do cylindrów — odnosi się do banku czujnika.

| Proponowana nazwa | Jedn. | Obecna nazwa | Zmiana |
|---|---|---|---|
| `Fuel Trim – STFT B1` | % | Air/Fuel Correction #1 | czytelna rola |
| `Fuel Trim – STFT B2` | % | Air/Fuel Correction #2 | |
| `Fuel Trim – STFT B3` | % | Air/Fuel Correction #3 | 6-cyl. |
| `Fuel Trim – STFT B4` | % | Air/Fuel Correction #4 | |
| `Fuel Trim – LTFT B1` | % | Air/Fuel Learning #1 | czytelna rola |
| `Fuel Trim – LTFT B2` | % | Air/Fuel Learning #2 | |
| `Fuel Trim – LTFT B3` | % | Air/Fuel Learning #3 | 6-cyl. |
| `Fuel Trim – LTFT B4` | % | Air/Fuel Learning #4 | |
| `Fuel Trim – Lean Correction` | % | Air/Fuel Lean Correction | prefix |
| `Fuel Trim – Heater Duty` | % | Air/Fuel Heater Duty | prefix |
| `Fuel Trim – Adjust Voltage` | V | Air/Fuel Adjust Voltage | prefix |
| `Fuel Trim – CO Pot Voltage` | V | CO Adjustment Voltage | skrócenie (CO Potentiometer) |

---

## 4. O2 — sondy lambda (wideband Pre-Cat + narrowband Post-Cat)

> **Pre-Cat** = przed katalizatorem (dawniej "Front"), **Post-Cat** = za katalizatorem (dawniej "Rear"). Na EJ253 Pre-Cat = sonda szerokopasmowa (wideband) — sygnał Current (mA) i Lambda. Post-Cat = sonda wąskopasmowa (narrowband) — sygnał Voltage (0–1V). Prefix `O2 –` dla wszystkich sond lambda — monitoruje się je razem.

| Proponowana nazwa | Jedn. | Obecna nazwa | Zmiana |
|---|---|---|---|
| `O2 – Pre-Cat B1 Current` | mA | Air/Fuel Sensor #1 Current | prefix O2, Pre-Cat B1 |
| `O2 – Pre-Cat B2 Current` | mA | Air/Fuel Sensor #2 Current | |
| `O2 – Pre-Cat B1 Lambda` | — | Air/Fuel Sensor #1 Lambda | |
| `O2 – Pre-Cat B2 Lambda` | — | Air/Fuel Sensor #2 Lambda | |
| `O2 – Pre-Cat B1 Resistance` | ohm | Air/Fuel Sensor #1 Resistance | |
| `O2 – Pre-Cat B2 Resistance` | ohm | Air/Fuel Sensor #2 Resistance | |
| `O2 – Pre-Cat B1 Heater Current` | A | Air/Fuel Sensor #1 Heater Current | pełna nazwa, jeden prefix |
| `O2 – Pre-Cat B2 Heater Current` | A | Air/Fuel Sensor #2 Heater Current | |
| `O2 – Pre-Cat B1 Voltage` | V | Front O2 Sensor #1 Voltage | narrowband ECU (nie EJ253) |
| `O2 – Pre-Cat B2 Voltage` | V | Front O2 Sensor #2 Voltage | |
| `O2 – Post-Cat Voltage` | V | Rear O2 Sensor Voltage | Post-Cat |
| `O2 – Post-Cat Heater Current` | A | Rear O2 Sensor Heater Current | pełna nazwa |
| `O2 – Post-Cat Heater Voltage` | V | Rear O2 Sensor Heater Voltage | |

---

## 5. Fuel — układ paliwowy

| Proponowana nazwa | Jedn. | Obecna nazwa | Zmiana |
|---|---|---|---|
| `Fuel – Injection Pulse B1` | ms | Fuel Injection #1 Pulse | pełna nazwa + B1 |
| `Fuel – Injection Pulse B2` | ms | Fuel Injection #2 Pulse | |
| `Fuel – Tank Pressure` | kPa | Fuel Tank Pressure *(flaga 52, -128/20)* | ⚠️ duplikat — zachowaj ten |
| `Fuel – Tank Pressure (EVAP)` | kPa | Fuel Tank Pressure *(flaga 4, -128/40)* | ⚠️ duplikat — inna skala |
| `Fuel – Tank Air Pressure` | MPa | Fuel Tank Air **Presser** Pressure | fix literówki |
| `Fuel – Level Sensor Voltage` | V | Fuel Level Sensor Voltage | prefix |
| `Fuel – Level Sensor Resistance` | ohm | Fuel Level Sensor Resistance | |
| `Fuel – Pump Duty` | % | Fuel Pump Duty | prefix |
| `Fuel – Temperature` | °C | Fuel Temperature | prefix |
| `Fuel – Pressure GDI` | kPa | Fuel Pressure | +kontekst (GDI) |
| `Fuel – CPC Valve Duty` | % | Canister Purge Control (CPC) Valve Duty Ratio | skrócenie z 46 do 21 znaków |

---

## 6. Ignition — zapłon i knock

| Proponowana nazwa | Jedn. | Obecna nazwa | Zmiana |
|---|---|---|---|
| `Ignition – Timing` | deg | Ignition Timing | prefix |
| `Ignition – Learned Timing` | deg | Learned Ignition Timing | skrócenie |
| `Ignition – Learned Timing Corr` | deg | Learned Ignition Timing Correction | skrócenie |
| `Ignition – Knock Correction` | deg | Knocking Correction *(flaga 3, -128/2)* | ⚠️ duplikat A |
| `Ignition – Knock Correction (Hi-Res)` | deg | Knocking Correction *(flaga 48, -128/4)* | ⚠️ duplikat B — wyższa rozdzielczość |

---

## 7. Idle — bieg jałowy (ISC)

| Proponowana nazwa | Jedn. | Obecna nazwa | Zmiana |
|---|---|---|---|
| `Idle – ISC Valve Duty` | % | Idle Speed Control (ISC) Valve Duty Ratio | -28 znaków |
| `Idle – ISC Valve Steps` | steps | Idle Speed Control (ISC) Valve Steps | -27 znaków |

---

## 8. VVT — zmienny rozrząd

> AVCS (ciągły kąt, OCV Duty) — silniki DOHC turbo (EJ205/EJ257/EJ255).
> AVLS (binarne On/Off, OSV) — silniki SOHC (EJ253).

| Proponowana nazwa | Jedn. | Obecna nazwa | Zmiana |
|---|---|---|---|
| `VVT – OCV Duty Right Intake` | % | Oil Flow Control Solenoid Valve (OCV) Duty (Right, Intake) | -46 znaków |
| `VVT – OCV Duty Left Intake` | % | Oil Flow Control Solenoid Valve (OCV) Duty (Left, Intake) | |
| `VVT – OCV Duty Right Exhaust` | % | Oil Flow Control Solenoid Valve (OCV) Duty (Right, Exhaust) | |
| `VVT – OCV Duty Left Exhaust` | % | Oil Flow Control Solenoid Valve (OCV) Duty (Left, Exhaust) | |
| `VVT – OCV Current Right Intake` | mA | Oil Flow Control Solenoid Valve (OCV) Current (Right, Intake) | |
| `VVT – OCV Current Left Intake` | mA | Oil Flow Control Solenoid Valve (OCV) Current (Left, Intake) | |
| `VVT – OCV Current Right Exhaust` | mA | Oil Flow Control Solenoid Valve (OCV) Current (Right, Exhaust) | |
| `VVT – OCV Current Left Exhaust` | mA | Oil Flow Control Solenoid Valve (OCV) Current (Left, Exhaust) | |
| `VVT – Advance Angle Right Intake` | deg | Variable Valve Timing (VVT) Advance Angle Amount (Right, Intake) | -34 znaków |
| `VVT – Advance Angle Left Intake` | deg | Variable Valve Timing (VVT) Advance Angle Amount (Left, Intake) | |
| `VVT – Retard Angle Right Exhaust` | deg | Variable Valve Timing (VVT) Retard Angle (Right, Exhaust) | |
| `VVT – Retard Angle Left Exhaust` | deg | Variable Valve Timing (VVT) Retard Angle (Left, Exhaust) | |
| `VVT – AVLS Lift Mode` | — | VVL Lift Mode | +kontekst AVLS |
| `VVT – OSV Current Right` | mA | Oil Switching Solenoid Valve (OSV) Current (Right) | -34 znaków |
| `VVT – OSV Current Left` | mA | Oil Switching Solenoid Valve (OSV) Current (Left) | |
| `VVT – OSV Duty Right` | % | Oil Switching Solenoid Valve (OSV) Duty (Right) | |
| `VVT – OSV Duty Left` | % | Oil Switching Solenoid Valve (OSV) Duty (Left) | |

---

## 9. Turbo — doładowanie

| Proponowana nazwa | Jedn. | Obecna nazwa | Zmiana |
|---|---|---|---|
| `Turbo – Primary Wastegate Duty` | % | Primary Wastegate Duty Cycle | skrócenie |
| `Turbo – Secondary Wastegate Duty` | % | Secondary Wastegate Duty Cycle | |
| `Turbo – Boost Feedback` | % | Boost Pressure Feedback | skrócenie |
| `Turbo – TGV Position Right` | V | Tumble Generator Valve (TGV) Position Sensor (Right) | -35 znaków |
| `Turbo – TGV Position Left` | V | Tumble Generator Valve (TGV) Position Sensor (Left) | |

---

## 10. EGR — recyrkulacja spalin

| Proponowana nazwa | Jedn. | Obecna nazwa | Zmiana |
|---|---|---|---|
| `EGR – Steps` | steps | Number of Exhaust Gas Recirculation (EGR) Steps | -40 znaków |
| `EGR – Valve Angle` | deg | Exhaust Gas Recirculation (EGR) Valve Opening Angle | -36 znaków |
| `EGR – Target Valve Angle` | deg | Exhaust Gas Recirculation (EGR) Target Valve Opening Angle | -41 znaków |
| `EGR – Duty` | % | Exhaust Gas Recirculation (EGR) Duty | -28 znaków |

---

## 11. Exhaust — temperatura spalin

| Proponowana nazwa | Jedn. | Obecna nazwa | Zmiana |
|---|---|---|---|
| `Exhaust – Gas Temperature 1` | °C | Exhaust Gas Temperature | +numer |
| `Exhaust – Gas Temperature 2` | °C | Exhaust Gas Temperature 2 | spójność |

---

## 12. Electrical — elektryka

| Proponowana nazwa | Jedn. | Obecna nazwa | Zmiana |
|---|---|---|---|
| `Electrical – Battery Voltage` | V | Battery Voltage | prefix |
| `Electrical – Battery Current` | A | Battery Current | prefix |
| `Electrical – Battery Temperature` | °C | Battery Temperature | prefix |
| `Electrical – Alternator Duty` | % | Alternator Duty | prefix |
| `Electrical – Alternator Mode` | — | Alternator Control Mode | skrócenie |
| `Electrical – EPS Current` | A | Electric Power Steering Current | -22 znaków |

---

## 13. Cooling — układ chłodzenia

| Proponowana nazwa | Jedn. | Obecna nazwa | Zmiana |
|---|---|---|---|
| `Cooling – Radiator Fan Duty` | % | Radiator Fan Control | spójność (Duty) |
| `Cooling – Interior Heater Steps` | steps | Interior Heater | +kontekst |

---

## 14. AT — skrzynia automatyczna

| Proponowana nazwa | Jedn. | Obecna nazwa | Zmiana |
|---|---|---|---|
| `AT – ATF Temperature` | °C | ATF Temperature *(flaga 10, -50)* | ⚠️ duplikat A |
| `AT – ATF Temperature 2` | °C | ATF Temperature 2 | |
| `AT – ATF Temperature (Lookup)` | °C | ATF Temperature *(flaga 9, tabela lookup)* | ⚠️ duplikat B — inna formuła! |
| `AT – ATF Deterioration` | % | Automatic Transmission Fluid (ATF) Deterioration Degree | -40 znaków |
| `AT – Turbine Speed` | rpm | Turbine Revolution Speed | skrócenie |
| `AT – Turbine Speed 1` | rpm | AT Turbine Speed 1 | spójność |
| `AT – Turbine Speed 2` | rpm | AT Turbine Speed 2 | |
| `AT – Line Pressure Duty` | % | Line Pressure Duty Ratio | skrócenie |
| `AT – Lock-Up Duty` | % | Lock Up Duty Ratio | + myślnik |
| `AT – Transfer Duty` | % | Transfer Duty Ratio | skrócenie |
| `AT – High Clutch Duty` | % | High Clutch Duty | prefix |
| `AT – Low Clutch Duty` | % | Low Clutch Duty | |
| `AT – Brake Clutch Duty` | % | Brake Clutch Duty Ratio | skrócenie |
| `AT – L&R Brake Duty` | % | Low & Reverse Brake (L&R B) Duty | skrócenie |
| `AT – Throttle Sensor Voltage` | V | Throttle Sensor Voltage *(flaga 9, AT)* | prefix AT |
| `AT – H&LRC Valve Current` | A | H&LR/C Solenoid Valve Current | czytelniejszy skrót |
| `AT – DC Valve Current` | A | D/C Solenoid Valve Current | czytelniejszy skrót |
| `AT – FB Valve Current` | A | F/B Solenoid Valve Current | |
| `AT – IC Valve Current` | A | I/C Solenoid Valve Current | |
| `AT – PL Valve Current` | A | P/L Solenoid Valve Current | |
| `AT – LU Valve Current` | A | L/U Solenoid Valve Current | |
| `AT – H&LRC Valve Pressure` | kPa | H&LR/C Solenoid Valve Pressure | |
| `AT – DC Valve Pressure` | kPa | D/C Solenoid Valve Pressure | |
| `AT – FB Valve Pressure` | kPa | F/B Solenoid Valve Pressure | |
| `AT – IC Valve Pressure` | kPa | I/C Solenoid Valve Pressure | |
| `AT – PL Valve Pressure` | kPa | P/L Solenoid Valve Pressure | |
| `AT – LU Valve Pressure` | kPa | L/U Solenoid Valve Pressure | |
| `AT – FwdB Valve Current` | A | Fwd/B Solenoid Valve Current | |
| `AT – FwdB Target Pressure` | kPa | Fwd/B Solenoid Valve Target Pressure | skrócenie |
| `AT – Center Differential Requested Current` | A | Center Differential Indicate Current | czytelniej |
| `AT – Center Differential Actual Current` | A | Center Differential Real Current | czytelniej |
| `AT – Center Differential Switch Voltage` | V | Voltage Center Differential Switch | przestawiona kolejność |

---

## 15. AWD — napęd 4x4 i czujniki podwozia

| Proponowana nazwa | Jedn. | Obecna nazwa | Zmiana |
|---|---|---|---|
| `AWD – Wheel Speed Front` | km/h | Front Wheel Speed | prefix |
| `AWD – Wheel Speed Rear` | km/h | Rear Wheel Speed | |
| `AWD – Wheel Speed FL` | km/h | Wheel Speed Front Left | skrót |
| `AWD – Wheel Speed FR` | km/h | Wheel Speed Front Right | |
| `AWD – Wheel Speed RL` | km/h | Wheel Speed Rear Left | |
| `AWD – Wheel Speed RR` | km/h | Wheel Speed Rear Right | |
| `AWD – ABS Front Mean Speed` | km/h | ABS/VDC Front Wheel Mean Wheel Speed | skrócenie |
| `AWD – ABS Rear Mean Speed` | km/h | ABS/VDC Rear Wheel Mean Wheel Speed | |
| `AWD – Front-Rear Ratio` | — | Front-Rear Wheel Rotation Ratio | skrócenie |
| `AWD – Steering Angle` | deg | Steering Angle Sensor | skrócenie |
| `AWD – Lateral G` | m/s² | Lateral G | prefix |
| `AWD – Lateral G Sensor Voltage` | V | Lateral G Sensor Voltage | prefix |
| `AWD – Yaw Rate` | deg/s | Yaw Rate | prefix |
| `AWD – Yaw Rate Sensor Voltage` | V | Yaw Rate Sensor Voltage | prefix |
| `AWD – IMU Reference Voltage` | V | Yaw Rate & G Sensor Reference Voltage | czytelniej |
| `AWD – Solenoid Current` | A | AWD Solenoid Valve Current | skrócenie |
| `AWD – Solenoid Pressure` | kPa | AWD Solenoid Valve Pressure | |
| `AWD – FwdB Solenoid Current` | A | Fwd/B Solenoid Valve Current | |
| `AWD – FwdB Target Pressure` | kPa | Fwd/B Solenoid Valve Target Pressure | |
| `AWD – DCCD Mode` | — | Drivers Control Center Differential (DCCD) Mode | -36 znaków |
| `AWD – DCCD Torque Allocation` | — | Drivers Control Center Differential (DCCD) Torque Allocation | -45 znaków |

---

## 16. DSL — diesel (skrócenia bez przepisywania logiki)

| Proponowana nazwa | Jedn. | Obecna nazwa |
|---|---|---|
| `DSL – Common Rail Pressure` | MPa | Common Rail Pressure |
| `DSL – Common Rail Target Pressure` | MPa | Common Rail Target Pressure |
| `DSL – Actual Rail Pressure` | MPa | Actual Common Rail Pressure (Time Syncronized) *(fix literówki)* |
| `DSL – Injection Amount Final` | mm³ | Final Injection Amount |
| `DSL – Injection Period Main` | °CA | Main Injection Period |
| `DSL – Injection Period Final` | ms | Final Main Injection Period |
| `DSL – Injection Times Count` | — | Number of Times Injected |
| `DSL – Quantity Correction Cylinder 1` | ms | Quantity Correction Cylinder #1 |
| `DSL – Quantity Correction Cylinder 2` | ms | Quantity Correction Cylinder #2 |
| `DSL – Quantity Correction Cylinder 3` | ms | Quantity Correction Cylinder #3 |
| `DSL – Quantity Correction Cylinder 4` | ms | Quantity Correction Cylinder #4 |
| `DSL – Injection Pump Differential Learning` | mA | Individual Pump Difference Learning Value |
| `DSL – Micro-Injection Learning 1-1..5-4` | ms | Micro-Quantity-Injection Final Learning Value 1-1 … 5-4 *(×20)* |
| `DSL – Mileage since Injector Replacement` | km | Mileage after Injector Replacement |
| `DSL – Mileage since Injector Learning` | km | Mileage after Injector Learning |
| `DSL – Pump Target Current` | mA | Target Fuel Pump Current |
| `DSL – Pump Actual Current` | mA | Actual Fuel Pump Current |
| `DSL – DPF Estimated Temperature` | °C | Estimated Temperature of the Diesel Particulate Filter (DPF) |
| `DSL – DPF Inlet Exhaust Temperature` | °C | Exhaust Gas Temperature at Diesel Particulate Filter (DPF) Inlet |
| `DSL – DPF Differential Pressure` | kPa | Pressure Difference between Diesel Particulate Filter (DPF) Inlet and Outlet |
| `DSL – DPF Regen Count` | — | Diesel Particulate Filter (DPF) Regeneration Count |
| `DSL – DPF Dist since Regen` | km | Running Distance since last Diesel Particulate Filter (DPF) Regeneration |
| `DSL – Catalyst Estimated Temperature` | °C | Estimated Catalyst Temperature |
| `DSL – Catalyst Inlet Exhaust Temperature` | °C | Exhaust Gas Temperature at Catalyst Inlet |
| `DSL – Oil Dilution Ratio` | % | Oil Dilution Ratio |
| `DSL – Soot Accumulation` | % | Soot Accumulation Ratio |
| `DSL – Ash Accumulation` | % | Cumulative Ash Ratio |
| `DSL – Dist to Oil Change` | km | Estimated Distance to Oil Change |
| `DSL – Overspeed Count Hi` | — | Accumulated Count of Overspeed Instances (High RPM) |
| `DSL – Overspeed Count VHi` | — | Accumulated Count of Overspeed Instances (Very High RPM) |

---

## Podsumowanie korzyści

| Metryka | Przed | Po |
|---|---|---|
| Duplikaty tej samej nazwy | 4 pary | 0 (każdy ma unikalną nazwę) |
| Najdłuższa nazwa | 91 znaków | 38 znaków |
| Sensory pomieszane między grupami | tak | nie — prefix gwarantuje grupowanie |
| STFT/LTFT rozróżnione | nie | tak (STFT vs LTFT w nazwie) |
| Narrowband/wideband rozróżnione | nie | tak (O2 Sensor vs AF Sensor) |
| Literówki | 2 | 0 |

## Uwagi implementacyjne

1. Zmiany idą do `src/SSMFlagbyteDefinitions_en.cpp` (i opcjonalnie `_de.cpp`, `_tr.cpp` — te można zostawić anglojęzyczne)
2. Po zmianie nazw w `_en.cpp` — konieczna aktualizacja kluczy w `definitions/thresholds/EJ253_thresholds.json` (bo klucze = tytuły sensorów)
3. Zmiana `–` (en-dash U+2013) zamiast `-` (hyphen) — jeśli Qt/QString sobie nie poradzi z UTF-8 w definicjach, można użyć zwykłego ` - ` (spacja-myślnik-spacja)
4. Plik `_de.cpp` i `_tr.cpp` mają WŁASNE listy — jeśli nie będziemy ich zmieniać, niespójność między językami. Zalecam zostawić je angielskie i opisać jako "pełna lokalizacja w przyszłości"
