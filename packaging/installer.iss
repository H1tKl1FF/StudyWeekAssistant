; Inno Setup script for StudyWeekAssistant-Setup.exe (used by build_windows.ps1).
; Installs for the current user only, so no administrator password is needed.

#define AppName "Study Week Assistant"
#define AppVersion "1.4.0"
#define AppExe "StudyWeekAssistant.exe"
; Same name as APP_MUTEX_NAME in launcher.py
#define AppMutexName "StudyWeekAssistant_6E0F3C2A"

[Setup]
AppId={{6E0F3C2A-5B7D-4E61-9A3F-2C8D1B4E7F90}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Woosong University student group
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=StudyWeekAssistant-Setup
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "..\.build\dist\StudyWeekAssistant\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[InstallDelete]
; remove files of an older version before copying the new one
Type: filesandordirs; Name: "{app}\_internal"

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Open {#AppName} now"; Flags: nowait postinstall skipifsilent

[Code]
{ A copy of the app that is still open keeps its files locked. Installing over it
  then deletes only part of the old files and the open app shows "Internal Server
  Error". So close it first - only copies started from this install folder, never
  other programs with the same file name. }
procedure CloseRunningCopy(Folder: String);
var
  Script: String;
  ResultCode: Integer;
begin
  Script := ExpandConstant('{tmp}\close_running_copy.ps1');
  SaveStringToFile(Script,
    'param($Folder)' + #13#10 +
    'Get-CimInstance Win32_Process -Filter "Name=''{#AppExe}''" |' + #13#10 +
    '  Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($Folder + ''\'', ''OrdinalIgnoreCase'') } |' + #13#10 +
    '  ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Wait-Process -Id $_.ProcessId -Timeout 10 -ErrorAction SilentlyContinue }' + #13#10,
    False);
  Exec('powershell.exe', '-NoProfile -ExecutionPolicy Bypass -File "' + Script + '" -Folder "' + Folder + '"',
       '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

{ The app marks itself as running with this name (see packaging/launcher.py).
  If PowerShell is blocked on the computer, the step above cannot close the app,
  but this check still notices it, so Setup never installs over an open app. }
function AppStillOpen(): Boolean;
begin
  Result := CheckForMutexes('{#AppMutexName}');
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  CloseRunningCopy(ExpandConstant('{app}'));
  if AppStillOpen() then
    Result := '{#AppName} is still open. Close its black window, then run Setup again.'
  else
    Result := '';
end;

{ Close the app only after the student has said Yes to "remove the app?" }
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    CloseRunningCopy(ExpandConstant('{app}'));
    while AppStillOpen() and
          (MsgBox('{#AppName} is still open. Close its black window, then click Retry.',
                  mbError, MB_RETRYCANCEL) = IDRETRY) do
      ;
  end;
end;
