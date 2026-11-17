$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Frontend = Join-Path $Root "frontend-app"
Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*$Root*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Get-CimInstance Win32_Process |
    Where-Object { $_.Name -eq "node.exe" -and $_.CommandLine -like "*$Frontend*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Set-Location $Root
docker compose down --remove-orphans
Write-Host "MCQ local services stopped. Database data remains in the Docker volume." -ForegroundColor Yellow
