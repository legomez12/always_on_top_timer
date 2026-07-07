# always_on_top_timer

A lightweight Windows desktop timer built with native Win32 UI APIs via Python `ctypes`.

The app opens two independent windows that share the same timer state:

- A control window with Start/Stop and Reset buttons
- A display-only window for clean second-screen viewing

Both windows are always on top, resizable, movable, and stay perfectly synchronized.

## Features

- Native Windows UI (Win32): no Qt or web UI runtime required
- Two synchronized always-on-top windows (control + display-only)
- Shared count-up timer model (single source of truth)
- Start/Stop and Reset controls in the main window
- Dynamic timer font scaling in both windows when resized
- Global hotkeys (work system-wide on Windows)

## Hotkeys

- `Ctrl+Shift+S`: Start / Stop
- `Ctrl+Shift+R`: Reset
- `Ctrl+Shift+Q`: Quit

## Requirements

- Windows 10/11
- Python 3.12+
- `uv` recommended for environment and execution

## Run

From the project root:

```powershell
uv sync
uv run python always_on_top_timer.py
```

## Technical Notes

- UI and event loop are implemented directly with Win32 (`user32`, `gdi32`) using `ctypes`.
- Timer state is managed in a shared controller/model and rendered in both windows.
- Global hotkeys use `RegisterHotKey` and are unregistered on exit.
- The timer uses `time.monotonic()` for stable elapsed-time tracking.

## Portable EXE Build (No Installer)

This project supports portable `.exe` output for Windows. No MSI/setup installer is created.

Build both one-folder and one-file artifacts:

```powershell
uv sync
./build-portable-exe.ps1 -Mode both -Clean
```

Output artifacts:

- `dist/AlwaysOnTopTimer/AlwaysOnTopTimer.exe` (one-folder, faster startup)
- `dist/AlwaysOnTopTimer.exe` (single-file, easier to copy)

Run behavior:

- Copy the executable (or one-folder dist) to another Windows machine and run directly.
- No installation step is required.

## Download From Releases

Download the latest prebuilt Windows executable package from GitHub Releases.

Recommended asset:

- `AlwaysOnTopTimer-vX.Y.Z-onefile.exe`

Optional verification:

1. Download `AlwaysOnTopTimer-vX.Y.Z-sha256.txt`.
2. Run a local hash check (PowerShell):

    ```powershell
    Get-FileHash .\AlwaysOnTopTimer-vX.Y.Z-onefile.exe -Algorithm SHA256
    ```

3. Confirm the hash matches the checksum file entry.

One file build: `v1.0.1` (2026-07-06)
