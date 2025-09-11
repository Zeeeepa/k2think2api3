from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Union, AsyncGenerator
import httpx
import json
import asyncio
import time
import os
import logging
import re
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置
VALID_API_KEY = os.getenv("VALID_API_KEY", "sk-k2think")
K2THINK_API_URL = os.getenv("K2THINK_API_URL", "https://www.k2think.ai/api/chat/completions")
K2THINK_TOKEN = os.getenv("K2THINK_TOKEN")
OUTPUT_THINKING = os.getenv("OUTPUT_THINKING", "true").lower() == "true"
TOOL_SUPPORT = os.getenv("TOOL_SUPPORT", "true").lower() == "true"
SCAN_LIMIT = int(os.getenv("SCAN_LIMIT", "200000"))

# 高级配置
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "60"))
MAX_KEEPALIVE_CONNECTIONS = int(os.getenv("MAX_KEEPALIVE_CONNECTIONS", "20"))
MAX_CONNECTIONS = int(os.getenv("MAX_CONNECTIONS", "100"))
DEBUG_LOGGING = os.getenv("DEBUG_LOGGING", "false").lower() == "true"
STREAM_DELAY = float(os.getenv("STREAM_DELAY", "0.05"))
STREAM_CHUNK_SIZE = int(os.getenv("STREAM_CHUNK_SIZE", "50"))
ENABLE_ACCESS_LOG = os.getenv("ENABLE_ACCESS_LOG", "true").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS", "*") != "*" else ["*"]

# 设置日志
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
if LOG_LEVEL == "DEBUG":
    logging.basicConfig(level=logging.DEBUG)
elif LOG_LEVEL == "WARNING":
    logging.basicConfig(level=logging.WARNING)
elif LOG_LEVEL == "ERROR":
    logging.basicConfig(level=logging.ERROR)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# 数据模型
class ContentPart(BaseModel):
    """Content part model for OpenAI's new content format"""
    type: str
    text: Optional[str] = None

class Message(BaseModel):
    role: str
    content: Optional[Union[str, List[ContentPart]]] = None
    tool_calls: Optional[List[Dict]] = None

class ChatCompletionRequest(BaseModel):
    model: str = "MBZUAI-IFM/K2-Think"
    messages: List[Message]
    stream: bool = False
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[Union[str, List[str]]] = None
    tools: Optional[List[Dict]] = None
    tool_choice: Optional[Union[str, Dict]] = None

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str
    permission: List[Dict] = []
    root: str
    parent: Optional[str] = None

class ModelsResponse(BaseModel):
    object: str = "list"
    data: List[ModelInfo]

# HTTP客户端工厂函数
def create_http_client() -> httpx.AsyncClient:
    """创建HTTP客户端"""
    base_kwargs = {
        "timeout": httpx.Timeout(timeout=None, connect=10.0),
        "limits": httpx.Limits(
            max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS, 
            max_connections=MAX_CONNECTIONS
        ),
        "follow_redirects": True
    }
    
    try:
        return httpx.AsyncClient(**base_kwargs)
    except Exception as e:
        logger.error(f"创建客户端失败: {e}")
        raise e

# 全局HTTP客户端管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

# 创建FastAPI应用
app = FastAPI(title="K2Think API Proxy", lifespan=lifespan)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def validate_api_key(authorization: str) -> bool:
    """验证API密钥"""
    if not authorization or not authorization.startswith("Bearer "):
        return False
    api_key = authorization[7:]  # 移除 "Bearer " 前缀
    return api_key == VALID_API_KEY

def generate_session_id() -> str:
    """生成会话ID"""
    import uuid
    return str(uuid.uuid4())

def generate_chat_id() -> str:
    """生成聊天ID"""
    import uuid
    return str(uuid.uuid4())

def get_current_datetime_info():
    """获取当前时间信息"""
    from datetime import datetime
    import pytz
    
    # 设置时区为上海
    tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(tz)
    
    return {
        "{{USER_NAME}}": "User",
        "{{USER_LOCATION}}": "Unknown",
        "{{CURRENT_DATETIME}}": now.strftime("%Y-%m-%d %H:%M:%S"),
        "{{CURRENT_DATE}}": now.strftime("%Y-%m-%d"),
        "{{CURRENT_TIME}}": now.strftime("%H:%M:%S"),
        "{{CURRENT_WEEKDAY}}": now.strftime("%A"),
        "{{CURRENT_TIMEZONE}}": "Asia/Shanghai",
        "{{USER_LANGUAGE}}": "en-US"
    }

