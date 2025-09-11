# K2Think API Proxy

基于 FastAPI 构建的 K2Think AI 模型代理服务，提供 OpenAI 兼容的 API 接口。

## 功能特性

- 🧠 **MBZUAI K2-Think 模型**: 支持 MBZUAI 开发的 K2-Think 推理模型
- 🔄 **OpenAI 兼容**: 完全兼容 OpenAI API 格式，无缝对接现有应用
- ⚡ **流式响应**: 支持实时流式聊天响应
- 🛡️ **直连访问**: 直接连接 K2Think API，无需代理配置
- 🚀 **高性能**: 异步处理架构，支持高并发请求
- 🐳 **容器化**: 支持 Docker 部署

## 快速开始

### 本地运行

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置你的 K2Think Token
```

3. **启动服务**
```bash
python k2think_proxy.py
```

服务将在 `http://localhost:8001` 启动。

### Docker 部署

1. **构建镜像**
```bash
docker build -t k2think-api .
```

2. **运行容器**
```bash
docker run -d \
  --name k2think-api \
  -p 8001:8001 \
  -e VALID_API_KEY="your-api-key" \
  -e K2THINK_TOKEN="your-k2think-token" \
  k2think-api
```

3. **使用 docker-compose**
```bash
# 先创建 .env 文件
cp .env.example .env
# 编辑 .env 文件配置

# 启动服务
docker-compose up -d
```

## API 接口

### 聊天补全

**POST** `/v1/chat/completions`

```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-k2think" \
  -d '{
    "model": "MBZUAI-IFM/K2-Think",
    "messages": [
      {"role": "user", "content": "你擅长什么？"}
    ],
    "stream": false
  }'
```

### 模型列表

**GET** `/v1/models`

```bash
curl http://localhost:8001/v1/models \
  -H "Authorization: Bearer sk-k2think"
```

## 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `VALID_API_KEY` | `sk-k2think` | API 访问密钥 |
| `K2THINK_TOKEN` | - | K2Think 服务 JWT Token |
| `OUTPUT_THINKING` | `true` | 是否输出思考过程 |
| `HOST` | `0.0.0.0` | 服务监听地址 |
| `PORT` | `8001` | 服务端口 |

## Python SDK 使用示例

```python
import openai

# 配置客户端
client = openai.OpenAI(
    base_url="http://localhost:8001/v1",
    api_key="sk-k2think"
)

# 发送聊天请求
response = client.chat.completions.create(
    model="MBZUAI-IFM/K2-Think",
    messages=[
        {"role": "user", "content": "解释一下量子计算的基本原理"}
    ],
    stream=False
)

print(response.choices[0].message.content)

# 流式聊天
stream = client.chat.completions.create(
    model="MBZUAI-IFM/K2-Think",
    messages=[
        {"role": "user", "content": "写一首关于人工智能的诗"}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

## 模型特性

K2-Think 模型具有以下特点：

- **推理能力**: 模型会先进行思考过程，然后给出答案
- **响应格式**: 使用 `<think></think>` 和 `<answer></answer>` 标签结构化输出
- **多语言支持**: 支持中文、英文等多种语言
- **专业领域**: 在数学、科学、编程等领域表现优秀

## 故障排除

### 常见问题

1. **Token 过期**
   - 更新 `.env` 文件中的 `K2THINK_TOKEN`
   - 从[K2Think](https://www.k2think.ai/  "访问K2Think官网")网站获取新的 JWT Token[]

2. **端口冲突**
   - 修改 `PORT` 环境变量
   - 或使用 Docker 端口映射

### 日志查看

```bash
# Docker 容器日志
docker logs k2think-api

# 本地运行日志
# 日志会直接输出到控制台
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！