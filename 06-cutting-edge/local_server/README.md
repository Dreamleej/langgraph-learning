# 🖥️ 本地服务器部署

## 📋 概述

本案例展示如何将LangGraph工作流部署为本地Web服务器，提供REST API和WebSocket接口。

## 🛠️ 技术栈

- **FastAPI**: 现代Python Web框架
- **WebSocket**: 实时双向通信
- **LangGraph**: AI工作流引擎
- **Uvicorn**: ASGI服务器
- **Pydantic**: 数据验证和序列化

## 🚀 功能特性

### 🌐 REST API
- `POST /chat` - 同步聊天接口
- `GET /health` - 健康检查
- `GET /sessions` - 活跃会话列表
- `GET /docs` - 自动API文档

### 🔌 WebSocket
- 实时双向通信
- 会话管理
- 连接状态跟踪

### 🎨 Web界面
- 内置聊天界面
- 实时消息显示
- 响应式设计

## 🏃‍♂️ 快速开始

### 1. 安装依赖
```bash
pip install fastapi uvicorn python-multipart websockets
```

### 2. 启动服务
```bash
cd 06-cutting-edge/local_server
python main.py
```

### 3. 访问服务
- **Web界面**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 📡 API使用示例

### REST API调用
```python
import requests

# 发送聊天消息
response = requests.post("http://localhost:8000/chat", json={
    "message": "你好，介绍一下LangGraph",
    "context": {"user_type": "developer"}
})

print(response.json())
```

### WebSocket连接
```python
import asyncio
import websockets
import json

async def chat_with_websocket():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # 发送消息
        await websocket.send(json.dumps({
            "message": "LangGraph是什么？"
        }))
        
        # 接收响应
        response = await websocket.recv()
        print(json.loads(response))

asyncio.run(chat_with_websocket())
```

## 🏗️ 架构设计

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │  FastAPI App    │    │  LangGraph App  │
│                 │    │                 │    │                 │
│  - HTML界面     │◄──►│  - REST API     │◄──►│  - 工作流引擎   │
│  - WebSocket    │    │  - WebSocket    │    │  - 状态管理     │
│  - JavaScript   │    │  - 中间件       │    │  - 检查点       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 核心组件

### 1. ChatState
```python
class ChatState(TypedDict):
    messages: List[Dict[str, str]]
    current_input: str
    response: str
    session_id: str
    timestamp: str
    context: Dict[str, Any]
```

### 2. 工作流节点
- **process_message**: 处理用户消息
- **add_context**: 添加上下文信息

### 3. API端点
- **聊天处理**: `/chat`
- **实时通信**: `/ws`
- **系统监控**: `/health`, `/sessions`

## 🎯 使用场景

### 💬 聊天机器人
- 客服系统
- 智能助手
- 对话式应用

### 🔄 实时处理
- 流式数据分析
- 实时推荐
- 监控告警

### 🌐 Web服务
- API网关
- 微服务架构
- 事件驱动系统

## 📊 性能优化

### 异步处理
```python
@app.post("/chat")
async def chat(request: ChatRequest):
    # 异步处理消息
    result = await process_async(request)
    return result
```

### 连接池管理
```python
# 活跃连接管理
active_connections: Dict[str, WebSocket] = {}

# 自动清理断开的连接
def cleanup_connections():
    # 定期清理逻辑
    pass
```

### 负载均衡
- 支持水平扩展
- 会话亲和性
- 健康检查

## 🔒 安全考虑

### 输入验证
- Pydantic模型验证
- SQL注入防护
- XSS攻击防护

### 认证授权
```python
# 添加认证中间件
from fastapi import Depends, HTTPException, status

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # 验证token逻辑
    pass
```

### 限流控制
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request, chat_request: ChatRequest):
    # 限流逻辑
    pass
```

## 📝 部署建议

### Docker部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 生产环境配置
```python
# 生产环境启动
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    workers=4,
    reload=False,
    access_log=True,
    log_level="info"
)
```

## 🐛 调试技巧

### 日志配置
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 错误处理
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return {
        "error": str(exc),
        "timestamp": datetime.now().isoformat()
    }
```

## 🎉 总结

本案例展示了如何将LangGraph工作流部署为生产级的Web服务，包括：

✅ REST API和WebSocket支持  
✅ 实时通信和会话管理  
✅ 异步处理和性能优化  
✅ 安全考虑和生产部署  

这为构建实际的AI应用提供了完整的解决方案！