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
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

echo "✅ Python version: $(python3 --version)"

# Create/activate virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
pip install gunicorn eventlet -q

# Create necessary directories
mkdir -p map_data
mkdir -p logs

echo ""
echo "=========================================="
echo "🚀 Starting Production Server"
echo "=========================================="
echo "Configuration:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Workers: $WORKERS"
echo "  Server: Gunicorn + Eventlet (WebSocket support)"
echo ""
echo "📍 Server URLs:"
echo "  - http://localhost:$PORT"
echo "  - http://$(hostname -I | awk '{print $1}'):$PORT"
echo ""
echo "📝 Logs: logs/server.log"
echo ""

# Start with Gunicorn and eventlet for WebSocket support
gunicorn --worker-class eventlet -w 1 \
    --bind $HOST:$PORT \
    --timeout 120 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level info \
    map_server:app
