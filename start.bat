@echo off
REM One-click start for uv + bun project — run from E:\Abhau
REM Requires: uv and bun on PATH
echo [1/2] Starting backend on http://localhost:8000 ...
start "AI-Validator API :8000" cmd /k "uv run uvicorn backend.app:app --reload --port 8000"
echo Waiting 4s for API to boot...
timeout /t 4 /nobreak >nul
echo [2/2] Starting frontend on http://localhost:3000 ...
start "AI-Validator WEB :3000" cmd /k "bun --cwd frontend run dev"
echo Done. Open http://localhost:3000  and http://localhost:8000/docs
pause
