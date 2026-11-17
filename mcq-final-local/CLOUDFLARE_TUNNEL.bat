@echo off
setlocal
if exist "C:\cloudflared\cloudflared.exe" (
  "C:\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:5173
  goto :eof
)
where cloudflared >nul 2>nul
if %errorlevel%==0 (
  cloudflared tunnel --url http://127.0.0.1:5173
  goto :eof
)
echo.
echo cloudflared was not found.
echo Install cloudflared from:
echo https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
echo Then put cloudflared.exe in C:\cloudflared\ or add it to PATH.
pause
