import sys

from timer_app import TimerApp
from win32_api import configure_winapi_signatures


if sys.platform != "win32":
    raise SystemExit("This app is Windows-only and uses the Win32 API.")


def main():
    configure_winapi_signatures()
    TimerApp().run()


if __name__ == "__main__":
    main()
