@echo off
chcp 65001 >nul
set ROOT=%~dp0

if not exist "%ROOT%code\backend\main.py" (
  echo Missing backend entry: code\backend\main.py
  exit /b 1
)

if not exist "%ROOT%code\frontend\package.json" (
  echo Missing frontend package: code\frontend\package.json
  exit /b 1
)

title AI-Video-Backend
start cmd /k "cd /d %ROOT%code\backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 /nobreak >nul

title AI-Video-Frontend
start cmd /k "cd /d %ROOT%code\frontend && npm run dev"

echo Backend started on http://localhost:8000
echo Frontend started on http://localhost:8080
echo.
echo Press any key to close this window...
pause >nul
