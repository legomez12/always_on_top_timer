import ctypes
import sys
from ctypes import wintypes

from timer_constants import (
    BS_PUSHBUTTON,
    BTN_RESET_ID,
    BTN_TOGGLE_ID,
    COLOR_WINDOW,
    CONTROL_DEFAULT_HEIGHT,
    CONTROL_DEFAULT_WIDTH,
    CS_HREDRAW,
    CS_VREDRAW,
    CW_USEDEFAULT,
    DISPLAY_DEFAULT_HEIGHT,
    DISPLAY_DEFAULT_WIDTH,
    HOTKEY_QUIT,
    HOTKEY_RESET,
    HOTKEY_TOGGLE,
    HWND_TOPMOST,
    LIGHT_TEXT_COLOR,
    MOD_CONTROL,
    MOD_SHIFT,
    SS_CENTER,
    SS_CENTERIMAGE,
    SW_SHOW,
    SWP_NOACTIVATE,
    SWP_NOMOVE,
    SWP_NOSIZE,
    TIMER_ID,
    TIMER_INTERVAL_MS,
    TRANSPARENT,
    VK_Q,
    VK_R,
    VK_S,
    WM_CLOSE,
    WM_COMMAND,
    WM_CTLCOLORBTN,
    WM_CTLCOLORSTATIC,
    WM_DESTROY,
    WM_HOTKEY,
    WM_SETFONT,
    WM_SIZE,
    WM_TIMER,
    WS_CHILD,
    WS_CLIPCHILDREN,
    WS_OVERLAPPEDWINDOW,
    WS_VISIBLE,
)
from timer_model import TimerModel
from win32_api import (
    apply_windows11_window_style,
    configure_winapi_signatures,
    create_dark_brushes,
    detect_windows_dark_mode,
    gdi32,
    kernel32,
    user32,
)
from win32_types import RECT, WNDCLASSEXW, WNDPROC


if sys.platform != "win32":
    raise SystemExit("This app is Windows-only and uses the Win32 API.")


