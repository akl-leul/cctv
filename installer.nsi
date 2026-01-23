
; NSIS installer script for CCTV Face Detection System

!define APPNAME "CCTV Face Detection System"
!define VERSION "1.0.0"
!define PUBLISHER "CCTV Systems"
!define URL "https://github.com/cctv-face-detection"

; Include Modern UI
!include "MUI2.nsh"
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"

; General settings
Name "${APPNAME}"
OutFile "CCTV_Face_Detection_System_Installer.exe"
InstallDir "$PROGRAMFILES\${APPNAME}"
InstallDirRegKey "Software\${APPNAME}"
RequestExecutionLevel admin
ShowInstDetails show
ShowUninstDetails show

; Version information
VIProductVersion "${VERSION}"
VIAddVersionKey /V "${VERSION}" "${PUBLISHER}" "${APPNAME}"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; License page
!insertmacro MUI_PAGE_LICENSE
LicenseData "License Agreement"
LicenseText "This software is provided as-is without warranty. By installing this software, you agree to the terms of use."

; Components page
!insertmacro MUI_PAGE_COMPONENTS
Section "Core Components" SecCore
    SectionIn RO "Required files (do not remove)" SecCore
        SetOutPath "$INSTDIR"
        File "CCTV_Face_Detection_System.exe"
        File /r "haarcascades"
        File /r "templates"
        File /r "icon.ico"
    SectionEnd
SectionEnd

; Create shortcuts
Section "Shortcuts" SecShortcuts
    CreateShortCut "$INSTDIR\CCTV_Face_Detection_System.exe" "$DESKTOP\${APPNAME}.lnk"
    CreateShortCut "$INSTDIR\CCTV_Face_Detection_System.exe" "$SMPROGRAMS\${APPNAME}.lnk"
SectionEnd

; Registry entries for file associations
Section "File Associations" SecFileAssoc
    WriteRegStr HKCR ".jpg" "" "JPEG Image"
    WriteRegStr HKCR ".jpg\OpenWithProgids" "CCTV_Face_Detection_System.exe" 0
    WriteRegStr HKCR "CCTV_Face_Detection_System.exe\shell\open\command" "" '"$INSTDIR\CCTV_Face_Detection_System.exe" "%1"'
SectionEnd

; Uninstaller
Section "Uninstall"
    DeleteRegKey HKCR ".jpg\OpenWithProgids" "CCTV_Face_Detection_System.exe"
    DeleteRegKey HKCR "CCTV_Face_Detection_System.exe"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    RMDir /r "$INSTDIR"
    Delete "$DESKTOP\${APPNAME}.lnk"
    Delete "$SMPROGRAMS\${APPNAME}.lnk"
SectionEnd
