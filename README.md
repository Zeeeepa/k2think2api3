# K2Think API Proxy

🚀 **OpenAI-compatible API proxy for MBZUAI K2-Think model** - Built with FastAPI

---

## ⚡ **INSTANT DEPLOYMENT - ONE COMMAND!**

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
├── scripts/           # All deployment scripts (NEW!)
│   ├── all.sh        # Smart all-in-one deployment (NEW!)
│   ├── setup.sh      # Setup script
│   ├── deploy.sh     # Deployment script
│   ├── install.sh    # Interactive installer
│   └── send_request.sh  # Test request script
├── k2think_proxy.py  # Main proxy server
├── get_tokens.py     # Token management
├── csds.sh           # Compatibility wrapper
└── README.md         # This file
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

