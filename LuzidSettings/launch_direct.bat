@echo off
REM Simple launcher for LuzidSettings
REM Bypasses venv issues by using direct Python

cd /d "%~dp0"

py -3.14 run.py

pause
