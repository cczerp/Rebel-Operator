@echo off
echo 🚀 Starting Agent API Server for n8n
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
echo Starting API server on port 3030...
echo.

node server.js
