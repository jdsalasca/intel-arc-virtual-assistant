@echo off
echo ================================================
echo   OpenVINO GenAI Server Setup Script
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python is installed
python --version

echo.
echo 📦 Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully

echo.
echo 📁 Setting up environment file...
if not exist .env (
    copy .env.example .env
    echo ✅ Created .env file from template
    echo ℹ️  You can edit .env to customize settings
) else (
    echo ℹ️  .env file already exists
)

echo.
echo 🎉 Setup complete!
echo.
echo To start the server, run:
echo   python start_server.py
echo.
echo To test the server, run:
echo   python test_client.py
echo.
echo For more information, see README.md
echo.
pause