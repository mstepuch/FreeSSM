# FreeSSM Modernization Plan

**Fork:** github.com/mstepuch/FreeSSM  
**Upstream:** github.com/Comer352L/FreeSSM  
**Started:** 2026-04-20  

---

## Phase 1: Foundation & Quick Wins
*Goal: Make the app more usable without touching core protocol/communication code.*

### 1.1 Fix UI Layout Issues
- **Branch:** `feature/fix-layout`
- **Problem:** Buttons/icons clipped on modern Windows DPI scaling
- **Scope:** Adjust FreeSSM.ui layout policies, minimum sizes, icon scaling
- **Files:** `ui/FreeSSM.ui`, possibly `src/FreeSSM.cpp` (icon loading)
- **Risk:** Low — UI-only, no logic changes
- **Verify:** Visual check at 100%, 125%, 150% scaling

### 1.2 CSV Data Logging (Measuring Blocks)
- **Branch:** `feature/csv-logging`
- **Problem:** Real-time sensor data displayed but never saved to file
- **Scope:** Add Start/Stop logging button + CSV writer to `CUcontent_MBsSWs`
- **Files:**
  - `src/CUcontent_MBsSWs.h` — add logging state, QFile member, slot declarations
  - `src/CUcontent_MBsSWs.cpp` — implement start/stop logging, CSV write on data update
  - `ui/CUcontent_MBsSWs.ui` — add Log button to toolbar area
- **CSV format:** `timestamp, param1_name, param1_value, param1_unit, param2_name, ...`
- **Risk:** Low — additive change, no modification of existing data flow
- **Verify:** Start logging, observe file growing, stop, open in Excel

### 1.3 Export Diagnostic Codes to File
- **Branch:** `feature/export-dtc`
- **Problem:** DTCs can only be printed to physical printer, no file export
- **Scope:** Add "Save to file" button alongside existing "Print" button
- **Files:**
  - `src/CUcontent_DCs_abstract.h` — declare export slot
  - `src/CUcontent_DCs_abstract.cpp` — implement CSV/text export
- **Risk:** Low — additive, uses existing data already gathered for print
- **Verify:** Export codes, verify file content matches screen

---

## Phase 2: Code Quality & Compatibility
*Goal: Clean up deprecated APIs, improve stability.*

### 2.1 Drop Qt4 Support
- **Branch:** `feature/drop-qt4`
- **Problem:** Conditional Qt4/Qt5 code duplication throughout codebase
- **Scope:** Remove all `QT_MAJOR_VERSION < 5` blocks, remove deprecated API usage
- **Files:** Multiple (grep for `QT_VERSION`, `QT_MAJOR_VERSION`, `setResizeMode`)
- **Key changes:**
  - `setResizeMode()` → `setSectionResizeMode()`
  - Remove `QDesktopWidget` usage → use `QScreen`
  - Remove Qt4-specific DLL install targets from `.pro`
  - Set minimum Qt version to 5.12+
- **Risk:** Medium — touches many files, but changes are mechanical
- **Verify:** Clean compile with zero new warnings, full app walkthrough

### 2.2 Add Polish Translation
- **Branch:** `feature/polish-translation`
- **Problem:** Only EN, DE, TR supported; no Polish
- **Scope:** Create `FreeSSM_pl.ts`, add to `.pro`, add language enum
- **Files:**
  - `FreeSSM_pl.ts` — new translation file
  - `src/Languages.h` — add Polish enum
  - `src/FreeSSM.cpp` — add Polish to language selection
  - `FreeSSM.pro` — add to TRANSLATIONS
- **Risk:** Low — additive
- **Verify:** Switch to Polish in Preferences, verify UI strings

---

## Phase 3: Interface & Protocol Enhancements
*Goal: Better adapter support, enable experimental features.*

