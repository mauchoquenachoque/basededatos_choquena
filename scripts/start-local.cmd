@echo off
REM Arranca backend + frontend sin cambiar ExecutionPolicy del sistema.
cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-local.ps1"
