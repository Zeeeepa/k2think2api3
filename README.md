# K2Think API Proxy

基于 FastAPI 构建的 K2Think AI 模型代理服务，提供 OpenAI 兼容的 API 接口。

## 功能特性

- 🧠 **MBZUAI K2-Think 模型**: 支持 MBZUAI 开发的 K2-Think 推理模型
- 🔄 **OpenAI 兼容**: 完全兼容 OpenAI API 格式，无缝对接现有应用
- ⚡ **流式响应**: 支持实时流式聊天响应
- 🛠️ **工具调用**: 支持 OpenAI Function Calling，可集成外部工具和API
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
| `TOOL_SUPPORT` | `true` | 是否启用工具调用功能 |
| `SCAN_LIMIT` | `200000` | 工具调用扫描的文本长度限制 |
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

## 工具调用功能

K2Think API 代理现在支持 OpenAI Function Calling 规范的工具调用功能。

### 功能特性

- ✅ 支持 OpenAI 标准的 `tools` 和 `tool_choice` 参数
- ✅ 自动工具提示注入和消息处理
- ✅ 流式和非流式响应中的工具调用检测
- ✅ 智能 JSON 解析和工具调用提取
- ✅ 支持多种工具调用格式（JSON 代码块、内联 JSON、自然语言）

### 环境变量配置

### 快速配置检查

使用配置检查脚本验证你的环境变量设置：

```bash
# 检查当前配置
python check_config_simple.py

# 查看配置示例
python check_config_simple.py --example
```

### 配置变量说明

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `TOOL_SUPPORT` | `true` | 是否启用工具调用功能 |
| `SCAN_LIMIT` | `200000` | 工具调用扫描的文本长度限制 |

### 使用示例

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8001/v1",
    api_key="sk-k2think"
)

# 定义工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，例如：北京、上海"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

# 发送工具调用请求
response = client.chat.completions.create(
    model="MBZUAI-IFM/K2-Think",
    messages=[
        {"role": "user", "content": "北京今天天气怎么样？"}
    ],
    tools=tools,
    tool_choice="auto"  # auto, none, required 或指定特定工具
)

# 处理响应
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        function_name = tool_call.function.name
        function_args = tool_call.function.arguments
        print(f"调用工具: {function_name}")
        print(f"参数: {function_args}")
        
        # 在这里执行实际的工具调用
        # tool_result = execute_tool(function_name, function_args)
        
        # 继续对话，将工具结果返回给模型
        # ...
```

### 测试工具调用

项目包含完整的测试套件，位于 `test/` 文件夹：

```bash
# 运行所有测试
cd test
python run_all_tests.py

# 运行特定测试
python run_all_tests.py debug_test      # 基础功能测试
python run_all_tests.py test_tools      # 完整工具调用测试  
python run_all_tests.py test_contentpart # ContentPart序列化测试
python run_all_tests.py test_message_accumulation # 消息累积测试

# 查看工具调用示例
python tool_example.py
```

测试套件包含：
- 🧪 基础功能和调试测试
- 🛠️ 完整工具调用功能测试
- 📝 ContentPart 序列化问题测试
- 📊 消息累积问题验证测试

详细说明请参考 [`test/README.md`](test/README.md)。

### tool_choice 参数说明

- `"auto"`: 让模型自动决定是否使用工具（推荐）
- `"none"`: 禁用工具调用
- `"required"`: 强制模型使用工具
- `{"type": "function", "function": {"name": "tool_name"}}`: 强制使用特定工具

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！