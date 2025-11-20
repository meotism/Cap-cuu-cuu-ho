@echo off
REM SOS Emergency Map Server - Windows Startup Script

echo ==========================================
echo     SOS Emergency Map Server
echo ==========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created!
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing dependencies...
pip install --upgrade pip -q
pip install -r requirements.txt -q

if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

REM Create map_data directory if it doesn't exist
if not exist "map_data" (
    echo Creating map_data directory...
    mkdir map_data
)

echo.
echo ==========================================
echo Starting server...
echo ==========================================
echo.
echo Server will be available at:
echo   - http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ==========================================
echo.

REM Start the server
python map_server.py

pause
