@ECHO OFF

call %~dp0setenv.bat

python %~dp0build.py --target %1 deploy
