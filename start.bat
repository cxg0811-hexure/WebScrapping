@echo off
REM Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
cd /d "%~dp0"
python -m pip install -q -r requirements.txt
echo Starting Phone Price Tracker on http://localhost:8000
python -m uvicorn app:app --host 0.0.0.0 --port 8000

