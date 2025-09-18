@echo off
echo Starting JDDB Backend Server...
cd backend
call venv\Scripts\activate.bat
python scripts\dev_server.py
pause
