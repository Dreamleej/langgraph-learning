"""
05-exercises: 基础挑战练习

这个文件包含了LangGraph基础概念的练习题目，帮助您巩固
从基础模块学到的知识。

练习包括：
- 状态管理基础
- 节点和边的基本使用
- 简单的条件路由
- 基础错误处理

每个练习都有详细的要求、提示和解答。
"""

from typing import TypedDict, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
import sys
import os
import time
import random

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import print_step, print_result, print_error

# ================================
 练习 1: 简单计算器工作流
# ================================

def exercise_1_calculator():
    """
    练习 1: 简单计算器工作流
    
    要求:
    1. 创建一个能执行基本运算的工作流
    2. 支持加、减、乘、除四种运算
    3. 包含输入验证
    4. 处理除零错误
    
    状态定义:
    - operation: 运算类型 ('add', 'subtract', 'multiply', 'divide')
    - num1: 第一个数字
    - num2: 第二个数字
    - result: 计算结果
    - error: 错误信息
    """
    
    # 在这里实现你的解决方案
    pass


class CalculatorState(TypedDict):
    operation: str
    num1: float
    num2: float
    result: float
    error: str

def validate_input(state: CalculatorState) -> CalculatorState:
    """验证输入数据"""
    operation = state.get("operation", "")
    num1 = state.get("num1")
    num2 = state.get("num2")
    
    if operation not in ["add", "subtract", "multiply", "divide"]:
        return {"error": f"无效的运算: {operation}"}
    
    if not isinstance(num1, (int, float)):
        return {"error": "num1 必须是数字"}
    
    if not isinstance(num2, (int, float)):
        return {"error": "num2 必须是数字"}
    
    return {}

def perform_calculation(state: CalculatorState) -> CalculatorState:
    """执行计算"""
    operation = state.get("operation", "")
    num1 = state.get("num1", 0)
    num2 = state.get("num2", 0)
    
    try:
        if operation == "add":
            result = num1 + num2
        elif operation == "subtract":
            result = num1 - num2
        elif operation == "multiply":
            result = num1 * num2
        elif operation == "divide":
            if num2 == 0:
                return {"error": "除数不能为零"}
            result = num1 / num2
        else:
            return {"error": f"未知运算: {operation}"}
        
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

def format_result(state: CalculatorState) -> CalculatorState:
    """格式化结果"""
    error = state.get("error", "")
    if error:
        formatted_result = f"计算错误: {error}"
    else:
        num1 = state.get("num1", 0)
        num2 = state.get("num2", 0)
        operation = state.get("operation", "")
        result = state.get("result", 0)
        
        operation_symbols = {
            "add": "+",
            "subtract": "-",
            "multiply": "*",
            "divide": "/"
        }
        
        symbol = operation_symbols.get(operation, operation)
        formatted_result = f"{num1} {symbol} {num2} = {result}"
    
    return {"result": formatted_result}

def route_after_calculation(state: CalculatorState) -> Literal["format", "error"]:
    """计算后的路由"""
    error = state.get("error", "")
    return "error" if error else "format"

def build_calculator_workflow():
    """构建计算器工作流"""
    workflow = StateGraph(CalculatorState)
    
    workflow.add_node("validate", validate_input)
    workflow.add_node("calculate", perform_calculation)
    workflow.add_node("format", format_result)
    
    workflow.set_entry_point("validate")
    workflow.add_edge("validate", "calculate")
    workflow.add_conditional_edges(
        "calculate",
        route_after_calculation,
        {
            "format": "format",
            "error": "format"
        }
    )
    workflow.add_edge("format", END)
    
    return workflow.compile()

