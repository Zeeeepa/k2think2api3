# 🚀 Complete Deployment Script - `deploy_complete.sh`

The ultimate all-in-one deployment script for K2Think API that handles **everything** from clone to production validation.

---

## ✨ What It Does

This single script executes a complete deployment pipeline:

### Phase 1: Clone & Setup 📦
- Clones or updates the repository
- Checks out the specified branch
- Runs interactive credential setup
- Installs all dependencies in virtual environment

### Phase 2: Deploy Server 🎯
- Starts the K2Think API server
- Waits for server initialization
- Verifies health endpoint responds

### Phase 3: Validate Deployment 🧪
- Makes actual OpenAI API call to test endpoint
- Validates response format and content
- Prints formatted response with token usage
- Confirms server is working correctly

### Phase 4: Continuous Operation 📊
- Displays server information and usage examples
- Shows management commands
- Optionally monitors logs in real-time
- Server continues running after script exits

---

## 🎯 Quick Start

### One-Command Deployment

```bash
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/deploy_complete.sh -o deploy_complete.sh
bash deploy_complete.sh
```

### Deploy Specific Branch

```bash
bash deploy_complete.sh your-branch-name
```

### Custom Port

```bash
PORT=8080 bash deploy_complete.sh
```

---

## 📋 Requirements

- **Git** - For cloning repository
- **Python 3.7+** - For running the server
- **curl** - For validation tests
- **K2Think Account** - Required credentials (script will prompt)

---

## 🔥 Features

### Beautiful Colored Output
- ✅ **Green** for success messages
- ⚠️ **Yellow** for warnings
- ❌ **Red** for errors
- ℹ️ **Blue** for information
- 🎨 **Cyan** for headers

### Smart Error Handling
- Validates each phase before continuing
- Provides helpful error messages
- Suggests troubleshooting steps
- Graceful failure with clear diagnostics

### Comprehensive Validation
```python
# Real OpenAI API call validation:
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_KEY",
    base_url="http://localhost:7000/v1"
)

response = client.chat.completions.create(
    model="k2-think",
    messages=[{"role": "user", "content": "What is your model name?"}]
)
```

### Production-Ready Output
```
============================================================================
📥 RESPONSE RECEIVED
============================================================================

🤖 Model: MBZUAI-IFM/K2-Think
🆔 ID: chatcmpl-1760012356
📅 Created: 1760012356
🎯 Finish Reason: stop

💬 Response Content:
┌──────────────────────────────────────────────────────────────────────────┐
│ I am K2-Think, a model developed by Mohamed bin Zayed University of     │
│ Artificial Intelligence (MBZUAI).                                        │
└──────────────────────────────────────────────────────────────────────────┘

📊 Token Usage:
   • Prompt tokens: 23
   • Completion tokens: 28
   • Total tokens: 51

============================================================================
✅ VALIDATION SUCCESSFUL!
============================================================================
```

---

## 📝 Script Phases Explained

### Phase 1: Clone & Setup
```bash
▶ Cloning repository...
▶ Checking out branch: main
▶ Running setup...
✅ Setup complete!
```

**What happens:**
1. Clones repository or updates existing
2. Checks out specified branch
3. Prompts for K2Think credentials (if needed)
4. Creates virtual environment
5. Installs all dependencies
6. Creates configuration files

### Phase 2: Deploy Server
```bash
▶ Starting K2Think API server on port 7000...
▶ Waiting for server to initialize...
✅ Server is ready!
```

**What happens:**
1. Stops any existing server
2. Activates virtual environment
3. Starts server in background
4. Waits for health endpoint
5. Verifies server is responding

### Phase 3: Validate Deployment
```bash
🧪 K2Think API - OpenAI Client Validation Test
📡 Testing connection to: http://localhost:7000/v1
🔑 Using API key: sk-k2think-proxy-...
📤 Sending test message...
📥 RESPONSE RECEIVED
✅ VALIDATION SUCCESSFUL!
```

**What happens:**
1. Loads API key from `.env`
2. Creates OpenAI client instance
3. Sends actual test message
4. Validates response format
5. Prints formatted response
6. Confirms token usage

### Phase 4: Continuous Operation
```bash
🌐 Server Information:
   • API URL: http://localhost:7000/v1
   • Health Check: http://localhost:7000/health

📝 Usage Examples:
   [Python and cURL examples shown]

🛠️  Management Commands:
   • View logs: tail -f server.log
   • Stop server: kill $(cat .server.pid)

📊 Live Server Logs:
   [Real-time log streaming]
```

**What happens:**
1. Displays server endpoints
2. Shows usage examples
3. Lists management commands
4. Optionally follows logs
5. Server continues running

---

## 🛠️ Management Commands

### View Server Logs
```bash
tail -f k2think2api3/server.log
```

### Stop Server
```bash
kill $(cat k2think2api3/.server.pid)
```

### Restart Server
```bash
cd k2think2api3
bash deploy.sh
```

### Health Check
```bash
curl http://localhost:7000/health
```

