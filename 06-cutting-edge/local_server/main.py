#!/usr/bin/env python3
"""
本地服务器部署应用
使用FastAPI部署LangGraph工作流为Web服务
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import json
import uvicorn
from datetime import datetime
import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict

# 导入配置
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from config import get_llm


class ChatState(TypedDict):
    """聊天状态"""
    messages: List[Dict[str, str]]
    current_input: str
    response: str
    session_id: str
    timestamp: str
    context: Dict[str, Any]


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """聊天响应模型"""
    response: str
    session_id: str
    timestamp: str
    context: Dict[str, Any]


# 创建LangGraph工作流
def create_chat_workflow():
    """创建聊天工作流"""
    
    def process_message(state: ChatState) -> ChatState:
        """处理用户消息"""
        print_step(f"处理消息: {state['current_input'][:50]}...")
        
        # 获取LLM响应
        llm = get_llm()
        messages = state.get("messages", [])
        
        # 构建提示词
        prompt = f"""
你是一个智能助手。请根据用户的输入提供有帮助的回复。

用户消息: {state['current_input']}
历史对话: {messages[-3:] if messages else '无'}

请提供简洁、有用的回复:
"""
        
        try:
            response = llm.invoke(prompt)
            ai_response = response.content
        except Exception as e:
            ai_response = f"抱歉，处理您的请求时出现了错误: {str(e)}"
        
        return {
            "response": ai_response,
            "timestamp": datetime.now().isoformat(),
            "messages": messages + [
                {"role": "user", "content": state["current_input"], "timestamp": state["timestamp"]},
                {"role": "assistant", "content": ai_response, "timestamp": datetime.now().isoformat()}
            ]
        }
    
    def add_context(state: ChatState) -> ChatState:
        """添加上下文信息"""
        print_step("添加上下文信息")
        
        # 更新上下文
        current_context = state.get("context", {})
        current_context.update({
            "message_count": len(state.get("messages", [])),
            "last_active": datetime.now().isoformat(),
            "status": "active"
        })
        
        return {"context": current_context}
    
    # 构建工作流
    workflow = StateGraph(ChatState)
    
    # 添加节点
    workflow.add_node("process_message", process_message)
    workflow.add_node("add_context", add_context)
    
    # 添加边
    workflow.add_edge(START, "process_message")
    workflow.add_edge("process_message", "add_context")
    workflow.add_edge("add_context", END)
    
    # 使用内存检查点
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


def print_step(step: str):
    """打印步骤信息"""
    print(f"🔄 {step}")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)


# 创建FastAPI应用
app = FastAPI(
    title="LangGraph 本地服务器",
    description="使用FastAPI部署的LangGraph聊天服务",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建聊天工作流实例
chat_app = create_chat_workflow()

# 存储WebSocket连接
active_connections: Dict[str, WebSocket] = {}


@app.get("/", response_class=HTMLResponse)
async def root():
    """主页"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LangGraph 聊天服务</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .chat-box { border: 1px solid #ddd; height: 400px; overflow-y: auto; padding: 20px; margin: 20px 0; }
            .input-area { display: flex; gap: 10px; }
            input { flex: 1; padding: 10px; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
            .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
            .user { background: #e3f2fd; text-align: right; }
            .assistant { background: #f5f5f5; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 LangGraph 聊天服务</h1>
            <div id="chatBox" class="chat-box"></div>
            <div class="input-area">
                <input type="text" id="messageInput" placeholder="输入您的消息..." onkeypress="if(event.key==='Enter') sendMessage()">
                <button onclick="sendMessage()">发送</button>
            </div>
        </div>

        <script>
            const ws = new WebSocket(`ws://${window.location.host}/ws`);
            const chatBox = document.getElementById('chatBox');
            const messageInput = document.getElementById('messageInput');
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                addMessage(data.message, 'assistant');
            };
            
            function sendMessage() {
                const message = messageInput.value.trim();
                if (!message) return;
                
                addMessage(message, 'user');
                ws.send(JSON.stringify({message: message}));
                messageInput.value = '';
            }
            
            function addMessage(message, type) {
                const div = document.createElement('div');
                div.className = `message ${type}`;
                div.textContent = message;
                chatBox.appendChild(div);
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
    return html_content


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """聊天接口"""
    try:
        # 生成或使用现有的会话ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # 构建初始状态
        initial_state = {
            "messages": [],
            "current_input": request.message,
            "response": "",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "context": request.context or {}
        }
        
        # 运行工作流
        config = {"configurable": {"thread_id": session_id}}
        result = chat_app.invoke(initial_state, config=config)
        
        return ChatResponse(
            response=result.get("response", ""),
            session_id=session_id,
            timestamp=result.get("timestamp", ""),
            context=result.get("context", {})
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点"""
    await websocket.accept()
    
    # 生成会话ID
    session_id = str(uuid.uuid4())
    active_connections[session_id] = websocket
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # 处理消息
            initial_state = {
                "messages": [],
                "current_input": message_data.get("message", ""),
                "response": "",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "context": message_data.get("context", {})
            }
            
            # 运行工作流
            config = {"configurable": {"thread_id": session_id}}
            result = chat_app.invoke(initial_state, config=config)
            
            # 发送响应
            response = {
                "message": result.get("response", ""),
                "session_id": session_id,
                "timestamp": result.get("timestamp", ""),
                "context": result.get("context", {})
            }
            
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        # 连接断开
        if session_id in active_connections:
            del active_connections[session_id]
    except Exception as e:
        print(f"WebSocket错误: {e}")
        if session_id in active_connections:
            del active_connections[session_id]


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(active_connections),
        "service": "LangGraph Chat Service"
    }


@app.get("/sessions")
async def get_sessions():
    """获取活跃会话"""
    return {
        "active_sessions": list(active_connections.keys()),
        "count": len(active_connections),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    print("🚀 启动LangGraph本地服务器...")
    print("📡 API文档: http://localhost:8000/docs")
    print("💬 聊天界面: http://localhost:8000")
    print("🔌 WebSocket: ws://localhost:8000/ws")
    print("❤️  健康检查: http://localhost:8000/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )