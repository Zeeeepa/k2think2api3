# K2Think API Proxy

🚀 **OpenAI-compatible API proxy for MBZUAI K2-Think model** - Built with FastAPI

---

## ⚡ **INSTANT DEPLOYMENT - ONE COMMAND!**

**For initial setup only:**

```bash
export K2_EMAIL="your@email.com"
export  K2_PASSWORD="yourpassword" 
git clone https://github.com/Zeeeepa/k2think2api3
cd k2think2api3
bash scripts/setup.sh
```

```bash
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/scripts/all.sh | bash
```

**That's it!** The smart script will:
- ✅ Auto-detect if you're in the project directory
- ✅ Search common locations for existing installation
- ✅ Clone repository if not found
- ✅ Prompt for your K2 credentials
- ✅ Install all dependencies
- ✅ Start the server on port 7000
- ✅ **Print actual working examples with your localhost URL**
- ✅ **Show live API response**
- ✅ Display your API key and usage instructions

**No manual steps. Everything automated. Real examples ready to copy!** 🎉

---

## 🎯 Quick Start Options

### Option 1: Smart All-in-One Script (Recommended)
```bash
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/scripts/all.sh | bash
```

### Option 2: With Pre-Set Credentials
```bash
export K2_EMAIL="your@email.com" K2_PASSWORD="yourpassword" && curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/scripts/all.sh | bash
```

### Option 3: If Already Cloned
```bash
cd k2think2api3
bash scripts/all.sh
```

---

## 🌟 Core Features

- 🧠 **K2-Think Model**: MBZUAI's advanced reasoning model
- 🔄 **OpenAI Compatible**: Drop-in replacement for OpenAI API
- ⚡ **Streaming Support**: Real-time chat responses
- 🛠️ **Function Calling**: Full OpenAI tool/function calling support
- 📊 **File Upload**: Images and document support
- 🔐 **Token Management**: Automatic rotation and validation
- 🎯 **Smart Scripts**: Auto-detect, auto-configure, auto-deploy

---

## 📚 Documentation

- 📖 [Complete Installation Guide](./INSTALL.md)
- 🚀 [Quick Start Guide](./QUICKSTART.md)
- 🔧 [URL Format Guide](./DEPLOYMENT_URL_GUIDE.md)

---

## 🐍 What You Get After Running all.sh

The script will print ready-to-use examples like:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:7000/v1",
    api_key="sk-k2think-..." # Your actual API key
)

