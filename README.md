# K2Think API Proxy

基于 FastAPI 构建的 K2Think AI 模型代理服务，提供 OpenAI 兼容的 API 接口。

## ✨ 核心功能特性

- 🧠 **MBZUAI K2-Think 模型**: 支持 MBZUAI 开发的 K2-Think 推理模型
- 🔄 **OpenAI 兼容**: 完全兼容 OpenAI API 格式，无缝对接现有应用
- ⚡ **流式响应**: 支持实时流式聊天响应，支持控制thinking输出
- 🛠️ **工具调用**: 支持 OpenAI Function Calling，可集成外部工具和API
- 📊 **文件上传**: 支持文件、图像上传
- 🚀 **多实例部署**: 支持同时运行多个独立实例，每个实例使用不同凭证
- 🎯 **统一管理**: 集中管理所有实例的启动、停止、监控

## 智能Token管理系统

### 🔄 Token轮询与负载均衡

- 多token轮流使用，自动故障转移
- 支持大规模token池（支持数百个token）

### 🛡️ 智能失效检测与自愈

- **自动失效检测**: 三次失败后自动禁用失效token
- **连续失效自动刷新**: 当连续两个token失效时，自动触发强制刷新（仅在token池数量>2时生效）
- **智能重试机制**: 失效token会被跳过，确保服务连续性

### 📈 Token池管理

- 完整的管理API查看状态、重置token等
- 实时监控token使用情况和失效统计
- 支持手动重置和重新加载

### 🔄 Token自动更新

- 定期从账户文件自动生成新的token池
- **原子性更新**: 零停机时间，更新过程中服务保持可用
- **智能触发**: 支持定时更新和连续失效触发的强制更新

### 🌐 网络适应性

- 支持HTTP/HTTPS代理配置，适应不同网络环境
- 🚀 **高性能**: 异步处理架构，支持高并发请求
- 🐳 **容器化**: 支持 Docker 部署

## 🚀 快速开始

### 多实例部署（推荐）

使用 `k2think` 命令管理多个独立的 K2Think 实例，每个实例可以使用不同的凭证和端口。

#### 创建实例

```bash
# 方式1: 交互式输入凭证
./k2think create prod-api --port 8001

# 方式2: 使用环境变量（推荐用于自动化）
export K2_EMAIL="user@example.com"
export K2_PASSWORD="your-password"
./k2think create prod-api --port 8001

# 方式3: 命令行参数（不推荐，会暴露在进程列表中）
./k2think create prod-api --port 8001 --email user@example.com --password your-password

# 系统会自动：
# 1. 从 CLI > 环境变量 > 交互提示 获取凭证（优先级顺序）
# 2. 分配端口（如果未指定）
# 3. 创建实例目录结构
# 4. 生成 docker-compose.yml 和 .env
# 5. 保存凭证并设置安全权限（0600）
# 6. 获取认证 token
```

#### 管理实例

```bash
# 启动实例
./k2think start prod-api

# 停止实例
./k2think stop prod-api

# 重启实例
./k2think restart prod-api

# 查看所有实例
./k2think list

# 查看活动端点
./k2think endpoints

# 查看实例详情
./k2think status prod-api

# 查看日志
./k2think logs prod-api
./k2think logs prod-api -f  # 实时跟踪

# 删除实例
./k2think delete test-api
./k2think delete test-api --keep-data  # 保留数据备份

# 批量操作
./k2think start-all     # 启动所有已停止的实例
./k2think stop-all      # 停止所有运行中的实例
./k2think restart-all   # 重启所有实例

# 健康检查
./k2think health        # 检查所有实例健康状态

# 克隆实例
./k2think clone prod prod-backup --port 8010  # 克隆实例到新端口
```

#### 示例：运行多个实例

