@echo off
echo ===================================================
echo   Starting CROX (CS Project)
echo ===================================================
echo.

:: Auto-detect Python executable
set "PYTHON_EXE="

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python"
    goto :python_found
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=py"
    goto :python_found
)

for %%V in (313 312 311 310 39 314 38) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        goto :python_found
    )
)

for %%V in (313 312 311 310 39 314 38) do (
    if exist "C:\Program Files\Python%%V\python.exe" (
        set "PYTHON_EXE=C:\Program Files\Python%%V\python.exe"
        goto :python_found
    )
    if exist "C:\Program Files (x86)\Python%%V\python.exe" (
        set "PYTHON_EXE=C:\Program Files (x86)\Python%%V\python.exe"
        goto :python_found
    )
)

:python_found
if not defined PYTHON_EXE (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3 from https://www.python.org/
    pause
    exit /b
)

echo [1/2] Installing required dependencies...
"%PYTHON_EXE%" -m pip install -r requirements.txt >nul 2>&1

echo.
echo [2/2] Starting Local Server...
echo.
echo ===================================================
echo   SERVER RUNNING! 
echo   Keep this window open and go to:
echo   http://127.0.0.1:5000 in your web browser.
echo ===================================================
echo.

"%PYTHON_EXE%" app.py
pause
