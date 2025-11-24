"""
02-intermediate: 条件路由高级用法

本示例展示LangGraph中高级条件路由技术，包括多层条件判断、
动态路由决策和复杂业务逻辑的处理。

学习要点：
1. 多层条件嵌套
2. 动态路由决策
3. 基于数据质量的路由
4. 复杂业务逻辑的条件判断
"""

from typing import TypedDict, Literal, Dict, Any
from langgraph.graph import StateGraph, END
import sys
import os
import random
import re

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import print_step, print_result, print_error

# 1. 状态定义
class ConditionalState(TypedDict):
    """
    条件路由工作流状态
    """
    content: str
    content_type: str
    quality_score: float
    priority: str
    classification: str
    processing_path: list
    metadata: Dict[str, Any]

class QualityMetrics(TypedDict):
    """质量指标状态"""
    grammar_score: float
    relevance_score: float
    completeness_score: float
    overall_score: float

class RouteDecision(TypedDict):
    """路由决策状态"""
    primary_route: str
    fallback_route: str
    route_reason: str
    confidence: float

# 2. 数据分类和评估节点

def content_classifier(state: ConditionalState) -> ConditionalState:
    """
    内容分类节点 - 分析内容类型
    """
    print_step("内容分类分析")
    
    content = state.get("content", "")
    processing_path = state.get("processing_path", [])
    
    # 简单的内容分类逻辑
    if re.search(r'问题|疑问|help|帮助', content, re.IGNORECASE):
        content_type = "question"
    elif re.search(r'bug|错误|error|问题', content, re.IGNORECASE):
        content_type = "bug_report"
    elif re.search(r'建议|改进|suggestion', content, re.IGNORECASE):
        content_type = "suggestion"
    elif re.search(r'表扬|感谢|thanks', content, re.IGNORECASE):
        content_type = "feedback"
    else:
        content_type = "general"
    
    processing_path.append(f"classified_as_{content_type}")
    
    print(f"内容分类结果: {content_type}")
    
    return {
        "content_type": content_type,
        "processing_path": processing_path
    }

def priority_analyzer(state: ConditionalState) -> ConditionalState:
    """
    优先级分析节点 - 确定处理优先级
    """
    print_step("优先级分析")
    
    content = state.get("content", "")
    content_type = state.get("content_type", "general")
    processing_path = state.get("processing_path", [])
    
    # 优先级判断逻辑
    priority = "normal"
    
    if content_type == "bug_report":
        # 包含紧急关键词
        if re.search(r'紧急|urgent|critical|critical', content, re.IGNORECASE):
            priority = "high"
        else:
            priority = "medium"
    elif content_type == "question":
        # 问题是否包含生产环境关键词
        if re.search(r'生产|production|线上|live', content, re.IGNORECASE):
            priority = "high"
        else:
            priority = "normal"
    elif content_type == "feedback":
        priority = "low"
    
    processing_path.append(f"priority_{priority}")
    
    print(f"优先级分析结果: {priority}")
    
    return {
        "priority": priority,
        "processing_path": processing_path
    }

def quality_evaluator(state: ConditionalState) -> ConditionalState:
    """
    质量评估节点 - 评估内容质量
    """
    print_step("内容质量评估")
    
    content = state.get("content", "")
    processing_path = state.get("processing_path", [])
    
    # 模拟质量评估
    length_score = min(len(content) / 100, 1.0)  # 长度评分
    grammar_score = random.uniform(0.7, 1.0)  # 语法评分（模拟）
    relevance_score = random.uniform(0.6, 1.0)  # 相关性评分（模拟）
    
    # 综合评分
    quality_score = (length_score + grammar_score + relevance_score) / 3
    
    processing_path.append(f"quality_{quality_score:.2f}")
    
    print(f"质量评估结果: {quality_score:.2f}")
    print(f"  - 长度评分: {length_score:.2f}")
    print(f"  - 语法评分: {grammar_score:.2f}")
    print(f"  - 相关性评分: {relevance_score:.2f}")
    
    return {
        "quality_score": quality_score,
        "processing_path": processing_path
    }

# 3. 处理节点

def urgent_handler(state: ConditionalState) -> ConditionalState:
    """
    紧急处理节点
    """
    print_step("紧急处理")
    
    processing_path = state.get("processing_path", [])
    processing_path.append("urgent_handled")
    
    return {
        "classification": "urgent_processed",
        "processing_path": processing_path
    }

def standard_handler(state: ConditionalState) -> ConditionalState:
    """
    标准处理节点
    """
    print_step("标准处理")
    
    processing_path = state.get("processing_path", [])
    processing_path.append("standard_handled")
    
    return {
        "classification": "standard_processed",
        "processing_path": processing_path
    }

