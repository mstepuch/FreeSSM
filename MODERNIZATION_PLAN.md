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