def test_calculator():
    """测试计算器工作流"""
    print_step("测试计算器工作流")
    
    app = build_calculator_workflow()
    
    test_cases = [
        {"operation": "add", "num1": 5, "num2": 3},
        {"operation": "subtract", "num1": 10, "num2": 4},
        {"operation": "multiply", "num1": 6, "num2": 7},
        {"operation": "divide", "num1": 20, "num2": 4},
        {"operation": "divide", "num1": 10, "num2": 0},  # 除零错误
        {"operation": "power", "num1": 2, "num2": 3},  # 无效运算
    ]
    
    for test_case in test_cases:
        print(f"\n测试: {test_case}")
        try:
            result = app.invoke(test_case)
            print(f"结果: {result.get('result', 'No result')}")
        except Exception as e:
            print(f"执行失败: {e}")


# ================================
 练习 2: 文本处理工作流
# ================================

def exercise_2_text_processor():
    """
    练习 2: 文本处理工作流
    
    要求:
    1. 实现文本分析功能
    2. 统计字符数、单词数、句子数
    3. 检测文本情感（简单版本）
    4. 生成文本摘要
    
    状态定义:
    - text: 输入文本
    - char_count: 字符数
    - word_count: 单词数
    - sentence_count: 句子数
    - sentiment: 情感分析结果
    - summary: 文本摘要
    """
    
    # 在这里实现你的解决方案
    pass


class TextProcessorState(TypedDict):
    text: str
    char_count: int
    word_count: int
    sentence_count: int
    sentiment: str
    summary: str

def count_characters(state: TextProcessorState) -> TextProcessorState:
    """统计字符数"""
    text = state.get("text", "")
    char_count = len(text)
    return {"char_count": char_count}

def count_words(state: TextProcessorState) -> TextProcessorState:
    """统计单词数"""
    text = state.get("text", "")
    words = text.split()
    word_count = len(words)
    return {"word_count": word_count}

def count_sentences(state: TextProcessorState) -> TextProcessorState:
    """统计句子数"""
    text = state.get("text", "")
    import re
    sentences = re.split(r'[.!?]+', text)
    # 移除空字符串
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences)
    return {"sentence_count": sentence_count}

def analyze_sentiment(state: TextProcessorState) -> TextProcessorState:
    """分析情感"""
    text = state.get("text", "").lower()
    
    positive_words = ["good", "great", "excellent", "amazing", "wonderful", "好", "棒", "优秀", "很好"]
    negative_words = ["bad", "terrible", "awful", "horrible", "worst", "差", "糟糕", "不好", "很差"]
    
    positive_count = sum(1 for word in positive_words if word in text)
    negative_count = sum(1 for word in negative_words if word in text)
    
    if positive_count > negative_count:
        sentiment = "positive"
    elif negative_count > positive_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    return {"sentiment": sentiment}

def generate_summary(state: TextProcessorState) -> TextProcessorState:
    """生成摘要"""
    text = state.get("text", "")
    char_count = state.get("char_count", 0)
    word_count = state.get("word_count", 0)
    sentence_count = state.get("sentence_count", 0)
    sentiment = state.get("sentiment", "neutral")
    
    # 简单的摘要
    summary = f"""
文本分析结果:
- 字符数: {char_count}
- 单词数: {word_count}  
- 句子数: {sentence_count}
- 情感倾向: {sentiment}
""".strip()
    
    return {"summary": summary}

def build_text_processor_workflow():
    """构建文本处理工作流"""
    workflow = StateGraph(TextProcessorState)
    
    workflow.add_node("count_chars", count_characters)
    workflow.add_node("count_words", count_words)
    workflow.add_node("count_sentences", count_sentences)
    workflow.add_node("analyze_sentiment", analyze_sentiment)
    workflow.add_node("generate_summary", generate_summary)
    
    workflow.set_entry_point("count_chars")
    workflow.add_edge("count_chars", "count_words")
    workflow.add_edge("count_words", "count_sentences")
    workflow.add_edge("count_sentences", "analyze_sentiment")
    workflow.add_edge("analyze_sentiment", "generate_summary")
    workflow.add_edge("generate_summary", END)
    
    return workflow.compile()

