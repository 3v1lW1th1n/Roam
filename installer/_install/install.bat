@ECHO OFF
: Set to the address of the local and remote server
Set REMOTESERVER=None
Set LOCALSERVER=None

CALL ..\setenv.bat

TITLE IntraMaps Roam Installer
python "%~dp0postinstall.py" --remote_server %REMOTESERVER% --local_server %LOCALSERVER%
pause
