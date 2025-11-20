#!/bin/bash

# Quick fix for "Address already in use" error

echo "🔍 Checking port 5000..."

if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 5000 is in use. Killing processes..."
    
    # Show what's using the port
    echo ""
    echo "Processes using port 5000:"
    lsof -i :5000
    echo ""
    
    # Kill processes
    sudo kill -9 $(lsof -t -i:5000) 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ Port 5000 cleared successfully"
    else
        echo "❌ Failed to clear port. Try manually:"
        echo "   sudo lsof -i :5000"
        echo "   sudo kill -9 <PID>"
    fi
else
    echo "✅ Port 5000 is available"
fi

echo ""
echo "Ready to start server!"