def extract_answer_content(full_content: str) -> str:
    """删除第一个<answer>标签和最后一个</answer>标签，保留内容"""
    if not full_content:
        return full_content
    if OUTPUT_THINKING:
        # 删除第一个<answer>
        answer_start = full_content.find('<answer>')
        if answer_start != -1:
            full_content = full_content[:answer_start] + full_content[answer_start + 8:]

        # 删除最后一个</answer>
        answer_end = full_content.rfind('</answer>')
        if answer_end != -1:
            full_content = full_content[:answer_end] + full_content[answer_end + 9:]

        return full_content.strip()
    else:
        # 删除<think>部分（包括标签）
        think_start = full_content.find('<think>')
        think_end = full_content.find('</think>')
        if think_start != -1 and think_end != -1:
            full_content = full_content[:think_start] + full_content[think_end + 8:]
        
        # 删除<answer>标签及其内容之外的部分
        answer_start = full_content.find('<answer>')
        answer_end = full_content.rfind('</answer>')
        if answer_start != -1 and answer_end != -1:
            content = full_content[answer_start + 8:answer_end]
            return content.strip()

        return full_content.strip()

def content_to_string(content) -> str:
    """Convert content from various formats to string"""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if hasattr(p, 'text'):  # ContentPart object
                parts.append(getattr(p, 'text', ''))
            elif isinstance(p, dict) and p.get("type") == "text":
                parts.append(p.get("text", ""))
            elif isinstance(p, str):
                parts.append(p)
            else:
                # 处理其他类型的对象
                try:
                    if hasattr(p, '__dict__'):
                        # 如果是对象，尝试获取text属性或转换为字符串
                        parts.append(str(getattr(p, 'text', str(p))))
                    else:
                        parts.append(str(p))
                except:
                    continue
        return " ".join(parts)
    # 处理其他类型
    try:
        return str(content)
    except:
        return ""

def generate_tool_prompt(tools: List[Dict]) -> str:
    """Generate concise tool injection prompt"""
    if not tools:
        return ""

    tool_definitions = []
    for tool in tools:
        if tool.get("type") != "function":
            continue

        function_spec = tool.get("function", {}) or {}
        function_name = function_spec.get("name", "unknown")
        function_description = function_spec.get("description", "")
        parameters = function_spec.get("parameters", {}) or {}

        # Create concise tool definition
        tool_info = f"{function_name}: {function_description}"
        
        # Add simplified parameter info
        parameter_properties = parameters.get("properties", {}) or {}
        required_parameters = set(parameters.get("required", []) or [])

        if parameter_properties:
            param_list = []
            for param_name, param_details in parameter_properties.items():
                param_desc = (param_details or {}).get("description", "")
                is_required = param_name in required_parameters
                param_list.append(f"{param_name}{'*' if is_required else ''}: {param_desc}")
            tool_info += f" Parameters: {', '.join(param_list)}"

        tool_definitions.append(tool_info)

    if not tool_definitions:
        return ""

    # Build concise tool prompt
    prompt_template = (
        f"\n\nAvailable tools: {'; '.join(tool_definitions)}. "
        "To use a tool, respond with JSON: "
        '{"tool_calls":[{"id":"call_xxx","type":"function","function":{"name":"tool_name","arguments":"{\\"param\\":\\"value\\"}"}}]}'
    )

    return prompt_template

