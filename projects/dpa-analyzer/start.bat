@echo off
REM DPA Privacy Legal Review AI Agent - Windows Startup Script

echo 🚀 Starting DPA Privacy Legal Review AI Agent...
echo.

REM Check if Ollama is running
echo 📝 Checking Ollama status...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo ❌ Ollama is not running. Please start Ollama first:
    echo    ollama serve
    echo.
    echo 📥 If you haven't installed a model yet, run:
    echo    ollama pull llama3.1:8b
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Ollama is running
)

REM Start backend
echo.
echo 🔧 Starting backend server...
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt >nul 2>&1

REM Start FastAPI server
echo 🚀 Starting FastAPI server on port 8000...
start /b python main.py

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend
echo.
echo 🌐 Starting frontend server on port 3000...

REM Start simple HTTP server
start /b python -m http.server 3000

echo.
echo ✅ Application started successfully!
echo.
echo 📱 Open your browser and go to: http://localhost:3000
echo 🔧 Backend API available at: http://localhost:8000
echo.
echo 📋 Press any key to stop the application
echo.

pause >nul

echo.
echo 🛑 Shutting down servers...
taskkill /f /im python.exe >nul 2>&1
echo ✅ Servers stopped
