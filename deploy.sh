#!/bin/bash
set -e

echo "🚀 K2Think API Proxy - Deploy Script"
echo "====================================="

# Check if setup was run
if [ ! -d "data" ] || [ ! -f ".env" ]; then
    echo "⚠️  Setup not complete. Running setup first..."
    bash setup.sh
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "✨ Activating virtual environment..."
    source venv/bin/activate
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check for running instance
if [ -f ".server.pid" ]; then
    OLD_PID=$(cat .server.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "⚠️  Server already running (PID: $OLD_PID)"
        echo "   Use 'kill $OLD_PID' to stop it first"
        exit 1
    else
        rm .server.pid
    fi
fi

# Start the server
echo "🎯 Starting K2Think API Proxy..."
echo "   Port: ${PORT:-7000}"
echo "   Log file: server.log"

nohup python3 k2think_proxy.py > server.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > .server.pid

# Wait for server to start
echo "⏳ Waiting for server to initialize..."
sleep 5

# Check if server is running
if ps -p $SERVER_PID > /dev/null 2>&1; then
    # Try to connect
    MAX_RETRIES=10
    RETRY=0
    while [ $RETRY -lt $MAX_RETRIES ]; do
        if curl -s http://localhost:${PORT:-7000}/ > /dev/null 2>&1; then
            echo "✅ Server started successfully!"
            echo ""
            echo "📊 Server Information:"
            curl -s http://localhost:${PORT:-7000}/ | python3 -m json.tool 2>/dev/null || echo "   Running on http://localhost:${PORT:-7000}"
            echo ""
            echo "📝 Useful commands:"
            echo "   • View logs: tail -f server.log"
            echo "   • Stop server: kill $SERVER_PID"
            echo "   • Test API: ./send_request.sh"
            echo "   • PID file: .server.pid"
            exit 0
        fi
        RETRY=$((RETRY+1))
        sleep 2
    done
    echo "⚠️  Server process running but not responding"
    echo "   Check server.log for errors"
    tail -20 server.log
    exit 1
else
    echo "❌ Server failed to start!"
    echo "   Check server.log for errors:"
    tail -30 server.log
    rm .server.pid
    exit 1
fi
