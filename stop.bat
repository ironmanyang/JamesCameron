@echo off
chcp 65001 >nul

taskkill /FI "WINDOWTITLE eq AI-Video-Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq AI-Video-Frontend*" /F >nul 2>&1

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo All processes stopped and ports released.
