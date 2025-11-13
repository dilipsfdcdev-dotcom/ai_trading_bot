@echo off
REM AI Trading Bot - Simple Startup Script for Windows
REM This script starts both backend and frontend together

echo ===================================
echo   AI Trading Bot - Starting Up
echo ===================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

echo [OK] Python and Node.js found
echo.

REM Check if backend/.env exists
if not exist "backend\.env" (
    echo [WARNING] Creating backend/.env from .env.example
    if exist "backend\.env.example" (
        copy "backend\.env.example" "backend\.env"
        echo Please edit backend/.env with your credentials
        echo.
    )
)

REM Check if frontend/.env.local exists
if not exist "frontend\.env.local" (
    echo [WARNING] Creating frontend/.env.local
    echo NEXT_PUBLIC_API_URL=http://localhost:8000 > frontend\.env.local
    echo NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws >> frontend\.env.local
)

REM Install backend dependencies if needed
if not exist "backend\.dependencies_installed" (
    echo Installing backend dependencies...
    cd backend
    pip install -r requirements.txt
    echo installed > .dependencies_installed
    cd ..
    echo [OK] Backend dependencies installed
    echo.
)

REM Install frontend dependencies if needed
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
    echo [OK] Frontend dependencies installed
    echo.
)

echo ===================================
echo   Starting Services...
echo ===================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press Ctrl+C to stop both services
echo.

REM Start backend in a new window
start "AI Trading Bot - Backend" /D "%CD%\backend" cmd /k "python main.py"

REM Wait a bit for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in a new window
start "AI Trading Bot - Frontend" /D "%CD%\frontend" cmd /k "npm run dev"

echo.
echo [OK] Both services started in separate windows
echo You can close this window now
echo.
pause