def test_text_processor():
    """测试文本处理工作流"""
    print_step("测试文本处理工作流")
    
    app = build_text_processor_workflow()
    
    test_texts = [
        "This is a great example of text processing!",
        "The weather is terrible today.",
        "I love learning new technologies like LangGraph.",
        "这是一段中文文本，用来测试文本处理功能。"
    ]
    
    for text in test_texts:
        print(f"\n测试文本: {text}")
        state = {"text": text}
        try:
            result = app.invoke(state)
            print("分析结果:")
            print(result.get("summary", "No summary"))
        except Exception as e:
            print(f"执行失败: {e}")


# ================================
 练习 3: 简单待办事项管理
# ================================

def exercise_3_todo_manager():
    """
    练习 3: 简单待办事项管理
    
    要求:
    1. 添加待办事项
    2. 标记完成状态
    3. 按优先级排序
    4. 生成待办事项列表
    
    状态定义:
    - action: 操作类型 ('add', 'complete', 'list', 'sort')
    - todo_text: 待办事项文本
    - priority: 优先级 (1-5)
    - todos: 待办事项列表
    - completed: 完成的待办事项列表
    - output: 输出结果
    """
    
    # 在这里实现你的解决方案
    pass


class TodoManagerState(TypedDict):
    action: str
    todo_text: str
    priority: int
    todos: List[Dict[str, Any]]
    completed: List[Dict[str, Any]]
    output: str

def add_todo(state: TodoManagerState) -> TodoManagerState:
    """添加待办事项"""
    todos = state.get("todos", [])
    todo_text = state.get("todo_text", "")
    priority = state.get("priority", 3)
    
    new_todo = {
        "id": len(todos) + 1,
        "text": todo_text,
        "priority": priority,
        "created_at": time.time(),
        "completed": False
    }
    
    todos.append(new_todo)
    return {"todos": todos}

def complete_todo(state: TodoManagerState) -> TodoManagerState:
    """标记待办事项完成"""
    todos = state.get("todos", [])
    todo_text = state.get("todo_text", "")
    completed = state.get("completed", [])
    
    # 找到匹配的待办事项
    for i, todo in enumerate(todos):
        if todo["text"] == todo_text and not todo["completed"]:
            todos[i]["completed"] = True
            todos[i]["completed_at"] = time.time()
            completed.append(todos[i])
            break
    
    return {"todos": todos, "completed": completed}

def sort_todos(state: TodoManagerState) -> TodoManagerState:
    """按优先级排序待办事项"""
    todos = state.get("todos", [])
    
    # 按优先级排序（1最高，5最低）
    sorted_todos = sorted(todos, key=lambda x: x["priority"])
    
    return {"todos": sorted_todos}

def generate_todo_output(state: TodoManagerState) -> TodoManagerState:
    """生成待办事项输出"""
    action = state.get("action", "")
    todos = state.get("todos", [])
    completed = state.get("completed", [])
    
    if action == "add":
        output = f"待办事项已添加: {state.get('todo_text', '')}"
    elif action == "complete":
        output = f"待办事项已完成: {state.get('todo_text', '')}"
    elif action == "list":
        pending_todos = [todo for todo in todos if not todo["completed"]]
        if pending_todos:
            output = "待办事项列表:\n"
            for i, todo in enumerate(pending_todos, 1):
                output += f"{i}. [{todo['priority']}] {todo['text']}\n"
        else:
            output = "没有待办事项"
    else:  # action == "sort"
        output = "待办事项已按优先级排序"
        for i, todo in enumerate(todos, 1):
            status = "✓" if todo["completed"] else "○"
            output += f"\n{i}. {status} [{todo['priority']}] {todo['text']}"
    
    return {"output": output}

def route_todo_action(state: TodoManagerState) -> Literal["add", "complete", "sort", "output"]:
    """路由待办事项操作"""
    action = state.get("action", "")
    return action if action in ["add", "complete", "sort"] else "output"

