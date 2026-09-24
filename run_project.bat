@echo off
echo ===================================================
echo   Starting CROX (CS Project)
echo ===================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3 from https://www.python.org/
    pause
    exit /b
)

echo [1/2] Installing required dependencies...
pip install -r requirements.txt >nul 2>&1

echo.
echo [2/2] Starting Local Server...
echo.
echo ===================================================
echo   SERVER RUNNING! 
echo   Keep this window open and go to:
echo   http://127.0.0.1:5000 in your web browser.
echo ===================================================
echo.

python app.py
pause
