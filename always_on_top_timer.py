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

WM_CREATE = 0x0001
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

DEFAULT_WIDTH = 520
DEFAULT_HEIGHT = 260


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


class TimerApp:
    def __init__(self):
        self.hinstance = kernel32.GetModuleHandleW(None)
        self.class_name = "AlwaysOnTopTimerWindow"
        self.title = "Always On Top Timer"

        self.hwnd = None
        self.label_hwnd = None
        self.toggle_hwnd = None
        self.reset_hwnd = None
        self.hfont = None

        self.elapsed_seconds = 0.0
        self.running = False
        self.last_start_monotonic = None

        self._wndproc_ref = WNDPROC(self.wnd_proc)

    def run(self):
        self.register_window_class()
        self.create_main_window()
        self.create_child_controls()
        self.register_hotkeys()
        self.set_always_on_top()
        user32.SetTimer(self.hwnd, TIMER_ID, TIMER_INTERVAL_MS, None)

        user32.ShowWindow(self.hwnd, SW_SHOW)
        user32.UpdateWindow(self.hwnd)

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

    def create_main_window(self):
        self.hwnd = user32.CreateWindowExW(
            0,
            self.class_name,
            self.title,
            WS_OVERLAPPEDWINDOW | WS_VISIBLE,
            CW_USEDEFAULT,
            CW_USEDEFAULT,
            DEFAULT_WIDTH,
            DEFAULT_HEIGHT,
            None,
            None,
            self.hinstance,
            None,
        )
        if not self.hwnd:
            err = ctypes.get_last_error()
            raise OSError(err, "CreateWindowExW failed")

    def create_child_controls(self):
        self.label_hwnd = user32.CreateWindowExW(
            0,
            "STATIC",
            "00:00:00",
            WS_CHILD | WS_VISIBLE | SS_CENTER,
            0,
            0,
            100,
            100,
            self.hwnd,
            None,
            self.hinstance,
            None,
        )
        if not self.label_hwnd:
            err = ctypes.get_last_error()
            raise OSError(err, "CreateWindowExW failed for STATIC control")

        self.toggle_hwnd = user32.CreateWindowExW(
            0,
            "BUTTON",
            "Start",
            WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
            0,
            0,
            100,
            32,
            self.hwnd,
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
            self.hwnd,
            ctypes.c_void_p(BTN_RESET_ID),
            self.hinstance,
            None,
        )
        if not self.reset_hwnd:
            err = ctypes.get_last_error()
            raise OSError(err, "CreateWindowExW failed for Reset button")

        self.update_layout()
        self.update_display()

    def register_hotkeys(self):
        user32.RegisterHotKey(self.hwnd, HOTKEY_TOGGLE, MOD_CONTROL | MOD_SHIFT, VK_S)
        user32.RegisterHotKey(self.hwnd, HOTKEY_RESET, MOD_CONTROL | MOD_SHIFT, VK_R)
        user32.RegisterHotKey(self.hwnd, HOTKEY_QUIT, MOD_CONTROL | MOD_SHIFT, VK_Q)

    def unregister_hotkeys(self):
        user32.UnregisterHotKey(self.hwnd, HOTKEY_TOGGLE)
        user32.UnregisterHotKey(self.hwnd, HOTKEY_RESET)
        user32.UnregisterHotKey(self.hwnd, HOTKEY_QUIT)

    def set_always_on_top(self):
        user32.SetWindowPos(
            self.hwnd,
            HWND_TOPMOST,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
        )

    def toggle_timer(self):
        if self.running:
            if self.last_start_monotonic is not None:
                self.elapsed_seconds += time.monotonic() - self.last_start_monotonic
            self.running = False
            self.last_start_monotonic = None
            user32.SetWindowTextW(self.toggle_hwnd, "Start")
        else:
            self.running = True
            self.last_start_monotonic = time.monotonic()
            user32.SetWindowTextW(self.toggle_hwnd, "Stop")

        self.update_display()

    def reset_timer(self):
        self.elapsed_seconds = 0.0
        if self.running:
            self.last_start_monotonic = time.monotonic()
        self.update_display()

    def current_total_seconds(self):
        total = self.elapsed_seconds
        if self.running and self.last_start_monotonic is not None:
            total += time.monotonic() - self.last_start_monotonic
        return total

    def update_display(self):
        total_seconds = int(self.current_total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        user32.SetWindowTextW(self.label_hwnd, f"{hours:02}:{minutes:02}:{seconds:02}")

    def update_layout(self):
        rect = RECT()
        user32.GetClientRect(self.hwnd, ctypes.byref(rect))

        width = max(320, rect.right - rect.left)
        height = max(180, rect.bottom - rect.top)

        padding = 12
        button_height = 34
        button_spacing = 12
        label_height = max(70, height - button_height - (padding * 3))

        button_width = (width - (padding * 2) - button_spacing) // 2

        user32.MoveWindow(
            self.label_hwnd,
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

        self.update_label_font(width, label_height)

    def update_label_font(self, width, label_height):
        target_points = max(24, min(width // 7, label_height // 2))
        hdc = user32.GetDC(self.hwnd)
        dpi = gdi32.GetDeviceCaps(hdc, 90)
        user32.ReleaseDC(self.hwnd, hdc)

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
            old_font = self.hfont
            self.hfont = new_font
            user32.SendMessageW(self.label_hwnd, WM_SETFONT, self.hfont, 1)
            if old_font:
                gdi32.DeleteObject(old_font)

    def handle_command(self, wparam):
        command_id = wparam & 0xFFFF
        if command_id == BTN_TOGGLE_ID:
            self.toggle_timer()
        elif command_id == BTN_RESET_ID:
            self.reset_timer()

    def wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_CREATE:
            return 0

        if msg == WM_SIZE:
            if self.label_hwnd and self.toggle_hwnd and self.reset_hwnd:
                self.update_layout()
            return 0

        if msg == WM_COMMAND:
            self.handle_command(wparam)
            return 0

        if msg == WM_HOTKEY:
            if wparam == HOTKEY_TOGGLE:
                self.toggle_timer()
            elif wparam == HOTKEY_RESET:
                self.reset_timer()
            elif wparam == HOTKEY_QUIT:
                user32.DestroyWindow(hwnd)
            return 0

        if msg == WM_TIMER:
            if wparam == TIMER_ID:
                self.update_display()
                self.set_always_on_top()
            return 0

        if msg == WM_DESTROY:
            user32.KillTimer(hwnd, TIMER_ID)
            self.unregister_hotkeys()
            if self.hfont:
                gdi32.DeleteObject(self.hfont)
                self.hfont = None
            user32.PostQuitMessage(0)
            return 0

        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def main():
    configure_winapi_signatures()
    TimerApp().run()


if __name__ == "__main__":
    main()