@echo off
setlocal enabledelayedexpansion
title EASP Enterprise AI Security Platform - Launcher

:: Anchor working directory to the script's exact folder
cd /d "%~dp0"

echo ====================================================================
echo   EASP - Enterprise AI Security Platform
echo   Launching Dual-Engine AI Microservice, Backend, and Frontend
echo ====================================================================
echo.

:: 0. Check MongoDB Service (if installed as Windows service)
echo [*] Checking Database status...
net start MongoDB >nul 2>&1

:: Detect correct Python executable
set "PYTHON_EXE=python"
if exist "C:\Users\kimoa\miniconda3\python.exe" (
    set "PYTHON_EXE=C:\Users\kimoa\miniconda3\python.exe"
)

echo [*] Using Python: !PYTHON_EXE!
echo.

:: 1. Start Python FastAPI AI Microservice (Port 8000)
echo [1/3] Starting Python FastAPI AI Microservice (Port 8000)...
start "EASP [1/3] - AI Microservice (Port 8000)" cmd /k "cd /d "%~dp0ai_service" && "!PYTHON_EXE!" app.py"

timeout /t 4 /nobreak >nul

:: 2. Start Node.js Express Backend (Port 5000)
echo [2/3] Starting Node.js Express Backend (Port 5000)...
start "EASP [2/3] - Backend (Port 5000)" cmd /k "cd /d "%~dp0backend" && npm start"

timeout /t 4 /nobreak >nul

:: 3. Start React Vite Frontend (Port 3000)
echo [3/3] Starting React Vite Frontend (Port 3000)...
start "EASP [3/3] - Frontend (Port 3000)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

timeout /t 3 /nobreak >nul

:: Automatically open browser
start http://localhost:3000

echo.
echo ====================================================================
echo   SUCCESS: All 3 EASP services are running!
echo   Web Interface:  http://localhost:3000
echo   AI Microservice: http://localhost:8000/docs
echo   Backend API:    http://localhost:5000
echo.
echo   Default Credentials:
echo     Admin:    admin@easp.local    / Password123!
echo     Analyst:  analyst@easp.local  / Password123!
echo     Employee: employee@easp.local / Password123!
echo ====================================================================
echo.
echo Keep this launcher or the opened service windows active while working.
pause

