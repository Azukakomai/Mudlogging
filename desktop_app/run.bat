@echo off
title MudLog Pro Desktop Software
echo =======================================================
echo   MudLog Pro Desktop Software
echo   Created By Mohammad Azka Khairur Rahman
echo =======================================================
echo.
echo Launching MudLog Pro Desktop Software...
echo.

py main.py
if %ERRORLEVEL% NEQ 0 (
    python main.py
)

pause
