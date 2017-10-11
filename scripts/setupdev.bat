@ECHO OFF
REM ---------------------------------------------------------------------------------------

REM Script to install the needed dev tools into the Python install that comes with OSGeo4W
REM Change %OSGEO4W_ROOT% in setenv.bat to change in the install folder.

REM ---------------------------------------------------------------------------------------

IF NOT EXIST "%VS90COMNTOOLS%" GOTO NOVS

pushd %~dp0
CALL setenv.bat
CALL "%OSGEO4W_ROOT%\bin\o4w_env.bat"

pushd ..\libs\py2exe-0.6.9
python setup.py install
popd
python -m pip install -r ..\requirements.txt --allow-all-external
GOTO END

:NOVS
ECHO You don't seem to have Visual Studio C++ 2008 installed.
ECHO We need that to build py2exe
GOTO END

:END
pause
