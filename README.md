# always_on_top_timer

A lightweight Windows desktop timer built with native Win32 UI APIs via Python `ctypes`.

The app is always on top, renders a large auto-scaling timer display, and supports system-wide hotkeys so you can control it even when the window is not focused.

## Features

- Native Windows UI (Win32): no Qt or web UI runtime required
- Always-on-top timer window
- Count-up timer with Start/Stop and Reset buttons
- Dynamic timer font scaling when the window is resized
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
- Global hotkeys use `RegisterHotKey` and are unregistered on exit.
- The timer uses `time.monotonic()` for stable elapsed-time tracking.
