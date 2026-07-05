import sys
import time
import ctypes
from ctypes import wintypes

from PySide6.QtCore import Qt, QTimer, QAbstractNativeEventFilter, QCoreApplication
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget


if sys.platform == "win32":
    user32 = ctypes.WinDLL("user32")
else:
    user32 = None

WM_HOTKEY = 0x0312

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

VK_S = 0x53
VK_R = 0x52
VK_Q = 0x51


class GlobalHotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, window):
        super().__init__()
        self.window = window

    def nativeEventFilter(self, event_type, message):
        msg = wintypes.MSG.from_address(int(message))

        if msg.message == WM_HOTKEY:
            hotkey_id = msg.wParam

            if hotkey_id == 1:
                self.window.toggle_timer()
                return True, 0

            if hotkey_id == 2:
                self.window.reset_timer()
                return True, 0

            if hotkey_id == 3:
                self.window.close()
                return True, 0

        return False, 0


class TimerWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Always On Top Timer")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        self.elapsed_seconds = 0.0
        self.running = False
        self.last_start_time = None

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_display)

        self.label = QLabel("00:00:00")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.start_stop_button = QPushButton("Start / Stop")
        self.reset_button = QPushButton("Reset")

        self.start_stop_button.clicked.connect(self.toggle_timer)
        self.reset_button.clicked.connect(self.reset_timer)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_stop_button)
        button_layout.addWidget(self.reset_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.label, stretch=1)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.resize(420, 220)

        self.setup_shortcuts()

        if user32 is not None:
            self.hotkey_filter = GlobalHotkeyFilter(self)
            app_instance = QCoreApplication.instance()
            if app_instance is not None:
                app_instance.installNativeEventFilter(self.hotkey_filter)
        else:
            self.hotkey_filter = None

        self.register_hotkeys()
        QTimer.singleShot(0, self.enforce_always_on_top)
        self.update_font_size()

    def setup_shortcuts(self):
        self.toggle_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        self.reset_shortcut = QShortcut(QKeySequence("Ctrl+Shift+R"), self)
        self.quit_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Q"), self)

        self.toggle_shortcut.activated.connect(self.toggle_timer)
        self.reset_shortcut.activated.connect(self.reset_timer)
        self.quit_shortcut.activated.connect(self.close)

    def enforce_always_on_top(self):
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.show()
        self.raise_()
        self.activateWindow()

    def register_hotkeys(self):
        # Ctrl + Shift + S = Start / Stop
        # Ctrl + Shift + R = Reset
        # Ctrl + Shift + Q = Quit

        if user32 is None:
            return

        user32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_SHIFT, VK_S)
        user32.RegisterHotKey(None, 2, MOD_CONTROL | MOD_SHIFT, VK_R)
        user32.RegisterHotKey(None, 3, MOD_CONTROL | MOD_SHIFT, VK_Q)

    def unregister_hotkeys(self):
        if user32 is None:
            return

        user32.UnregisterHotKey(None, 1)
        user32.UnregisterHotKey(None, 2)
        user32.UnregisterHotKey(None, 3)

    def toggle_timer(self):
        if self.running:
            if self.last_start_time is not None:
                self.elapsed_seconds += time.monotonic() - self.last_start_time
            self.running = False
            self.timer.stop()
            self.start_stop_button.setText("Start")
        else:
            self.last_start_time = time.monotonic()
            self.running = True
            self.timer.start()
            self.start_stop_button.setText("Stop")

        self.update_display()

    def reset_timer(self):
        self.elapsed_seconds = 0

        if self.running:
            self.last_start_time = time.monotonic()

        self.update_display()

    def update_display(self):
        total_seconds = self.elapsed_seconds

        if self.running and self.last_start_time is not None:
            total_seconds += time.monotonic() - self.last_start_time

        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)

        self.label.setText(f"{hours:02}:{minutes:02}:{seconds:02}")

    def resizeEvent(self, event):
        self.update_font_size()
        super().resizeEvent(event)

    def update_font_size(self):
        width = self.width()
        height = self.height()

        font_size = max(20, min(width // 7, height // 2))

        font = QFont("Segoe UI", font_size)
        font.setBold(True)
        self.label.setFont(font)

    def closeEvent(self, event):
        self.unregister_hotkeys()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = TimerWindow()
    window.show()

    sys.exit(app.exec())