"""
01-basics: 节点和边的详解

本示例深入讲解LangGraph中节点和边的各种使用方式。
节点和边是构建复杂工作流的基础组件。

学习要点：
1. 不同类型的节点
2. 条件边的使用
3. 循环和递归结构
4. 复杂工作流设计
5. 节点参数和返回值
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
import sys
import os
import random

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import print_step, print_result, print_error

# 1. 状态定义
class WorkflowState(TypedDict):
    """
    工作流状态
    """
    current_step: str
    data: str
    results: list
    counter: int
    condition_met: bool
    loop_count: int

# 2. 基础节点类型

# 数据处理节点
def data_processor(state: WorkflowState) -> WorkflowState:
    """
    数据处理节点 - 最基础的节点类型
    接收数据，处理，返回结果
    """
    print_step(f"数据处理节点 - 当前步骤: {state.get('current_step', 'unknown')}")
    
    # 获取或初始化数据
    data = state.get("data", "初始数据")
    counter = state.get("counter", 0)
    
    # 处理数据
    processed_data = f"处理后的数据: {data} (步骤 {counter + 1})"
    results = state.get("results", [])
    results.append(processed_data)
    
    print(f"处理结果: {processed_data}")
    
    return {
        "data": processed_data,
        "results": results,
        "counter": counter + 1,
        "current_step": "data_processing"
    }

# 验证节点
def validator(state: WorkflowState) -> WorkflowState:
    """
    验证节点 - 检查条件或数据
    """
    print_step("验证节点")
    
    counter = state.get("counter", 0)
    
    # 简单的验证逻辑
    condition_met = counter >= 3
    
    print(f"验证结果: counter={counter}, condition_met={condition_met}")
    
    return {
        "condition_met": condition_met,
        "current_step": "validation"
    }

# 转换节点
def transformer(state: WorkflowState) -> WorkflowState:
    """
    转换节点 - 转换数据格式或结构
    """
    print_step("转换节点")
    
    data = state.get("data", "")
    counter = state.get("counter", 0)
    
    # 转换数据
    transformed_data = {
        "original": data,
        "uppercase": data.upper() if data else "",
        "length": len(data),
        "step": counter
    }
    
    print(f"转换结果: {transformed_data}")
    
    return {
        "data": str(transformed_data),
        "current_step": "transformation"
    }

# 汇总节点
def aggregator(state: WorkflowState) -> WorkflowState:
    """
    汇总节点 - 汇总所有结果
    """
    print_step("汇总节点")
    
    results = state.get("results", [])
    counter = state.get("counter", 0)
    
    summary = f"""
