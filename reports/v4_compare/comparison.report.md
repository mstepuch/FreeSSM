# FreeSSM Cross-Fuel Comparison Report

**Petrol log:** `logs\FreeSSM_log_cleared_memory_cold_start_gasoline_only.csv` (health 0/100)  
**LPG log:**    `logs\FreeSSM_log2.csv` (health 66/100)

## Auto-narrative
- WOT lambda petrol=1.02 (lean) vs lpg=0.99 (correct). The same engine cannot keep stoich at WOT on petrol but can on LPG. Mechanical/intake/ignition causes are excluded; the fault is on the petrol fuel side (injectors, pump, regulator, filter).
- Health score gap = 66 (petrol is materially worse). When the same engine scores very differently between fuels, the problem is fuel-specific to petrol.

## Side-by-side metrics
| Metric | Petrol | LPG | Δ (petrol - lpg) | Unit |
|---|---:|---:|---:|---|
| Idle LTFT (median) | -6.30 | -6.30 | +0.00 | % |
| Idle STFT (mean) | -3.03 | +0.18 | -3.21 | % |
| Cruise LTFT (median) | +0.00 | -3.90 | +3.90 | % |
| Cruise STFT std | +3.01 | +4.98 | -1.97 | % |
| WOT lambda (median) | +1.02 | +0.99 | +0.03 |  |
| WOT STFT p95 | +24.20 | +2.30 | +21.90 | % |
| WOT STFT mean | +9.43 | -0.14 | +9.57 | % |
| Idle MAP (kPa abs) | +33.00 | +25.00 | +8.00 | kPa |
| Idle MAF (g/s) | +3.84 | +2.85 | +0.99 | g/s |
| Knock learn p95 (loaded) | +6.00 | +7.00 | -1.00 | deg |
| Health score | 0 | 66 | -66 | /100 |

## Checks with different severity between fuels
| Check | Petrol | LPG | Fuel-specific |
|---|---|---|---|
| Lambda CL tracking | alarm | pass | petrol |
| Power enrichment (WOT) | alarm | pass | petrol |
| WOT fuel delivery | alarm | pass | petrol |
| Injector cross-load signature | alarm | pass | petrol |
| Idle LTFT (warm) | warn | pass | petrol |
| Idle RPM stability | warn | pass | petrol |
| Learned knock advance | warn | info | petrol |
| Ignition timing during warmup | warn | pass | petrol |
| STFT volatility (cruise) | pass | warn | lpg |
| Manifold vacuum at idle | pass | warn | lpg |
