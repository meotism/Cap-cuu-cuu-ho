#!/bin/bash

# SOS Emergency Map Server - Linux Startup Script

echo "=========================================="
echo "🆘 SOS Emergency Map Server"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $PYTHON_VERSION"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip -q

# Install requirements
echo "📦 Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    echo "✅ Dependencies installed"
else
    echo "❌ requirements.txt not found"
    exit 1
fi

# Create map_data directory if it doesn't exist
if [ ! -d "map_data" ]; then
    echo "📁 Creating map_data directory..."
    mkdir -p map_data
fi

# Check if map_server.py exists
if [ ! -f "map_server.py" ]; then
    echo "❌ Error: map_server.py not found"
    exit 1
fi

# Check if port 5000 is already in use
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 5000 is already in use"
    echo "Stopping existing server..."
    kill -9 $(lsof -t -i:5000) 2>/dev/null
    sleep 2
    echo "✅ Port cleared"
fi

echo ""
echo "=========================================="
echo "🚀 Starting server..."
echo "=========================================="
echo ""
echo "📍 Server will be available at:"
echo "   - http://localhost:5000"
echo "   - http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python3 map_server.py
