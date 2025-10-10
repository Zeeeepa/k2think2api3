# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

K2Think API Proxy is a FastAPI-based OpenAI-compatible API proxy for MBZUAI's K2-Think model. It provides token management, streaming support, function calling, and automated deployment capabilities.

## Common Development Commands

### Setup and Installation
```bash
# One-command installation (recommended for new setups)
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/scripts/all.sh | bash

# Manual setup
git clone https://github.com/Zeeeepa/k2think2api3
cd k2think2api3
bash scripts/setup.sh
```

### Server Management
```bash
# Start/restart server
bash scripts/deploy.sh

# Stop server
kill $(cat .server.pid)

# View server logs
tail -f server.log

# Health check
curl http://localhost:7000/health
```

### Testing
```bash
# Test API with OpenAI SDK
bash scripts/send_request.sh

# Manual test with curl
curl http://localhost:7000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-k2think-proxy-xxxxxxxxxx" \
  -d '{"model": "MBZUAI-IFM/K2-Think", "messages": [{"role": "user", "content": "Hello!"}]}'
```

### Token Management
```bash
# Get new tokens (requires accounts.txt with credentials)
python get_tokens.py

# View token statistics
curl http://localhost:7000/admin/tokens/stats

# Force token update
curl http://localhost:7000/admin/tokens/updater/force-update
```

### Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Export environment variables for development
source scripts/export_env.sh
```

## Architecture Overview

### Core Components

**Main Proxy Server (`k2think_proxy.py`)**:
- FastAPI application entry point
- Handles CORS, middleware, and lifecycle management
- Routes requests to appropriate handlers

**API Handler (`src/api_handler.py`)**:
- Processes OpenAI-compatible requests
- Manages chat completions, models list, and streaming
- Integrates with token manager and tool handler

**Token Manager (`src/token_manager.py`)**:
- Manages token pool with round-robin load balancing
- Handles token failure tracking and rotation
- Provides thread-safe token access

**Token Updater (`src/token_updater.py`)**:
- Automatic token refresh using K2 credentials
- Background token validation and updates
- Integrates with `get_tokens.py` script

**Response Processor (`src/response_processor.py`)**:
- Transforms K2Think responses to OpenAI format
- Handles streaming and non-streaming responses
- Manages thinking content display/hiding

**Tool Handler (`src/tool_handler.py`)**:
- Implements OpenAI function calling compatibility
- Converts tool calls between K2 and OpenAI formats
- Handles tool execution and response formatting

**Configuration (`src/config.py`)**:
- Centralized environment variable management
- Configuration validation and defaults
- Runtime configuration access

### Key Features

- **Multi-token rotation**: Automatic load balancing across multiple tokens
- **Self-healing**: Failed tokens are automatically rotated and refreshed
- **OpenAI compatibility**: Drop-in replacement for OpenAI API clients
- **Streaming support**: Real-time response streaming with SSE
- **Function calling**: Full OpenAI tool/function calling support
- **Automated deployment**: Smart scripts handle installation and setup

## Configuration

### Required Environment Variables
```bash
VALID_API_KEY=sk-k2think-xxxxx        # API key for client authentication
TOKENS_FILE=data/tokens.txt           # File containing K2Think tokens (one per line)
```

### Optional Configuration
```bash
# Server settings
HOST=0.0.0.0                          # Listen address
PORT=7001                             # Server port

# Token auto-update
ENABLE_TOKEN_AUTO_UPDATE=true         # Enable automatic token refresh
TOKEN_UPDATE_INTERVAL=3600           # Update interval in seconds
ACCOUNTS_FILE=data/accounts.txt      # K2 credentials file

# Model selection
# MBZUAI-IFM/K2-Think (shows thinking) / MBZUAI-IFM/K2Think-nothink (hides thinking)
```

### File Structure
```
data/
├── tokens.txt      # K2Think JWT tokens (one per line)
├── accounts.txt    # K2 account credentials (JSON format)
└── stats.json      # Token usage statistics

src/                # Core application modules
scripts/            # Deployment and management scripts
venv/               # Python virtual environment
.env                # Environment configuration
server.log          # Application logs
.server.pid         # Server process ID
```

## Development Notes

### Token Management
- Tokens are stored in `data/tokens.txt` (one per line)
- Failed tokens are automatically marked and rotated
- Token statistics are tracked in `data/stats.json`
- Auto-update requires valid credentials in `accounts.txt`

### API Endpoints
- `/v1/chat/completions` - Main chat endpoint (OpenAI compatible)
- `/v1/models` - Available models list
- `/health` - Health check endpoint
- `/admin/tokens/*` - Token management endpoints (require auth)

### Error Handling
- Authentication errors return 401 status
- Rate limiting returns 429 status
- Upstream errors are properly logged and forwarded
- Failed tokens trigger automatic rotation

### Performance Considerations
- Async/await architecture for high concurrency
- Connection pooling with configurable limits
- Streaming responses with configurable chunk sizes
- Token pool management reduces request latency