response = client.chat.completions.create(
    model="MBZUAI-IFM/K2-Think",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

**Plus live curl examples with your actual localhost URL and API key!**

---

## 📁 Project Structure

```
k2think2api3/
├── 📂 scripts/              # All deployment scripts
│   ├── all.sh              # 🎯 Smart all-in-one deployment
│   ├── setup.sh            # 🔧 Environment setup
│   ├── deploy.sh           # 🚀 Server deployment
│   ├── install.sh          # 📦 Interactive installer
│   ├── send_request.sh     # 🧪 API testing
│   └── export_env.sh       # 🔐 Environment variables
├── k2think_proxy.py        # Main proxy server
├── get_tokens.py           # Token management
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker support
└── README.md               # This file
```

---

## 🛠️ Deployment Scripts Guide

### 📋 scripts/all.sh - Complete Deployment (Recommended)

**The master script that does everything:**

```bash
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/scripts/all.sh | bash
```

**What it does:**
1. ✅ Auto-detects if you're in project directory
2. ✅ Searches common locations (~/k2think2api3, ~/projects/k2think2api3)
3. ✅ Clones repository if not found
4. ✅ Prompts for K2 credentials (if needed)
5. ✅ Runs setup (venv, dependencies, .env)
6. ✅ Starts server on port 7000
7. ✅ Tests with Python SDK
8. ✅ Shows live API response
9. ✅ Prints working examples with actual URLs
10. ✅ Exports environment variables

**With credentials:**
```bash
export K2_EMAIL="your@email.com" K2_PASSWORD="yourpass" && \
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/scripts/all.sh | bash
```

---

### 🔧 scripts/setup.sh - Environment Setup

**For initial setup only:**

```bash
git clone https://github.com/Zeeeepa/k2think2api3
cd k2think2api3
bash scripts/setup.sh
```

**What it does:**
- Creates Python virtual environment
- Installs dependencies from requirements.txt
- Creates accounts.txt (if credentials provided)
- Generates .env configuration
- Installs OpenAI package for testing

**Required environment variables:**
- `K2_EMAIL` - Your K2Think account email
- `K2_PASSWORD` - Your K2Think password

---

### 🚀 scripts/deploy.sh - Server Deployment

**For starting/restarting the server:**

```bash
cd k2think2api3
bash scripts/deploy.sh
```

**What it does:**
- Activates virtual environment
- Starts server in background (port 7000)
- Creates PID file (.server.pid)
- Waits for initialization
- Shows server information
- Displays management commands

**Features:**
- Detects if server already running
- Provides kill command if needed
- Shows health endpoint
- Logs to server.log

---

### 🧪 scripts/send_request.sh - API Testing

**For testing the deployed API:**

```bash
cd k2think2api3
bash scripts/send_request.sh
```

**What it does:**
- Checks if server is running
- Activates virtual environment
- Uses OpenAI Python SDK
- Sends test request
- Shows formatted response
- Displays token usage

**Example output:**
```
======================================================================
📥 RESPONSE RECEIVED
======================================================================
Model: MBZUAI-IFM/K2-Think
ID: chatcmpl-1760096305

Content:
----------------------------------------------------------------------
Hello! I'm K2-Think.
----------------------------------------------------------------------

Token Usage:
  • Prompt tokens: 438
  • Completion tokens: 132
  • Total tokens: 570
======================================================================
```

---

### 🔐 scripts/export_env.sh - Environment Variables

**For exporting environment variables:**

```bash
source <(curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/scripts/export_env.sh)
```

**What it does:**
- Reads API key from .env
- Exports OPENAI_API_KEY
- Exports OPENAI_BASE_URL
- Shows usage example

**After sourcing, you can use:**
```python
from openai import OpenAI
client = OpenAI()  # Uses environment variables
```

---

### 📦 scripts/install.sh - Interactive Installer

**For guided installation:**

```bash
cd k2think2api3
bash scripts/install.sh
```

**What it does:**
- Interactive prompts for configuration
- Checks system requirements
- Installs dependencies
- Sets up accounts
- Configures environment
- Tests installation

---

## 🔄 Common Workflows

### First Time Setup
```bash
# One command does everything
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/scripts/all.sh | bash
```

### Manual Step-by-Step
```bash
# 1. Clone repository
git clone https://github.com/Zeeeepa/k2think2api3.git
cd k2think2api3

# 2. Setup environment
bash scripts/setup.sh

# 3. Start server
bash scripts/deploy.sh

# 4. Test API
bash scripts/send_request.sh
```

### Restart Server
```bash
cd k2think2api3
kill $(cat .server.pid)
bash scripts/deploy.sh
```

### Check Status
```bash
cd k2think2api3
curl http://localhost:7000/health
tail -f server.log
```

---

## 🔥 Advanced Features

### 🔄 Intelligent Token Management
- Multi-token rotation with automatic failover
- Smart failure detection
- Auto-refresh on consecutive failures
- Zero-downtime updates

### 🛡️ Self-Healing System
- Automatic token validation
- Continuous health monitoring
- Intelligent retry mechanisms

### 🚀 Performance
- Async/await architecture
- High concurrency support
- Streaming responses
- Efficient token pooling

---

## 🆘 Troubleshooting

The all.sh script provides complete management commands:

```bash
# View logs
tail -f ~/k2think2api3/server.log

# Stop server
kill $(cat ~/k2think2api3/.server.pid)

# Restart
cd ~/k2think2api3 && bash scripts/deploy.sh

# Health check
curl http://localhost:7000/health
```

---

## ⭐ Star History

If this helps you, please star the repo! ⭐

---

## 原版中文文档 / Original Chinese Documentation

<details>
<summary>点击展开中文文档 / Click to expand Chinese documentation</summary>

基于 FastAPI 构建的 K2Think AI 模型代理服务，提供 OpenAI 兼容的 API 接口。

### 核心功能特性

- 🧠 **MBZUAI K2-Think 模型**: 支持 MBZUAI 开发的 K2-Think 推理模型
- 🔄 **OpenAI 兼容**: 完全兼容 OpenAI API 格式，无缝对接现有应用
- ⚡ **流式响应**: 支持实时流式聊天响应
- 🛠️ **工具调用**: 支持 OpenAI Function Calling
- 📊 **文件上传**: 支持文件、图像上传

### 一键部署

```bash
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/scripts/all.sh | bash
```

</details>