def build_todo_manager_workflow():
    """构建待办事项管理工作流"""
    workflow = StateGraph(TodoManagerState)
    
    workflow.add_node("add", add_todo)
    workflow.add_node("complete", complete_todo)
    workflow.add_node("sort", sort_todos)
    workflow.add_node("output", generate_todo_output)
    
    workflow.set_entry_point("add")  # 默认入口，实际根据路由确定
    workflow.add_conditional_edges(
        "add",
        route_todo_action,
        {
            "add": "add",
            "complete": "complete",
            "sort": "sort",
            "output": "output"
        }
    )
    workflow.add_conditional_edges(
        "complete",
        route_todo_action,
        {
            "add": "add",
            "complete": "complete",
            "sort": "sort",
            "output": "output"
        }
    )
    workflow.add_conditional_edges(
        "sort",
        route_todo_action,
        {
            "add": "add",
            "complete": "complete",
            "sort": "sort",
            "output": "output"
        }
    )
    workflow.add_edge("output", END)
    
    return workflow.compile()

def test_todo_manager():
    """测试待办事项管理工作流"""
    print_step("测试待办事项管理工作流")
    
    app = build_todo_manager_workflow()
    
    # 添加待办事项
    print("\n1. 添加待办事项:")
    state1 = {
        "action": "add",
        "todo_text": "学习LangGraph",
        "priority": 1,
        "todos": [],
        "completed": []
    }
    result1 = app.invoke(state1)
    print(result1.get("output", ""))
    
    state2 = {
        "action": "add",
        "todo_text": "完成项目报告",
        "priority": 2,
        "todos": result1.get("todos", []),
        "completed": []
    }
    result2 = app.invoke(state2)
    print(result2.get("output", ""))
    
    # 列出待办事项
    print("\n2. 列出待办事项:")
    state3 = {
        "action": "list",
        "todos": result2.get("todos", []),
        "completed": result2.get("completed", [])
    }
    result3 = app.invoke(state3)
    print(result3.get("output", ""))
    
    # 标记完成
    print("\n3. 标记完成:")
    state4 = {
        "action": "complete",
        "todo_text": "学习LangGraph",
        "todos": result3.get("todos", []),
        "completed": result3.get("completed", [])
    }
    result4 = app.invoke(state4)
    print(result4.get("output", ""))


# ================================
 主测试函数
# ================================

def run_basic_exercises():
    """运行所有基础练习"""
    print("🎯 LangGraph 基础挑战练习")
    print("=" * 60)
    
    while True:
        print("\n请选择练习:")
        print("1. 计算器工作流")
        print("2. 文本处理工作流")
        print("3. 待办事项管理")
        print("4. 运行所有练习")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-4): ").strip()
        
        if choice == "1":
            test_calculator()
        elif choice == "2":
            test_text_processor()
        elif choice == "3":
            test_todo_manager()
        elif choice == "4":
            print("\n" + "="*50)
            print("运行所有基础练习")
            print("="*50)
            test_calculator()
            print("\n" + "-"*30)
            test_text_processor()
            print("\n" + "-"*30)
            test_todo_manager()
        elif choice == "0":
            print_step("感谢完成基础练习！")
            break
        else:
            print_error("无效选择，请重试")
    
    print_result("基础挑战练习完成！")


# ================================
 学习提示和答案检查
# ================================

def check_exercise_solutions():
    """检查练习答案"""
    print_step("练习解答检查")
    
    print("""
练习解答说明:

1. 计算器工作流
   - 实现了完整的四则运算
   - 包含输入验证
   - 处理除零错误
   - 结果格式化

2. 文本处理工作流  
   - 统计字符、单词、句子数
   - 简单情感分析
   - 生成结构化摘要

3. 待办事项管理
   - 支持添加、完成、列表功能
   - 优先级排序
   - 状态跟踪

每个练习都展示了LangGraph的核心概念：
- 状态定义和管理
- 节点函数实现
- 条件路由
- 工作流构建
    """)


if __name__ == "__main__":
    run_basic_exercises()
    
    # 提供查看解答的选项
    show_solutions = input("\n是否查看练习解答提示？(y/n): ").strip().lower()
    if show_solutions in ['y', 'yes']:
        check_exercise_solutions()