```bash
# 生产环境
./k2think create prod --port 8001 --email prod@company.com

# 测试环境
./k2think create staging --port 8002 --email staging@company.com

# 开发环境
./k2think create dev --port 8003 --email dev@company.com

# 启动所有实例
./k2think start prod
./k2think start staging
./k2think start dev

# 查看所有活动端点
./k2think endpoints
```

输出示例：
```
╔══════════════════════════════════════════════════════════════════╗
║              K2THINK DEPLOYMENT MANAGER                          ║
╠══════════════════════════════════════════════════════════════════╣
║ Total Instances: 3  |  Running: 3  |  Stopped: 0                ║
╚══════════════════════════════════════════════════════════════════╝

NAME          STATUS    PORT   ENDPOINT                    
----------------------------------------------------------------------
prod          ✓ running 8001   http://localhost:8001       
staging       ✓ running 8002   http://localhost:8002       
dev           ✓ running 8003   http://localhost:8003       
```

### 单实例部署（传统方式）

#### 本地运行

1. **安装依赖**

```bash
pip install -r requirements.txt
```

2. **配置环境变量**

```bash
cp .env.example .env
# 编辑 .env 文件，配置你的API密钥和其他选项
```

3. **准备Token文件**

有两种方式管理Token：

**方式一：手动管理（传统方式）**

```bash
# 复制token示例文件并编辑
cd data
cp tokens.example.txt tokens.txt
# 编辑tokens.txt文件，添加你的实际K2Think tokens
```

**方式二：自动更新（推荐）**

```bash
# 准备账户文件
echo '{"email": "your-email@example.com", "k2_password": "your-password"}' > accounts.txt
# 可以添加多个账户，每行一个JSON对象
```

4. **启动服务**

```bash
python k2think_proxy.py
```

服务将在 `http://localhost:8001` 启动。

### Docker 部署

#### 使用 docker-compose（推荐）

```bash
# 准备配置文件
cp .env.example .env
cd data
cp accounts.example.txt accounts.txt

# 编辑配置
# 编辑 .env 文件配置API密钥等
# 编辑 accounts.txt 添加K2Think账户信息，格式：{"email": "xxx@yyy.zzz", "k2_password": "xxx"}，一行一个

# 启动服务
docker-compose up -d

# 检查服务状态
docker-compose logs -f k2think-api
```

#### 手动构建部署

