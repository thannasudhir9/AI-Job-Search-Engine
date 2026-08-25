@echo off
cd /d %~dp0..\\backend
.venv\\Scripts\\python.exe ..\\scripts\\import_saved_jobs.py
pause
