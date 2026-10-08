#!/bin/bash

# DPA Privacy Legal Review AI Agent - Startup Script

echo "🚀 Starting DPA Privacy Legal Review AI Agent..."
echo ""

# Check if Ollama is running
echo "📝 Checking Ollama status..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama is not running. Please start Ollama first:"
    echo "   ollama serve"
    echo ""
    echo "📥 If you haven't installed a model yet, run:"
    echo "   ollama pull llama3.1:8b"
    echo ""
    exit 1
else
    echo "✅ Ollama is running"
fi

# Start backend
echo ""
echo "🔧 Starting backend server..."
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Start FastAPI server in background
echo "🚀 Starting FastAPI server on port 8000..."
python main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
echo ""
echo "🌐 Starting frontend server on port 3000..."

# Start simple HTTP server in background
python3 -m http.server 3000 &
FRONTEND_PID=$!

echo ""
echo "✅ Application started successfully!"
echo ""
echo "📱 Open your browser and go to: http://localhost:3000"
echo "🔧 Backend API available at: http://localhost:8000"
echo ""
echo "📋 To stop the application, press Ctrl+C"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT TERM

# Wait for user to stop the script
wait