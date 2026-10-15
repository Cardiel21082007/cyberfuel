@echo off 
echo Creando acceso directo en el escritorio... 
set "SCRIPT_PATH=%~dp0INICIAR_CYBERFUEL.bat" 
set "ICON_PATH=%~dp0icono_apast.ico" 
set "DESKTOP=%USERPROFILE%\Desktop" 
set "SHORTCUT=%DESKTOP%\CyberFuel ULTRA.lnk" 
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%SCRIPT_PATH%'; $s.WorkingDirectory = '%~dp0'; $s.IconLocation = '%ICON_PATH%'; $s.Save()" 
echo Listo! Busca el icono en tu Escritorio. 
pause 
