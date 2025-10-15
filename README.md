# K2Think API Proxy - Complete Documentation

**🚀 OpenAI-compatible API proxy for MBZUAI K2-Think model | Built with FastAPI**

---

## 🔓 Open Proxy Mode (NEW!)

The proxy now operates in **open mode** by default - the most flexible way to use K2-Think!

### What This Means

- ✅ **Any API Key Accepted**: Use `sk-any`, `test`, `random-key`, or even empty strings
- ✅ **Any Model Name Accepted**: `gpt-4`, `gpt-5`, `claude-3`, `my-model` - all route to K2-Think
- ✅ **Drop-in OpenAI Replacement**: Perfect replacement for OpenAI API endpoints
- ✅ **Zero Configuration**: No need to manage API keys or model names
- ✅ **Centralized Auth**: Server handles all K2Think authentication

### Quick Example

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-any",  # ✅ Any key works!
    base_url="http://localhost:7000/v1"
)

result = client.chat.completions.create(
    model="gpt-5",  # ✅ Any model works!
    messages=[{"role": "user", "content": "Write a haiku about code."}]
)

print(result.choices[0].message.content)
```

**Output:**
```
Code lines softly hum,  
Syntax weaves logic's soft song—  
Machines come alive.
```

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Open Proxy Mode Details](#open-proxy-mode-details)
3. [Installation Methods](#installation-methods)
4. [Core Features](#core-features)
5. [Project Structure](#project-structure)
6. [Configuration](#configuration)
7. [Using the API](#using-the-api)
8. [Server Management](#server-management)
9. [API Reference](#api-reference)
10. [Troubleshooting](#troubleshooting)
11. [Advanced Features](#advanced-features)
12. [Changelog](#changelog)
13. [中文文档](#中文文档)

---

## Quick Start

### ⚡ One-Command Installation (Recommended)

The fastest way to get started - everything is automated:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/install.sh)
```

**What happens automatically:**
1. ✅ Asks for your K2 credentials
2. ✅ Clones the repository
3. ✅ Installs dependencies
4. ✅ Starts the server on port 7000
5. ✅ Runs a test request
6. ✅ Displays usage instructions

### With Pre-Set Credentials (No Prompts)

```bash
export K2_EMAIL="your@email.com"
export K2_PASSWORD="yourpassword"
bash <(curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/install.sh)
```

---

## Open Proxy Mode Details

### How It Works

1. **Client Request**: Client sends request with any API key + any model name
2. **Key Bypass**: Server accepts the key without validation
3. **Model Mapping**: Server maps client's model name → `MBZUAI-IFM/K2-Think`
4. **Token Injection**: Server uses its own K2Think JWT token
5. **Upstream Request**: Server forwards to K2Think backend
6. **Response**: Server returns K2Think response to client

### Token Management

The server automatically manages K2Think JWT tokens:

- **Stored in**: `data/tokens.txt`
- **Credentials from**: `data/accounts.txt`
- **Auto-refresh**: When tokens expire (401 errors)
- **Zero-downtime**: Token rotation without service interruption

### Testing Different Configurations

```python
# Test 1: Different API keys
for api_key in ["sk-test-1", "random-key", "any-string", ""]:
    client = OpenAI(api_key=api_key or "empty", base_url="http://localhost:7000/v1")
    result = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hi"}]
    )
    print(f"✅ API key '{api_key or '(empty)'}' accepted")

# Test 2: Different model names
for model in ["gpt-4", "gpt-5", "claude-3", "my-model"]:
    client = OpenAI(api_key="test", base_url="http://localhost:7000/v1")
    result = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Hi"}]
    )
    print(f"✅ Model '{model}' accepted → routed to K2-Think")
```

### Benefits

**For Users:**
- 🎉 **Zero Configuration** - No need to manage API keys
- 🔄 **Model Flexibility** - Use any model name they prefer
- 🚀 **Instant Setup** - One command to get started
- 🔒 **Security** - Server handles all authentication

**For Developers:**
- 📦 **Easy Integration** - Works with existing OpenAI clients
- 🔧 **No Code Changes** - Drop-in replacement for OpenAI API
- 🧪 **Testing Friendly** - Use any mock keys for testing
- 📊 **Centralized Auth** - All tokens managed server-side

