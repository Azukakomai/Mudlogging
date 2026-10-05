@echo off
setlocal enabledelayedexpansion
title MudLog Pro Desktop Software
cd /d "%~dp0desktop_app"

echo =======================================================
echo   MudLog Pro Desktop Software
echo   Created By Mohammad Azka Khairur Rahman
echo =======================================================
echo.
echo Launching MudLog Pro Desktop Software...
echo.

:: Detect Python executable
set "PYTHON_EXE="

:: 1. Check local python core installation
if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
) else if exist "%LOCALAPPDATA%\Python\bin\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Python\bin\python.exe"
)

:: 2. Check py launcher
if not defined PYTHON_EXE (
    where py >nul 2>&1
    if !ERRORLEVEL! EQU 0 set "PYTHON_EXE=py"
)

:: 3. Check python on PATH
if not defined PYTHON_EXE (
    where python >nul 2>&1
    if !ERRORLEVEL! EQU 0 set "PYTHON_EXE=python"
)

if defined PYTHON_EXE (
    "%PYTHON_EXE%" main.py
) else (
    echo [ERROR] Python not found. Please ensure Python is installed.
    pause
)
