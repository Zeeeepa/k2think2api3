#!/bin/bash
# One-liner Local deployment verification script
# Usage: bash test_local_deployment.sh

set -e

echo "🖥️  Testing Local Python Deployment..."
echo "======================================"
echo ""

# Test credentials (replace with real ones)
EMAIL="${K2THINK_EMAIL:-developer@pixelium.uk}"
PASSWORD="${K2THINK_PASSWORD:-developer123?}"

echo "Using credentials:"
echo "  Email: $EMAIL"
echo "  Password: ******"
echo ""

# Run deployment in background with auto-inputs
echo "📦 Starting local server..."
(echo "$EMAIL" && sleep 1 && echo "$PASSWORD" && sleep 1 && echo "$PASSWORD") | python3 start.py &
START_PID=$!

# Wait for server to be fully ready
echo "⏳ Waiting 15 seconds for server to be fully ready..."
sleep 15

# Check if server is still running
if ! ps -p $START_PID > /dev/null; then
    echo "❌ Server failed to start"
    exit 1
fi

# Test the API
echo ""
echo "🧪 Testing API endpoint..."
PORT=8001
RESPONSE=$(curl -s -w "\n%{http_code}" http://127.0.0.1:$PORT/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-k2think' \
  -d '{
    "model": "MBZUAI-IFM/K2-Think",
    "messages": [{"role": "user", "content": "Say hello in 5 words"}],
    "stream": false
  }')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo ""
echo "📊 Results:"
echo "  HTTP Status: $HTTP_CODE"

# Stop the server
echo ""
echo "🛑 Stopping server..."
kill $START_PID 2>/dev/null || true
pkill -f k2think_proxy.py 2>/dev/null || true
sleep 2

if [ "$HTTP_CODE" -eq 200 ]; then
    echo "  ✅ SUCCESS - API is working!"
    echo ""
    echo "Response snippet:"
    echo "$BODY" | python3 -m json.tool | head -30
    
    # Check for thinking tags
    if echo "$BODY" | grep -q "<think>"; then
        echo ""
        echo "  ✅ Thinking mode is enabled (<think> tags found)"
    fi
    
    echo ""
    echo "🎉 Local deployment VERIFIED and WORKING!"
    echo ""
    echo "To run again: python3 start.py"
else
    echo "  ❌ FAILED - HTTP $HTTP_CODE"
    echo "$BODY"
    exit 1
fi