def process_messages_with_tools(messages: List[Dict], tools: Optional[List[Dict]] = None, tool_choice: Optional[Union[str, Dict]] = None) -> List[Dict]:
    """Process messages and inject tool prompts"""
    if not tools or not TOOL_SUPPORT or (tool_choice == "none"):
        # 如果没有工具或禁用工具，直接返回原消息
        return [dict(m) for m in messages]
    
    tools_prompt = generate_tool_prompt(tools)
    
    # 限制工具提示长度，避免过长导致上游API拒绝
    if len(tools_prompt) > 1000:
        logger.warning(f"工具提示过长 ({len(tools_prompt)} 字符)，将截断")
        tools_prompt = tools_prompt[:1000] + "..."
    
    processed = []
    has_system = any(m.get("role") == "system" for m in messages)

    if has_system:
        # 如果已有系统消息，在第一个系统消息中添加工具提示
        for m in messages:
            if m.get("role") == "system":
                mm = dict(m)
                content = content_to_string(mm.get("content", ""))
                # 确保系统消息不会过长
                new_content = content + tools_prompt
                if len(new_content) > 2000:
                    logger.warning(f"系统消息过长 ({len(new_content)} 字符)，使用简化版本")
                    mm["content"] = "你是一个有用的助手。" + tools_prompt
                else:
                    mm["content"] = new_content
                processed.append(mm)
                # 只在第一个系统消息中添加工具提示
                tools_prompt = ""
            else:
                processed.append(dict(m))
    else:
        # 如果没有系统消息，需要添加一个，但只有当确实需要工具时
        if tools_prompt.strip():
            processed = [{"role": "system", "content": "你是一个有用的助手。" + tools_prompt}]
            processed.extend([dict(m) for m in messages])
        else:
            processed = [dict(m) for m in messages]

    # Add simplified tool choice hints
    if tool_choice == "required":
        if processed and processed[-1].get("role") == "user":
            last = processed[-1]
            content = content_to_string(last.get("content", ""))
            last["content"] = content + "\n请使用工具来处理这个请求。"
    elif isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
        fname = (tool_choice.get("function") or {}).get("name")
        if fname and processed and processed[-1].get("role") == "user":
            last = processed[-1]
            content = content_to_string(last.get("content", ""))
            last["content"] = content + f"\n请使用 {fname} 工具。"

    # Handle tool/function messages
    final_msgs = []
    for m in processed:
        role = m.get("role")
        if role in ("tool", "function"):
            tool_name = m.get("name", "unknown")
            tool_content = content_to_string(m.get("content", ""))
            if isinstance(tool_content, dict):
                tool_content = json.dumps(tool_content, ensure_ascii=False)

            # 简化工具结果消息
            content = f"工具 {tool_name} 结果: {tool_content}"
            if not content.strip():
                content = f"工具 {tool_name} 执行完成"

            final_msgs.append({
                "role": "assistant",
                "content": content,
            })
        else:
            # For regular messages, ensure content is string format
            final_msg = dict(m)
            content = content_to_string(final_msg.get("content", ""))
            final_msg["content"] = content
            final_msgs.append(final_msg)

    return final_msgs

# Tool Extraction Patterns
TOOL_CALL_FENCE_PATTERN = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)
FUNCTION_CALL_PATTERN = re.compile(r"调用函数\s*[：:]\s*([\w\-\.]+)\s*(?:参数|arguments)[：:]\s*(\{.*?\})", re.DOTALL)