### Test API Call
```bash
curl -X POST http://localhost:7000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "k2-think",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## 🔧 Configuration Options

### Environment Variables

**PORT** - Server port (default: 7000)
```bash
PORT=8080 bash deploy_complete.sh
```

**K2_EMAIL** - K2Think account email
```bash
K2_EMAIL="your@email.com" bash deploy_complete.sh
```

**K2_PASSWORD** - K2Think account password
```bash
K2_PASSWORD="yourpassword" bash deploy_complete.sh
```

**Combined:**
```bash
PORT=8080 K2_EMAIL="your@email.com" K2_PASSWORD="pass" bash deploy_complete.sh
```

---

## 📊 Expected Output

### Successful Deployment
```
🚀 K2Think API - Complete Deployment System

Configuration:
   • Repository: https://github.com/Zeeeepa/k2think2api3.git
   • Branch: main
   • Port: 7000
   • Working Directory: /path/to/k2think2api3

============================================================================
PHASE 1: Clone & Setup
============================================================================

▶ Cloning repository...
▶ Running setup...
✅ Setup complete!

============================================================================
PHASE 2: Deploy Server
============================================================================

▶ Starting K2Think API server on port 7000...
▶ Waiting for server to initialize...
✅ Server is ready!

============================================================================
PHASE 3: Validate Deployment
============================================================================

🧪 K2Think API - OpenAI Client Validation Test

📡 Testing connection to: http://localhost:7000/v1
📤 Sending test message: 'What is your model name?'
⏳ Waiting for response...

📥 RESPONSE RECEIVED
[Formatted response shown]

✅ VALIDATION SUCCESSFUL!

============================================================================
PHASE 4: Server Ready - Continuous Operation
============================================================================

✅ Deployment complete! Server is now running.

[Server info, usage examples, and live logs follow]
```

---

## ❌ Troubleshooting

### Server Won't Start
```
❌ Server failed to start within 30 seconds
💡 Troubleshooting:
   1. Check if server is running: curl http://localhost:7000/health
   2. Verify accounts.txt has valid K2Think credentials
   3. Check server logs: tail -f server.log
```

**Solution:**
1. Verify K2Think credentials in `accounts.txt`
2. Check logs: `tail -f k2think2api3/server.log`
3. Ensure port 7000 is not already in use

### Validation Failed
```
❌ VALIDATION FAILED
🔴 Error: Connection refused

💡 Troubleshooting:
   1. Check if server is running
   2. Verify accounts.txt credentials
   3. Check server logs
```

**Solution:**
1. Ensure credentials are valid
2. Wait a bit longer for server initialization
3. Check if tokens are available

### Port Already in Use
```
❌ Port 7000 is already in use
```

**Solution:**
```bash
PORT=8080 bash deploy_complete.sh
```

---

## 🆚 Comparison: CSDS vs Deploy Complete

| Feature | csds.sh | deploy_complete.sh |
|---------|---------|-------------------|
| Clone repo | ✅ | ✅ |
| Setup env | ✅ | ✅ |
| Deploy server | ✅ | ✅ |
| Basic test | ✅ | ✅ |
| **OpenAI validation** | ❌ | ✅ |
| **Formatted response** | ❌ | ✅ |
| **Token usage** | ❌ | ✅ |
| **Live monitoring** | ❌ | ✅ |
| **Usage examples** | ❌ | ✅ |
| **Colored output** | Basic | ✅ Full |
| **Error diagnostics** | Basic | ✅ Detailed |

---

## 🎯 Use Cases

### Development
```bash
# Quick dev environment setup
bash deploy_complete.sh dev-branch
```

### Production
```bash
# Production deployment with validation
bash deploy_complete.sh main
```

### Testing
```bash
# Test specific feature branch
bash deploy_complete.sh feature/new-endpoint
```

### CI/CD Integration
```bash
#!/bin/bash
# In your CI/CD pipeline
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/deploy_complete.sh | bash -s main
```

---

## 🔒 Security Notes

- ✅ Credentials stored locally only
- ✅ Virtual environment isolation
- ✅ No credentials logged
- ✅ Secure API key handling
- ✅ Validation before going live

---

## 📚 Related Documentation

- [README.md](README.md) - Main documentation
- [CREDENTIAL_SETUP.md](CREDENTIAL_SETUP.md) - Credential management
- [setup.sh](setup.sh) - Setup script details
- [deploy.sh](deploy.sh) - Deployment script details

---

## 🎉 Summary

`deploy_complete.sh` is the **ultimate deployment solution** that:

✅ Handles entire deployment pipeline automatically  
✅ Validates with actual OpenAI API calls  
✅ Provides beautiful formatted output  
✅ Monitors server in real-time  
✅ Continues running after validation  
✅ Production-ready with comprehensive error handling  

**One command. Complete deployment. Production validation.**

```bash
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/deploy_complete.sh -o deploy_complete.sh
bash deploy_complete.sh
```

🚀 **That's it!** Your K2Think API is deployed, validated, and ready to serve OpenAI-compatible requests!

