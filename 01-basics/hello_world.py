"""
01-basics: Hello World - 第一个LangGraph程序

这是您学习LangGraph的第一个示例！
我们将创建一个简单的问候程序，展示LangGraph的基本结构。

学习要点：
1. 如何定义状态类型
2. 如何创建简单的节点
3. 如何构建和编译状态图
4. 如何运行工作流
"""

from langgraph.graph.state import CompiledStateGraph, StateGraph
from typing import TypedDict
from langgraph.graph import StateGraph, END
import sys
import os

# 添加父目录到路径，以便导入utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import print_step, print_result, print_error

# 1. 定义状态类型
class GreetingState(TypedDict):
    """
    问候工作流的状态定义
    
    这里我们定义了两个字段：
    - name: 要问候的人名
    - greeting: 生成的问候语
    """
    name: str
    greeting: str

# 2. 定义节点函数
def create_greeting(state: GreetingState) -> GreetingState:
    """
    创建问候语的节点
    
    输入：包含name的状态
    输出：更新了greeting的状态
    
    这是LangGraph节点的标准写法：
    1. 接收state作为参数
    2. 处理数据
    3. 返回更新后的state
    """
    name: str = state.get("name", "世界")
    
    # 创建简单的问候语
    greeting = f"你好，{name}！欢迎使用LangGraph！"
    
    print_step(f"生成问候语: {greeting}")
    
    return {"greeting": greeting}

def display_greeting(state: GreetingState) -> GreetingState:
    """
    显示问候语的节点
    
    这个节点负责将生成的问候语显示出来
    在实际应用中，这里可能是发送消息、保存数据等操作
    """
    greeting = state.get("greeting", "")
    
    print_result(f"最终问候语: {greeting}")
    
    # 我们不需要修改状态，直接返回
    return state

# 3. 构建状态图
def build_greeting_graph():
    """
    构建问候工作流的状态图
    
    这里展示了LangGraph的核心概念：
    1. 创建StateGraph实例
    2. 添加节点
    3. 添加边（定义执行顺序）
    4. 编译图
    """
    
    print_step("构建LangGraph状态图")
    
    # 创建状态图实例
    workflow: StateGraph = StateGraph(GreetingState)
    
    # 添加节点
    workflow.add_node("create_greeting", create_greeting)
    workflow.add_node("display_greeting", display_greeting)
    
    # 设置入口点
    workflow.set_entry_point("create_greeting")
    
    # 添加边（定义执行顺序）
    workflow.add_edge("create_greeting", "display_greeting")
    workflow.add_edge("display_greeting", END)
    
    # 编译状态图
    app = workflow.compile()
    
    print_result("状态图构建完成！")
    print("图结构: create_greeting -> display_greeting -> END")
    
    return app

# 4. 运行工作流
def run_demo():
    """
    运行Hello World演示
    """
    print_step("开始LangGraph Hello World演示")
    
    # 构建状态图
    app = build_greeting_graph()
    
    # 准备初始状态
    initial_state = {
        "name": "LangGraph学习者",
        "greeting": ""
    }
    
    print(f"初始状态: {initial_state}")
    
    try:
        # 运行工作流(阻塞式)
        result = app.invoke(initial_state)
        
        print_step("工作流执行完成")
        print(f"最终状态: {result}")
        
    except Exception as e:
        print_error(f"执行失败: {e}")

# 5. 交互式演示
def interactive_demo():
    """
    交互式演示，让用户输入名字和语言
    """
    print_step("交互式LangGraph演示")
    
    app: CompiledStateGraph = build_greeting_graph()
    
    print("\n请输入以下信息：")
    name = input("你的名字: ").strip()
    if not name:
        name = "朋友"
    
    initial_state = {
        "name": name,
        "greeting": ""
    }
    
    try:
        result = app.invoke(initial_state)
        print_step(f"个性化问候完成！")
        
    except Exception as e:
        print_error(f"交互式演示失败: {e}")

# 6. 流式执行演示
def streaming_demo():
    """
    演示LangGraph的流式执行功能
    """
    print_step("流式执行演示")
    
    app = build_greeting_graph()
    
    initial_state = {
        "name": "流式用户",
        "greeting": ""
    }
    
    print("开始流式执行(流式)...")
    
    try:
        for output in app.stream(initial_state):
            print(f"流式输出: {output}")
            print("-" * 30)
        
        print_result("流式执行完成！")
        
    except Exception as e:
        print_error(f"流式执行失败: {e}")

# 主程序
if __name__ == "__main__":
    print("🎉 LangGraph Hello World 学习程序")
    print("=" * 50)
    
    while True:
        print("请选择演示模式:")
        print("1. 基本演示")
        print("2. 交互式演示")
        print("3. 流式执行演示")
        print("0. 退出")
        
        choice = input("请输入选择 (0-3): ").strip()
        
        if choice == "1":
            run_demo()
        elif choice == "2":
            interactive_demo()
        elif choice == "3":
            streaming_demo()
        elif choice == "0":
            print_step("感谢使用！")
            break
        else:
            print_error("无效选择，请重试")
    
    print_result("Hello World学习完成！")