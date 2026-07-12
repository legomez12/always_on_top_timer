import ctypes
from ctypes import wintypes

from timer_constants import (
    BS_PUSHBUTTON,
    BTN_DISPLAY_ID,
    BTN_RESET_ID,
    BTN_THEME_ID,
    BTN_TOPMOST_ID,
    BTN_TOGGLE_ID,
    COLOR_WINDOW,
    CONTROL_DEFAULT_HEIGHT,
    CONTROL_DEFAULT_WIDTH,
    CS_HREDRAW,
    CS_VREDRAW,
    CW_USEDEFAULT,
    DARK_BG_COLOR,
    DARK_BUTTON_BG_COLOR,
    DISPLAY_DEFAULT_HEIGHT,
    DISPLAY_DEFAULT_WIDTH,
    HOTKEY_QUIT,
    HOTKEY_RESET,
    HOTKEY_TOGGLE,
    HWND_NOTOPMOST,
    HWND_TOPMOST,
    LIGHT_TEXT_COLOR,
    MOD_CONTROL,
    MOD_SHIFT,
    SS_CENTER,
    SS_CENTERIMAGE,
    SW_HIDE,
    SW_SHOW,
    SWP_NOACTIVATE,
    SWP_NOMOVE,
    SWP_NOSIZE,
    SECOND_ROW_BUTTON_FONT_SCALE,
    SECOND_ROW_BUTTON_SIZE_SCALE,
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
    WM_ERASEBKGND,
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
    create_dark_brushes,
    detect_windows_dark_mode,
    gdi32,
    kernel32,
    user32,
)
from win32_types import RECT, WNDCLASSEXW, WNDPROC