```bash
# 构建镜像
docker build -t k2think-api .

# 运行容器
docker run -d \
  --name k2think-api \
  -p 8001:8001 \
  -v $(pwd)/tokens.txt:/app/tokens.txt \
  -v $(pwd)/accounts.txt:/app/accounts.txt:ro \
  -v $(pwd)/.env:/app/.env:ro \
  k2think-api
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

### Token管理接口

查看token池状态：

```bash
curl http://localhost:8001/admin/tokens/stats
```

查看连续失效状态：

```bash
curl http://localhost:8001/admin/tokens/consecutive-failures
```

重置连续失效计数：

```bash
curl -X POST http://localhost:8001/admin/tokens/reset-consecutive
```

重置指定token：

```bash
curl -X POST http://localhost:8001/admin/tokens/reset/0
```

重置所有token：

```bash
curl -X POST http://localhost:8001/admin/tokens/reset-all
```

重新加载token文件：

```bash
curl -X POST http://localhost:8001/admin/tokens/reload
```

查看token更新器状态（仅在启用自动更新时可用）：

```bash
curl http://localhost:8001/admin/tokens/updater/status
```

强制更新tokens（仅在启用自动更新时可用）：

```bash
curl -X POST http://localhost:8001/admin/tokens/updater/force-update
```

### 健康检查

```bash
curl http://localhost:8001/health
```

## 环境变量配置

### 基础配置

| 变量名              | 默认值                                      | 说明                 |
| ------------------- | ------------------------------------------- | -------------------- |
| `VALID_API_KEY`   | 无默认值                                    | API 访问密钥（必需） |
| `K2THINK_API_URL` | https://www.k2think.ai/api/chat/completions | K2Think API端点      |

### Token管理配置

| 变量名                 | 默认值         | 说明              |
| ---------------------- | -------------- | ----------------- |
| `TOKENS_FILE`        | `tokens.txt` | Token文件路径     |
| `MAX_TOKEN_FAILURES` | `3`          | Token最大失败次数 |

### Token自动更新配置

| 变量名                       | 默认值            | 说明                                    |
| ---------------------------- | ----------------- | --------------------------------------- |
| `ENABLE_TOKEN_AUTO_UPDATE` | `false`         | 是否启用token自动更新                   |
| `TOKEN_UPDATE_INTERVAL`    | `86400`         | token更新间隔（秒），默认24小时         |
| `ACCOUNTS_FILE`            | `accounts.txt`  | 账户文件路径                            |
| `GET_TOKENS_SCRIPT`        | `get_tokens.py` | token获取脚本路径                       |
| `PROXY_URL`                | 空                | HTTP/HTTPS代理地址（用于get_tokens.py） |

### 服务器配置

| 变量名   | 默认值      | 说明         |
| -------- | ----------- | ------------ |
| `HOST` | `0.0.0.0` | 服务监听地址 |
| `PORT` | `8001`    | 服务端口     |

### 工具调用配置

| 变量名                    | 默认值   | 说明                             |
| ------------------------- | -------- | -------------------------------- |
| `ENABLE_TOOLIFY`        | `true` | 是否启用工具调用功能             |
| `TOOLIFY_CUSTOM_PROMPT` | `""`   | 自定义工具调用提示词模板（可选） |

详细配置说明请参考 `.env.example` 文件。

## 智能Token管理系统详解

### 连续失效自动刷新机制

这是系统的核心自愈功能，当检测到连续的token失效时，自动触发强制刷新：

#### 工作原理

1. **连续失效检测**

   - 系统跟踪连续失效的token数量
   - 当连续两个token失效时触发自动刷新
   - 仅在token池数量大于2时启用（避免小规模token池误触发）
2. **智能触发条件**

   - 连续失效阈值：2个token
   - 最小token池大小：3个token
   - 自动更新必须启用：`ENABLE_TOKEN_AUTO_UPDATE=true`
3. **自动刷新过程**

   - 异步执行，不阻塞当前API请求
   - 使用原子性更新机制
   - 刷新成功后自动重新加载token池
   - 重置连续失效计数器

#### 监控和管理

```bash
# 查看连续失效状态
curl http://localhost:8001/admin/tokens/consecutive-failures

# 响应示例
{
  "status": "success",
  "data": {
    "consecutive_failures": 1,
    "threshold": 2,
    "token_pool_size": 710,
    "auto_refresh_enabled": true,
    "last_check": "实时检测"
  }
}

# 手动重置连续失效计数
curl -X POST http://localhost:8001/admin/tokens/reset-consecutive
```

### Token自动更新机制

#### 功能说明

Token自动更新机制允许系统定期从账户文件自动生成新的token池，无需手动维护tokens.txt文件。

#### 配置步骤

1. **准备账户文件**

创建 `accounts.txt` 文件，每行一个JSON格式的账户信息：

```json
{"email": "user1@example.com", "k2_password": "password1"}
{"email": "user2@example.com", "k2_password": "password2"}
{"email": "user3@example.com", "k2_password": "password3"}
```

2. **启用自动更新**

在 `.env` 文件中配置：

```bash
# 启用token自动更新
ENABLE_TOKEN_AUTO_UPDATE=true

# 设置更新间隔（秒）
TOKEN_UPDATE_INTERVAL=86400  # 每24小时更新一次

# 配置文件路径
ACCOUNTS_FILE=accounts.txt
TOKENS_FILE=tokens.txt
GET_TOKENS_SCRIPT=get_tokens.py

