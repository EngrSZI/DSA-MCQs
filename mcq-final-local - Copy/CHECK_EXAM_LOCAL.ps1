Write-Host "Checking MCQ application..." -ForegroundColor Cyan
try {
  $health = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 5
  $healthData = $health.Content | ConvertFrom-Json
  Write-Host "FastAPI: $($health.StatusCode) OK" -ForegroundColor Green
  if ($healthData.nsct_exam) {
    Write-Host "NSCT exam: $($healthData.nsct_exam.title)" -ForegroundColor Green
    Write-Host "Published: $($healthData.nsct_exam.is_published); Active: $($healthData.nsct_exam.is_active); Linked questions: $($healthData.nsct_exam.question_count)" -ForegroundColor Cyan
  } else {
    Write-Host "NSCT exam is missing from the database. Restart with START_EXAM_LOCAL.ps1 and inspect the API startup window." -ForegroundColor Red
  }
} catch {
  Write-Host "Could not query FastAPI health/database on port 8000: $($_.Exception.Message)" -ForegroundColor Red
}
try {
  $front = Invoke-WebRequest -Uri "http://127.0.0.1:5173/" -UseBasicParsing -TimeoutSec 5
  Write-Host "Frontend: $($front.StatusCode) OK" -ForegroundColor Green
} catch {
  Write-Host "Frontend is not running on port 5173." -ForegroundColor Red
}
