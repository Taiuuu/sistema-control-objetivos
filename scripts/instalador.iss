#define MyAppName "VESP Control"
#define MyAppVersion "1.0.5"
#define MyAppPublisher "V.E.S.P Organizations"
#define MyAppExeName "VESP Control.exe"

[Setup]
AppId={{VESP-CONTROL-2024}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=VESP_Control_Instalador
OutputDir=instalador
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=C:\Proyecto Vesp\sistema-control-objetivos\assets\vesp.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Opciones adicionales:"

[Files]
Source: "C:\Proyecto Vesp\sistema-control-objetivos\dist\VESP Control\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Ejecutar {#MyAppName}"; Flags: nowait postinstall skipifsilent