def quality_review_handler(state: ConditionalState) -> ConditionalState:
    """
    质量审核处理节点
    """
    print_step("质量审核处理")
    
    processing_path = state.get("processing_path", [])
    processing_path.append("quality_review")
    
    return {
        "classification": "quality_review_needed",
        "processing_path": processing_path
    }

def auto_reject_handler(state: ConditionalState) -> ConditionalState:
    """
    自动拒绝处理节点
    """
    print_step("自动拒绝")
    
    processing_path = state.get("processing_path", [])
    processing_path.append("auto_rejected")
    
    return {
        "classification": "auto_rejected",
        "processing_path": processing_path
    }

# 4. 高级条件路由函数

def route_by_priority_and_quality(state: ConditionalState) -> Literal["urgent", "standard", "quality_review", "reject"]:
    """
    基于优先级和质量的复合路由决策
    """
    print_step("复合路由决策")
    
    priority = state.get("priority", "normal")
    quality_score = state.get("quality_score", 0.0)
    content_type = state.get("content_type", "general")
    
    print(f"路由决策参数:")
    print(f"  - 优先级: {priority}")
    print(f"  - 质量评分: {quality_score:.2f}")
    print(f"  - 内容类型: {content_type}")
    
    # 复杂路由逻辑
    if priority == "high" and quality_score >= 0.5:
        print("路由决策: urgent (高优先级 + 质量合格)")
        return "urgent"
    elif priority == "high" and quality_score < 0.5:
        print("路由决策: quality_review (高优先级但质量不足)")
        return "quality_review"
    elif priority == "normal" and quality_score >= 0.7:
        print("路由决策: standard (正常优先级 + 高质量)")
        return "standard"
    elif priority == "normal" and quality_score < 0.3:
        print("路由决策: reject (质量过低)")
        return "reject"
    elif priority == "low" and quality_score >= 0.8:
        print("路由决策: standard (低优先级但质量很高)")
        return "standard"
    else:
        print("路由决策: standard (默认标准处理)")
        return "standard"

def secondary_routing(state: ConditionalState) -> Literal["escalate", "delegate", "archive"]:
    """
    二级路由决策 - 用于进一步细分处理
    """
    content_type = state.get("content_type", "general")
    classification = state.get("classification", "")
    processing_path = state.get("processing_path", [])
    
    print_step("二级路由决策")
    print(f"当前分类: {classification}")
    print(f"内容类型: {content_type}")
    
    # 基于处理结果进行二级路由
    if classification == "urgent_processed":
        if content_type in ["bug_report", "question"]:
            print("二级路由: escalate")
            return "escalate"
        else:
            print("二级路由: delegate")
            return "delegate"
    elif classification == "standard_processed":
        if len(processing_path) > 3:  # 处理路径较长，可能复杂
            print("二级路由: delegate")
            return "delegate"
        else:
            print("二级路由: archive")
            return "archive"
    else:
        print("二级路由: archive")
        return "archive"

# 5. 二级处理节点

def escalate_handler(state: ConditionalState) -> ConditionalState:
    """升级处理"""
    print_step("升级处理")
    processing_path = state.get("processing_path", [])
    processing_path.append("escalated")
    return {"processing_path": processing_path}

def delegate_handler(state: ConditionalState) -> ConditionalState:
    """委派处理"""
    print_step("委派处理")
    processing_path = state.get("processing_path", [])
    processing_path.append("delegated")
    return {"processing_path": processing_path}

def archive_handler(state: ConditionalState) -> ConditionalState:
    """归档处理"""
    print_step("归档处理")
    processing_path = state.get("processing_path", [])
    processing_path.append("archived")
    return {"processing_path": processing_path}

# 6. 构建高级条件路由工作流

