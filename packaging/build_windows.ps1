# Build dist\StudyWeekAssistant-Setup.exe from this project.
# Run from the project folder:   powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1
# Needs: Python 3.11+ and Inno Setup 6 (winget install JRSoftware.InnoSetup)

$ErrorActionPreference = "Stop"
$project = Split-Path -Parent $PSScriptRoot
$build = Join-Path $project ".build"
$venv = Join-Path $build "venv"
$python = Join-Path $venv "Scripts\python.exe"

$iscc = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw "Inno Setup 6 was not found. Install it with: winget install JRSoftware.InnoSetup" }

Write-Host "1/4 Preparing a separate build environment..."
if (-not (Test-Path $python)) { py -3 -m venv $venv; if ($LASTEXITCODE) { throw "Could not create the build environment." } }
& $python -m pip install --quiet --upgrade pip
& $python -m pip install --quiet -r (Join-Path $project "requirements.txt") pyinstaller
if ($LASTEXITCODE) { throw "Installing the libraries failed." }

Write-Host "2/4 Drawing the icon..."
& $python (Join-Path $PSScriptRoot "make_icon.py")
if ($LASTEXITCODE) { throw "Drawing the icon failed." }

Write-Host "3/4 Bundling the app with PyInstaller (a few minutes)..."
& $python -m PyInstaller --noconfirm --clean --log-level WARN `
    --distpath (Join-Path $build "dist") --workpath (Join-Path $build "work") `
    (Join-Path $PSScriptRoot "StudyWeekAssistant.spec")
if ($LASTEXITCODE) { throw "PyInstaller failed." }

Write-Host "4/4 Making the installer with Inno Setup..."
& $iscc /Q (Join-Path $PSScriptRoot "installer.iss")
if ($LASTEXITCODE) { throw "Inno Setup failed." }

$setup = Join-Path $project "dist\StudyWeekAssistant-Setup.exe"
Write-Host ("Done: {0} ({1:N0} MB)" -f $setup, ((Get-Item $setup).Length / 1MB))