class TimerApp:
    def __init__(self):
        self.hinstance = kernel32.GetModuleHandleW(None)
        self.class_name = "AlwaysOnTopTimerWindow"
        self.control_title = "Always On Top Timer - Control"
        self.display_title = "Always On Top Timer - Display"

        self.control_hwnd = None
        self.display_hwnd = None

        self.control_label_hwnd = None
        self.display_label_hwnd = None
        self.toggle_hwnd = None
        self.reset_hwnd = None

        self.control_hfont = None
        self.display_hfont = None

        self.use_dark_mode = detect_windows_dark_mode()
        self.background_brush = None
        self.button_background_brush = None
        if self.use_dark_mode:
            self.background_brush, self.button_background_brush = create_dark_brushes()

        self.model = TimerModel()

        self.hotkeys_registered = False
        self.shutting_down = False
        self.alive_windows = 0
        self.last_rendered_time_text = ""

        self._wndproc_ref = WNDPROC(self.wnd_proc)

    def run(self):
        self.register_window_class()
        self.create_windows()
        self.create_child_controls()

        self.register_hotkeys()
        self.enforce_always_on_top()
        user32.SetTimer(self.control_hwnd, TIMER_ID, TIMER_INTERVAL_MS, None)

        user32.ShowWindow(self.control_hwnd, SW_SHOW)
        user32.UpdateWindow(self.control_hwnd)
        user32.ShowWindow(self.display_hwnd, SW_SHOW)
        user32.UpdateWindow(self.display_hwnd)

        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def register_window_class(self):
        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.style = CS_HREDRAW | CS_VREDRAW
        wc.lpfnWndProc = self._wndproc_ref
        wc.cbClsExtra = 0
        wc.cbWndExtra = 0
        wc.hInstance = self.hinstance
        wc.hIcon = user32.LoadIconW(None, ctypes.c_void_p(32512))
        wc.hCursor = user32.LoadCursorW(None, ctypes.c_void_p(32512))
        if self.use_dark_mode and self.background_brush:
            wc.hbrBackground = self.background_brush
        else:
            wc.hbrBackground = ctypes.c_void_p(COLOR_WINDOW + 1)
        wc.lpszMenuName = None
        wc.lpszClassName = self.class_name
        wc.hIconSm = wc.hIcon

        atom = user32.RegisterClassExW(ctypes.byref(wc))
        if atom == 0:
            err = ctypes.get_last_error()
            raise OSError(err, "RegisterClassExW failed")

    def create_windows(self):
        self.control_hwnd = user32.CreateWindowExW(
            0,
            self.class_name,
            self.control_title,
            WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN | WS_VISIBLE,
            CW_USEDEFAULT,
            CW_USEDEFAULT,
            CONTROL_DEFAULT_WIDTH,
            CONTROL_DEFAULT_HEIGHT,
            None,
            None,
            self.hinstance,
            None,
        )
        if not self.control_hwnd:
            err = ctypes.get_last_error()
            raise OSError(err, "CreateWindowExW failed for control window")

        self.display_hwnd = user32.CreateWindowExW(
            0,
            self.class_name,
            self.display_title,
            WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN | WS_VISIBLE,
            CW_USEDEFAULT,
            CW_USEDEFAULT,
            DISPLAY_DEFAULT_WIDTH,
            DISPLAY_DEFAULT_HEIGHT,
            None,
            None,
            self.hinstance,
            None,
        )
        if not self.display_hwnd:
            err = ctypes.get_last_error()
            raise OSError(err, "CreateWindowExW failed for display window")

        apply_windows11_window_style(self.control_hwnd, self.use_dark_mode)
        apply_windows11_window_style(self.display_hwnd, self.use_dark_mode)

        self.alive_windows = 2

    def create_timer_label(self, parent_hwnd):
        label_hwnd = user32.CreateWindowExW(
            0,
            "STATIC",
            "00:00:00",
            WS_CHILD | WS_VISIBLE | SS_CENTER | SS_CENTERIMAGE,
            0,
            0,
            100,
            100,
            parent_hwnd,
            None,
            self.hinstance,
            None,
        )
        if not label_hwnd:
            err = ctypes.get_last_error()
            raise OSError(err, "CreateWindowExW failed for STATIC control")
        return label_hwnd

    def create_child_controls(self):
        self.control_label_hwnd = self.create_timer_label(self.control_hwnd)
        self.display_label_hwnd = self.create_timer_label(self.display_hwnd)

        self.toggle_hwnd = user32.CreateWindowExW(
            0,
            "BUTTON",
            "Start",
            WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
            0,
            0,
            100,
            32,
            self.control_hwnd,
            ctypes.c_void_p(BTN_TOGGLE_ID),
            self.hinstance,
            None,
        )
        if not self.toggle_hwnd:
            err = ctypes.get_last_error()
            raise OSError(err, "CreateWindowExW failed for Start button")

        self.reset_hwnd = user32.CreateWindowExW(
            0,
            "BUTTON",
            "Reset",
            WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
            0,
            0,
            100,
            32,
            self.control_hwnd,
            ctypes.c_void_p(BTN_RESET_ID),
            self.hinstance,
            None,
        )
        if not self.reset_hwnd:
            err = ctypes.get_last_error()
            raise OSError(err, "CreateWindowExW failed for Reset button")

        self.update_control_layout()
        self.update_display_layout()
        self.update_timer_labels()
        self.update_toggle_button()

    def register_hotkeys(self):
        user32.RegisterHotKey(self.control_hwnd, HOTKEY_TOGGLE, MOD_CONTROL | MOD_SHIFT, VK_S)
        user32.RegisterHotKey(self.control_hwnd, HOTKEY_RESET, MOD_CONTROL | MOD_SHIFT, VK_R)
        user32.RegisterHotKey(self.control_hwnd, HOTKEY_QUIT, MOD_CONTROL | MOD_SHIFT, VK_Q)
        self.hotkeys_registered = True

    def unregister_hotkeys(self):
        if not self.hotkeys_registered:
            return
        user32.UnregisterHotKey(self.control_hwnd, HOTKEY_TOGGLE)
        user32.UnregisterHotKey(self.control_hwnd, HOTKEY_RESET)
        user32.UnregisterHotKey(self.control_hwnd, HOTKEY_QUIT)
        self.hotkeys_registered = False

    def set_window_always_on_top(self, hwnd):
        user32.SetWindowPos(
            hwnd,
            HWND_TOPMOST,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
        )

    def enforce_always_on_top(self):
        if self.control_hwnd:
            self.set_window_always_on_top(self.control_hwnd)
        if self.display_hwnd:
            self.set_window_always_on_top(self.display_hwnd)

    def update_toggle_button(self):
        if self.toggle_hwnd:
            user32.SetWindowTextW(self.toggle_hwnd, "Stop" if self.model.running else "Start")

    def update_timer_labels(self):
        text = self.model.formatted_time()
        if text == self.last_rendered_time_text:
            return

        self.last_rendered_time_text = text
        if self.control_label_hwnd:
            user32.SetWindowTextW(self.control_label_hwnd, text)
        if self.display_label_hwnd:
            user32.SetWindowTextW(self.display_label_hwnd, text)

    def toggle_timer(self):
        self.model.toggle()
        self.update_toggle_button()
        self.update_timer_labels()

    def reset_timer(self):
        self.model.reset()
        self.update_timer_labels()

    def get_client_size(self, hwnd):
        rect = RECT()
        user32.GetClientRect(hwnd, ctypes.byref(rect))
        return rect.right - rect.left, rect.bottom - rect.top

    def update_control_layout(self):
        width, height = self.get_client_size(self.control_hwnd)
        width = max(320, width)
        height = max(180, height)

        padding = 12
        button_height = 34
        button_spacing = 12
        label_height = max(70, height - button_height - (padding * 3))

        button_width = (width - (padding * 2) - button_spacing) // 2

        user32.MoveWindow(
            self.control_label_hwnd,
            padding,
            padding,
            width - (padding * 2),
            label_height,
            True,
        )

        button_y = padding * 2 + label_height
        user32.MoveWindow(self.toggle_hwnd, padding, button_y, button_width, button_height, True)
        user32.MoveWindow(
            self.reset_hwnd,
            padding + button_width + button_spacing,
            button_y,
            button_width,
            button_height,
            True,
        )

        self.update_label_font(
            self.control_hwnd,
            self.control_label_hwnd,
            width,
            label_height,
            is_control_window=True,
        )

    def update_display_layout(self):
        width, height = self.get_client_size(self.display_hwnd)
        width = max(240, width)
        height = max(120, height)

        padding = 12

        user32.MoveWindow(
            self.display_label_hwnd,
            padding,
            padding,
            width - (padding * 2),
            height - (padding * 2),
            True,
        )

        self.update_label_font(
            self.display_hwnd,
            self.display_label_hwnd,
            width,
            height,
            is_control_window=False,
        )

    def update_label_font(self, window_hwnd, label_hwnd, width, height, is_control_window):
        if is_control_window:
            target_points = max(24, min(width // 7, height // 2))
        else:
            target_points = max(28, min(width // 6, height // 2))

        hdc = user32.GetDC(window_hwnd)
        dpi = gdi32.GetDeviceCaps(hdc, 90)
        user32.ReleaseDC(window_hwnd, hdc)

        height_px = -int(target_points * dpi / 72)

        new_font = gdi32.CreateFontW(
            height_px,
            0,
            0,
            0,
            700,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            "Segoe UI" if is_control_window else "Segoe UI Variable Display",
        )

        if new_font:
            if is_control_window:
                old_font = self.control_hfont
                self.control_hfont = new_font
            else:
                old_font = self.display_hfont
                self.display_hfont = new_font

            user32.SendMessageW(label_hwnd, WM_SETFONT, new_font, 1)
            if old_font and old_font != new_font:
                gdi32.DeleteObject(old_font)

    def handle_command(self, wparam):
        command_id = wparam & 0xFFFF
        if command_id == BTN_TOGGLE_ID:
            self.toggle_timer()
        elif command_id == BTN_RESET_ID:
            self.reset_timer()

    def cleanup_window_resources(self, hwnd):
        if hwnd == self.control_hwnd:
            if self.control_hfont:
                gdi32.DeleteObject(self.control_hfont)
                self.control_hfont = None
            self.control_hwnd = None
            self.control_label_hwnd = None
            self.toggle_hwnd = None
            self.reset_hwnd = None
        elif hwnd == self.display_hwnd:
            if self.display_hfont:
                gdi32.DeleteObject(self.display_hfont)
                self.display_hfont = None
            self.display_hwnd = None
            self.display_label_hwnd = None

    def cleanup_theme_resources(self):
        if self.background_brush:
            gdi32.DeleteObject(self.background_brush)
            self.background_brush = None
        if self.button_background_brush:
            gdi32.DeleteObject(self.button_background_brush)
            self.button_background_brush = None

    def initiate_shutdown(self):
        if self.shutting_down:
            return

        self.shutting_down = True
        self.unregister_hotkeys()

        if self.control_hwnd:
            user32.KillTimer(self.control_hwnd, TIMER_ID)

        control_hwnd = self.control_hwnd
        display_hwnd = self.display_hwnd

        if control_hwnd:
            user32.DestroyWindow(control_hwnd)
        if display_hwnd and display_hwnd != control_hwnd:
            user32.DestroyWindow(display_hwnd)

    def handle_window_destroy(self, hwnd):
        self.cleanup_window_resources(hwnd)
        self.alive_windows -= 1
        if self.alive_windows <= 0:
            self.cleanup_theme_resources()
            user32.PostQuitMessage(0)

    def wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_CLOSE:
            self.initiate_shutdown()
            return 0

        if msg == WM_SIZE:
            if hwnd == self.control_hwnd and self.control_label_hwnd and self.toggle_hwnd and self.reset_hwnd:
                self.update_control_layout()
                self.set_window_always_on_top(self.control_hwnd)
            elif hwnd == self.display_hwnd and self.display_label_hwnd:
                self.update_display_layout()
                self.set_window_always_on_top(self.display_hwnd)
            return 0

        if msg == WM_COMMAND:
            if hwnd == self.control_hwnd:
                self.handle_command(wparam)
            return 0

        if msg == WM_CTLCOLORSTATIC and self.use_dark_mode and self.background_brush:
            hdc = wintypes.HDC(wparam)
            gdi32.SetTextColor(hdc, LIGHT_TEXT_COLOR)
            gdi32.SetBkMode(hdc, TRANSPARENT)
            gdi32.SetBkColor(hdc, DARK_BG_COLOR)
            return self.background_brush

        if msg == WM_CTLCOLORBTN and self.use_dark_mode:
            hdc = wintypes.HDC(wparam)
            gdi32.SetTextColor(hdc, LIGHT_TEXT_COLOR)
            gdi32.SetBkColor(hdc, DARK_BUTTON_BG_COLOR)
            if self.button_background_brush:
                return self.button_background_brush
            return self.background_brush if self.background_brush else 0

        if msg == WM_HOTKEY:
            if wparam == HOTKEY_TOGGLE:
                self.toggle_timer()
            elif wparam == HOTKEY_RESET:
                self.reset_timer()
            elif wparam == HOTKEY_QUIT:
                self.initiate_shutdown()
            return 0

        if msg == WM_TIMER:
            if hwnd == self.control_hwnd and wparam == TIMER_ID:
                self.update_timer_labels()
            return 0

        if msg == WM_DESTROY:
            self.handle_window_destroy(hwnd)
            return 0

        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def main():
    configure_winapi_signatures()
    TimerApp().run()


if __name__ == "__main__":
    main()