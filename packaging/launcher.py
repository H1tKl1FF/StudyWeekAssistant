"""
Start Study Week Assistant from the Windows app (StudyWeekAssistant.exe).

This file is only used for the Windows installer. It starts the normal
browser app (app_browser.py, unchanged) on this computer and opens it in the
default web browser. Closing the black window stops the app.
"""
import os
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


def app_folder():
    """Folder that holds app_browser.py, project_code.py and .streamlit/."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # inside the built app
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def app_is_running():
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=1) as reply:
            return reply.status == 200
    except OSError:
        return False


def open_browser_when_ready():
    waited = 0.0
    while waited < START_TIMEOUT_SECONDS:
        if app_is_running():
            webbrowser.open(APP_URL)
            print(f"The app is open in your browser: {APP_URL}")
            return
        time.sleep(CHECK_EVERY_SECONDS)
        waited += CHECK_EVERY_SECONDS
    print("The app is taking long to start. Open this address in your browser:", APP_URL)


def main():
    if app_is_running():
        webbrowser.open(APP_URL)
        return 0

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


if __name__ == "__main__":
    sys.exit(main())