def build_advanced_routing_workflow():
    """
    构建高级条件路由工作流
    """
    print_step("构建高级条件路由工作流")
    
    workflow = StateGraph(ConditionalState)
    
    # 添加分析节点
    workflow.add_node("classify", content_classifier)
    workflow.add_node("analyze_priority", priority_analyzer)
    workflow.add_node("evaluate_quality", quality_evaluator)
    
    # 添加处理节点
    workflow.add_node("urgent_handler", urgent_handler)
    workflow.add_node("standard_handler", standard_handler)
    workflow.add_node("quality_review_handler", quality_review_handler)
    workflow.add_node("auto_reject_handler", auto_reject_handler)
    
    # 添加二级处理节点
    workflow.add_node("escalate", escalate_handler)
    workflow.add_node("delegate", delegate_handler)
    workflow.add_node("archive", archive_handler)
    
    # 设置入口点
    workflow.set_entry_point("classify")
    
    # 第一层：分析阶段
    workflow.add_edge("classify", "analyze_priority")
    workflow.add_edge("analyze_priority", "evaluate_quality")
    
    # 第二层：主要条件路由
    workflow.add_conditional_edges(
        "evaluate_quality",
        route_by_priority_and_quality,
        {
            "urgent": "urgent_handler",
            "standard": "standard_handler",
            "quality_review": "quality_review_handler",
            "reject": "auto_reject_handler"
        }
    )
    
    # 第三层：二级条件路由
    for primary_node in ["urgent_handler", "standard_handler", "quality_review_handler"]:
        workflow.add_conditional_edges(
            primary_node,
            secondary_routing,
            {
                "escalate": "escalate",
                "delegate": "delegate",
                "archive": "archive"
            }
        )
    
    # 自动拒绝直接归档
    workflow.add_edge("auto_reject_handler", "archive")
    
    # 所有二级处理节点都流向结束
    workflow.add_edge("escalate", END)
    workflow.add_edge("delegate", END)
    workflow.add_edge("archive", END)
    
    return workflow.compile()

# 7. 演示函数

def demo_basic_routing():
    """基础路由演示"""
    print_step("基础条件路由演示")
    
    test_cases = [
        {
            "content": "生产环境出现紧急bug，系统崩溃",
            "description": "高优先级问题"
        },
        {
            "content": "建议增加新的功能模块",
            "description": "一般建议"
        },
        {
            "content": "hi",  # 内容过短
            "description": "低质量内容"
        },
        {
            "content": "感谢团队的支持，产品很棒！",
            "description": "正面反馈"
        }
    ]
    
    app = build_advanced_routing_workflow()
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"测试用例 {i}: {case['description']}")
        print(f"{'='*60}")
        
        initial_state = {
            "content": case["content"],
            "content_type": "",
            "quality_score": 0.0,
            "priority": "normal",
            "classification": "",
            "processing_path": [],
            "metadata": {}
        }
        
        try:
            result = app.invoke(initial_state)
            print_result(f"最终处理路径: {result['processing_path']}")
            print(f"最终分类: {result['classification']}")
        except Exception as e:
            print_error(f"处理失败: {e}")

def demo_routing_with_metadata():
    """带元数据的路由演示"""
    print_step("带元数据的路由演示")
    
    app = build_advanced_routing_workflow()
    
    initial_state = {
        "content": "生产系统出现性能问题，用户反馈响应缓慢",
        "content_type": "",
        "quality_score": 0.0,
        "priority": "normal",
        "classification": "",
        "processing_path": [],
        "metadata": {
            "user_id": "user123",
            "department": "production",
            "timestamp": "2024-01-15T10:30:00",
            "impact_level": "medium"
        }
    }
    
    print("初始状态:")
    for key, value in initial_state.items():
        print(f"  {key}: {value}")
    
    result = app.invoke(initial_state)
    
    print_result("带元数据路由完成")
    print(f"处理路径: {result['processing_path']}")

def analyze_routing_logic():
    """分析路由逻辑"""
    print_step("路由逻辑分析")
    
    print("""
高级条件路由的关键特点：

1. 多层决策
   - 第一层：内容分类
   - 第二层：优先级分析  
   - 第三层：质量评估
   - 第四层：复合路由决策
   - 第五层：二级路由分发

2. 动态路由规则
   - 基于内容类型的不同处理逻辑
   - 基于优先级的紧急程度判断
   - 基于质量评分的筛选机制
   - 基于处理历史的路径优化

3. 智能回退机制
   - 质量不足时的人工审核
   - 低质量内容的自动拒绝
   - 复杂问题的升级处理
   - 简单问题的自动归档

4. 可扩展性
   - 新的内容类型可以轻松添加
   - 路由规则可以动态调整
   - 处理节点可以独立优化
   - 元数据支持更丰富的决策

这种设计模式适用于：
- 客服工单系统
- 内容审核平台
- 代码审查流程
- 质量管理系统
    """)

# 主程序
if __name__ == "__main__":
    print("🔀 LangGraph 高级条件路由学习程序")
    print("=" * 60)
    
    while True:
        print("\n请选择演示:")
        print("1. 基础路由演示")
        print("2. 带元数据的路由演示")
        print("3. 路由逻辑分析")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-3): ").strip()
        
        if choice == "1":
            demo_basic_routing()
        elif choice == "2":
            demo_routing_with_metadata()
        elif choice == "3":
            analyze_routing_logic()
        elif choice == "0":
            print_step("感谢学习高级条件路由！")
            break
        else:
            print_error("无效选择，请重试")
    
    print_result("高级条件路由学习完成！")