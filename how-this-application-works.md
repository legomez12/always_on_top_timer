# How This Application Works

## Core Files

1. always_on_top_timer.py
   - Entry point.
   - Verifies Windows.
   - Configures Win32 signatures, then starts TimerApp.

2. timer_app.py
   - Main app controller.
   - Creates windows/controls.
   - Handles message loop, hotkeys, layout, drawing, and shutdown.

3. timer_model.py
   - Timer state and logic only.
   - Start, stop, reset, elapsed time, formatted output.

4. timer_constants.py
   - Central Win32 and app constants.

5. win32_api.py
   - Win32 DLL bindings and ctypes signatures.
   - Dark-mode/theme helper logic.

6. win32_types.py
   - ctypes Win32 structures and callback types.

## Runtime Flow

1. always_on_top_timer.py starts and configures WinAPI signatures.
2. TimerApp initializes state and UI.
3. TimerApp creates control + display windows.
4. TimerApp registers global hotkeys and timer tick updates.
5. Win32 message loop dispatches events.
6. timer_model.py remains the single source of timer truth for both windows.

## Load and Dependency Flow

```text
always_on_top_timer.py
  -> win32_api.configure_winapi_signatures()
  -> TimerApp (timer_app.py)
       -> timer_constants.py
       -> timer_model.py
       -> win32_api.py
       -> win32_types.py

build-portable-exe.ps1
  -> pyproject.toml + uv.lock
  -> always_on_top_timer.spec / AlwaysOnTopTimer.spec
  -> dist/
```

## Build and Packaging (Minimal)

1. build-portable-exe.ps1 builds onefile/onedir artifacts.
2. spec files define PyInstaller packaging behavior.
3. dist/ contains final executables.
