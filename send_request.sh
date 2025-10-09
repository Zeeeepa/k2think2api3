#!/bin/bash

echo "🧪 K2Think API - Test Request Script"
echo "====================================="

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

PORT=${PORT:-7000}
API_KEY=${VALID_API_KEY:-test-key-123}

# Check if server is running
if ! curl -s http://localhost:$PORT/ > /dev/null 2>&1; then
    echo "❌ Server not responding on port $PORT"
    echo "   Run ./deploy.sh first to start the server"
    exit 1
fi

echo "✅ Server is running on port $PORT"
echo ""
echo "📤 Sending test request..."
echo ""

# Create Python test script
cat > /tmp/test_k2think.py << EOF
from openai import OpenAI

# Initialize client with K2Think API
client = OpenAI(
    base_url="http://localhost:$PORT/v1",
    api_key="$API_KEY"
)

print("🔄 Calling K2Think API...")
print("")

# Send request
response = client.chat.completions.create(
    model="MBZUAI-IFM/K2-Think",
    messages=[
        {"role": "user", "content": "What is your model name?"}
    ]
)

print("=" * 60)
print("📥 RESPONSE RECEIVED")
print("=" * 60)
print(f"Model: {response.model}")
print(f"ID: {response.id}")
print(f"")
print(f"Content:")
print("-" * 60)
print(response.choices[0].message.content)
print("-" * 60)
print(f"")
print(f"Token Usage:")
print(f"  • Prompt tokens: {response.usage.prompt_tokens}")
print(f"  • Completion tokens: {response.usage.completion_tokens}")
print(f"  • Total tokens: {response.usage.total_tokens}")
print("=" * 60)
EOF

# Run the test
python3 /tmp/test_k2think.py

# Cleanup
rm /tmp/test_k2think.py

echo ""
echo "✅ Test complete!"