def extract_tool_invocations(text: str) -> Optional[List[Dict]]:
    """Extract tool invocations from response text"""
    if not text:
        return None

    # Limit scan size for performance
    scannable_text = text[:SCAN_LIMIT]

    # Attempt 1: Extract from JSON code blocks
    json_blocks = TOOL_CALL_FENCE_PATTERN.findall(scannable_text)
    for json_block in json_blocks:
        try:
            parsed_data = json.loads(json_block)
            tool_calls = parsed_data.get("tool_calls")
            if tool_calls and isinstance(tool_calls, list):
                # Ensure arguments field is a string
                for tc in tool_calls:
                    if "function" in tc:
                        func = tc["function"]
                        if "arguments" in func:
                            if isinstance(func["arguments"], dict):
                                # Convert dict to JSON string
                                func["arguments"] = json.dumps(func["arguments"], ensure_ascii=False)
                            elif not isinstance(func["arguments"], str):
                                func["arguments"] = json.dumps(func["arguments"], ensure_ascii=False)
                return tool_calls
        except (json.JSONDecodeError, AttributeError):
            continue

    # Attempt 2: Extract inline JSON objects using bracket balance method
    i = 0
    while i < len(scannable_text):
        if scannable_text[i] == '{':
            # 尝试找到匹配的右括号
            brace_count = 1
            j = i + 1
            in_string = False
            escape_next = False
            
            while j < len(scannable_text) and brace_count > 0:
                if escape_next:
                    escape_next = False
                elif scannable_text[j] == '\\':
                    escape_next = True
                elif scannable_text[j] == '"' and not escape_next:
                    in_string = not in_string
                elif not in_string:
                    if scannable_text[j] == '{':
                        brace_count += 1
                    elif scannable_text[j] == '}':
                        brace_count -= 1
                j += 1
            
            if brace_count == 0:
                # 找到了完整的 JSON 对象
                json_str = scannable_text[i:j]
                try:
                    parsed_data = json.loads(json_str)
                    tool_calls = parsed_data.get("tool_calls")
                    if tool_calls and isinstance(tool_calls, list):
                        # Ensure arguments field is a string
                        for tc in tool_calls:
                            if "function" in tc:
                                func = tc["function"]
                                if "arguments" in func:
                                    if isinstance(func["arguments"], dict):
                                        # Convert dict to JSON string
                                        func["arguments"] = json.dumps(func["arguments"], ensure_ascii=False)
                                    elif not isinstance(func["arguments"], str):
                                        func["arguments"] = json.dumps(func["arguments"], ensure_ascii=False)
                        return tool_calls
                except (json.JSONDecodeError, AttributeError):
                    pass
            
            i += 1
        else:
            i += 1

    # Attempt 3: Parse natural language function calls
    natural_lang_match = FUNCTION_CALL_PATTERN.search(scannable_text)
    if natural_lang_match:
        function_name = natural_lang_match.group(1).strip()
        arguments_str = natural_lang_match.group(2).strip()
        try:
            # Validate JSON format
            json.loads(arguments_str)
            return [
                {
                    "id": f"call_{int(time.time() * 1000000)}",
                    "type": "function",
                    "function": {"name": function_name, "arguments": arguments_str},
                }
            ]
        except json.JSONDecodeError:
            return None

    return None

def remove_tool_json_content(text: str) -> str:
    """Remove tool JSON content from response text - using bracket balance method"""
    
    def remove_tool_call_block(match: re.Match) -> str:
        json_content = match.group(1)
        try:
            parsed_data = json.loads(json_content)
            if "tool_calls" in parsed_data:
                return ""
        except (json.JSONDecodeError, AttributeError):
            pass
        return match.group(0)
    
    # Step 1: Remove fenced tool JSON blocks
    cleaned_text = TOOL_CALL_FENCE_PATTERN.sub(remove_tool_call_block, text)
    
    # Step 2: Remove inline tool JSON - 使用基于括号平衡的智能方法
    result = []
    i = 0
    while i < len(cleaned_text):
        if cleaned_text[i] == '{':
            # 尝试找到匹配的右括号
            brace_count = 1
            j = i + 1
            in_string = False
            escape_next = False
            
            while j < len(cleaned_text) and brace_count > 0:
                if escape_next:
                    escape_next = False
                elif cleaned_text[j] == '\\':
                    escape_next = True
                elif cleaned_text[j] == '"' and not escape_next:
                    in_string = not in_string
                elif not in_string:
                    if cleaned_text[j] == '{':
                        brace_count += 1
                    elif cleaned_text[j] == '}':
                        brace_count -= 1
                j += 1
            
            if brace_count == 0:
                # 找到了完整的 JSON 对象
                json_str = cleaned_text[i:j]
                try:
                    parsed = json.loads(json_str)
                    if "tool_calls" in parsed:
                        # 这是一个工具调用，跳过它
                        i = j
                        continue
                except:
                    pass
            
            # 不是工具调用或无法解析，保留这个字符
            result.append(cleaned_text[i])
            i += 1
        else:
            result.append(cleaned_text[i])
            i += 1
    
    return ''.join(result).strip()

