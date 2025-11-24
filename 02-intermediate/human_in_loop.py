"""
02-intermediate: 人工干预和交互

本示例展示如何在LangGraph工作流中实现人工干预，
包括等待用户输入、人工决策点和交互式工作流。

学习要点：
1. 等待用户输入的节点
2. 人工决策点
3. 暂停和恢复工作流
4. 用户界面交互
"""

from typing import TypedDict, Literal, Dict, Any
from langgraph.graph import StateGraph, END
import sys
import os
import time

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import print_step, print_result, print_error

# 1. 状态定义
class HumanLoopState(TypedDict):
    """
    人工干预工作流状态
    """
    task_id: str
    task_type: str
    task_data: Dict[str, Any]
    auto_suggestion: str
    human_decision: str
    human_input: str
    status: str
    approval_history: list
    modification_count: int
    final_output: str

class ReviewState(TypedDict):
    """
    审核状态
    """
    content: str
    auto_review: str
    human_review: str
    review_score: int
    review_comments: list
    approval_status: str

# 2. 自动处理节点

def auto_analyzer(state: HumanLoopState) -> HumanLoopState:
    """
    自动分析节点 - 生成初步建议
    """
    print_step("自动分析")
    
    task_data = state.get("task_data", {})
    task_type = state.get("task_type", "")
    
    # 根据任务类型生成自动建议
    if task_type == "content_review":
        content = task_data.get("content", "")
        auto_suggestion = f"建议发布此内容 (长度: {len(content)} 字符)"
    elif task_type == "approval_request":
        requester = task_data.get("requester", "未知")
        auto_suggestion = f"建议批准 {requester} 的请求"
    elif task_type == "data_validation":
        data_score = task_data.get("validation_score", 0.5)
        if data_score > 0.8:
            auto_suggestion = "数据质量良好，建议通过"
        else:
            auto_suggestion = "数据质量待改进，建议人工审核"
    else:
        auto_suggestion = "建议进行人工审核"
    
    print(f"自动分析结果: {auto_suggestion}")
    
    return {
        "auto_suggestion": auto_suggestion,
        "status": "auto_analyzed"
    }

def content_generator(state: HumanLoopState) -> HumanLoopState:
    """
    内容生成节点 - 自动生成内容供人工修改
    """
    print_step("内容生成")
    
    task_data = state.get("task_data", {})
    topic = task_data.get("topic", "通用主题")
    style = task_data.get("style", "正式")
    
    # 模拟内容生成
    if style == "正式":
        generated_content = f"""
关于{topic}的正式报告：

1. 背景介绍
2. 详细分析
3. 结论建议

此报告基于当前可获得的信息自动生成。
        """
    elif style == "轻松":
        generated_content = f"""
嘿，我们来聊聊{topic}！

这里有一些有趣的信息和想法...
        """
    else:
        generated_content = f"关于{topic}的内容自动生成完成。"
    
    print("内容生成完成")
    print(f"生成的内容长度: {len(generated_content)} 字符")
    
    # 将生成的内容存入task_data
    updated_task_data = task_data.copy()
    updated_task_data["generated_content"] = generated_content
    
    return {
        "task_data": updated_task_data,
        "status": "content_generated"
    }

def data_validator(state: HumanLoopState) -> HumanLoopState:
    """
    数据验证节点 - 自动验证数据质量
    """
    print_step("数据验证")
    
    task_data = state.get("task_data", {})
    validation_results = {}
    
    # 模拟各种数据验证
    for key, value in task_data.items():
        if isinstance(value, str):
            validation_results[f"{key}_length"] = len(value)
            validation_results[f"{key}_has_content"] = len(value) > 0
        elif isinstance(value, (int, float)):
            validation_results[f"{key}_is_number"] = True
            validation_results[f"{key}_is_positive"] = value > 0 if value != 0 else True
    
    # 计算总体质量分数
    total_checks = len(validation_results)
    passed_checks = sum(1 for check in validation_results.values() if check)
    quality_score = passed_checks / total_checks if total_checks > 0 else 0
    
    validation_summary = f"数据验证完成，质量分数: {quality_score:.2f} ({passed_checks}/{total_checks})"
    
    print(f"验证结果: {validation_summary}")
    
    updated_task_data = task_data.copy()
    updated_task_data["validation_results"] = validation_results
    updated_task_data["quality_score"] = quality_score
    
    return {
        "task_data": updated_task_data,
        "status": "validated"
    }