# 可选：配置代理（如果需要）
PROXY_URL=http://username:password@proxy_host:proxy_port
```

3. **更新触发方式**

系统支持多种更新触发方式：

- **定时更新**: 按照设置的间隔定期更新
- **连续失效触发**: 当连续两个token失效时自动触发
- **手动强制更新**: 通过API手动触发更新
- **启动时更新**: 如果token文件为空或无效，启动时立即更新

#### 原子性更新机制

为了确保token更新过程中服务的连续性，系统采用了原子性更新机制：

1. **临时文件生成**: 新token首先写入 `tokens.txt.tmp` 临时文件
2. **验证检查**: 确认临时文件存在且不为空
3. **备份当前文件**: 将现有 `tokens.txt` 重命名为 `tokens.txt.backup`
4. **原子性替换**: 将临时文件重命名为 `tokens.txt`
5. **重新加载**: 通知token管理器重新加载新的token池

#### 更新状态监控

通过管理接口可以实时监控更新状态：

```bash
# 查看详细更新状态
curl http://localhost:8001/admin/tokens/updater/status

# 响应示例
{
  "status": "success",
  "data": {
    "is_running": true,
    "is_updating": false,
    "update_interval": 86400,
    "last_update": "2024-01-01T12:00:00",
    "update_count": 5,
    "error_count": 0,
    "last_error": null,
    "next_update": "2024-01-01T13:00:00",
    "files": {
      "get_tokens_script": true,
      "accounts_file": true,
      "tokens_file": true
    }
  }
}
```

#### 服务保障特性

- ✅ **零停机时间**: 更新过程中API服务保持可用
- ✅ **请求不中断**: 正在处理的请求不会受到影响
- ✅ **自动恢复**: 连续失效时自动触发刷新
- ✅ **回滚机制**: 更新失败时保留原有token文件
- ✅ **状态透明**: 可实时查看更新进度和状态
- ✅ **错误处理**: 更新失败时记录详细错误信息

## 工具调用功能

K2Think API 代理支持 OpenAI Function Calling 规范的工具调用功能。

### 功能特性

- ✅ 支持 OpenAI 标准的 `tools` 和 `tool_choice` 参数
- ✅ 自动工具提示注入和消息处理
- ✅ 流式和非流式响应中的工具调用检测
- ✅ 智能 JSON 解析和工具调用提取
- ✅ 支持多种工具调用格式（JSON 代码块、内联 JSON、自然语言）

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
```

### tool_choice 参数说明

- `"auto"`: 让模型自动决定是否使用工具（推荐）
- `"none"`: 禁用工具调用
- `"required"`: 强制模型使用工具
- `{"type": "function", "function": {"name": "tool_name"}}`: 强制使用特定工具

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
- **思考内容控制**:
  - `MBZUAI-IFM/K2-Think`: 包含完整的思考过程
  - `MBZUAI-IFM/K2-Think-nothink`: 仅输出最终答案
- **多语言支持**: 支持中文、英文等多种语言
- **专业领域**: 在数学、科学、编程等领域表现优秀

## 完整配置示例

### .env 文件示例

```bash
# 基础配置
VALID_API_KEY=sk-k2think
HOST=0.0.0.0
PORT=8001

# Token管理
TOKENS_FILE=tokens.txt
MAX_TOKEN_FAILURES=3

# Token自动更新（推荐）
ENABLE_TOKEN_AUTO_UPDATE=true
TOKEN_UPDATE_INTERVAL=86400 # 24小时
ACCOUNTS_FILE=accounts.txt
GET_TOKENS_SCRIPT=get_tokens.py

# 代理配置（可选）
PROXY_URL=http://username:password@proxy.example.com:8080

# 功能开关
ENABLE_TOOLIFY=true
DEBUG_LOGGING=false

# 工具调用配置（可选）
# TOOLIFY_CUSTOM_PROMPT="自定义提示词模板"
```

### accounts.txt 文件示例