async def make_request(method: str, url: str, headers: dict, json_data: dict = None, 
                      stream: bool = False) -> httpx.Response:
    """发送HTTP请求"""
    client = None
    
    try:
        client = create_http_client()
        
        if stream:
            # 流式请求返回context manager
            return client.stream(method, url, headers=headers, json=json_data, timeout=None)
        else:
            response = await client.request(method, url, headers=headers, json=json_data, timeout=REQUEST_TIMEOUT)
            
            # 详细记录非200响应
            if response.status_code != 200:
                logger.error(f"上游API返回错误状态码: {response.status_code}")
                logger.error(f"响应头: {dict(response.headers)}")
                try:
                    error_body = response.text
                    logger.error(f"错误响应体: {error_body}")
                except:
                    logger.error("无法读取错误响应体")
            
            response.raise_for_status()
            return response
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP状态错误: {e.response.status_code} - {e.response.text}")
        if client and not stream:
            await client.aclose()
        raise e
    except Exception as e:
        logger.error(f"请求异常: {e}")
        if client and not stream:
            await client.aclose()
        raise e

@app.get("/")
async def homepage():
    """首页 - 返回服务状态"""
    return JSONResponse(content={
        "status": "success",
        "message": "K2Think API Proxy is running",
        "service": "K2Think API Gateway", 
        "model": "MBZUAI-IFM/K2-Think",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/v1/chat/completions",
            "models": "/v1/models"
        }
    })

@app.get("/health")
async def health_check():
    """健康检查"""
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": int(time.time())
    })

@app.get("/favicon.ico")
async def favicon():
    """返回favicon"""
    return Response(content="", media_type="image/x-icon")

@app.get("/v1/models")
async def get_models() -> ModelsResponse:
    """获取模型列表"""
    model_info = ModelInfo(
        id="MBZUAI-IFM/K2-Think",
        created=int(time.time()),
        owned_by="MBZUAI",
        root="mbzuai-k2-think-2508"
    )
    return ModelsResponse(data=[model_info])


@app.get("/favicon.ico")
async def favicon():
    """返回favicon"""
    return Response(content="", media_type="image/x-icon")

@app.get("/v1/models")
async def get_models() -> ModelsResponse:
    """获取模型列表"""
    model_info = ModelInfo(
        id="MBZUAI-IFM/K2-Think",
        created=int(time.time()),
        owned_by="MBZUAI",
        root="mbzuai-k2-think-2508"
    )
    return ModelsResponse(data=[model_info])

async def process_non_stream_response(k2think_payload: dict, headers: dict) -> tuple[str, dict]:
    """处理非流式响应"""
    try:
        response = await make_request(
            "POST", 
            K2THINK_API_URL, 
            headers, 
            k2think_payload, 
            stream=False
        )
        
        # K2Think 非流式请求返回标准JSON格式
        result = response.json()
        
        # 提取内容
        full_content = ""
        if result.get('choices') and len(result['choices']) > 0:
            choice = result['choices'][0]
            if choice.get('message') and choice['message'].get('content'):
                raw_content = choice['message']['content']
                # 提取<answer>标签中的内容，去除标签
                full_content = extract_answer_content(raw_content)
        
        # 提取token信息
        token_info = result.get('usage', {
            "prompt_tokens": 0, 
            "completion_tokens": 0, 
            "total_tokens": 0
        })
        
        await response.aclose()
        return full_content, token_info
                    
    except Exception as e:
        logger.error(f"处理非流式响应错误: {e}")
        raise

