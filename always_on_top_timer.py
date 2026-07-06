import ctypes
import sys
import time
from ctypes import wintypes


if sys.platform != "win32":
    raise SystemExit("This app is Windows-only and uses the Win32 API.")


user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

LRESULT = ctypes.c_ssize_t
HCURSOR = wintypes.HANDLE
WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)

UINT_PTR = getattr(
    wintypes,
    "UINT_PTR",
    ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else wintypes.UINT,
)


CW_USEDEFAULT = -2147483648

CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001

WS_CHILD = 0x40000000
WS_VISIBLE = 0x10000000
WS_OVERLAPPEDWINDOW = 0x00CF0000

BS_PUSHBUTTON = 0x00000000
SS_CENTER = 0x00000001

SW_SHOW = 5

WM_CLOSE = 0x0010
WM_DESTROY = 0x0002
WM_SIZE = 0x0005
WM_COMMAND = 0x0111
WM_SETFONT = 0x0030
WM_HOTKEY = 0x0312
WM_TIMER = 0x0113

MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004

VK_S = 0x53
VK_R = 0x52
VK_Q = 0x51

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
HWND_TOPMOST = -1

HOTKEY_TOGGLE = 1
HOTKEY_RESET = 2
HOTKEY_QUIT = 3

TIMER_ID = 1
TIMER_INTERVAL_MS = 100

BTN_TOGGLE_ID = 1001
BTN_RESET_ID = 1002

CONTROL_DEFAULT_WIDTH = 520
CONTROL_DEFAULT_HEIGHT = 260
DISPLAY_DEFAULT_WIDTH = 520
DISPLAY_DEFAULT_HEIGHT = 180


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", HCURSOR),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HICON),
    ]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


def configure_winapi_signatures():
    # Explicit signatures avoid 64-bit truncation/overflow in message params.
    user32.DefWindowProcW.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    user32.DefWindowProcW.restype = LRESULT

    user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.DispatchMessageW.restype = LRESULT

    user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.TranslateMessage.restype = wintypes.BOOL

    user32.GetMessageW.argtypes = [
        ctypes.POINTER(wintypes.MSG),
        wintypes.HWND,
        wintypes.UINT,
        wintypes.UINT,
    ]
    user32.GetMessageW.restype = wintypes.BOOL

    user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
    user32.RegisterClassExW.restype = wintypes.ATOM

    user32.CreateWindowExW.argtypes = [
        wintypes.DWORD,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.HWND,
        wintypes.HMENU,
        wintypes.HINSTANCE,
        wintypes.LPVOID,
    ]
    user32.CreateWindowExW.restype = wintypes.HWND

    user32.SetWindowPos.argtypes = [
        wintypes.HWND,
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    ]
    user32.SetWindowPos.restype = wintypes.BOOL

    user32.SendMessageW.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    user32.SendMessageW.restype = LRESULT

    user32.SetTimer.argtypes = [
        wintypes.HWND,
        UINT_PTR,
        wintypes.UINT,
        wintypes.LPVOID,
    ]
    user32.SetTimer.restype = UINT_PTR

    user32.KillTimer.argtypes = [wintypes.HWND, UINT_PTR]
    user32.KillTimer.restype = wintypes.BOOL

    user32.RegisterHotKey.argtypes = [
        wintypes.HWND,
        ctypes.c_int,
        wintypes.UINT,
        wintypes.UINT,
    ]
    user32.RegisterHotKey.restype = wintypes.BOOL

    user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.UnregisterHotKey.restype = wintypes.BOOL

    gdi32.GetDeviceCaps.argtypes = [wintypes.HDC, ctypes.c_int]
    gdi32.GetDeviceCaps.restype = ctypes.c_int

    user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
    user32.GetClientRect.restype = wintypes.BOOL

    user32.MoveWindow.argtypes = [
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.BOOL,
    ]
    user32.MoveWindow.restype = wintypes.BOOL

    user32.SetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
    user32.SetWindowTextW.restype = wintypes.BOOL

    user32.DestroyWindow.argtypes = [wintypes.HWND]
    user32.DestroyWindow.restype = wintypes.BOOL

    user32.PostQuitMessage.argtypes = [ctypes.c_int]
    user32.PostQuitMessage.restype = None

    user32.GetDC.argtypes = [wintypes.HWND]
    user32.GetDC.restype = wintypes.HDC

    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    user32.ReleaseDC.restype = ctypes.c_int

    gdi32.CreateFontW.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPCWSTR,
    ]
    gdi32.CreateFontW.restype = wintypes.HFONT

    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi32.DeleteObject.restype = wintypes.BOOL


class TimerModel:
    def __init__(self):
        self.elapsed_seconds = 0.0
        self.running = False
        self.last_start_monotonic = None

    def toggle(self):
        if self.running:
            if self.last_start_monotonic is not None:
                self.elapsed_seconds += time.monotonic() - self.last_start_monotonic
            self.running = False
            self.last_start_monotonic = None
        else:
            self.running = True
            self.last_start_monotonic = time.monotonic()

    def reset(self):
        self.elapsed_seconds = 0.0
        if self.running:
            self.last_start_monotonic = time.monotonic()

    def total_seconds(self):
        total = self.elapsed_seconds
        if self.running and self.last_start_monotonic is not None:
            total += time.monotonic() - self.last_start_monotonic
        return int(total)

    def formatted_time(self):
        total_seconds = self.total_seconds()
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"


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

        self.model = TimerModel()

        self.hotkeys_registered = False
        self.shutting_down = False
        self.alive_windows = 0

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
        wc.hbrBackground = ctypes.c_void_p(5 + 1)
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
            WS_OVERLAPPEDWINDOW | WS_VISIBLE,
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
            WS_OVERLAPPEDWINDOW | WS_VISIBLE,
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

        self.alive_windows = 2

    def create_timer_label(self, parent_hwnd):
        label_hwnd = user32.CreateWindowExW(
            0,
            "STATIC",
            "00:00:00",
            WS_CHILD | WS_VISIBLE | SS_CENTER,
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
            "Segoe UI",
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
            user32.PostQuitMessage(0)

    def wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_CLOSE:
            self.initiate_shutdown()
            return 0

        if msg == WM_SIZE:
            if hwnd == self.control_hwnd and self.control_label_hwnd and self.toggle_hwnd and self.reset_hwnd:
                self.update_control_layout()
            elif hwnd == self.display_hwnd and self.display_label_hwnd:
                self.update_display_layout()
            return 0

        if msg == WM_COMMAND:
            if hwnd == self.control_hwnd:
                self.handle_command(wparam)
            return 0

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
                self.enforce_always_on_top()
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