### Security Considerations

⚠️ **Important**: Since API key validation is bypassed:

- ✅ Deploy in trusted network environment
- ✅ Configure network-level security (firewall, VPN)
- ✅ Restrict access to authorized users/networks
- ✅ Secure the server's `data/tokens.txt` and `data/accounts.txt`
- ✅ Use environment variables for sensitive data

---

## Installation Methods

### Method 1: Bash Process Substitution (Recommended)

**Most foolproof method - prevents URL mistakes:**

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/install.sh)
```

**Why this is better:**
- 🔒 Bash process substitution `<()` prevents file system errors
- 🎯 Single command = less room for mistakes
- 🚀 Cleaner, more professional
- ✅ Industry-standard pattern (used by Homebrew, rustup, nvm)

### Method 2: Download and Inspect First

If you want to review the script before running:

```bash
# Download
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/install.sh -o install.sh

# Review (optional)
cat install.sh

# Run
bash install.sh
```

### Method 3: Manual Step-by-Step

For those who prefer manual control:

```bash
# 1. Clone repository
git clone https://github.com/Zeeeepa/k2think2api3.git
cd k2think2api3

# 2. Set credentials
export K2_EMAIL="your@email.com"
export K2_PASSWORD="yourpassword"

# 3. Setup environment
bash scripts/setup.sh

# 4. Start server
bash scripts/start.sh

# 5. Test API
bash scripts/send_request.sh
```

---

## Core Features

### 🧠 K2-Think Model Integration
- Full support for MBZUAI's K2-Think reasoning model
- Advanced AI capabilities with reasoning chains
- Optimized for complex problem-solving

### 🔄 OpenAI Compatibility
- **Drop-in replacement** for OpenAI API
- Compatible with all OpenAI SDKs and libraries
- Same API format and behavior
- Seamless migration from OpenAI

### ⚡ Streaming Support
- Real-time streaming chat responses
- Efficient token-by-token output
- Low latency for better user experience

### 🛠️ Function Calling
- Full OpenAI Function Calling support
- Tool use capabilities
- Structured data extraction
- Agent-ready architecture

### 📊 File Upload Support
- Image upload and analysis
- Document processing
- Multi-modal capabilities

### 🔐 Intelligent Token Management
- **Multi-token rotation** with automatic failover
- Smart failure detection
- Auto-refresh on consecutive failures
- Zero-downtime token updates
- Continuous health monitoring

---

## Project Structure

```
k2think2api3/
├── 📂 src/                  # Source code
│   ├── api_handler.py       # API request handling (Open Proxy Mode!)
│   ├── config.py            # Configuration management
│   ├── token_manager.py     # Token rotation and management
│   └── token_updater.py     # Automatic token refresh
├── 📂 data/                 # Runtime data
│   ├── accounts.txt         # K2 credentials (JSON format)
│   └── tokens.txt           # Auto-refreshing K2Think JWT tokens
├── 📂 scripts/              # Deployment scripts
│   ├── all.sh               # 🎯 Complete one-command setup
│   ├── setup.sh             # Environment setup
│   ├── start.sh             # Server startup
│   └── send_request.sh      # API testing
├── k2think_proxy.py         # Main server entry point
├── get_tokens.py            # Token acquisition utility
├── requirements.txt         # Python dependencies
├── .env                     # Configuration (auto-generated)
├── server.log               # Server logs
└── README.md                # This file
```

---

## Configuration

### Environment Variables (.env)

The `.env` file is auto-generated during setup. Key settings:

```bash
# Server Configuration
PORT=7000
HOST=0.0.0.0

# Token Auto-Update (requires accounts.txt)
ENABLE_TOKEN_AUTO_UPDATE=true
TOKEN_UPDATE_INTERVAL=3600  # 1 hour in seconds

# Debug Mode
DEBUG_LOGGING=false
```

### Accounts Configuration (data/accounts.txt)

JSON format for K2 credentials:

```json
{"email": "your@email.com", "k2_password": "yourpassword"}
```

**Security Notes:**
- Never commit this file to version control
- Keep file permissions restrictive (chmod 600)
- Use environment variables when possible

---

## Using the API

### Python (OpenAI SDK)

```python
from openai import OpenAI

