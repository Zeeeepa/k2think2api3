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
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据模型
class Message(BaseModel):
    role: str
    content: str

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
        "limits": httpx.Limits(max_keepalive_connections=20, max_connections=100),
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置
VALID_API_KEY = os.getenv("VALID_API_KEY", "sk-k2think")
K2THINK_API_URL = os.getenv("K2THINK_API_URL", "https://www.k2think.ai/api/chat/completions")
K2THINK_TOKEN = os.getenv("K2THINK_TOKEN")


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

    # 删除第一个<answer>
    answer_start = full_content.find('<answer>')
    if answer_start != -1:
        full_content = full_content[:answer_start] + full_content[answer_start + 8:]

    # 删除最后一个</answer>
    answer_end = full_content.rfind('</answer>')
    if answer_end != -1:
        full_content = full_content[:answer_end] + full_content[answer_end + 9:]

    return full_content.strip()

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
            response = await client.request(method, url, headers=headers, json=json_data, timeout=60.0)
            response.raise_for_status()
            return response
            
    except Exception as e:
        logger.error(f"请求失败: {e}")
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
        
        chunk_size = 50  # 每次发送n个字符
        
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
            await asyncio.sleep(0.05)
        
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
        # 构建 K2Think 格式的请求体
        k2think_payload = {
            "stream": request.stream,
            "model": "MBZUAI-IFM/K2-Think",
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
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
                process_stream_response(k2think_payload, headers),
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
            
            openai_response = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "MBZUAI-IFM/K2-Think",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": full_content
                    },
                    "finish_reason": "stop"
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
    uvicorn.run(app, host=host, port=port, access_log=True)