### 3.1 Enable ELM327 K-Line (ISO14230) Support
- **Branch:** `feature/elm327-kline`
- **Problem:** AT-command adapter ISO14230 support exists but is disabled (#ifdef)
- **Scope:** Enable `__ENABLE_SSM2_ISO14230_EXPERIMENTAL_SUPPORT__`, test, stabilize
- **Files:**
  - `src/ATcommandControlledDiagInterface.cpp` — uncomment/enable define
  - Possibly fix issues discovered during testing
- **Risk:** Medium — experimental code, needs real hardware testing
- **Verify:** Connect ELM327 via K-line, attempt ECU communication

### 3.2 Improve Serial Port Enumeration (Bluetooth)
- **Branch:** `feature/bluetooth-serial`
- **Problem:** Windows BT serial ports may not always appear in registry scan
- **Scope:** Enhance `windows/serialCOM.cpp` port discovery
- **Files:** `src/windows/serialCOM.cpp`
- **Risk:** Medium — platform-specific, needs BT hardware to test
- **Verify:** Pair BT adapter, verify port appears in Preferences dropdown

---

## Phase 4: Advanced Features (Future)
*These require more design work and possibly upstream discussion.*

### 4.1 Real-Time Data Charts
- Add QCustomPlot or QtCharts for graphing sensor trends
- Depends on: 1.2 (CSV logging data flow)

### 4.2 Session Save/Load
- Save complete diagnostic session (DTCs + MB readings + metadata) to JSON/XML
- Replay sessions offline

### 4.3 Modern UI Refresh
- Dark mode support
- Responsive layout for different screen sizes
- Replace fixed-size dialogs with proper QMainWindow + dock widgets

### 4.4 Qt6 Port
- Depends on: 2.1 (Drop Qt4)
- Address remaining Qt5 deprecations
- Test with Qt 6.5 LTS

---

## Priority Order

| # | Task | Effort | Value | Dependencies |
|---|------|--------|-------|--------------|
| 1 | Fix UI Layout (1.1) | Small | High | None |
| 2 | CSV Data Logging (1.2) | Medium | Critical | None |
| 3 | Export DTCs (1.3) | Small | High | None |
| 4 | Polish Translation (2.2) | Small | Medium | None |
| 5 | Drop Qt4 (2.1) | Medium | Medium | None |
| 6 | ELM327 K-Line (3.1) | Medium | High | Hardware test |
| 7 | BT Serial (3.2) | Medium | Medium | BT hardware |
| 8 | Charts (4.1) | Large | High | 1.2 |
| 9 | Qt6 Port (4.4) | Large | Medium | 2.1 |

---

## Research Findings Summary (Gemini Deep Search, April 2026)

Full report: [doc/subaru-diagnostics-research.md](doc/subaru-diagnostics-research.md)

### Key Insights for This Fork

**Target car: Subaru Outback 2006 2.5L gasoline (EJ253, SSM2 via K-Line)**

1. **SSM2 K-Line is our sweet spot.** Cars from 1999–2008 use SSM2 over K-Line at 4800 baud.
   FreeSSM already supports this fully via `SerialPassThroughDiagInterface` (VAG KKL / FTDI).
   Our 2006 Outback falls squarely in this range — all features should work out of the box.

2. **SSM2 via CAN (2008–2021)** extends the same logical protocol over ISO 15765-2 (ISO-TP).
   Already supported via J2534 interface. No protocol changes needed for these cars, only
   multi-frame message handling is required (already implemented in J2534DiagInterface).

3. **UDS (2020+ models) is out of scope.** New Subaru Global Platform uses ISO 14229 with
   Seed/Key crypto — completely different from SSM2. Implementing UDS would be a rewrite,
   not an extension. We won't pursue this.

4. **Security Gateway (SGW) kills open-source access for 2024+ cars.** Requires AutoAuth
   subscription and cloud authentication. Not feasible for FreeSSM. Our focus stays on
   pre-SGW vehicles (≤2021).

5. **Tactrix OpenPort 2.0 is dead.** Company shut down, clones are unreliable (especially
   for K-Line on 16-bit ECUs). FreeSSM's J2534 loader should support any compliant DLL —
   this already works, but improved detection (Issue #83) is wanted by users.

6. **ELM327 for SSM2 is problematic.** Cheap clones have buffer overflow issues with long
   multi-frame SSM2 messages over CAN. For K-Line (our car), ELM327 ISO14230 mode exists
   in FreeSSM but is disabled. Premium adapters (OBDLink MX+, vLinker MC+) handle it better.

7. **PR #81 (CSV logging)** by jmadden173 already exists as a draft — tested on a 2004
   Outback (same generation as ours). We should review and build on it rather than starting
   from scratch.

8. **BtSsm app** proves that SSM2 over K-Line + Bluetooth is viable for pre-2015 cars.
   Users mount phone dashboards connected via VAG KKL + USB-OTG on Android.

9. **External XML definitions** (like RomRaider Logger uses) are the correct long-term
   architecture. FreeSSM currently hardcodes definitions in C++ source. Not a priority for
   us now, but worth noting for upstream contributions.

10. **Solterra uses Toyota GTS+, not SSM at all.** Completely irrelevant for FreeSSM.

### What This Means for Our Priority Order

| Priority | Task | Rationale |
|----------|------|-----------|
| **1** | CSV Data Logging (1.2) | Most requested feature, PR #81 exists as reference, directly useful for our 2006 Outback |
| **2** | Export DTCs (1.3) | Quick win, no file export exists despite data being available |
| **3** | Fix UI Layout (1.1) | DPI scaling issues on modern Windows |
| **4** | Polish Translation (2.2) | Personal use, low effort |
| **5** | ELM327 K-Line (3.1) | Enable existing disabled code — allows using cheap BT adapters for K-Line cars |
| **6** | BT Serial Ports (3.2) | Needed for wireless diagnosis on older cars like ours |
| **7** | Drop Qt4 (2.1) | Code cleanup, easier maintenance |
| **8** | Charts (4.1) | Nice-to-have once logging works |
| **9** | Qt6 Port (4.4) | Future-proofing |

### Out of Scope (Confirmed by Research)

- **UDS protocol implementation** — too complex, requires crypto reverse engineering
- **Security Gateway bypass** — legally and technically infeasible for open-source
- **e-BOXER / hybrid diagnostics** — requires UDS + CAN-FD, different ecosystem
- **Solterra support** — Toyota platform, not Subaru SSM
- **SSM3/4/5 compatibility** — these are dealer software brands, not protocols

---

## Development Standards

See repo memory: development rules applied to all changes.

1. One feature branch per task
2. Compile after every file edit (`mingw32-make -j4 release`)
3. Read target files fully before modifying
4. Match original code style (camelCase, `_memberVars`)
5. C++11 standard, no new external dependencies
6. Atomic commits with conventional commit messages
7. Visual verification after UI changes
8. Zero new compiler warnings