class TimerApp:
    def __init__(self):
        self.hinstance = self._kernel32_get_module_handle(module_name=None)
        self.class_name = "AlwaysOnTopTimerWindow"
        self.control_title = "Always On Top Timer - Control"
        self.display_title = "Always On Top Timer - Display"

        self.control_hwnd = None
        self.display_hwnd = None

        self.control_label_hwnd = None
        self.display_label_hwnd = None
        self.toggle_hwnd = None
        self.reset_hwnd = None
        self.theme_hwnd = None
        self.topmost_hwnd = None
        self.display_toggle_hwnd = None

        self.control_hfont = None
        self.display_hfont = None
        self.top_row_button_hfont = None
        self.bottom_row_button_hfont = None

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
        self.always_on_top_enabled = True
        self.display_visible = True

        self._wndproc_ref = WNDPROC(self.wnd_proc)

    # External API wrappers use keyword-only inputs so call sites are self-documenting.
    def _kernel32_get_module_handle(self, *, module_name):
        return kernel32.GetModuleHandleW(module_name)

    def _user32_set_timer(self, *, window_handle, timer_id, interval_ms, callback):
        return user32.SetTimer(window_handle, timer_id, interval_ms, callback)

    def _user32_show_window(self, *, window_handle, show_command):
        return user32.ShowWindow(window_handle, show_command)

    def _user32_update_window(self, *, window_handle):
        return user32.UpdateWindow(window_handle)

    def _user32_get_message(self, *, msg_ptr, window_handle, min_filter, max_filter):
        return user32.GetMessageW(msg_ptr, window_handle, min_filter, max_filter)

    def _user32_translate_message(self, *, msg_ptr):
        return user32.TranslateMessage(msg_ptr)

    def _user32_dispatch_message(self, *, msg_ptr):
        return user32.DispatchMessageW(msg_ptr)

    def _user32_load_icon(self, *, instance_handle, icon_id):
        return user32.LoadIconW(instance_handle, icon_id)

    def _user32_load_cursor(self, *, instance_handle, cursor_id):
        return user32.LoadCursorW(instance_handle, cursor_id)

    def _user32_register_class_ex(self, *, window_class_ptr):
        return user32.RegisterClassExW(window_class_ptr)

    def _user32_create_window_ex(
        self,
        *,
        ex_style,
        class_name,
        window_name,
        style,
        x,
        y,
        width,
        height,
        parent_handle,
        menu_handle,
        instance_handle,
        param,
    ):
        return user32.CreateWindowExW(
            ex_style,
            class_name,
            window_name,
            style,
            x,
            y,
            width,
            height,
            parent_handle,
            menu_handle,
            instance_handle,
            param,
        )

    def _user32_register_hotkey(self, *, window_handle, hotkey_id, modifiers, virtual_key):
        return user32.RegisterHotKey(window_handle, hotkey_id, modifiers, virtual_key)

    def _user32_unregister_hotkey(self, *, window_handle, hotkey_id):
        return user32.UnregisterHotKey(window_handle, hotkey_id)

    def _user32_set_window_pos(self, *, window_handle, insert_after, x, y, width, height, flags):
        return user32.SetWindowPos(window_handle, insert_after, x, y, width, height, flags)

    def _user32_set_window_text(self, *, window_handle, text):
        return user32.SetWindowTextW(window_handle, text)

    def _user32_invalidate_rect(self, *, window_handle, rect_ptr, erase_background):
        return user32.InvalidateRect(window_handle, rect_ptr, erase_background)

    def _user32_get_client_rect(self, *, window_handle, rect_ptr):
        return user32.GetClientRect(window_handle, rect_ptr)

    def _user32_move_window(self, *, window_handle, x, y, width, height, repaint):
        return user32.MoveWindow(window_handle, x, y, width, height, repaint)

    def _user32_send_set_font(self, *, window_handle, font_handle, redraw):
        redraw_flag = 1 if redraw else 0
        return user32.SendMessageW(window_handle, WM_SETFONT, font_handle, redraw_flag)

    def _user32_kill_timer(self, *, window_handle, timer_id):
        return user32.KillTimer(window_handle, timer_id)

    def _user32_destroy_window(self, *, window_handle):
        return user32.DestroyWindow(window_handle)

    def _user32_post_quit_message(self, *, exit_code):
        user32.PostQuitMessage(exit_code)

    def _user32_get_dc(self, *, window_handle):
        return user32.GetDC(window_handle)

    def _user32_release_dc(self, *, window_handle, device_context):
        return user32.ReleaseDC(window_handle, device_context)

    def _user32_fill_rect(self, *, device_context, rect_ptr, brush_handle):
        return user32.FillRect(device_context, rect_ptr, brush_handle)

    def _user32_def_window_proc(self, *, window_handle, msg, wparam, lparam):
        return user32.DefWindowProcW(window_handle, msg, wparam, lparam)

    def _gdi_get_device_caps(self, *, device_context, index):
        return gdi32.GetDeviceCaps(device_context, index)

    def _gdi_create_font(
        self,
        *,
        height,
        width,
        escapement,
        orientation,
        weight,
        italic,
        underline,
        strike_out,
        char_set,
        out_precision,
        clip_precision,
        quality,
        pitch_and_family,
        face_name,
    ):
        return gdi32.CreateFontW(
            height,
            width,
            escapement,
            orientation,
            weight,
            italic,
            underline,
            strike_out,
            char_set,
            out_precision,
            clip_precision,
            quality,
            pitch_and_family,
            face_name,
        )

    def _gdi_delete_object(self, *, object_handle):
        return gdi32.DeleteObject(object_handle)

    def _gdi_set_text_color(self, *, device_context, color_ref):
        return gdi32.SetTextColor(device_context, color_ref)

    def _gdi_set_background_mode(self, *, device_context, background_mode):
        return gdi32.SetBkMode(device_context, background_mode)

    def _gdi_set_background_color(self, *, device_context, color_ref):
        return gdi32.SetBkColor(device_context, color_ref)

    def run(self):
        self.register_window_class()
        self.create_windows()
        self.create_child_controls()

        self.register_hotkeys()
        self.enforce_always_on_top()
        timer_hwnd = self.control_hwnd
        timer_id = TIMER_ID
        timer_interval_ms = TIMER_INTERVAL_MS
        timer_callback = None
        self._user32_set_timer(
            window_handle=timer_hwnd,
            timer_id=timer_id,
            interval_ms=timer_interval_ms,
            callback=timer_callback,
        )

        self._user32_show_window(window_handle=self.control_hwnd, show_command=SW_SHOW)
        self._user32_update_window(window_handle=self.control_hwnd)
        self._user32_show_window(window_handle=self.display_hwnd, show_command=SW_SHOW)
        self._user32_update_window(window_handle=self.display_hwnd)

        msg = wintypes.MSG()
        msg_ptr = ctypes.byref(msg)
        while self._user32_get_message(msg_ptr=msg_ptr, window_handle=None, min_filter=0, max_filter=0) > 0:
            self._user32_translate_message(msg_ptr=msg_ptr)
            self._user32_dispatch_message(msg_ptr=msg_ptr)

    def register_window_class(self):
        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.style = CS_HREDRAW | CS_VREDRAW
        wc.lpfnWndProc = self._wndproc_ref
        wc.cbClsExtra = 0
        wc.cbWndExtra = 0
        wc.hInstance = self.hinstance
        idi_application = ctypes.c_void_p(32512)
        idc_arrow = ctypes.c_void_p(32512)
        wc.hIcon = self._user32_load_icon(instance_handle=None, icon_id=idi_application)
        wc.hCursor = self._user32_load_cursor(instance_handle=None, cursor_id=idc_arrow)
        wc.hbrBackground = ctypes.c_void_p(COLOR_WINDOW + 1)
        wc.lpszMenuName = None
        wc.lpszClassName = self.class_name
        wc.hIconSm = wc.hIcon

        atom = self._user32_register_class_ex(window_class_ptr=ctypes.byref(wc))
        if atom == 0:
            err = ctypes.get_last_error()
            raise OSError(err, "RegisterClassExW failed")

    def create_windows(self):
        self.control_hwnd = self._user32_create_window_ex(
            ex_style=0,
            class_name=self.class_name,
            window_name=self.control_title,
            style=WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN | WS_VISIBLE,
            x=CW_USEDEFAULT,
            y=CW_USEDEFAULT,
            width=CONTROL_DEFAULT_WIDTH,
            height=CONTROL_DEFAULT_HEIGHT,
            parent_handle=None,
            menu_handle=None,
            instance_handle=self.hinstance,
            param=None,
        )
        if not self.control_hwnd:
            err = ctypes.get_last_error()
            raise OSError(err, "CreateWindowExW failed for control window")

        self.display_hwnd = self._user32_create_window_ex(
            ex_style=0,
            class_name=self.class_name,
            window_name=self.display_title,
            style=WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN | WS_VISIBLE,
            x=CW_USEDEFAULT,
            y=CW_USEDEFAULT,
            width=DISPLAY_DEFAULT_WIDTH,
            height=DISPLAY_DEFAULT_HEIGHT,
            parent_handle=None,
            menu_handle=None,
            instance_handle=self.hinstance,
            param=None,
        )
        if not self.display_hwnd:
            err = ctypes.get_last_error()
            raise OSError(err, "CreateWindowExW failed for display window")

        apply_windows11_window_style(self.control_hwnd, self.use_dark_mode)
        apply_windows11_window_style(self.display_hwnd, self.use_dark_mode)

        self.alive_windows = 2

    def create_timer_label(self, parent_hwnd):
        label_hwnd = self._user32_create_window_ex(
            ex_style=0,
            class_name="STATIC",
            window_name="00:00:00",
            style=WS_CHILD | WS_VISIBLE | SS_CENTER | SS_CENTERIMAGE,
            x=0,
            y=0,
            width=100,
            height=100,
            parent_handle=parent_hwnd,
            menu_handle=None,
            instance_handle=self.hinstance,
            param=None,
        )
        if not label_hwnd:
            err = ctypes.get_last_error()
            raise OSError(err, "CreateWindowExW failed for STATIC control")
        return label_hwnd

    def create_child_controls(self):
        self.control_label_hwnd = self.create_timer_label(self.control_hwnd)
        self.display_label_hwnd = self.create_timer_label(self.display_hwnd)

        self.toggle_hwnd = self._user32_create_window_ex(
            ex_style=0,
            class_name="BUTTON",
            window_name="Start (Ctrl+Shift+S)",
            style=WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
            x=0,
            y=0,
            width=100,
            height=32,
            parent_handle=self.control_hwnd,
            menu_handle=ctypes.c_void_p(BTN_TOGGLE_ID),
            instance_handle=self.hinstance,
            param=None,
        )
        if not self.toggle_hwnd:
            err = ctypes.get_last_error()
            raise OSError(err, "CreateWindowExW failed for Start button")

        self.reset_hwnd = self._user32_create_window_ex(
            ex_style=0,
            class_name="BUTTON",
            window_name="Reset (Ctrl+Shift+R)",
            style=WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
            x=0,
            y=0,
            width=100,
            height=32,
            parent_handle=self.control_hwnd,
            menu_handle=ctypes.c_void_p(BTN_RESET_ID),
            instance_handle=self.hinstance,
            param=None,
        )
        if not self.reset_hwnd:
            err = ctypes.get_last_error()
            raise OSError(err, "CreateWindowExW failed for Reset button")

        self.theme_hwnd = self._user32_create_window_ex(
            ex_style=0,
            class_name="BUTTON",
            window_name="Theme: Dark",
            style=WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
            x=0,
            y=0,
            width=100,
            height=32,
            parent_handle=self.control_hwnd,
            menu_handle=ctypes.c_void_p(BTN_THEME_ID),
            instance_handle=self.hinstance,
            param=None,
        )
        if not self.theme_hwnd:
            err = ctypes.get_last_error()
            raise OSError(err, "CreateWindowExW failed for Theme button")

        self.topmost_hwnd = self._user32_create_window_ex(
            ex_style=0,
            class_name="BUTTON",
            window_name="Always On Top: On",
            style=WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
            x=0,
            y=0,
            width=100,
            height=32,
            parent_handle=self.control_hwnd,
            menu_handle=ctypes.c_void_p(BTN_TOPMOST_ID),
            instance_handle=self.hinstance,
            param=None,
        )
        if not self.topmost_hwnd:
            err = ctypes.get_last_error()
            raise OSError(err, "CreateWindowExW failed for Always-On-Top button")

        self.display_toggle_hwnd = self._user32_create_window_ex(
            ex_style=0,
            class_name="BUTTON",
            window_name="Display: Hide",
            style=WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
            x=0,
            y=0,
            width=100,
            height=32,
            parent_handle=self.control_hwnd,
            menu_handle=ctypes.c_void_p(BTN_DISPLAY_ID),
            instance_handle=self.hinstance,
            param=None,
        )
        if not self.display_toggle_hwnd:
            err = ctypes.get_last_error()
            raise OSError(err, "CreateWindowExW failed for Display toggle button")

        self.update_control_layout()
        self.update_display_layout()
        self.update_timer_labels()
        self.update_toggle_button()
        self.update_theme_button()
        self.update_always_on_top_button()
        self.update_display_toggle_button()

    def register_hotkeys(self):
        hotkey_modifiers = MOD_CONTROL | MOD_SHIFT
        self._user32_register_hotkey(
            window_handle=self.control_hwnd,
            hotkey_id=HOTKEY_TOGGLE,
            modifiers=hotkey_modifiers,
            virtual_key=VK_S,
        )
        self._user32_register_hotkey(
            window_handle=self.control_hwnd,
            hotkey_id=HOTKEY_RESET,
            modifiers=hotkey_modifiers,
            virtual_key=VK_R,
        )
        self._user32_register_hotkey(
            window_handle=self.control_hwnd,
            hotkey_id=HOTKEY_QUIT,
            modifiers=hotkey_modifiers,
            virtual_key=VK_Q,
        )
        self.hotkeys_registered = True

    def unregister_hotkeys(self):
        if not self.hotkeys_registered:
            return
        self._user32_unregister_hotkey(window_handle=self.control_hwnd, hotkey_id=HOTKEY_TOGGLE)
        self._user32_unregister_hotkey(window_handle=self.control_hwnd, hotkey_id=HOTKEY_RESET)
        self._user32_unregister_hotkey(window_handle=self.control_hwnd, hotkey_id=HOTKEY_QUIT)
        self.hotkeys_registered = False

    def set_window_always_on_top(self, hwnd):
        x = 0
        y = 0
        width = 0
        height = 0
        set_window_pos_flags = SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
        self._user32_set_window_pos(
            window_handle=hwnd,
            insert_after=HWND_TOPMOST,
            x=x,
            y=y,
            width=width,
            height=height,
            flags=set_window_pos_flags,
        )

    def clear_window_always_on_top(self, hwnd):
        x = 0
        y = 0
        width = 0
        height = 0
        set_window_pos_flags = SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
        self._user32_set_window_pos(
            window_handle=hwnd,
            insert_after=HWND_NOTOPMOST,
            x=x,
            y=y,
            width=width,
            height=height,
            flags=set_window_pos_flags,
        )

    def enforce_always_on_top(self):
        if self.control_hwnd:
            if self.always_on_top_enabled:
                self.set_window_always_on_top(self.control_hwnd)
            else:
                self.clear_window_always_on_top(self.control_hwnd)
        if self.display_hwnd:
            if self.always_on_top_enabled:
                self.set_window_always_on_top(self.display_hwnd)
            else:
                self.clear_window_always_on_top(self.display_hwnd)

    def update_toggle_button(self):
        if self.toggle_hwnd:
            self._user32_set_window_text(
                window_handle=self.toggle_hwnd,
                text="Stop (Ctrl+Shift+S)" if self.model.running else "Start (Ctrl+Shift+S)",
            )

    def update_theme_button(self):
        if self.theme_hwnd:
            self._user32_set_window_text(
                window_handle=self.theme_hwnd,
                text="Theme: Dark" if self.use_dark_mode else "Theme: Light",
            )

    def update_always_on_top_button(self):
        if self.topmost_hwnd:
            self._user32_set_window_text(
                window_handle=self.topmost_hwnd,
                text="Always On Top: On" if self.always_on_top_enabled else "Always On Top: Off",
            )

    def update_display_toggle_button(self):
        if self.display_toggle_hwnd:
            self._user32_set_window_text(
                window_handle=self.display_toggle_hwnd,
                text="Display: Hide" if self.display_visible else "Display: Show",
            )

    def toggle_always_on_top(self):
        self.always_on_top_enabled = not self.always_on_top_enabled
        self.enforce_always_on_top()
        self.update_always_on_top_button()

    def toggle_display_window_visibility(self):
        if not self.display_hwnd:
            return

        self.display_visible = not self.display_visible
        self._user32_show_window(
            window_handle=self.display_hwnd,
            show_command=SW_SHOW if self.display_visible else SW_HIDE,
        )

        if self.display_visible:
            self._user32_update_window(window_handle=self.display_hwnd)
            if self.always_on_top_enabled:
                self.set_window_always_on_top(self.display_hwnd)

        self.update_display_toggle_button()

    def refresh_theme_brushes(self):
        self.cleanup_theme_resources()
        if self.use_dark_mode:
            self.background_brush, self.button_background_brush = create_dark_brushes()

    def request_repaint(self, hwnd):
        if hwnd:
            self._user32_invalidate_rect(window_handle=hwnd, rect_ptr=None, erase_background=True)
            self._user32_update_window(window_handle=hwnd)

    def toggle_theme(self):
        self.use_dark_mode = not self.use_dark_mode
        self.refresh_theme_brushes()

        if self.control_hwnd:
            apply_windows11_window_style(self.control_hwnd, self.use_dark_mode)
        if self.display_hwnd:
            apply_windows11_window_style(self.display_hwnd, self.use_dark_mode)

        self.update_theme_button()

        self.request_repaint(self.control_hwnd)
        self.request_repaint(self.display_hwnd)
        self.request_repaint(self.control_label_hwnd)
        self.request_repaint(self.display_label_hwnd)
        self.request_repaint(self.toggle_hwnd)
        self.request_repaint(self.reset_hwnd)
        self.request_repaint(self.theme_hwnd)
        self.request_repaint(self.topmost_hwnd)
        self.request_repaint(self.display_toggle_hwnd)

    def update_timer_labels(self):
        text = self.model.formatted_time()
        if text == self.last_rendered_time_text:
            return

        self.last_rendered_time_text = text
        if self.control_label_hwnd:
            self._user32_set_window_text(window_handle=self.control_label_hwnd, text=text)
        if self.display_label_hwnd:
            self._user32_set_window_text(window_handle=self.display_label_hwnd, text=text)

    def toggle_timer(self):
        self.model.toggle()
        self.update_toggle_button()
        self.update_timer_labels()

    def reset_timer(self):
        self.model.reset()
        self.update_timer_labels()

    def get_client_size(self, hwnd):
        rect = RECT()
        self._user32_get_client_rect(window_handle=hwnd, rect_ptr=ctypes.byref(rect))
        return rect.right - rect.left, rect.bottom - rect.top

    def update_control_layout(self):
        width, height = self.get_client_size(self.control_hwnd)
        width = max(320, width)
        height = max(180, height)

        padding = 12
        button_height = 34
        second_row_button_height = max(20, int(button_height * SECOND_ROW_BUTTON_SIZE_SCALE))
        button_spacing = 12
        label_height = max(70, height - (button_height + second_row_button_height + button_spacing + (padding * 3)))

        top_row_button_width = (width - (padding * 2) - button_spacing) // 2
        bottom_row_button_width = (width - (padding * 2) - (button_spacing * 2)) // 3

        self._user32_move_window(
            window_handle=self.control_label_hwnd,
            x=padding,
            y=padding,
            width=width - (padding * 2),
            height=label_height,
            repaint=True,
        )

        button_y = padding * 2 + label_height
        self._user32_move_window(
            window_handle=self.toggle_hwnd,
            x=padding,
            y=button_y,
            width=top_row_button_width,
            height=button_height,
            repaint=True,
        )
        self._user32_move_window(
            window_handle=self.reset_hwnd,
            x=padding + top_row_button_width + button_spacing,
            y=button_y,
            width=top_row_button_width,
            height=button_height,
            repaint=True,
        )
        second_row_y = button_y + button_height + button_spacing
        self._user32_move_window(
            window_handle=self.theme_hwnd,
            x=padding,
            y=second_row_y,
            width=bottom_row_button_width,
            height=second_row_button_height,
            repaint=True,
        )
        self._user32_move_window(
            window_handle=self.topmost_hwnd,
            x=padding + bottom_row_button_width + button_spacing,
            y=second_row_y,
            width=bottom_row_button_width,
            height=second_row_button_height,
            repaint=True,
        )
        self._user32_move_window(
            window_handle=self.display_toggle_hwnd,
            x=padding + (bottom_row_button_width * 2) + (button_spacing * 2),
            y=second_row_y,
            width=bottom_row_button_width,
            height=second_row_button_height,
            repaint=True,
        )

        self.update_button_font(self.control_hwnd)

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

        self._user32_move_window(
            window_handle=self.display_label_hwnd,
            x=padding,
            y=padding,
            width=width - (padding * 2),
            height=height - (padding * 2),
            repaint=True,
        )

        self.update_label_font(
            self.display_hwnd,
            self.display_label_hwnd,
            width,
            height,
            is_control_window=False,
        )

    def update_button_font(self, window_hwnd):
        hdc = self._user32_get_dc(window_handle=window_hwnd)
        dpi = self._gdi_get_device_caps(device_context=hdc, index=90)
        self._user32_release_dc(window_handle=window_hwnd, device_context=hdc)

        top_height_px = -int(9 * dpi / 72)
        bottom_height_px = -int((9 * SECOND_ROW_BUTTON_FONT_SCALE) * dpi / 72)

        new_top_font = self._gdi_create_font(
            height=top_height_px,
            width=0,
            escapement=0,
            orientation=0,
            weight=400,
            italic=0,
            underline=0,
            strike_out=0,
            char_set=0,
            out_precision=0,
            clip_precision=0,
            quality=0,
            pitch_and_family=0,
            face_name="Segoe UI",
        )
        new_bottom_font = self._gdi_create_font(
            height=bottom_height_px,
            width=0,
            escapement=0,
            orientation=0,
            weight=400,
            italic=0,
            underline=0,
            strike_out=0,
            char_set=0,
            out_precision=0,
            clip_precision=0,
            quality=0,
            pitch_and_family=0,
            face_name="Segoe UI",
        )

        if not new_top_font or not new_bottom_font:
            if new_top_font:
                self._gdi_delete_object(object_handle=new_top_font)
            if new_bottom_font:
                self._gdi_delete_object(object_handle=new_bottom_font)
            return

        old_top_font = self.top_row_button_hfont
        old_bottom_font = self.bottom_row_button_hfont
        self.top_row_button_hfont = new_top_font
        self.bottom_row_button_hfont = new_bottom_font

        for btn in [self.toggle_hwnd, self.reset_hwnd]:
            if btn:
                self._user32_send_set_font(window_handle=btn, font_handle=new_top_font, redraw=True)

        for btn in [self.theme_hwnd, self.topmost_hwnd, self.display_toggle_hwnd]:
            if btn:
                self._user32_send_set_font(window_handle=btn, font_handle=new_bottom_font, redraw=True)

        if old_top_font and old_top_font != new_top_font:
            self._gdi_delete_object(object_handle=old_top_font)
        if old_bottom_font and old_bottom_font != new_bottom_font:
            self._gdi_delete_object(object_handle=old_bottom_font)

    def update_label_font(self, window_hwnd, label_hwnd, width, height, is_control_window):
        if is_control_window:
            target_points = max(24, min(width // 7, height // 2))
        else:
            target_points = max(28, min(width // 6, height // 2))

        hdc = self._user32_get_dc(window_handle=window_hwnd)
        dpi = self._gdi_get_device_caps(device_context=hdc, index=90)
        self._user32_release_dc(window_handle=window_hwnd, device_context=hdc)

        height_px = -int(target_points * dpi / 72)

        new_font = self._gdi_create_font(
            height=height_px,
            width=0,
            escapement=0,
            orientation=0,
            weight=700,
            italic=0,
            underline=0,
            strike_out=0,
            char_set=0,
            out_precision=0,
            clip_precision=0,
            quality=0,
            pitch_and_family=0,
            face_name="Segoe UI" if is_control_window else "Segoe UI Variable Display",
        )

        if new_font:
            if is_control_window:
                old_font = self.control_hfont
                self.control_hfont = new_font
            else:
                old_font = self.display_hfont
                self.display_hfont = new_font

            self._user32_send_set_font(window_handle=label_hwnd, font_handle=new_font, redraw=True)
            if old_font and old_font != new_font:
                self._gdi_delete_object(object_handle=old_font)

    def handle_command(self, wparam):
        command_id = wparam & 0xFFFF
        if command_id == BTN_TOGGLE_ID:
            self.toggle_timer()
        elif command_id == BTN_RESET_ID:
            self.reset_timer()
        elif command_id == BTN_THEME_ID:
            self.toggle_theme()
        elif command_id == BTN_TOPMOST_ID:
            self.toggle_always_on_top()
        elif command_id == BTN_DISPLAY_ID:
            self.toggle_display_window_visibility()

    def cleanup_window_resources(self, hwnd):
        if hwnd == self.control_hwnd:
            if self.control_hfont:
                self._gdi_delete_object(object_handle=self.control_hfont)
                self.control_hfont = None
            self.control_hwnd = None
            self.control_label_hwnd = None
            self.toggle_hwnd = None
            self.reset_hwnd = None
            self.theme_hwnd = None
            self.topmost_hwnd = None
            self.display_toggle_hwnd = None
            if self.top_row_button_hfont:
                self._gdi_delete_object(object_handle=self.top_row_button_hfont)
                self.top_row_button_hfont = None
            if self.bottom_row_button_hfont:
                self._gdi_delete_object(object_handle=self.bottom_row_button_hfont)
                self.bottom_row_button_hfont = None
        elif hwnd == self.display_hwnd:
            if self.display_hfont:
                self._gdi_delete_object(object_handle=self.display_hfont)
                self.display_hfont = None
            self.display_hwnd = None
            self.display_label_hwnd = None
            self.display_visible = False

    def cleanup_theme_resources(self):
        if self.background_brush:
            self._gdi_delete_object(object_handle=self.background_brush)
            self.background_brush = None
        if self.button_background_brush:
            self._gdi_delete_object(object_handle=self.button_background_brush)
            self.button_background_brush = None

    def initiate_shutdown(self):
        if self.shutting_down:
            return

        self.shutting_down = True
        self.unregister_hotkeys()

        if self.control_hwnd:
            self._user32_kill_timer(window_handle=self.control_hwnd, timer_id=TIMER_ID)

        control_hwnd = self.control_hwnd
        display_hwnd = self.display_hwnd

        if control_hwnd:
            self._user32_destroy_window(window_handle=control_hwnd)
        if display_hwnd and display_hwnd != control_hwnd:
            self._user32_destroy_window(window_handle=display_hwnd)

    def handle_window_destroy(self, hwnd):
        self.cleanup_window_resources(hwnd)
        self.alive_windows -= 1
        if self.alive_windows <= 0:
            self.cleanup_theme_resources()
            self._user32_post_quit_message(exit_code=0)

    def wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_CLOSE:
            self.initiate_shutdown()
            return 0

        if msg == WM_ERASEBKGND and self.use_dark_mode and self.background_brush:
            rect = RECT()
            self._user32_get_client_rect(window_handle=hwnd, rect_ptr=ctypes.byref(rect))
            self._user32_fill_rect(
                device_context=wintypes.HDC(wparam),
                rect_ptr=ctypes.byref(rect),
                brush_handle=self.background_brush,
            )
            return 1

        if msg == WM_SIZE:
            if (
                hwnd == self.control_hwnd
                and self.control_label_hwnd
                and self.toggle_hwnd
                and self.reset_hwnd
                and self.theme_hwnd
                and self.topmost_hwnd
                and self.display_toggle_hwnd
            ):
                self.update_control_layout()
            elif hwnd == self.display_hwnd and self.display_label_hwnd:
                self.update_display_layout()
            return 0

        if msg == WM_COMMAND:
            if hwnd == self.control_hwnd:
                self.handle_command(wparam)
            return 0

        if msg == WM_CTLCOLORSTATIC and self.use_dark_mode and self.background_brush:
            hdc = wintypes.HDC(wparam)
            self._gdi_set_text_color(device_context=hdc, color_ref=LIGHT_TEXT_COLOR)
            self._gdi_set_background_mode(device_context=hdc, background_mode=TRANSPARENT)
            self._gdi_set_background_color(device_context=hdc, color_ref=DARK_BG_COLOR)
            return self.background_brush

        if msg == WM_CTLCOLORBTN and self.use_dark_mode:
            hdc = wintypes.HDC(wparam)
            self._gdi_set_text_color(device_context=hdc, color_ref=LIGHT_TEXT_COLOR)
            self._gdi_set_background_color(device_context=hdc, color_ref=DARK_BUTTON_BG_COLOR)
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

        return self._user32_def_window_proc(window_handle=hwnd, msg=msg, wparam=wparam, lparam=lparam)
