# PyInstaller recipe for StudyWeekAssistant.exe (used by build_windows.ps1).
# The app files are copied unchanged; only launcher.py is new.
import os
from PyInstaller.utils.hooks import collect_all, copy_metadata

project = os.path.dirname(SPECPATH)

datas, binaries, hiddenimports = [], [], []
for package in ("streamlit",):
    package_datas, package_binaries, package_imports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_imports
datas += copy_metadata("streamlit")

# The app itself, exactly as in the project folder
datas += [
    (os.path.join(project, "app_browser.py"), "."),
    (os.path.join(project, "project_code.py"), "."),
    (os.path.join(project, ".streamlit", "config.toml"), ".streamlit"),
]
# The look of the app (colours, type, layout): styles/tokens.css, base.css, app.css
datas += [(os.path.join(project, "styles", f), "styles")
          for f in ("tokens.css", "base.css", "app.css")]
# The demo week reads its invented students from test_cases/case1_normal_week
for folder, _, files in os.walk(os.path.join(project, "test_cases")):
    target = os.path.relpath(folder, project)
    datas += [(os.path.join(folder, f), target) for f in files if f != "actual_output.txt"]

# Libraries that app_browser.py and project_code.py import
hiddenimports += [
    "csv", "html", "importlib", "io", "json", "re", "subprocess",
    "datetime", "requests", "PIL", "PIL.Image",
]

a = Analysis(
    [os.path.join(SPECPATH, "launcher.py")],
    pathex=[project],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "pytest", "IPython", "matplotlib"],
    noarchive=False,
)
pyz = PYZ(a.pure)

icon = os.path.join(SPECPATH, "app_icon.ico")
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="StudyWeekAssistant",
    console=True,               # the small window that keeps the app running
    icon=icon if os.path.exists(icon) else None,
    version=os.path.join(SPECPATH, "version_info.txt"),
)
coll = COLLECT(exe, a.binaries, a.datas, name="StudyWeekAssistant")
