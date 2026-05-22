@echo off
chcp 65001 >nul
set ROOT=%~dp0

if not exist "%ROOT%start_hidden.ps1" (
  echo Missing launcher script: start_hidden.ps1
  exit /b 1
)

start "" powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%ROOT%start_hidden.ps1"
exit /b 0
