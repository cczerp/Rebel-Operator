@echo off
setlocal enabledelayedexpansion

echo 🚀 Starting full dev stack...

REM -------- CONFIG --------
set DEV_ROOT=C:\dev
set N8N_DIR=%DEV_ROOT%\n8n
set SERVER_DIR=%DEV_ROOT%\server
set CURSOR_PROJECT=%DEV_ROOT%\cursor-project

REM -------- EXECUTABLES --------
set NPX_CMD=npx
set NODE_CMD=node
set NGROK_CMD=ngrok
set CURSOR_CMD=cursor

REM -------- START WINDOWS TERMINAL --------
wt ^
 new-tab cmd /k "cd /d %N8N_DIR% && %NPX_CMD% n8n" ^
 ; split-pane -H cmd /k "echo n8n logs pane" ^
 ; new-tab cmd /k "cd /d %SERVER_DIR% && %NODE_CMD% server.js" ^
 ; new-tab cmd /k "%NGROK_CMD% http 3333"

REM -------- START CURSOR --------
start "" %CURSOR_CMD% "%CURSOR_PROJECT%"

echo.
echo 🟢 DEV STACK LIVE
echo.
echo ❗ Stop everything by running stop-dev.cmd
echo.

pause
