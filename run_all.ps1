# EASP Enterprise AI Security Platform - PowerShell Launcher
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  EASP - Enterprise AI Security Platform Launcher" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

$root = $PSScriptRoot

Write-Host "`n[1/3] Starting Python FastAPI AI Microservice (Port 8000)..." -ForegroundColor Yellow
$pythonExe = "C:\Users\kimoa\miniconda3\python.exe"
if (-not (Test-Path $pythonExe)) { $pythonExe = "python" }
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\ai_service'; Write-Host '--- EASP AI Microservice (Port 8000) ---' -ForegroundColor Green; & '$pythonExe' app.py"

Start-Sleep -Seconds 3

Write-Host "[2/3] Starting Node.js Express Backend (Port 5000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; Write-Host '--- EASP Backend (Port 5000) ---' -ForegroundColor Green; npm start"

Start-Sleep -Seconds 3

Write-Host "[3/3] Starting React Vite Frontend (Port 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; Write-Host '--- EASP Frontend (Port 5173) ---' -ForegroundColor Green; npm run dev"

Write-Host "`nAll 3 services have been launched in separate PowerShell windows!" -ForegroundColor Green
Write-Host "Open your browser at: http://localhost:5173`n" -ForegroundColor Cyan
Write-Host "Default Logins:" -ForegroundColor Yellow
Write-Host "  Administrator: admin@easp.local    / Password123!"
Write-Host "  Analyst:       analyst@easp.local  / Password123!"
Write-Host "  Employee:      employee@easp.local / Password123!"
