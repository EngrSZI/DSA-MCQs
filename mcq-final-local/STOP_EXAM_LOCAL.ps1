$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*$Root*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Set-Location $Root
docker compose down --remove-orphans
Write-Host "MCQ local services stopped. Database data remains in the Docker volume." -ForegroundColor Yellow
