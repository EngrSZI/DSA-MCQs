$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend-app"

Write-Host "=== MCQ Examination System - Local Server ===" -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is not installed or is not in PATH. Install Docker Desktop and run it first."
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is not installed or is not in PATH."
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "Node.js/npm is not installed or is not in PATH."
}

Write-Host "Starting PostgreSQL..." -ForegroundColor Yellow
Set-Location $Root

$DbContainer = "mcq-db"
$ExistingDb = docker ps -aq --filter "name=^/$DbContainer$"
if ($ExistingDb) {
    Write-Host "Removing stale database container '$DbContainer'..." -ForegroundColor Yellow
    docker rm -f $DbContainer | Out-Null
}

docker compose up -d

$Venv = Join-Path $Backend ".venv"
if (Test-Path $Venv) {
    $CfgPath = Join-Path $Venv "pyvenv.cfg"
    if (Test-Path $CfgPath) {
        $Cfg = Get-Content $CfgPath -Raw
        if ($Cfg -match "command = .* -m venv (.+)") {
            $VenvTarget = $Matches[1].Trim()
            if ($VenvTarget -and $VenvTarget -ne (Resolve-Path $Backend).Path) {
                Write-Host "Refreshing stale Python environment from a previous project path..." -ForegroundColor Yellow
                $StalePyProcesses = Get-CimInstance Win32_Process | Where-Object {
                    $_.Name -match "python|pip" -and $_.CommandLine -match "mcq-examination-system"
                }
                foreach ($Proc in $StalePyProcesses) {
                    Stop-Process -Id $Proc.ProcessId -Force -ErrorAction SilentlyContinue
                }
                Remove-Item -Recurse -Force $Venv -ErrorAction SilentlyContinue
            }
        }
    }
}

if (-not (Test-Path $Venv)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv $Venv
}

$Py = Join-Path $Venv "Scripts\python.exe"
$Pip = Join-Path $Venv "Scripts\pip.exe"
if (-not (Test-Path $Py) -or -not (Test-Path $Pip)) {
    Write-Host "Python environment is incomplete. Recreating it..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $Venv -ErrorAction SilentlyContinue
    python -m venv $Venv
    $Py = Join-Path $Venv "Scripts\python.exe"
    $Pip = Join-Path $Venv "Scripts\pip.exe"
}

Write-Host "Installing/updating backend dependencies..." -ForegroundColor Yellow
& $Pip install -r (Join-Path $Backend "requirements.txt")

Write-Host "Applying database migrations..." -ForegroundColor Yellow
Set-Location $Root
& $Py -m alembic upgrade head

Write-Host "Importing/updating the NSCT all-subject question bank..." -ForegroundColor Yellow
& $Py (Join-Path $Backend "seed_nsct_exam.py")

Write-Host "Ensuring local administrator account exists..." -ForegroundColor Yellow
& $Py (Join-Path $Backend "create_admin.py")

Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location $Frontend
npm install

Write-Host "Starting FastAPI in a new window..." -ForegroundColor Green
$backendCmd = "Set-Location '$Root'; & '$Py' -m uvicorn --app-dir backend app.main:app --host 0.0.0.0 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $backendCmd

Start-Sleep -Seconds 3

Write-Host "Starting React/Vite in a new window..." -ForegroundColor Green
$frontendCmd = "Set-Location '$Frontend'; npm run dev -- --host 0.0.0.0"
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $frontendCmd

Write-Host "" 
Write-Host "Local student URL: http://localhost:5173/" -ForegroundColor Cyan
Write-Host "API health:        http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "API docs:          http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Student URLs on this network:" -ForegroundColor Cyan
$LanAddresses = Get-NetIPConfiguration |
    Where-Object { $_.IPv4DefaultGateway -and $_.IPv4Address } |
    ForEach-Object { $_.IPv4Address.IPAddress } |
    Where-Object { $_ -notlike "127.*" -and $_ -notlike "169.254.*" } |
    Sort-Object -Unique
foreach ($Address in $LanAddresses) {
    Write-Host "  http://${Address}:5173/" -ForegroundColor Cyan
}
Write-Host "" 
Write-Host "Allow inbound TCP port 5173 through Windows Firewall on the Private network profile." -ForegroundColor Yellow
Write-Host "Students must connect to the same trusted Wi-Fi/LAN. Keep this computer, Docker, FastAPI, and Vite running." -ForegroundColor Yellow
