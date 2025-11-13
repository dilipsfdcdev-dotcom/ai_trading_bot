@echo off
REM Quick dependency installer for AI Trading Bot

echo ===================================
echo   Installing Dependencies
echo ===================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

echo [OK] Python and Node.js found
echo.

REM Install backend dependencies
echo [1/2] Installing Python dependencies...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies
    echo Try running: pip install --upgrade pip
    cd ..
    pause
    exit /b 1
)
echo installed > .dependencies_installed
cd ..
echo [OK] Python dependencies installed
echo.

REM Install frontend dependencies
echo [2/2] Installing Node.js dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install Node.js dependencies
    cd ..
    pause
    exit /b 1
)
cd ..
echo [OK] Node.js dependencies installed
echo.

echo ===================================
echo   Installation Complete!
echo ===================================
echo.
echo You can now run: .\start.bat
echo.
pause