工作流执行完成！
- 总步骤数: {counter}
- 结果数量: {len(results)}
- 所有结果: {results}
"""
    
    print_result(summary)
    
    return {
        "data": summary,
        "current_step": "aggregation"
    }

# 循环控制节点
def loop_controller(state: WorkflowState) -> WorkflowState:
    """
    循环控制节点 - 管理循环逻辑
    """
    print_step("循环控制节点")
    
    loop_count = state.get("loop_count", 0)
    condition_met = state.get("condition_met", False)
    
    # 决定是否继续循环
    if condition_met or loop_count >= 5:
        print("循环结束条件已满足")
        return {
            "current_step": "loop_end",
            "loop_count": loop_count
        }
    else:
        print(f"继续循环，当前循环次数: {loop_count}")
        return {
            "current_step": "loop_continue",
            "loop_count": loop_count + 1
        }

# 错误处理节点
def error_handler(state: WorkflowState) -> WorkflowState:
    """
    错误处理节点 - 处理工作流中的错误
    """
    print_step("错误处理节点")
    
    data = state.get("data", "")
    
    error_data = f"错误已处理 - 原数据: {data}"
    
    print_result(error_data)
    
    return {
        "data": error_data,
        "current_step": "error_handled"
    }

# 3. 条件路由函数
def should_continue(state: WorkflowState) -> Literal["continue", "end"]:
    """
    条件路由函数 - 决定下一步执行路径
    
    这是LangGraph条件边的核心：
    - 函数名任意的，但返回值必须是字面量类型
    - 返回值对应下一步的节点名称
    - 基于状态决定路由方向
    """
    condition_met = state.get("condition_met", False)
    counter = state.get("counter", 0)
    
    print(f"条件路由检查: condition_met={condition_met}, counter={counter}")
    
    if condition_met:
        print("路由到: end")
        return "end"
    else:
        print("路由到: continue")
        return "continue"

def route_by_quality(state: WorkflowState) -> Literal["high_quality", "low_quality", "error"]:
    """
    基于质量的路由决策
    """
    results = state.get("results", [])
    counter = state.get("counter", 0)
    
    # 模拟质量评估
    quality_score = random.randint(1, 10)
    
    print(f"质量评估得分: {quality_score}")
    
    if quality_score >= 8:
        return "high_quality"
    elif quality_score >= 5:
        return "low_quality"
    else:
        return "error"

# 4. 构建不同类型的图

def linear_workflow():
    """
    线性工作流 - 最简单的工作流结构
    A -> B -> C -> END
    """
    print_step("构建线性工作流")
    
    workflow = StateGraph(WorkflowState)
    
    # 添加节点
    workflow.add_node("process", data_processor)
    workflow.add_node("validate", validator)
    workflow.add_node("transform", transformer)
    workflow.add_node("aggregate", aggregator)
    
    # 设置入口点
    workflow.set_entry_point("process")
    
    # 添加边（线性执行）
    workflow.add_edge("process", "validate")
    workflow.add_edge("validate", "transform")
    workflow.add_edge("transform", "aggregate")
    workflow.add_edge("aggregate", END)
    
    return workflow.compile()

def conditional_workflow():
    """
    条件工作流 - 包含条件判断的工作流
    """
    print_step("构建条件工作流")
    
    workflow = StateGraph(WorkflowState)
    
    # 添加节点
    workflow.add_node("process", data_processor)
    workflow.add_node("check_condition", validator)
    workflow.add_node("high_quality", transformer)  # 高质量处理
    workflow.add_node("low_quality", loop_controller)  # 低质量处理
    workflow.add_node("error_handler", error_handler)
    workflow.add_node("end", aggregator)
    
    # 设置入口点
    workflow.set_entry_point("process")
    
    # 添加边
    workflow.add_edge("process", "check_condition")
    
    # 添加条件边 - 这是关键！
    workflow.add_conditional_edges(
        "check_condition",  # 源节点
        route_by_quality,   # 路由函数
        {
            "high_quality": "high_quality",
            "low_quality": "low_quality", 
            "error": "error_handler"
        }
    )
    
    # 添加结束边
    workflow.add_edge("high_quality", "end")
    workflow.add_edge("low_quality", "end")
    workflow.add_edge("error_handler", "end")
    workflow.add_edge("end", END)
    
    return workflow.compile()

def loop_workflow():
    """
    循环工作流 - 包含循环逻辑的工作流
    """
    print_step("构建循环工作流")
    
    workflow = StateGraph(WorkflowState)
    
    # 添加节点
    workflow.add_node("process", data_processor)
    workflow.add_node("check_loop", loop_controller)
    workflow.add_node("end", aggregator)
    
    # 设置入口点
    workflow.set_entry_point("process")
    
    # 添加边
    workflow.add_edge("process", "check_loop")
    
    # 条件边 - 决定是否继续循环
    workflow.add_conditional_edges(
        "check_loop",
        lambda state: "continue" if state.get("current_step") == "loop_continue" else "end",
        {
            "continue": "process",  # 回到处理节点，形成循环
            "end": "end"
        }
    )
    
    workflow.add_edge("end", END)
    
    return workflow.compile()

def complex_workflow():
    """
    复杂工作流 - 结合多种结构
    """
    print_step("构建复杂工作流")
    
    workflow = StateGraph(WorkflowState)
    
    # 添加节点
    workflow.add_node("initial_process", data_processor)
    workflow.add_node("quality_check", validator)
    workflow.add_node("branch_high", transformer)
    workflow.add_node("branch_low", data_processor)
    workflow.add_node("loop_control", loop_controller)
    workflow.add_node("final_aggregate", aggregator)
    
    # 设置入口点
    workflow.set_entry_point("initial_process")
    
    # 添加边
    workflow.add_edge("initial_process", "quality_check")
    
    # 第一层条件分支
    workflow.add_conditional_edges(
        "quality_check",
        should_continue,
        {
            "continue": "branch_high",
            "end": "branch_low"
        }
    )
    
    # 高质量分支
    workflow.add_edge("branch_high", "final_aggregate")
    
    # 低质量分支（可能需要循环）
    workflow.add_edge("branch_low", "loop_control")
    
    # 循环控制
    workflow.add_conditional_edges(
        "loop_control",
        lambda state: "continue" if state.get("loop_count", 0) < 2 else "final",
        {
            "continue": "branch_low",  # 回到分支节点
            "final": "final_aggregate"
        }
    )
    
    workflow.add_edge("final_aggregate", END)
    
    return workflow.compile()

# 5. 演示函数
def demo_linear_workflow():
    """演示线性工作流"""
    print_step("线性工作流演示")
    
    app = linear_workflow()
    
    initial_state = {
        "current_step": "start",
        "data": "测试数据",
        "results": [],
        "counter": 0,
        "condition_met": False,
        "loop_count": 0
    }
    
    print(f"初始状态: {initial_state}")
    
    result = app.invoke(initial_state)
    print_result(f"线性工作流结果: {result}")

def demo_conditional_workflow():
    """演示条件工作流"""
    print_step("条件工作流演示")
    
    app = conditional_workflow()
    
    # 运行多次，观察不同的路由结果
    for i in range(3):
        print(f"\n--- 运行 {i+1} ---")
        
        initial_state = {
            "current_step": "start",
            "data": f"测试数据 {i+1}",
            "results": [],
            "counter": 0,
            "condition_met": False,
            "loop_count": 0
        }
        
        result = app.invoke(initial_state)
        print(f"结果: {result.get('current_step')}")

def demo_loop_workflow():
    """演示循环工作流"""
    print_step("循环工作流演示")
    
    app = loop_workflow()
    
    initial_state = {
        "current_step": "start",
        "data": "循环测试数据",
        "results": [],
        "counter": 0,
        "condition_met": False,
        "loop_count": 0
    }
    
    print(f"初始状态: {initial_state}")
    
    result = app.invoke(initial_state)
    print_result(f"循环工作流结果: {result}")

def demo_complex_workflow():
    """演示复杂工作流"""
    print_step("复杂工作流演示")
    
    app = complex_workflow()
    
    initial_state = {
        "current_step": "start",
        "data": "复杂工作流测试",
        "results": [],
        "counter": 0,
        "condition_met": False,
        "loop_count": 0
    }
    
    print(f"初始状态: {initial_state}")
    
    result = app.invoke(initial_state)
    print_result(f"复杂工作流结果: {result}")

# 主程序
if __name__ == "__main__":
    print("🔗 LangGraph 节点和边学习程序")
    print("=" * 50)
    
    while True:
        print("\n请选择演示:")
        print("1. 线性工作流")
        print("2. 条件工作流")
        print("3. 循环工作流")
        print("4. 复杂工作流")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-4): ").strip()
        
        if choice == "1":
            demo_linear_workflow()
        elif choice == "2":
            demo_conditional_workflow()
        elif choice == "3":
            demo_loop_workflow()
        elif choice == "4":
            demo_complex_workflow()
        elif choice == "0":
            print_step("感谢学习节点和边！")
            break
        else:
            print_error("无效选择，请重试")
    
    print_result("节点和边学习完成！")