# 3. 人工干预节点

def human_approval_node(state: HumanLoopState) -> HumanLoopState:
    """
    人工审批节点 - 等待人工决策
    """
    print_step("等待人工审批")
    
    auto_suggestion = state.get("auto_suggestion", "")
    task_id = state.get("task_id", "")
    task_type = state.get("task_type", "")
    
    print(f"\n{'='*50}")
    print("📋 审批任务")
    print(f"{'='*50}")
    print(f"任务ID: {task_id}")
    print(f"任务类型: {task_type}")
    print(f"\n系统建议: {auto_suggestion}")
    
    # 显示任务详情
    task_data = state.get("task_data", {})
    if task_data:
        print(f"\n任务详情:")
        for key, value in task_data.items():
            print(f"  {key}: {value}")
    
    print(f"\n{'='*50}")
    print("请选择审批结果:")
    print("1. 批准 (approve)")
    print("2. 拒绝 (reject)")
    print("3. 需要修改 (modify)")
    print("4. 稍后处理 (later)")
    
    # 等待用户输入
    while True:
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            decision = "approve"
            break
        elif choice == "2":
            decision = "reject"
            break
        elif choice == "3":
            decision = "modify"
            break
        elif choice == "4":
            decision = "later"
            break
        else:
            print("无效选择，请重试")
    
    # 记录决策
    approval_history = state.get("approval_history", [])
    approval_history.append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "decision": decision,
        "auto_suggestion": auto_suggestion
    })
    
    print(f"人工决策: {decision}")
    
    return {
        "human_decision": decision,
        "approval_history": approval_history,
        "status": "human_approved"
    }

def human_input_node(state: HumanLoopState) -> HumanLoopState:
    """
    人工输入节点 - 获取用户输入
    """
    print_step("等待人工输入")
    
    task_data = state.get("task_data", {})
    generated_content = task_data.get("generated_content", "")
    final_content = task_data.get("final_content", "")
    modification_count = state.get("modification_count", 0)
    
    print(f"\n{'='*50}")
    print("✏️ 内容编辑")
    print(f"{'='*50}")
    print(f"当前修改次数: {modification_count}")
    
    # 优先显示最终内容（已编辑的内容），如果没有则显示生成的内容
    current_content = final_content if final_content else generated_content
    
    if current_content:
        print(f"\n当前内容:")
        print("-" * 30)
        print(current_content)
        print("-" * 30)
    
    print(f"\n编辑选项:")
    print("1. 直接输入新内容")
    print("2. 在现有内容基础上修改")
    print("3. 使用当前内容")
    
    choice = input("\n请选择 (1-3): ").strip()
    
    final_content = ""
    
    if choice == "1":
        print("\n请输入新内容 (输入 'END' 结束):")
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        final_content = "\n".join(lines)
        
    elif choice == "2":
        print("\n请输入修改内容 (将替换当前内容，输入 'END' 结束):")
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        final_content = "\n".join(lines)
        
    elif choice == "3":
        final_content = current_content
    
    else:
        print("无效选择，使用当前内容")
        final_content = current_content
    
    print(f"\n输入的内容长度: {len(final_content)} 字符")
    
    updated_task_data = task_data.copy()
    updated_task_data["final_content"] = final_content
    
    return {
        "task_data": updated_task_data,
        "human_input": final_content,
        "modification_count": modification_count + 1,
        "status": "input_received"
    }

def human_validation_node(state: HumanLoopState) -> HumanLoopState:
    """
    人工验证节点 - 人工确认数据
    """
    print_step("人工验证")
    
    task_data = state.get("task_data", {})
    validation_results = task_data.get("validation_results", {})
    quality_score = task_data.get("quality_score", 0)
    
    print(f"\n{'='*50}")
    print("✅ 人工验证")
    print(f"{'='*50}")
    print(f"系统质量分数: {quality_score:.2f}")
    
    if validation_results:
        print(f"\n验证结果:")
        for key, value in validation_results.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}: {value}")
    
    print(f"\n请确认此数据是否满足要求:")
    print("1. 确认满足 (confirm)")
    print("2. 需要改进 (improve)")
    print("3. 拒绝数据 (reject)")
    
    while True:
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == "1":
            decision = "confirm"
            break
        elif choice == "2":
            decision = "improve"
            break
        elif choice == "3":
            decision = "reject"
            break
        else:
            print("无效选择，请重试")
    
    print(f"人工验证结果: {decision}")
    
    return {
        "human_decision": decision,
        "status": "human_validated"
    }

