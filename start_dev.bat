@echo off
echo.
echo ================================================
echo Intel Virtual Assistant - Development Environment
echo ================================================
echo.

REM Check if we're in the right directory
if not exist "main.py" (
    echo Error: Please run this script from the project root directory
    pause
    exit /b 1
)

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Start the development servers
echo Starting development environment...
python dev_server.py

pause