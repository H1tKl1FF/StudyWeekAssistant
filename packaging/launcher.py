"""
Start Study Week Assistant from the Windows app (StudyWeekAssistant.exe).

This file is only used for the Windows installer. It starts the normal
browser app (app_browser.py, unchanged) on this computer and opens it in the
default web browser. Closing the black window stops the app.
"""
import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser

PORT = 8611                       # fixed, so a second start reuses the running app
APP_URL = f"http://localhost:{PORT}"
HEALTH_URL = APP_URL + "/_stcore/health"
START_TIMEOUT_SECONDS = 90
CHECK_EVERY_SECONDS = 0.5
# A name only this app uses while it runs. A second start sees it and reuses
# the running copy; the installer sees it and asks to close the app first.
# Keep it the same as AppMutexName in packaging/installer.iss.
APP_MUTEX_NAME = "StudyWeekAssistant_6E0F3C2A"
ERROR_ALREADY_EXISTS = 183

# Never send the check for the local app through a proxy set up on the computer
NO_PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def app_folder():
    """Folder that holds app_browser.py, project_code.py and .streamlit/."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # inside the built app
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def claim_app_name():
    """Mark this app as running. Returns True if another copy already did."""
    try:
        import ctypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    except (ImportError, AttributeError, OSError):
        return False                  # not Windows (running from source on a Mac)
    kernel32.CreateMutexW(None, False, APP_MUTEX_NAME)   # released when this window closes
    return ctypes.get_last_error() == ERROR_ALREADY_EXISTS


def app_is_running():
    try:
        with NO_PROXY.open(HEALTH_URL, timeout=1) as reply:
            return reply.status == 200
    except OSError:
        return False


def port_is_taken():
    """True if any program already listens on our port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(1)
        return probe.connect_ex(("127.0.0.1", PORT)) == 0


def open_browser_when_ready():
    waited = 0.0
    while waited < START_TIMEOUT_SECONDS:
        if app_is_running():
            webbrowser.open(APP_URL)
            print(f"The app is open in your browser: {APP_URL}")
            return True
        time.sleep(CHECK_EVERY_SECONDS)
        waited += CHECK_EVERY_SECONDS
    print("The app is taking long to start. Open this address in your browser:", APP_URL)
    return False


def start_app():
    if claim_app_name():
        # This app is already open in another window: just show it again
        print("Study Week Assistant is already running. Opening it in your browser...")
        open_browser_when_ready()
        return 0

    if port_is_taken():
        print(f"Another program is already using port {PORT}, so the app cannot start.")
        print("This is often an older Study Week Assistant window that is still open.")
        print("Close that window (or restart the computer) and open the app again.")
        input("\nPress Enter to close this window.")
        return 1

    folder = app_folder()
    os.chdir(folder)  # Streamlit reads the colour theme from .streamlit/config.toml here
    print("Study Week Assistant is starting...")
    print("Keep this window open while you use the app. Close it to stop the app.\n")
    threading.Thread(target=open_browser_when_ready, daemon=True).start()

    from streamlit.web import cli as streamlit_cli

    sys.argv = [
        "streamlit", "run", os.path.join(folder, "app_browser.py"),
        "--global.developmentMode", "false",
        "--server.port", str(PORT),
        "--server.address", "localhost",   # only this computer can open it
        "--server.headless", "true",
        "--server.fileWatcherType", "none",
        "--browser.gatherUsageStats", "false",
    ]
    return streamlit_cli.main()


def main():
    """Start the app; if anything goes wrong, keep the window open so the message can be read."""
    try:
        return start_app()
    except SystemExit:
        raise
    except Exception as problem:  # last safety net: show the error instead of a vanishing window
        print(f"\nThe app could not start: {problem}")
        input("Press Enter to close this window.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
