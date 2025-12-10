#!/bin/bash
# One-liner Docker deployment verification script
# Usage: bash test_docker_deployment.sh

set -e

echo "🐳 Testing Docker Deployment..."
echo "================================"
echo ""

# Test credentials (replace with real ones)
EMAIL="${K2THINK_EMAIL:-developer@pixelium.uk}"
PASSWORD="${K2THINK_PASSWORD:-developer123?}"

echo "Using credentials:"
echo "  Email: $EMAIL"
echo "  Password: ******"
echo ""

# Run deployment with auto-inputs
echo "$EMAIL" | python3 start_docker.py << EOF
$PASSWORD
$PASSWORD
EOF

# Wait for container to be fully ready
echo ""
echo "⏳ Waiting 10 seconds for container to be fully ready..."
sleep 10

# Test the API
echo ""
echo "🧪 Testing API endpoint..."
PORT=${HOST_PORT:-8001}
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
    echo "🎉 Docker deployment VERIFIED and WORKING!"
    echo ""
    echo "API Endpoint: http://127.0.0.1:$PORT/v1/chat/completions"
    echo "To stop: docker compose down"
else
    echo "  ❌ FAILED - HTTP $HTTP_CODE"
    echo "$BODY"
    exit 1
fi