# Initialize client - any API key works!
client = OpenAI(
    api_key="sk-any",  # Can be anything
    base_url="http://localhost:7000/v1"
)

# Simple request - any model name works!
response = client.chat.completions.create(
    model="gpt-4",  # Will route to K2-Think
    messages=[
        {"role": "user", "content": "Explain quantum computing"}
    ]
)

print(response.choices[0].message.content)

# Streaming request
stream = client.chat.completions.create(
    model="gpt-5",  # Will route to K2-Think
    messages=[
        {"role": "user", "content": "Write a story"}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)

# Function calling
response = client.chat.completions.create(
    model="claude-3",  # Will route to K2-Think
    messages=[{"role": "user", "content": "What's the weather?"}],
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather information",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                }
            }
        }
    }]
)
```

### cURL

```bash
# Simple request
curl http://localhost:7000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-any" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Streaming request
curl http://localhost:7000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key" \
  -d '{
    "model": "gpt-5",
    "messages": [{"role": "user", "content": "Tell me a joke"}],
    "stream": true
  }'
```

### JavaScript/TypeScript

```javascript
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: 'sk-any',  // Any key works
  baseURL: 'http://localhost:7000/v1'
});

async function main() {
  const response = await client.chat.completions.create({
    model: 'gpt-4',  // Will route to K2-Think
    messages: [{ role: 'user', content: 'Hello!' }]
  });
  
  console.log(response.choices[0].message.content);
}

main();
```

---

## Server Management

### Start Server

```bash
cd k2think2api3
bash scripts/start.sh
```

### Stop Server

```bash
# Using PID file
kill $(cat .server.pid)

# Or find and kill
pkill -f k2think_proxy
```

### Restart Server

```bash
cd k2think2api3
kill $(cat .server.pid)
bash scripts/start.sh
```

### View Logs

```bash
# Real-time logs
tail -f server.log

# Recent logs
tail -n 100 server.log

# Search logs
grep "error" server.log
```

### Check Server Status

```bash
# Health check
curl http://localhost:7000/health

# Token statistics
curl http://localhost:7000/admin/tokens/stats

# Server process
ps aux | grep k2think_proxy
```

---

## API Reference

### Endpoints

#### POST /v1/chat/completions

Create a chat completion (OpenAI compatible).

**Request:**
```json
{
  "model": "gpt-4",  // Any model name
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false,
  "temperature": 0.7,
  "max_tokens": null
}
```

**Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "MBZUAI-IFM/K2-Think",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 9,
    "completion_tokens": 12,
    "total_tokens": 21
  }
}
```

#### GET /v1/models

List available models.

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "MBZUAI-IFM/K2-Think",
      "object": "model",
      "created": 1686935002,
      "owned_by": "MBZUAI"
    }
  ]
}
```

#### GET /health

Server health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

#### GET /admin/tokens/stats

Token pool statistics.

**Response:**
```json
{
  "total_tokens": 5,
  "available_tokens": 4,
  "failed_tokens": 1,
  "token_details": [...]
}
```

---

## Troubleshooting

### Server Won't Start

**Check if port 7000 is in use:**
```bash
lsof -i :7000
```

**View server logs:**
```bash
cat server.log
```

**Verify Python version:**
```bash
python3 --version  # Should be 3.8+
```

### "Module not found: openai"

**Use virtual environment:**
```bash
source venv/bin/activate
python your_script.py
```

**Or use venv Python directly:**
```bash
./venv/bin/python your_script.py
```

### Token Auto-Update Not Working

1. **Verify accounts.txt exists:**
   ```bash
   cat data/accounts.txt
   ```

2. **Check .env configuration:**
   ```bash
   grep ENABLE_TOKEN_AUTO_UPDATE .env
   ```

3. **View updater logs:**
   ```bash
   grep "token" server.log
   ```

### Connection Refused

**Ensure server is running:**
```bash
ps aux | grep k2think_proxy
```

**Test health endpoint:**
```bash
curl http://localhost:7000/health
```

---

## Advanced Features

### Custom Port Configuration

Edit `.env`:
```bash
PORT=8000  # Change from default 7000
```

Restart server:
```bash
kill $(cat .server.pid)
bash scripts/start.sh
```

### Production Deployment

1. **Use reverse proxy** (nginx, Apache)
2. **Set up SSL/TLS** for secure connections
3. **Configure rate limiting**
4. **Set up monitoring** and alerts
5. **Use process manager** (systemd, PM2)
6. **Implement log rotation**
7. **Set up automated backups**

### Docker Deployment

```bash
# Build image
docker build -t k2think-api .

