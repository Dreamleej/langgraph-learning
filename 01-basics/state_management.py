"""
01-basics: 状态管理详解

本示例深入讲解LangGraph中状态管理的核心概念。
状态是LangGraph工作流的灵魂，理解状态管理是掌握LangGraph的关键。

学习要点：
1. 状态的数据结构设计
2. 状态更新和传递
3. 状态检查和验证
4. 状态持久化概念
5. 复杂状态的使用
"""

from typing import TypedDict, List, Dict, Optional, Annotated
from langgraph.graph import StateGraph, END
import sys
import os
from datetime import datetime

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import print_step, print_result, print_error

# 1. 基础状态定义
class BasicState(TypedDict):
    """
    基础状态示例
    展示简单的键值对状态
    """
    message: str
    counter: int
    timestamp: str

# 2. 复杂状态定义
class ComplexState(TypedDict):
    """
    复杂状态示例
    展示嵌套数据结构和集合类型
    """
    user_info: Dict[str, str]
    messages: List[Dict[str, str]]
    metadata: Dict[str, any]
    processed_count: int
    errors: List[str]

# 3. 带验证的状态
class ValidatedState(TypedDict):
    """
    带验证的状态示例
    展示如何进行状态验证
    """
    email: str
    age: int
    username: str
    is_valid: bool

# 4. 状态管理工具函数
class StateManager:
    """
    状态管理工具类
    提供常用状态操作方法
    """
    
    @staticmethod
    def update_timestamp(state: BasicState) -> BasicState:
        """更新时间戳"""
        return {"timestamp": datetime.now().isoformat()}
    
    @staticmethod
    def increment_counter(state: BasicState, increment: int = 1) -> BasicState:
        """增加计数器"""
        current = state.get("counter", 0)
        return {"counter": current + increment}
    
    @staticmethod
    def add_message(state: ComplexState, role: str, content: str) -> ComplexState:
        """添加消息到消息列表"""
        messages = state.get("messages", [])
        new_message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        messages.append(new_message)
        return {"messages": messages}
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """简单的邮箱验证"""
        return "@" in email and "." in email.split("@")[-1]
    
    @staticmethod
    def validate_age(age: int) -> bool:
        """年龄验证"""
        return 0 <= age <= 150

# 5. 基础状态操作节点
def initialize_state(state: BasicState) -> BasicState:
    """
    初始化基础状态
    """
    print_step("初始化基础状态")
    
    updates = {
        "message": "状态已初始化",
        "counter": 0,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"初始化数据: {updates}")
    return updates

def update_state(state: BasicState) -> BasicState:
    """
    更新状态演示
    """
    print_step("更新状态")
    
    # 使用StateManger工具
    timestamp_update = StateManager.update_timestamp(state)
    counter_update = StateManager.increment_counter(state, 5)
    
    message = f"状态已更新 - 计数器: {counter_update['counter']}, 时间: {timestamp_update['timestamp']}"
    
    updates = {
        "message": message,
        **timestamp_update,
        **counter_update
    }
    
    print(f"状态更新: {updates}")
    return updates

# 6. 复杂状态操作节点
def process_complex_state(state: ComplexState) -> ComplexState:
    """
    处理复杂状态
    """
    print_step("处理复杂状态")
    
    # 添加系统消息
    message_update = StateManager.add_message(
        state, 
        "system", 
        "开始处理复杂状态"
    )
    
    # 更新处理计数
    processed_count = state.get("processed_count", 0) + 1
    
    # 更新元数据
    metadata = state.get("metadata", {})
    metadata["last_processed"] = datetime.now().isoformat()
    metadata["processing_step"] = processed_count
    
    updates = {
        **message_update,
        "processed_count": processed_count,
        "metadata": metadata
    }
    
    print(f"复杂状态处理完成: {updates}")
    return updates

def analyze_messages(state: ComplexState) -> ComplexState:
    """
    分析消息列表
    """
    print_step("分析消息")
    
    messages = state.get("messages", [])
    user_messages = [msg for msg in messages if msg.get("role") == "user"]
    system_messages = [msg for msg in messages if msg.get("role") == "system"]
    
    analysis = {
        "total_messages": len(messages),
        "user_messages": len(user_messages),
        "system_messages": len(system_messages)
    }
    
    # 添加分析结果
    message_update = StateManager.add_message(
        state,
        "analysis",
        f"消息分析结果: {analysis}"
    )
    
    print(f"消息分析: {analysis}")
    return message_update

