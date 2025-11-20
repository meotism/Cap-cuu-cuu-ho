#!/bin/bash

# SOS Emergency Map Server - Production Deployment Script with Gunicorn

echo "=========================================="
echo "🆘 SOS Emergency Map Server (Production)"
echo "=========================================="
echo ""

# Configuration
PORT=${PORT:-5000}
WORKERS=${WORKERS:-4}
HOST=${HOST:-0.0.0.0}

# Check if Python 3 is installed
if ! command -v python &> /dev/null; then
    echo "❌ Error: Python  is not installed"
    exit 1
fi

echo "✅ Python version: $(python --version)"

# Create/activate virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

source venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
pip install gunicorn -q

# Create necessary directories
mkdir -p map_data
mkdir -p logs

# Check if port is already in use
PORT_IN_USE=$(lsof -Pi :$PORT -sTCP:LISTEN -t 2>/dev/null)
if [ ! -z "$PORT_IN_USE" ]; then
    echo "⚠️  Port $PORT is already in use (PID: $PORT_IN_USE)"
    echo "Stopping existing server..."
    kill -9 $PORT_IN_USE 2>/dev/null
    sleep 2
    echo "✅ Port cleared"
fi

echo ""
echo "=========================================="
echo "🚀 Starting Production Server"
echo "=========================================="
echo "Configuration:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Workers: $WORKERS"
echo "  Server: Gunicorn + Threading (WebSocket support)"
echo ""
echo "📍 Server URLs:"
echo "  - http://localhost:$PORT"
echo "  - http://$(hostname -I | awk '{print $1}'):$PORT"
echo ""
echo "📝 Logs: logs/server.log"
echo ""

# Start with Gunicorn and threading for WebSocket support
PORT=${PORT:-5000}
WORKERS=${WORKERS:-4}
HOST=${HOST:-0.0.0.0}
gunicorn --worker-class gthread --threads 4 -w $WORKERS \
    --bind $HOST:$PORT \
    --timeout 120 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level info \
    map_server:app
