@echo off
title CROX - Python + MySQL Edition
color 0b
echo ========================================================
echo   CROX: Architecture Blueprint ^& Budget System
echo   [Pure Python + MySQL Desktop Edition]
echo ========================================================
echo.

:: Auto-detect Python executable
set "PYTHON_EXE="

:: 1. Check if 'python' works in PATH
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python"
    goto :python_found
)

:: 2. Check if 'py' launcher works
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=py"
    goto :python_found
)

:: 3. Check standard User AppData installations
for %%V in (313 312 311 310 39 314 38) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        goto :python_found
    )
)

:: 4. Check Program Files installations
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
    echo [ERROR] Python was not found in your PATH or standard directories.
    echo Please ensure Python 3 is installed from https://www.python.org/
    echo and check the box "Add Python to PATH" during installation.
    echo.
    pause
    exit /b
)

echo [Found Python] Using: "%PYTHON_EXE%"
echo.

:: Check drivers quickly without slowing down startup
"%PYTHON_EXE%" -c "import mysql.connector" >nul 2>&1
if %errorlevel% neq 0 (
    "%PYTHON_EXE%" -c "import pymysql" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [1/2] Checking MySQL Python drivers...
        "%PYTHON_EXE%" -m pip install --timeout 4 -r requirements.txt >nul 2>&1
    )
)

echo [2/2] Launching CROX Desktop Application...
echo.
"%PYTHON_EXE%" main.py

if %errorlevel% neq 0 (
    echo.
    echo Application closed with code %errorlevel%.
    pause
)
