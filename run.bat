@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo    SafeFall AI - Agentic Fall Detection & Context Emergency Response
echo ======================================================================
echo [INFO] Starting SafeFall AI Environment Initialization...

cd /d "%~dp0"

:: 1. Check Python installation
where python3.12 >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PY_CMD=python3.12"
) else (
    where py >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set "PY_CMD=py"
    ) else (
        where python >nul 2>nul
        if %ERRORLEVEL% EQU 0 (
            set "PY_CMD=python"
        ) else (
            echo [ERROR] Python not found in PATH! Please install Python 3.9+.
            pause
            exit /b 1
        )
    )
)

:: 2. Check virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo [INFO] Creating Python virtual environment in .venv ...
    %PY_CMD% -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
)

:: 3. Activate virtual environment
call .venv\Scripts\activate.bat

:: 4. Verify Streamlit installation
.venv\Scripts\python.exe -c "import streamlit" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Installing required dependencies from requirements.txt ...
    .venv\Scripts\pip.exe install -r requirements.txt
)

:: 5. Launch application
echo [INFO] Launching SafeFall AI Streamlit Dashboard...
echo [INFO] Open your web browser at: http://localhost:8501
.venv\Scripts\streamlit.exe run app.py --server.headless false

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Streamlit exited with an error code.
    pause
)
