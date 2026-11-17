Write-Host "Checking MCQ application..." -ForegroundColor Cyan
try {
  $health = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 5
  Write-Host "FastAPI: $($health.StatusCode) OK" -ForegroundColor Green
} catch {
  Write-Host "FastAPI is not running on port 8000." -ForegroundColor Red
}
try {
  $front = Invoke-WebRequest -Uri "http://127.0.0.1:5173/" -UseBasicParsing -TimeoutSec 5
  Write-Host "Frontend: $($front.StatusCode) OK" -ForegroundColor Green
} catch {
  Write-Host "Frontend is not running on port 5173." -ForegroundColor Red
}