async def process_stream_response(k2think_payload: dict, headers: dict) -> AsyncGenerator[str, None]:
    """处理流式响应 - 使用模拟流式输出"""
    try:
        # 将流式请求转换为非流式请求
        k2think_payload_copy = k2think_payload.copy()
        k2think_payload_copy["stream"] = False
        
        # 修改headers为非流式
        headers_copy = headers.copy()
        headers_copy["accept"] = "application/json"
        
        # 获取完整响应
        full_content, token_info = await process_non_stream_response(k2think_payload_copy, headers_copy)
        
        if not full_content:
            yield "data: [DONE]\n\n"
            return
        
        # 开始流式输出 - 发送开始chunk
        start_chunk = {
            "id": f"chatcmpl-{int(time.time() * 1000)}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "MBZUAI-IFM/K2-Think",
            "choices": [{
                "index": 0,
                "delta": {
                    "role": "assistant",
                    "content": ""
                },
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(start_chunk)}\n\n"
        
        # 模拟流式输出 - 按字符分块发送
        
        chunk_size = STREAM_CHUNK_SIZE  # 每次发送n个字符
        
        for i in range(0, len(full_content), chunk_size):
            chunk_content = full_content[i:i + chunk_size]
            
            chunk = {
                "id": f"chatcmpl-{int(time.time() * 1000)}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "MBZUAI-IFM/K2-Think",
                "choices": [{
                    "index": 0,
                    "delta": {
                        "content": chunk_content
                    },
                    "finish_reason": None
                }]
            }
            
            yield f"data: {json.dumps(chunk)}\n\n"
            # 添加小延迟模拟真实流式效果
            await asyncio.sleep(STREAM_DELAY)
        
        # 发送结束chunk
        end_chunk = {
            "id": f"chatcmpl-{int(time.time() * 1000)}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "MBZUAI-IFM/K2-Think",
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(end_chunk)}\n\n"
        yield "data: [DONE]\n\n"
                
    except Exception as e:
        logger.error(f"流式请求失败: {e}")
        # 发送错误信息
        error_chunk = {
            "id": f"chatcmpl-{int(time.time() * 1000)}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "MBZUAI-IFM/K2-Think",
            "choices": [{
                "index": 0,
                "delta": {
                    "content": f"Error: {str(e)}"
                },
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
        yield "data: [DONE]\n\n"

async def process_stream_response_with_tools(k2think_payload: dict, headers: dict, has_tools: bool = False) -> AsyncGenerator[str, None]:
    """处理流式响应 - 支持工具调用，优化性能"""
    try:
        # 发送开始chunk
        start_chunk = {
            "id": f"chatcmpl-{int(time.time() * 1000)}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "MBZUAI-IFM/K2-Think",
            "choices": [{
                "index": 0,
                "delta": {
                    "role": "assistant",
                    "content": ""
                },
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(start_chunk)}\n\n"
        
        # 优化的模拟流式输出 - 立即开始获取响应并流式发送
        k2think_payload_copy = k2think_payload.copy()
        k2think_payload_copy["stream"] = False
        
        headers_copy = headers.copy()
        headers_copy["accept"] = "application/json"
        
        # 获取完整响应
        full_content, token_info = await process_non_stream_response(k2think_payload_copy, headers_copy)
        
        if not full_content:
            yield "data: [DONE]\n\n"
            return
        
        # Handle tool calls for streaming
        finish_reason = "stop"
        if has_tools:
            tool_calls = extract_tool_invocations(full_content)
            if tool_calls:
                # Send tool calls with proper format
                for i, tc in enumerate(tool_calls):
                    tool_call_delta = {
                        "index": i,
                        "id": tc.get("id"),
                        "type": tc.get("type", "function"),
                        "function": tc.get("function", {}),
                    }
                    
                    tool_chunk = {
                        "id": f"chatcmpl-{int(time.time() * 1000)}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": "MBZUAI-IFM/K2-Think",
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "tool_calls": [tool_call_delta]
                            },
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(tool_chunk)}\n\n"
                
                finish_reason = "tool_calls"
            else:
                # Send regular content with true streaming feel
                trimmed_content = remove_tool_json_content(full_content)
                if trimmed_content:
                    # 快速流式输出 - 合理的块大小
                    chunk_size = STREAM_CHUNK_SIZE  # 每次发送n个字符，保持流式感觉但速度快
                    
                    for i in range(0, len(trimmed_content), chunk_size):
                        chunk_content = trimmed_content[i:i + chunk_size]
                        
                        chunk = {
                            "id": f"chatcmpl-{int(time.time() * 1000)}",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": "MBZUAI-IFM/K2-Think",
                            "choices": [{
                                "index": 0,
                                "delta": {
                                    "content": chunk_content
                                },
                                "finish_reason": None
                            }]
                        }
                        
                        yield f"data: {json.dumps(chunk)}\n\n"
                        # 添加极小延迟确保块分别发送
                        await asyncio.sleep(STREAM_DELAY/2)  # 毫秒延迟
        else:
            # No tools - send regular content with fast streaming
            chunk_size = STREAM_CHUNK_SIZE  # 每次发送n个字符，保持流式感觉但速度快
            
            for i in range(0, len(full_content), chunk_size):
                chunk_content = full_content[i:i + chunk_size]
                
                chunk = {
                    "id": f"chatcmpl-{int(time.time() * 1000)}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": "MBZUAI-IFM/K2-Think",
                    "choices": [{
                        "index": 0,
                        "delta": {
                            "content": chunk_content
                        },
                        "finish_reason": None
                    }]
                }
                
                yield f"data: {json.dumps(chunk)}\n\n"
                # 添加极小延迟确保块分别发送
                await asyncio.sleep(STREAM_DELAY/2)  # 毫秒延迟
        
        # 发送结束chunk
        end_chunk = {
            "id": f"chatcmpl-{int(time.time() * 1000)}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "MBZUAI-IFM/K2-Think",
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": finish_reason
            }]
        }
        yield f"data: {json.dumps(end_chunk)}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"流式响应处理错误: {e}")
        error_chunk = {
            "id": f"chatcmpl-{int(time.time() * 1000)}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "MBZUAI-IFM/K2-Think",
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "error"
            }]
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
        yield "data: [DONE]\n\n"

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, auth_request: Request):
    """处理聊天补全请求"""
    # 验证API密钥
    authorization = auth_request.headers.get("Authorization", "")
    if not validate_api_key(authorization):
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "message": "Invalid API key provided",
                    "type": "authentication_error"
                }
            }
        )
    
    try:
        # Process messages with tools - 确保内容被正确转换为字符串
        raw_messages = []
        for msg in request.messages:
            try:
                content = content_to_string(msg.content)
                raw_messages.append({
                    "role": msg.role, 
                    "content": content, 
                    "tool_calls": msg.tool_calls
                })
            except Exception as e:
                logger.error(f"处理消息时出错: {e}, 消息: {msg}")
                # 使用默认值
                raw_messages.append({
                    "role": msg.role, 
                    "content": str(msg.content) if msg.content else "", 
                    "tool_calls": msg.tool_calls
                })
        
        # Check if tools are enabled and present
        has_tools = (TOOL_SUPPORT and 
                    request.tools and 
                    len(request.tools) > 0 and 
                    request.tool_choice != "none")
        
        logger.info(f"🔧 工具调用状态: has_tools={has_tools}, tools_count={len(request.tools) if request.tools else 0}")
        logger.info(f"📥 接收到的原始消息数: {len(raw_messages)}")
        
        # 记录原始消息的角色分布
        role_count = {}
        for msg in raw_messages:
            role = msg.get("role", "unknown")
            role_count[role] = role_count.get(role, 0) + 1
        logger.info(f"📊 原始消息角色分布: {role_count}")
        
        if has_tools:
            processed_messages = process_messages_with_tools(
                raw_messages,
                request.tools,
                request.tool_choice
            )
            logger.info(f"🔄 消息处理完成，原始消息数: {len(raw_messages)}, 处理后消息数: {len(processed_messages)}")
            
            # 记录处理后消息的角色分布
            processed_role_count = {}
            for msg in processed_messages:
                role = msg.get("role", "unknown")
                processed_role_count[role] = processed_role_count.get(role, 0) + 1
            logger.info(f"📊 处理后消息角色分布: {processed_role_count}")
        else:
            processed_messages = raw_messages
            logger.info("⏭️  无工具调用，直接使用原始消息")
        
        # 构建 K2Think 格式的请求体 - 确保所有内容可JSON序列化
        k2think_messages = []
        for msg in processed_messages:
            try:
                # 确保消息内容是字符串
                content = content_to_string(msg.get("content", ""))
                k2think_messages.append({
                    "role": msg["role"], 
                    "content": content
                })
            except Exception as e:
                logger.error(f"构建K2Think消息时出错: {e}, 消息: {msg}")
                # 使用安全的默认值
                k2think_messages.append({
                    "role": msg.get("role", "user"), 
                    "content": str(msg.get("content", ""))
                })
        
        k2think_payload = {
            "stream": request.stream,
            "model": "MBZUAI-IFM/K2-Think",
            "messages": k2think_messages,
            "params": {},
            "tool_servers": [],
            "features": {
                "image_generation": False,
                "code_interpreter": False,
                "web_search": False
            },
            "variables": get_current_datetime_info(),
            "model_item": {
                "id": "MBZUAI-IFM/K2-Think",
                "object": "model",
                "owned_by": "MBZUAI",
                "root": "mbzuai-k2-think-2508",
                "parent": None,
                "status": "active",
                "connection_type": "external",
                "name": "MBZUAI-IFM/K2-Think"
            },
            "background_tasks": {
                "title_generation": True,
                "tags_generation": True
            },
            "chat_id": generate_chat_id(),
            "id": generate_session_id(),
            "session_id": generate_session_id()
        }
        
        # 验证JSON序列化并记录发送到上游的请求
        try:
            # 测试JSON序列化
            json.dumps(k2think_payload, ensure_ascii=False)
            logger.info(f"✅ K2Think请求体JSON序列化验证通过")
        except Exception as e:
            logger.error(f"❌ K2Think请求体JSON序列化失败: {e}")
            # 尝试修复序列化问题
            try:
                k2think_payload = json.loads(json.dumps(k2think_payload, default=str, ensure_ascii=False))
                logger.info("🔧 使用default=str修复了序列化问题")
            except Exception as fix_error:
                logger.error(f"无法修复序列化问题: {fix_error}")
                raise HTTPException(status_code=500, detail="请求数据序列化失败")
        
        logger.info(f"发送到 K2Think 的消息数量: {len(k2think_payload['messages'])}")
        if DEBUG_LOGGING or logger.level <= logging.DEBUG:
            for i, msg in enumerate(k2think_payload['messages']):
                content_preview = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
                logger.debug(f"消息 {i+1} ({msg['role']}): {content_preview}")
        
        # 设置请求头
        headers = {
            "accept": "text/event-stream,application/json" if request.stream else "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {K2THINK_TOKEN}",
            "origin": "https://www.k2think.ai",
            "referer": "https://www.k2think.ai/c/" + k2think_payload["chat_id"],
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0"
        }
        
        if request.stream:
            # 流式响应
            return StreamingResponse(
                process_stream_response_with_tools(k2think_payload, headers, has_tools),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            # 非流式响应
            full_content, token_info = await process_non_stream_response(k2think_payload, headers)
            
            # Handle tool calls for non-streaming
            tool_calls = None
            finish_reason = "stop"
            message_content = full_content
            
            if has_tools:
                tool_calls = extract_tool_invocations(full_content)
                if tool_calls:
                    # Content must be null when tool_calls are present (OpenAI spec)
                    message_content = None
                    finish_reason = "tool_calls"
                    logger.info(f"提取到工具调用: {json.dumps(tool_calls, ensure_ascii=False)}")
                else:
                    # Remove tool JSON from content
                    message_content = remove_tool_json_content(full_content)
                    if not message_content:
                        message_content = full_content  # 保留原内容如果清理后为空
            
            openai_response = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "MBZUAI-IFM/K2-Think",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": message_content,
                        **({"tool_calls": tool_calls} if tool_calls else {})
                    },
                    "finish_reason": finish_reason
                }],
                "usage": token_info
            }
            
            return JSONResponse(content=openai_response)
                
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP错误: {e.response.status_code}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail={
                "error": {
                    "message": f"上游服务错误: {e.response.status_code}",
                    "type": "upstream_error"
                }
            }
        )
    except httpx.TimeoutException:
        logger.error("请求超时")
        raise HTTPException(
            status_code=504,
            detail={
                "error": {
                    "message": "请求超时",
                    "type": "timeout_error"
                }
            }
        )
    except Exception as e:
        logger.error(f"API转发错误: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": str(e),
                    "type": "api_error"
                }
            }
        )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found"}
    )

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    
    # 配置日志级别
    log_level = "debug" if DEBUG_LOGGING else "info"
    
    uvicorn.run(
        app, 
        host=host, 
        port=port, 
        access_log=ENABLE_ACCESS_LOG,
        log_level=log_level
    )