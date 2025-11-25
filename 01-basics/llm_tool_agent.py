



import os
from datetime import datetime
from typing import Annotated, Literal, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
import sys
import os

# 添加父目录到路径，以便导入utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import print_step, print_result, print_error

# ==========================================
# 1. 配置硅基流动 (SiliconFlow)
# ==========================================
# 替换为你提供的 Key
SILICON_FLOW_API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = "https://api.siliconflow.cn/v1"

# 这里选择一个硅基流动支持的模型，例如 Qwen2.5 或 DeepSeek
MODEL_NAME = os.getenv("OPENAI_API_MODEL")

# 初始化 LLM
llm = ChatOpenAI(
    base_url=BASE_URL,
    api_key=SILICON_FLOW_API_KEY,
    model=MODEL_NAME,
    temperature=0,
    streaming=True # 开启流式
)

# ==========================================
# 2. 定义工具 (Tools)
# ==========================================
@tool
def get_current_time(format: str = "%Y-%m-%d %H:%M:%S"):
    """
    获取当前的具体时间。
    """
    return datetime.now().strftime(format)

tools = [get_current_time]

# 将工具绑定到 LLM
llm_with_tools = llm.bind_tools(tools)

# ==========================================
# 3. 定义状态 (State)
# ==========================================
class State(TypedDict):
    # messages 列表会自动追加新的消息 (add_messages reducer)
    messages: Annotated[list[BaseMessage], add_messages]

# ==========================================
# 4. 定义节点 (Nodes)
# ==========================================
def agent_node(state: State):
    """
    Agent 节点：负责调用 LLM 生成回复或决定调用工具
    """
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# 构建工具执行节点 (LangGraph 预置节点)
tool_node = ToolNode(tools)

# ==========================================
# 5. 构建图 (Graph)
# ==========================================
workflow = StateGraph(State)

# 添加节点
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

# 添加边 (Edges)
# 1. 从开始 -> Agent
workflow.add_edge(START, "agent")

# 2. 条件边：Agent 决定是结束还是调用工具
# tools_condition 是 LangGraph 预置的逻辑：如果 LLM 返回 tool_calls，则去 tools 节点，否则去 END
workflow.add_conditional_edges(
    "agent",
    tools_condition,
)

# 3. 从工具 -> 回到 Agent (让 LLM 根据工具结果生成最终回答)
workflow.add_edge("tools", "agent")

# 编译图
app = workflow.compile()

# ==========================================
# 6. 运行并流式输出 (Execution & Streaming)
# ==========================================
if __name__ == "__main__":
    user_input = "现在几点了？请告诉我具体时间。"
    
    print(f"User: {user_input}\n")
    print("Agent (Streaming): ", end="", flush=True)

    inputs = {"messages": [HumanMessage(content=user_input)]}

    # stream_mode="updates" 会返回图的状态更新
    # 为了实现打字机效果，我们使用 stream 事件流
    for event in app.stream(inputs, stream_mode="values"):
        # 获取当前状态中最新的一条消息
        last_message = event["messages"][-1]
        
        # 如果是 AI 的消息，且不是工具调用请求，则打印内容
        # 注意：LangGraph 的 stream 默认是按步骤返回完整消息。
        # 若要实现 token 级别的流式 (打字机效果)，通常结合 astream_events，
        # 但为了代码简洁，这里演示如何处理最终回复。
        
        pass # 这里主要用于通过状态变化驱动流程
        
    # 为了演示 Token 级别的流式输出（即真正的流式回答），
    # 我们通常使用 astream_events (异步) 或者在 invoke 内部捕获流。
    # 下面演示最简单直观的方法：使用 stream 捕获最后一步的生成。
    
    # 重新运行一个更底层的流式打印逻辑 (Token-by-Token):
    print("\n--- 重新演示 Token 级流式输出 ---\n")
    
    # 注意：LangGraph 的 .stream() 返回的是状态快照。
    # 要在 Console 中看到 token 一个个蹦出来，最好的方式是监听 llm 的调用。
    # 但在 LangGraph 抽象层上，我们这样做：
    
    messages = [HumanMessage(content=user_input)]
    current_state = inputs
    
    # 使用 app.stream_events (需要 async，这里用同步包装或者简化逻辑)
    # 这是一个简化的同步流式处理逻辑，专用于展示最终回复：
    
    import asyncio
    
    async def run_stream():
        print(f"User: {user_input}")
        print("Thinking...", end="\r")
        
        async for event in app.astream_events(inputs, version="v1"):
            kind = event["event"]

            # print_step(f"Event: {kind}")
            
            # 监听 LLM 的流式输出块
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    # 清除 "Thinking..." 并开始打印
                    print(content, end="", flush=True)
            
            # 可选：监听工具调用
            elif kind == "on_tool_start":
                print(f"\n[调用工具: {event['name']}] ... ", end="")
            elif kind == "on_tool_end":
                print("完成。\nResponse: ", end="")

    asyncio.run(run_stream())
    print("\n")