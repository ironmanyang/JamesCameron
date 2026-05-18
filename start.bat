@echo off
chcp 65001 >nul
title AI-Video-Backend
start cmd /k "cd /d %~dp0code\backend && uvicorn main:app --port 8000 --reload"

timeout /t 2 /nobreak >nul

title AI-Video-Frontend
start cmd /k "cd /d %~dp0code\frontend && npm run serve"

echo Backend started on http://localhost:8000
echo Frontend started on http://localhost:8080
echo.
echo Press any key to close this window...
pause >nul