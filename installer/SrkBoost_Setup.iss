; SRK Boost - Inno Setup Script v1.5.1
; Build this with Inno Setup 6: https://jrsoftware.org/isinfo.php
; Run: ISCC.exe SrkBoost_Setup.iss

#define MyAppName      "SRK Boost"
#define MyAppVersion   "1.5.1"
#define MyAppPublisher "SRK Boost"
#define MyAppURL       "https://srkboost.com"
#define MyAppExeName   "SRK Boost.exe"
#define MyAppID        "{{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}"

[Setup]
; Basic info
AppId={#MyAppID}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\release
OutputBaseFilename=SrkBoost-v{#MyAppVersion}-Setup
SetupIconFile=..\assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120

; Require Windows 10+
MinVersion=10.0

; Request admin
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Create uninstaller
Uninstallable=yes
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

; 64-bit only
ArchitecturesInstallIn64BitMode=x64

; Disable welcome page, show license
DisableWelcomePage=no
LicenseFile=

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "{cm:CreateDesktopIcon}";    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon";    Description: "Launch SRK Boost at startup"; GroupDescription: "Startup:"; Flags: unchecked
Name: "startmenuicon";  Description: "Create Start Menu shortcut";  GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Main application (output of PyInstaller COLLECT)
Source: "..\dist\SRK Boost\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start menu
Name: "{group}\{#MyAppName}";          Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

; Desktop
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"

; Startup
Name: "{autostartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
; Launch after install
Filename: "{app}\{#MyAppExeName}"; \
  Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
  Flags: nowait postinstall skipifsilent runascurrentuser

[UninstallDelete]
; Clean up user data on uninstall (optional)
Type: filesandordirs; Name: "{userappdata}\.srk_boost\logs"

[Registry]
; Add to "Programs and Features" with version info
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppID}"; \
  ValueType: string; ValueName: "DisplayVersion"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletevalue

[Code]
// Check for existing installation and offer to uninstall
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  UninstPath: String;
  UninstExe: String;
begin
  Result := True;
  UninstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppID}');
  if RegQueryStringValue(HKLM, UninstPath, 'UninstallString', UninstExe) then
  begin
    if MsgBox(ExpandConstant('{#MyAppName} is already installed. Uninstall the previous version first?'),
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      Exec(RemoveQuotes(UninstExe), '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;