# Run container
docker run -d \
  -p 7000:7000 \
  -e K2_EMAIL="your@email.com" \
  -e K2_PASSWORD="yourpassword" \
  --name k2think-api \
  k2think-api
```

---

## Changelog

### Version 2.1.0 - Open Proxy Mode (2025-01-15)

**Major Changes:**

1. **Open Proxy Mode Enabled**
   - ✅ Accept any API key from clients
   - ✅ Accept any model name (auto-route to K2-Think)
   - ✅ Bypass client key validation
   - ✅ Use server-managed K2Think tokens

2. **Code Changes**
   - Modified `src/api_handler.py`:
     - `validate_api_key()` now always returns `True`
     - `get_actual_model_id()` always returns K2-Think model
   - Modified `src/config.py`:
     - Made `VALID_API_KEY` optional
   - Enhanced token management and auto-refresh

3. **Documentation**
   - Added Open Proxy Mode section
   - Updated all examples to show flexibility
   - Added security considerations
   - Consolidated documentation

**Migration Guide:**

No changes needed for existing users! The system is fully backward compatible.

**Benefits:**
- Drop-in replacement for OpenAI API
- Simplified client configuration
- Zero-configuration testing
- Centralized authentication

---

## 中文文档

<details>
<summary>点击展开完整中文文档 / Click to expand full Chinese documentation</summary>

### 基于 FastAPI 构建的 K2Think AI 模型代理服务

提供 OpenAI 兼容的 API 接口，支持本地和 Docker 部署。

### 🔓 开放代理模式（新功能！）

代理服务器现在默认以**开放模式**运行：

- ✅ **接受任何 API 密钥**：可以使用任何密钥（如 `sk-any`、`test` 等）
- ✅ **接受任何模型名称**：所有模型名称都会路由到 K2-Think
- ✅ **OpenAI 完美替代**：可作为 OpenAI API 的直接替代品
- ✅ **零配置**：无需管理 API 密钥或模型名称

### 快速示例

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-any",  # 任何密钥都可以！
    base_url="http://localhost:7000/v1"
)

result = client.chat.completions.create(
    model="gpt-5",  # 任何模型名都可以！
    messages=[{"role": "user", "content": "你好！"}]
)

print(result.choices[0].message.content)
```

### 🚀 一键部署

```bash
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/scripts/all.sh | bash
```

### 快速命令

```bash
# 查看日志
tail -f server.log

# 停止服务器
kill $(cat .server.pid)

# 重启服务器
bash scripts/start.sh

# 测试 API
bash scripts/send_request.sh
```

</details>

---

## Support & Contributing

### Getting Help

- 📖 [GitHub Repository](https://github.com/Zeeeepa/k2think2api3)
- 🐛 [Report Issues](https://github.com/Zeeeepa/k2think2api3/issues)
- 💬 Check server logs: `tail -f server.log`
- 🔍 Verify configuration: `cat .env`

### Pro Tips

1. **Keep credentials secure**: Never commit `accounts.txt` or `.env`
2. **Monitor token usage**: Check `/admin/tokens/stats` regularly
3. **Use environment variables**: Easier than hardcoding
4. **Always use venv**: For consistent dependencies
5. **Logs are your friend**: Check `server.log` when troubleshooting
6. **Health checks**: Monitor `/health` in production

---

## License

This project is provided as-is for educational and development purposes.

---

**Happy coding! 🎉**

---

*Last updated: 2025-01-15*  
*Version: 2.1.0 - Open Proxy Mode*
