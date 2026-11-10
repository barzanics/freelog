[Setup]
AppName=WorkTracker
AppVersion=6.0.1
DefaultDirName={autopf}\WorkTracker
DefaultGroupName=WorkTracker
OutputBaseFilename=WorkTracker-Setup
Compression=lzma2
[Files]
Source: "..\dist\WorkTracker\*"; DestDir: "{app}"; Flags: recursesubdirs
[Icons]
Name: "{group}\WorkTracker"; Filename: "{app}\WorkTracker.exe"
Name: "{autodesktop}\WorkTracker"; Filename: "{app}\WorkTracker.exe"
