# K2Think API Proxy

🚀 **OpenAI-compatible API proxy for MBZUAI K2-Think model** - Built with FastAPI

---

## ⚡ **INSTANT DEPLOYMENT - ONE COMMAND!**

```bash
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/csds.sh | bash
```

**That's it!** The script will automatically:
- ✅ Clone the repository
- ✅ Prompt for your K2 credentials
- ✅ Install all dependencies
- ✅ Start the server on port 7000
- ✅ Run a test request
- ✅ Display your API key

**No manual steps. No configuration files. Just works.** 🎉

---

## 🌟 Core Features

- 🧠 **K2-Think Model**: MBZUAI's advanced reasoning model
- 🔄 **OpenAI Compatible**: Drop-in replacement for OpenAI API
- ⚡ **Streaming Support**: Real-time chat responses with thinking output control
- 🛠️ **Function Calling**: Full OpenAI tool/function calling support
- 📊 **File Upload**: Images and document support
- 🔐 **API Key Management**: Secure token rotation and validation

---

## 🎯 Quick Start Options

### Option 1: One-Line Deployment (Recommended)
```bash
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/csds.sh | bash
```

### Option 2: With Pre-Set Credentials
```bash
export K2_EMAIL="your@email.com" K2_PASSWORD="yourpassword" && curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/csds.sh | bash
```

### Option 3: Foolproof Installer (Interactive)
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/install.sh)
```

---

## 📚 Documentation

- 📖 [Complete Installation Guide](./INSTALL.md)
- 🚀 [Quick Start Guide](./QUICKSTART.md)
- 🔧 [URL Format Guide](./DEPLOYMENT_URL_GUIDE.md)

---

## 🐍 Usage Example

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:7000/v1",
    api_key="your-api-key"  # Get from .env file after deployment
)

response = client.chat.completions.create(
    model="MBZUAI-IFM/K2-Think",
    messages=[{"role": "user", "content": "What is quantum computing?"}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

---

## 🔥 Advanced Features

### 🔄 Intelligent Token Management
- **Multi-token rotation** with automatic failover
- **Smart failure detection** - auto-disable after 3 failures
- **Auto-refresh** on consecutive failures
- **Zero-downtime updates** - atomic token pool replacement
- **Load balancing** across hundreds of tokens

### 🛡️ Self-Healing System
- Automatic token validation
- Continuous health monitoring
- Intelligent retry mechanisms
- Real-time failure statistics

### 🌐 Network Adaptability
- HTTP/HTTPS proxy support
- Configurable timeouts
- Rate limiting
- Request logging

### 🚀 Performance
- Async/await architecture
- High concurrency support
- Streaming responses
- Efficient token pooling

---

## 🐳 Docker Deployment

```bash
docker build -t k2think-api .
docker run -d -p 7000:7000 \
  -e K2_EMAIL="your@email.com" \
  -e K2_PASSWORD="yourpassword" \
  k2think-api
```

---

## 📊 Management API

Once deployed, access management endpoints:

```bash
# Check token pool status
curl http://localhost:7000/admin/token-status

# Reset token pool
curl -X POST http://localhost:7000/admin/reset-tokens

# Health check
curl http://localhost:7000/health
```

---

## 🆘 Troubleshooting

### Server won't start?
```bash
# Check logs
tail -f ~/k2think2api3/server.log

# Verify port is available
lsof -i :7000

# Restart server
cd ~/k2think2api3 && bash deploy.sh
```

### Can't connect?
- Ensure server is running: `curl http://localhost:7000/health`
- Check firewall settings
- Verify API key is correct

---

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

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
- ⚡ **流式响应**: 支持实时流式聊天响应，支持控制thinking输出
- 🛠️ **工具调用**: 支持 OpenAI Function Calling，可集成外部工具和API
- 📊 **文件上传**: 支持文件、图像上传

### 智能Token管理系统

#### 🔄 Token轮询与负载均衡
- 多token轮流使用，自动故障转移
- 支持大规模token池（支持数百个token）

#### 🛡️ 智能失效检测与自愈
- **自动失效检测**: 三次失败后自动禁用失效token
- **连续失效自动刷新**: 当连续两个token失效时，自动触发强制刷新（仅在token池数量>2时生效）
- **智能重试机制**: 失效token会被跳过，确保服务连续性

#### 📈 Token池管理
- 完整的管理API查看状态、重置token等
- 实时监控token使用情况和失效统计
- 支持手动重置和重新加载

#### 🔄 Token自动更新
- 定期从账户文件自动生成新的token池
- **原子性更新**: 零停机时间，更新过程中服务保持可用
- **智能触发**: 支持定时更新和连续失效触发的强制更新

#### 🌐 网络适应性
- 支持HTTP/HTTPS代理配置，适应不同网络环境
- 🚀 **高性能**: 异步处理架构，支持高并发请求
- 🐳 **容器化**: 支持 Docker 部署

### 一键部署 (中文版)

```bash
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/csds.sh | bash
```

</details>

