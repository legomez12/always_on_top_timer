# How This Application Works

## Repository File Map (High-Level)

This section lists the repository files/folders and their purpose.

### Application Source Files

1. `always_on_top_timer.py`: Program entry point; checks platform, configures Win32 signatures, starts `TimerApp`.
2. `timer_app.py`: Main application controller; creates windows/controls, handles message loop, events, layout, and rendering.
3. `timer_model.py`: Pure timer state/logic (start-stop-reset, elapsed time, formatting).
4. `timer_constants.py`: Centralized Win32/app constants (messages, styles, IDs, colors, layout values).
5. `win32_api.py`: Win32/DWM API loading, ctypes signatures, dark-mode detection, and style helpers.
6. `win32_types.py`: ctypes structure/type definitions used by the Win32 layer.

### Build and Packaging Files

1. `build-portable-exe.ps1`: PowerShell build script for one-file/one-folder PyInstaller outputs.
2. `always_on_top_timer.spec`: PyInstaller spec for one-folder build flow.
3. `AlwaysOnTopTimer.spec`: PyInstaller spec variant for executable packaging.
4. `pyproject.toml`: Project metadata, Python requirement, and dev dependencies.
5. `uv.lock`: Locked dependency graph for reproducible `uv` environments.

### Documentation and Metadata

1. `README.md`: Project overview, usage, build/release notes.
2. `how-this-application-works.md`: Additional architecture and behavior explanation.
3. `LICENSE`: Open-source license text.
4. `.gitattributes`: Git line-ending and attribute rules.
5. `.gitignore`: Ignore rules for generated/local files.

### Automation and Project Support

1. `.github/`: CI/CD workflows (build validation and release automation).
2. `.copilot-chat/`: Request/plan history and project memory notes.
3. `.vscode/`: Local editor/workspace settings (developer convenience).

### Generated/Local Runtime Artifacts

1. `build/`: PyInstaller intermediate build artifacts.
2. `dist/`: Packaged executable outputs.
3. `.venv/`: Local virtual environment.
4. `.mypy_cache/`: Type-check cache files.
5. `__pycache__/`: Python bytecode caches.

## File Load and Dependency Flow

Indented view of what loads what at runtime:

```text
always_on_top_timer.py
   -> win32_api.configure_winapi_signatures()
          -> user32/gdi32/kernel32/dwmapi function signatures
   -> TimerApp (timer_app.py)
          -> imports timer_constants.py (message/style/ID values)
          -> imports timer_model.py (timer behavior/state)
          -> imports win32_api.py (API handles + style/dark-mode helpers)
          -> imports win32_types.py (WNDPROC, WNDCLASSEXW, RECT, etc.)
          -> creates Win32 windows and controls
          -> runs message loop and handles events/hotkeys

build-portable-exe.ps1
   -> pyproject.toml/uv.lock (environment + dependencies)
   -> always_on_top_timer.spec / AlwaysOnTopTimer.spec (PyInstaller build recipes)
   -> dist/ (final packaged artifacts)
```

## Architecture

1. Entry point: always_on_top_timer.py
2. App behavior/controller: timer_app.py
3. Shared timer state: timer_model.py
4. Win32 constant values: timer_constants.py
5. Win32 ctypes structures/callback types: win32_types.py
6. WinAPI bindings and theme helpers: win32_api.py

## Runtime Flow

1. always_on_top_timer.py checks Windows-only, configures WinAPI signatures, then starts TimerApp.
2. TimerApp in timer_app.py creates two native windows:
   - Control window with Start/Stop and Reset
   - Display-only timer window
3. TimerApp registers global hotkeys and a periodic Win32 timer.
4. The Win32 message loop processes events (resize, button click, hotkey, timer tick, close).
5. Both windows render from one shared TimerModel, so they always show the same timer value.

## Windows Modules Used

1. ctypes: bridge from Python to native Windows DLL functions.
2. ctypes.wintypes: Win32-compatible C data types.
3. user32 (via win32_api.py): windows, controls, hotkeys, message loop.
4. gdi32 (via win32_api.py): fonts, brushes, drawing colors.
5. kernel32 (via win32_api.py): module/process-level Win32 support.
6. dwmapi (via win32_api.py): Windows 11 visual attributes like rounded corners and dark title bars.
7. winreg (in win32_api.py): reads Windows theme preference (dark/light).

## Python Modules Used

1. sys: platform checks and process exit behavior.
2. ctypes and ctypes.wintypes: native interop plumbing.
3. time: monotonic timer calculations (inside TimerModel).
4. Project modules: timer_app.py, timer_model.py, timer_constants.py, win32_types.py, win32_api.py.

## How Modules Communicate

1. always_on_top_timer.py imports TimerApp and WinAPI setup, then starts the app.
2. timer_app.py imports:
   - constants from timer_constants.py
   - shared state from timer_model.py
   - WinAPI wrappers and DLL handles from win32_api.py
   - ctypes structures/callback types from win32_types.py
3. TimerApp updates timer state through TimerModel.
4. TimerApp updates native UI through functions and DLL handles provided by win32_api.py.
5. This separation keeps state logic, constants, Win32 plumbing, and UI/action flow cleanly decoupled.
