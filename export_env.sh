#!/bin/bash
# Helper script to export K2Think API environment variables
# Usage: source <(curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/export_env.sh)

PROJECT_DIR="$HOME/k2think2api3"

if [ -f "$PROJECT_DIR/.env" ]; then
    API_KEY=$(grep VALID_API_KEY "$PROJECT_DIR/.env" | cut -d'=' -f2)
    if [ ! -z "$API_KEY" ]; then
        export OPENAI_API_KEY="$API_KEY"
        export OPENAI_BASE_URL="http://localhost:7000/v1"
        echo "✅ Environment variables exported:"
        echo "   OPENAI_API_KEY=$API_KEY"
        echo "   OPENAI_BASE_URL=$OPENAI_BASE_URL"
        echo ""
        echo "🐍 Now you can use OpenAI SDK directly:"
        echo '   python -c "from openai import OpenAI; client = OpenAI(); print(client.chat.completions.create(model=\"MBZUAI-IFM/K2-Think\", messages=[{\"role\":\"user\",\"content\":\"Hello!\"}]).choices[0].message.content)"'
    else
        echo "❌ Error: Could not find VALID_API_KEY in .env file"
    fi
else
    echo "❌ Error: .env file not found at $PROJECT_DIR/.env"
    echo "   Run the deployment script first!"
fi

