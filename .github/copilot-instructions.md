# FreeSSM — Copilot Instructions

## Build & Deploy

### Po każdej kompilacji OBOWIĄZKOWE kroki:

1. Skompiluj release:
   ```powershell
   $env:PATH = "C:\Qt\5.15.2\mingw81_64\bin;C:\Qt\Tools\mingw810_64\bin;" + $env:PATH
   mingw32-make -j4 release
   ```

2. Utwórz folder wersji i skopiuj exe:
   ```powershell
   New-Item -ItemType Directory -Force "builds\vX.Y.Z-ms.N"
   Copy-Item "release\FreeSSM.exe" "builds\vX.Y.Z-ms.N\"
   ```

3. **ZAWSZE uruchom windeployqt** — bez tego exe nie uruchomi się na innym komputerze (brakuje DLL Qt):
   ```powershell
   windeployqt "builds\vX.Y.Z-ms.N\FreeSSM.exe"
   ```
   **UWAGA**: NIE używaj flagi `--release` — Qt 5.15.2 MinGW ma pluginy tylko jako debug build i windeployqt z `--release` zwróci błąd "Unable to find the platform plugin" i nie skopiuje nic.
   `windeployqt` jest w `C:\Qt\5.15.2\mingw81_64\bin\` i jest już w PATH po kroku 1.

4. **Skopiuj Qt5SerialPort.dll ręcznie** — windeployqt go nie wykrywa automatycznie, ale FreeSSM go wymaga:
   ```powershell
   Copy-Item "C:\Qt\5.15.2\mingw81_64\bin\Qt5SerialPort.dll" "builds\vX.Y.Z-ms.N\"
   ```

5. Skopiuj `definitions/` do folderu builds (pliki XML z definicjami protokołu SSM):
   ```powershell
   Copy-Item -Recurse "definitions" "builds\vX.Y.Z-ms.N\"
   ```

### Wynik: folder `builds\vX.Y.Z-ms.N\` musi zawierać:
- `FreeSSM.exe`
- Wszystkie DLL Qt (Qt5Core, Qt5Gui, Qt5Widgets, Qt5PrintSupport, Qt5SerialPort itd.)
- `platforms\` (qwindows.dll)
- `definitions\` (pliki XML)
- Ewentualne MinGW runtime DLL (libgcc, libstdc++, libwinpthread)

Tylko wtedy folder można przenieść na inny komputer i uruchomić bez instalacji Qt.

## Wersjonowanie

- `fix:` → bump PATCH (np. ms.7 → ms.8): zmień w `src/main.cpp`
- `feat:` → bump MINOR
- Zawsze tag `vX.Y.Z-ms.N` + `git push origin feature/simulation-mode --tags`

## Gałąź robocza

- Zawsze `feature/simulation-mode`
- Remote: `https://github.com/mstepuch/FreeSSM.git`