# 4. 后处理节点

def approval_processor(state: HumanLoopState) -> HumanLoopState:
    """
    审批处理节点
    """
    decision = state.get("human_decision", "")
    task_data = state.get("task_data", {})
    
    if decision == "approve":
        result = "审批通过"
        final_output = f"任务已批准: {task_data}"
    elif decision == "reject":
        result = "审批拒绝"
        final_output = f"任务已拒绝: {task_data}"
    elif decision == "modify":
        result = "需要修改"
        final_output = f"任务需要修改: {task_data}"
    else:
        result = "待处理"
        final_output = f"任务稍后处理: {task_data}"
    
    print_step(f"审批处理: {result}")
    
    return {
        "final_output": final_output,
        "status": "processed"
    }

def content_publisher(state: HumanLoopState) -> HumanLoopState:
    """
    内容发布节点
    """
    task_data = state.get("task_data", {})
    final_content = task_data.get("final_content", "")
    modification_count = state.get("modification_count", 0)
    
    print_step("发布内容")
    print(f"发布内容长度: {len(final_content)} 字符")
    print(f"总修改次数: {modification_count}")
    
    final_output = f"内容已发布，经过 {modification_count} 次修改"
    
    return {
        "final_output": final_output,
        "status": "published"
    }

def data_processor(state: HumanLoopState) -> HumanLoopState:
    """
    数据处理节点
    """
    decision = state.get("human_decision", "")
    task_data = state.get("task_data", {})
    
    if decision == "confirm":
        result = "数据已确认并处理"
        final_output = f"数据处理完成: {task_data.get('quality_score', 0):.2f}"
    elif decision == "improve":
        result = "数据需要改进"
        final_output = f"数据标记为需要改进: {task_data.get('validation_results', {})}"
    else:
        result = "数据被拒绝"
        final_output = f"数据处理失败: {task_data}"
    
    print_step(f"数据处理: {result}")
    
    return {
        "final_output": final_output,
        "status": "data_processed"
    }

# 5. 路由函数

def route_after_approval(state: HumanLoopState) -> Literal["process", "modify_loop", "end"]:
    """
    审批后的路由决策
    """
    decision = state.get("human_decision", "")
    task_type = state.get("task_type", "")
    
    if decision == "approve":
        print("路由: process (批准处理)")
        return "process"
    elif decision == "modify":
        if task_type == "content_creation":
            print("路由: modify_loop (内容修改循环)")
            return "modify_loop"
        else:
            print("路由: process (直接处理)")
            return "process"
    else:
        print("路由: end (结束)")
        return "end"

def route_after_validation(state: HumanLoopState) -> Literal["publish", "end"]:
    """
    验证后的路由决策
    """
    decision = state.get("human_decision", "")
    
    if decision == "confirm":
        print("路由: publish (发布)")
        return "publish"
    else:
        print("路由: end (结束)")
        return "end"

def check_modification_limit(state: HumanLoopState) -> Literal["continue", "end"]:
    """
    检查修改次数限制
    """
    modification_count = state.get("modification_count", 0)
    
    if modification_count >= 3:
        print("修改次数已达上限，结束流程")
        return "end"
    else:
        print("可以继续修改")
        return "continue"

# 6. 构建人工干预工作流

def build_approval_workflow():
    """构建审批工作流"""
    print_step("构建审批工作流")
    
    workflow = StateGraph(HumanLoopState)
    
    # 添加节点
    workflow.add_node("auto_analyze", auto_analyzer)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("process", approval_processor)
    
    # 设置入口点
    workflow.set_entry_point("auto_analyze")
    
    # 添加边
    workflow.add_edge("auto_analyze", "human_approval")
    
    workflow.add_conditional_edges(
        "human_approval",
        route_after_approval,
        {
            "process": "process",
            "modify_loop": "human_approval",  # 回到审批节点
            "end": END
        }
    )
    
    workflow.add_edge("process", END)
    
    return workflow.compile()