# 7. 验证状态节点
def validate_user_data(state: ValidatedState) -> ValidatedState:
    """
    验证用户数据
    """
    print_step("验证用户数据")
    
    email = state.get("email", "")
    age = state.get("age", 0)
    username = state.get("username", "")
    
    errors = []
    
    # 验证邮箱
    if not StateManager.validate_email(email):
        errors.append("邮箱格式无效")
    
    # 验证年龄
    if not StateManager.validate_age(age):
        errors.append("年龄无效 (应在0-150之间)")
    
    # 验证用户名
    if len(username) < 3:
        errors.append("用户名长度至少3个字符")
    
    is_valid = len(errors) == 0
    
    updates = {
        "is_valid": is_valid,
    }
    
    if not is_valid:
        print(f"验证失败，错误: {errors}")
    else:
        print_result("用户数据验证通过")
    
    return updates

# 8. 构建不同的状态图
def build_basic_state_graph():
    """构建基础状态图"""
    print_step("构建基础状态图")
    
    workflow = StateGraph(BasicState)
    
    workflow.add_node("initialize", initialize_state)
    workflow.add_node("update", update_state)
    
    workflow.set_entry_point("initialize")
    workflow.add_edge("initialize", "update")
    workflow.add_edge("update", END)
    
    return workflow.compile()

def build_complex_state_graph():
    """构建复杂状态图"""
    print_step("构建复杂状态图")
    
    workflow = StateGraph(ComplexState)
    
    workflow.add_node("process", process_complex_state)
    workflow.add_node("analyze", analyze_messages)
    
    workflow.set_entry_point("process")
    workflow.add_edge("process", "analyze")
    workflow.add_edge("analyze", END)
    
    return workflow.compile()

def build_validation_graph():
    """构建验证状态图"""
    print_step("构建验证状态图")
    
    workflow = StateGraph(ValidatedState)
    
    workflow.add_node("validate", validate_user_data)
    
    workflow.set_entry_point("validate")
    workflow.add_edge("validate", END)
    
    return workflow.compile()

# 9. 演示函数
def demo_basic_state():
    """演示基础状态管理"""
    print_step("基础状态管理演示")
    
    app = build_basic_state_graph()
    
    initial_state = {
        "message": "",
        "counter": 0,
        "timestamp": ""
    }
    
    print(f"初始状态: {initial_state}")
    
    result = app.invoke(initial_state)
    print_result(f"最终状态: {result}")

def demo_complex_state():
    """演示复杂状态管理"""
    print_step("复杂状态管理演示")
    
    app = build_complex_state_graph()
    
    initial_state = {
        "user_info": {"name": "张三", "id": "12345"},
        "messages": [
            {"role": "user", "content": "你好", "timestamp": "2024-01-01T10:00:00"}
        ],
        "metadata": {"version": "1.0"},
        "processed_count": 0,
        "errors": []
    }
    
    print(f"初始复杂状态: {initial_state}")
    
    result = app.invoke(initial_state)
    print_result(f"最终复杂状态: {result}")

def demo_validation():
    """演示状态验证"""
    print_step("状态验证演示")
    
    app = build_validation_graph()
    
    # 测试有效数据
    valid_data = {
        "email": "user@example.com",
        "age": 25,
        "username": "validuser",
        "is_valid": False
    }
    
    print("测试有效数据:")
    print(f"输入: {valid_data}")
    result1 = app.invoke(valid_data)
    print(f"输出: {result1}\n")
    
    # 测试无效数据
    invalid_data = {
        "email": "invalid-email",
        "age": 200,
        "username": "ab",
        "is_valid": False
    }
    
    print("测试无效数据:")
    print(f"输入: {invalid_data}")
    result2 = app.invoke(invalid_data)
    print(f"输出: {result2}")

def demo_state_persistence():
    """演示状态持久化概念"""
    print_step("状态持久化概念演示")
    
    print("""
状态持久化在LangGraph中非常重要：
    
1. 检查点(Checkpoints): 在关键节点保存状态
2. 恢复(Resume): 从检查点恢复执行
3. 内存管理: 处理长时间运行的工作流
4. 错误恢复: 从失败点重新开始
    
实际应用场景：
- 长时间运行的AI任务
- 需要人工介入的复杂工作流
- 分布式系统中的状态同步
- 用户会话管理
    
在后续的高级模块中，我们将深入学习如何实现这些功能。
    """)

# 主程序
if __name__ == "__main__":
    print("📊 LangGraph 状态管理学习程序")
    print("=" * 50)
    
    while True:
        print("\n请选择演示:")
        print("1. 基础状态管理")
        print("2. 复杂状态管理")
        print("3. 状态验证")
        print("4. 状态持久化概念")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-4): ").strip()
        
        if choice == "1":
            demo_basic_state()
        elif choice == "2":
            demo_complex_state()
        elif choice == "3":
            demo_validation()
        elif choice == "4":
            demo_state_persistence()
        elif choice == "0":
            print_step("感谢学习状态管理！")
            break
        else:
            print_error("无效选择，请重试")
    
    print_result("状态管理学习完成！")