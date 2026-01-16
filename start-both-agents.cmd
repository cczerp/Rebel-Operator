@echo off
echo 🚀 Starting BOTH AI Agent Servers for n8n
echo.

echo Checking Ollama connection...
curl -s http://localhost:11434/api/version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Ollama is running
) else (
    echo ❌ Ollama is NOT running!
    echo.
    echo Please start Ollama first:
    echo   - Open a new terminal and run: ollama serve
    echo.
    pause
    exit /b 1
)

echo.
echo Starting Judge Trudy on port 3030...
start "Judge Trudy" cmd /k "npm run start:trudy"

timeout /t 2 /nobreak >nul

echo Starting Qwen Ryche on port 3131...
start "Qwen Ryche" cmd /k "npm run start:qwen"

echo.
echo ✅ Both servers are starting!
echo    - Judge Trudy: http://localhost:3030
echo    - Qwen Ryche:  http://localhost:3131
echo.
pause