```json
{"email": "user1@example.com", "k2_password": "password1"}
{"email": "user2@example.com", "k2_password": "password2"}
```

## 故障排除

### 常见问题

1. **Token 相关问题**

   - **所有token失效**: 访问 `/admin/tokens/stats` 查看token状态，使用 `/admin/tokens/reset-all` 重置所有token
   - **连续失效**: 查看 `/admin/tokens/consecutive-failures` 了解连续失效状态，系统会自动触发刷新
   - **添加新token**:
     - 手动模式：编辑 `tokens.txt` 文件添加新token，然后访问 `/admin/tokens/reload` 重新加载
     - 自动模式：编辑 `accounts.txt` 添加新账户，然后访问 `/admin/tokens/updater/force-update` 强制更新
   - **查看token状态**: 访问 `/health` 端点查看简要统计，或 `/admin/tokens/stats` 查看详细信息
   - **自动更新问题**:
     - 访问 `/admin/tokens/updater/status` 查看更新器状态和错误信息
     - 检查 `is_updating` 字段确认是否正在更新中
     - 查看 `last_error` 字段了解最近的错误信息
2. **端口冲突**

   - 修改 `PORT` 环境变量
   - 或使用 Docker 端口映射

### 日志查看

```bash
# Docker 容器日志
docker logs k2think-api

# docker-compose日志
docker-compose logs -f k2think-api

# 本地运行日志
# 日志会直接输出到控制台
```

### 配置检查

使用配置检查脚本验证你的环境变量设置：

```bash
# 检查当前配置
python check_config_simple.py

# 查看配置示例
python check_config_simple.py --example
```

### Docker部署注意事项

1. **文件映射**

   - `tokens.txt` 通过volume映射到容器内，支持动态更新
   - 如果启用自动更新，`tokens.txt` 不能设置为只读（`:ro`）
   - `accounts.txt` 映射为只读，包含账户信息用于自动更新
   - `.env` 文件包含所有环境变量配置
2. **健康检查**

   - Docker容器包含健康检查机制
   - 可通过 `docker ps` 查看健康状态
3. **安全考虑**

   - 容器以非root用户运行
   - 敏感文件通过volume挂载而非打包到镜像中

## 🏗️ 多实例架构

### 目录结构

```
project/
├── k2think_manager.py          # 多实例管理器
├── k2think                     # 统一CLI入口
├── get_tokens.py               # Token获取工具
├── k2think_proxy.py            # 代理服务主程序
├── instances/                  # 实例目录
│   ├── instances.json          # 实例注册表
│   ├── prod-api/
│   │   ├── docker-compose.yml
│   │   ├── .env
│   │   └── data/
│   │       ├── accounts.txt
│   │       └── tokens.txt
│   ├── staging-api/
│   │   └── ...
│   └── dev-api/
│       └── ...
└── ...
```

### 关键特性

1. **独立隔离**: 每个实例拥有独立的容器、网络、凭证和端口
2. **桥接网络**: 使用 Docker 桥接网络，避免端口冲突，支持 Mac/Windows
3. **自动端口分配**: 从 8001 开始自动分配可用端口
4. **中央注册表**: `instances.json` 记录所有实例状态和配置
5. **完整中文支持**: UTF-8 编码，支持中文邮箱和密码输入
6. **多源凭证管理**: CLI 参数 → 环境变量 → 交互提示（优先级顺序）
7. **批量操作**: 一键启动/停止/重启所有实例
8. **健康监控**: 实时检查所有实例运行状态
9. **实例克隆**: 快速复制实例配置到新端口

### 多实例使用场景

- **多账户管理**: 为不同的 K2Think 账户运行独立实例
- **环境隔离**: 生产、测试、开发环境独立部署
- **负载分散**: 将请求分散到多个实例，提高并发能力
- **A/B 测试**: 同时运行不同配置的实例进行对比测试

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
