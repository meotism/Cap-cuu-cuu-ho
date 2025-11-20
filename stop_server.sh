#!/bin/bash

# Stop SOS Emergency Map Server

echo "Stopping SOS Emergency Map Server..."

# Find and kill Python processes running map_server.py
pkill -f "python.*map_server.py"

# Find and kill Gunicorn processes
pkill -f "gunicorn.*map_server:app"

if [ $? -eq 0 ]; then
    echo "✅ Server stopped successfully"
else
    echo "ℹ️  No running server found"
fi
