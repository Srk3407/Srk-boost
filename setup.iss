[Setup]
AppName=SRK Boost
AppVersion=1.0
AppPublisher=SRK Software
AppPublisherURL=https://srkboost.com
DefaultDirName={autopf}\SRK Boost
DefaultGroupName=SRK Boost
OutputBaseFilename=SRK_Boost_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstü kısayolu oluştur"; GroupDescription: "Ek görevler:"

[Files]
Source: "dist\SRK Boost.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SRK Boost"; Filename: "{app}\SRK Boost.exe"
Name: "{commondesktop}\SRK Boost"; Filename: "{app}\SRK Boost.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SRK Boost.exe"; Description: "SRK Boost'u başlat"; Flags: nowait postinstall skipifsilent
