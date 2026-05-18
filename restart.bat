@echo off
chcp 65001 >nul
echo Stopping services...
call "%~dp0stop.bat"
echo.
echo Starting services...
call "%~dp0start.bat"