def build_content_creation_workflow():
    """构建内容创建工作流"""
    print_step("构建内容创建工作流")
    
    workflow = StateGraph(HumanLoopState)
    
    # 添加节点
    workflow.add_node("generate", content_generator)
    workflow.add_node("human_input_node", human_input_node)
    workflow.add_node("publish", content_publisher)
    
    # 设置入口点
    workflow.set_entry_point("generate")
    
    # 添加边
    workflow.add_edge("generate", "human_input_node")
    
    workflow.add_conditional_edges(
        "human_input_node",
        check_modification_limit,
        {
            "continue": "human_input_node",  # 继续修改
            "end": "publish"  # 发布
        }
    )
    
    workflow.add_edge("publish", END)
    
    return workflow.compile()

def build_data_validation_workflow():
    """构建数据验证工作流"""
    print_step("构建数据验证工作流")
    
    workflow = StateGraph(HumanLoopState)
    
    # 添加节点
    workflow.add_node("validate", data_validator)
    workflow.add_node("human_validation", human_validation_node)
    workflow.add_node("process_data", data_processor)
    
    # 设置入口点
    workflow.set_entry_point("validate")
    
    # 添加边
    workflow.add_edge("validate", "human_validation")
    
    workflow.add_conditional_edges(
        "human_validation",
        route_after_validation,
        {
            "publish": "process_data",
            "end": END
        }
    )
    
    workflow.add_edge("process_data", END)
    
    return workflow.compile()

# 7. 演示函数

def demo_approval_workflow():
    """演示审批工作流"""
    print_step("审批工作流演示")
    
    app = build_approval_workflow()
    
    initial_state = {
        "task_id": "TASK-001",
        "task_type": "approval_request",
        "task_data": {
            "requester": "张三",
            "request_type": "项目预算",
            "amount": 10000,
            "description": "购买开发设备"
        },
        "auto_suggestion": "",
        "human_decision": "",
        "human_input": "",
        "status": "pending",
        "approval_history": [],
        "modification_count": 0,
        "final_output": ""
    }
    
    print("开始审批流程...")
    result = app.invoke(initial_state)
    print_result(f"审批完成: {result['final_output']}")

def demo_content_creation():
    """演示内容创建工作流"""
    print_step("内容创建工作流演示")
    
    app = build_content_creation_workflow()
    
    initial_state = {
        "task_id": "CONTENT-001",
        "task_type": "content_creation",
        "task_data": {
            "topic": "人工智能的发展趋势",
            "style": "正式"
        },
        "auto_suggestion": "",
        "human_decision": "",
        "human_input": "",
        "status": "pending",
        "approval_history": [],
        "modification_count": 0,
        "final_output": ""
    }
    
    print("开始内容创建流程...")
    result = app.invoke(initial_state)
    print_result(f"内容创建完成: {result['final_output']}")

def demo_data_validation():
    """演示数据验证工作流"""
    print_step("数据验证工作流演示")
    
    app = build_data_validation_workflow()
    
    initial_state = {
        "task_id": "DATA-001",
        "task_type": "data_validation",
        "task_data": {
            "username": "testuser",
            "email": "test@example.com",
            "age": 25,
            "score": 85
        },
        "auto_suggestion": "",
        "human_decision": "",
        "human_input": "",
        "status": "pending",
        "approval_history": [],
        "modification_count": 0,
        "final_output": ""
    }
    
    print("开始数据验证流程...")
    result = app.invoke(initial_state)
    print_result(f"数据验证完成: {result['final_output']}")

# 主程序
if __name__ == "__main__":
    print("👥 LangGraph 人工干预学习程序")
    print("=" * 60)
    
    while True:
        print("\n请选择演示:")
        print("1. 审批工作流")
        print("2. 内容创建工作流")
        print("3. 数据验证工作流")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-3): ").strip()
        
        if choice == "1":
            demo_approval_workflow()
        elif choice == "2":
            demo_content_creation()
        elif choice == "3":
            demo_data_validation()
        elif choice == "0":
            print_step("感谢学习人工干预！")
            break
        else:
            print_error("无效选择，请重试")
    
    print_result("人工干预学习完成！")