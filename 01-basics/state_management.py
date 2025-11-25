"""
01-basics: 状态管理详解

本示例深入讲解LangGraph中状态管理的各个方面。
状态是LangGraph工作流的核心，理解状态管理是掌握LangGraph的关键。

学习要点：
1. 状态的数据结构设计
2. 状态更新和传递机制
3. 状态检查和验证
4. 状态持久化概念
5. 复杂状态的数据流
6. 状态的条件访问和修改
7. 状态的分片和管理

状态管理概念：
- TypedDict定义：使用Python类型注解定义状态结构
- 状态传递：节点间状态的无缝传递
- 状态更新：增量更新vs完全替换
- 状态验证：确保状态数据的正确性
- 状态分片：将复杂状态分解为多个字段
- 状态检查点：保存和恢复状态的概念
- 条件状态访问：根据条件访问不同状态字段
"""

from typing import TypedDict, Optional, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
import sys
import os
import json
import copy

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import print_step, print_result, print_error

# 1. 复杂状态定义
class AdvancedWorkflowState(TypedDict):
    """
    高级工作流状态定义
    
    这个状态包含多个字段，展示了不同类型的状态数据：
    - user_info: 用户信息（字典）
    - session_data: 会话数据（字典）
    - processing_history: 处理历史（列表）
    - current_step: 当前步骤（字符串）
    - step_counter: 步骤计数器（整数）
    - flags: 各种标志位（字典）
    - metadata: 元数据（字典）
    - result_cache: 结果缓存（字典）
    - error_log: 错误日志（列表）
    """
    
    # 用户和会话信息
    user_info: Dict[str, Any]
    session_data: Dict[str, Any]
    
    # 处理流程
    processing_history: List[str]
    current_step: str
    step_counter: int
    
    # 控制标志
    flags: Dict[str, bool]
    
    # 业务数据
    input_data: Optional[str]
    processed_data: Optional[Dict[str, Any]]
    output_data: Optional[str]
    
    # 系统数据
    metadata: Dict[str, Any]
    result_cache: Dict[str, Any]
    error_log: List[Dict[str, Any]]

# 2. 状态初始化和验证节点
def initialize_state(state: AdvancedWorkflowState) -> AdvancedWorkflowState:
    """
    状态初始化节点
    
    展示如何初始化复杂状态：
    1. 设置默认值
    2. 验证必需字段
    3. 初始化缓存和日志
    """
    print_step("状态初始化")
    
    # 获取或初始化用户信息
    user_info = state.get("user_info", {})
    if not user_info:
        user_info = {
            "user_id": "demo_user_001",
            "user_name": "演示用户",
            "created_at": "2024-01-01T00:00:00Z"
        }
    
    # 初始化会话数据
    session_data = state.get("session_data", {})
    if not session_data or not session_data.get("session_id"):
        session_data = {
            "session_id": f"session_{hash(str(user_info)) % 10000}",
            "start_time": "2024-01-01T00:00:00Z",
            "language": "zh-CN"
        }
    
    # 初始化处理历史
    processing_history = state.get("processing_history", [])
    processing_history.append("状态初始化完成")
    
    # 初始化标志位
    flags = state.get("flags", {
        "is_valid": True,
        "has_errors": False,
        "is_complete": False,
        "need_validation": True
    })
    
    # 初始化元数据
    metadata = state.get("metadata", {
        "version": "1.0",
        "environment": "demo",
        "source": "state_management_demo"
    })
    
    # 初始化缓存和错误日志
    result_cache = state.get("result_cache", {})
    error_log = state.get("error_log", [])
    
    print(f"用户信息: {user_info}")
    print(f"会话ID: {session_data.get('session_id')}")
    print(f"处理历史: {len(processing_history)} 项")
    
    return {
        "user_info": user_info,
        "session_data": session_data,
        "processing_history": processing_history,
        "current_step": "initialization",
        "step_counter": 1,
        "flags": flags,
        "input_data": state.get("input_data", ""),
        "processed_data": state.get("processed_data"),
        "output_data": state.get("output_data"),
        "metadata": metadata,
        "result_cache": result_cache,
        "error_log": error_log
    }

def validate_state(state: AdvancedWorkflowState) -> AdvancedWorkflowState:
    """
    状态验证节点
    
    展示状态验证的重要性：
    1. 检查必需字段
    2. 验证数据格式
    3. 检查业务规则
    4. 记录验证结果
    """
    print_step("状态验证")
    
    errors = []
    warnings = []
    
    # 检查用户信息
    user_info = state.get("user_info", {})
    if not user_info.get("user_id"):
        errors.append("缺少用户ID")
    if not user_info.get("user_name"):
        warnings.append("用户名为空，使用默认值")
    
    # 检查会话数据
    session_data = state.get("session_data", {})
    if not session_data.get("session_id"):
        errors.append("缺少会话ID")
    
    # 检查输入数据
    input_data = state.get("input_data", "")
    if not input_data:
        warnings.append("输入数据为空")
    
    # 更新验证标志
    flags = state.get("flags", {})
    flags["is_valid"] = len(errors) == 0
    flags["has_errors"] = len(errors) > 0
    
    # 记录验证结果
    if errors or warnings:
        error_entry = {
            "timestamp": "2024-01-01T00:00:00Z",
            "step": "validation",
            "errors": errors,
            "warnings": warnings,
            "step_counter": state.get("step_counter", 0)
        }
        
        error_log = state.get("error_log", [])
        error_log.append(error_entry)
        
        if errors:
            print_error(f"验证失败: {errors}")
        if warnings:
            print(f"验证警告: {warnings}")
    else:
        print_result("状态验证通过")
    
    # 记录处理历史
    processing_history = state.get("processing_history", [])
    processing_history.append(f"状态验证完成 - 错误: {len(errors)}, 警告: {len(warnings)}")
    
    return {
        **state,
        "flags": flags,
        "error_log": state.get("error_log", []),
        "processing_history": processing_history,
        "current_step": "validation"
    }

# 3. 状态更新和管理节点
def update_processing_state(state: AdvancedWorkflowState) -> AdvancedWorkflowState:
    """
    更新处理状态节点
    
    展示状态更新的最佳实践：
    1. 增量更新而非完全替换
    2. 保持状态的一致性
    3. 记录变更历史
    4. 更新相关字段
    """
    print_step("更新处理状态")
    
    # 获取当前状态
    step_counter = state.get("step_counter", 0)
    input_data = state.get("input_data", "")
    flags = state.get("flags", {})
    
    # 模拟数据处理
    if input_data:
        processed_data = {
            "original_length": len(input_data),
            "word_count": len(input_data.split()),
            "processed_at": "2024-01-01T00:00:00Z",
            "processing_step": step_counter + 1,
            "data_hash": hash(input_data) % 10000
        }
        
        print(f"处理数据: {processed_data}")
        
        # 更新缓存
        result_cache = state.get("result_cache", {})
        result_cache[f"processed_data_{step_counter}"] = processed_data
        
        # 更新处理历史
        processing_history = state.get("processing_history", [])
        processing_history.append(f"数据处理完成 - 步骤 {step_counter + 1}")
        
        # 更新标志位
        flags["is_processing"] = True
        
        return {
            **state,
            "processed_data": processed_data,
            "result_cache": result_cache,
            "processing_history": processing_history,
            "step_counter": step_counter + 1,
            "flags": flags,
            "current_step": "processing"
        }
    else:
        print("无输入数据可处理")
        return {
            **state,
            "current_step": "no_processing_needed"
        }

def manage_state_cache(state: AdvancedWorkflowState) -> AdvancedWorkflowState:
    """
    状态缓存管理节点
    
    展示状态缓存的管理：
    1. 缓存热点数据
    2. 缓存失效策略
    3. 内存优化
    4. 缓存预热
    """
    print_step("管理状态缓存")
    
    result_cache = state.get("result_cache", {})
    processed_data = state.get("processed_data")
    step_counter = state.get("step_counter", 0)
    
    # 模拟缓存操作
    if processed_data:
        # 缓存当前处理结果
        cache_key = f"step_{step_counter}_result"
        result_cache[cache_key] = {
            "data": processed_data,
            "cached_at": "2024-01-01T00:00:00Z",
            "access_count": result_cache.get(cache_key, {}).get("access_count", 0) + 1
        }
        
        # 缓存清理：保持最多10个缓存项
        cache_keys = list(result_cache.keys())
        if len(cache_keys) > 10:
            oldest_key = cache_keys[0]
            del result_cache[oldest_key]
            print(f"清理过期缓存: {oldest_key}")
        
        print(f"缓存管理: 当前缓存项数 {len(result_cache)}")
    
    # 记录处理历史
    processing_history = state.get("processing_history", [])
    processing_history.append("缓存管理完成")
    
    return {
        **state,
        "result_cache": result_cache,
        "processing_history": processing_history,
        "current_step": "cache_management"
    }

# 4. 条件状态访问节点
def conditional_state_access(state: AdvancedWorkflowState) -> AdvancedWorkflowState:
    """
    条件状态访问节点
    
    展示如何根据条件访问和修改状态：
    1. 基于标志位的条件访问
    2. 基于数据的条件逻辑
    3. 状态的分层访问
    4. 状态的安全检查
    """
    print_step("条件状态访问")
    
    flags = state.get("flags", {})
    step_counter = state.get("step_counter", 0)
    error_log = state.get("error_log", [])
    
    # 根据条件进行不同的处理
    if flags.get("has_errors", False):
        print("检测到错误，执行错误处理逻辑")
        
        # 获取最近的错误
        if error_log:
            recent_errors = error_log[-1]
            print(f"最新错误: {recent_errors}")
        
        # 标记为需要重试
        flags["need_retry"] = True
        
    elif step_counter >= 5:
        print("达到最大步骤数，标记为完成")
        flags["is_complete"] = True
        
    elif step_counter < 3:
        print("步骤数较少，继续处理")
        flags["continue_processing"] = True
        
    else:
        print("中间步骤，执行标准逻辑")
        flags["standard_processing"] = True
    
    # 条件性地更新输出数据
    output_data = ""
    if flags.get("is_complete"):
        output_data = "处理完成！所有步骤已成功执行。"
    elif flags.get("need_retry"):
        output_data = "检测到错误，需要重试某些步骤。"
    else:
        output_data = f"处理中... 当前步骤: {step_counter}"
    
    # 记录处理历史
    processing_history = state.get("processing_history", [])
    processing_history.append(f"条件访问执行 - flags: {list(flags.keys())}")
    
    print(f"输出数据: {output_data}")
    
    return {
        **state,
        "flags": flags,
        "output_data": output_data,
        "processing_history": processing_history,
        "current_step": "conditional_access"
    }

# 5. 状态汇总和输出节点
def summarize_state(state: AdvancedWorkflowState) -> AdvancedWorkflowState:
    """
    状态汇总节点
    
    展示如何汇总复杂状态：
    1. 统计信息汇总
    2. 结果整理
    3. 状态快照
    4. 最终输出准备
    """
    print_step("状态汇总")
    
    # 收集统计信息
    step_counter = state.get("step_counter", 0)
    processing_history = state.get("processing_history", [])
    error_log = state.get("error_log", [])
    result_cache = state.get("result_cache", {})
    flags = state.get("flags", {})
    
    # 生成汇总报告
    summary_report = {
        "执行统计": {
            "总步骤数": step_counter,
            "处理历史数": len(processing_history),
            "错误数量": len(error_log),
            "缓存项数": len(result_cache)
        },
        "状态标志": flags,
        "最终状态": {
            "当前步骤": state.get("current_step"),
            "输入数据": state.get("input_data", "")[:50] + "..." if len(state.get("input_data", "")) > 50 else state.get("input_data", ""),
            "输出数据": state.get("output_data", "")
        },
        "处理历史": processing_history,
        "时间戳": "2024-01-01T00:00:00Z"
    }
    
    # 生成用户友好的汇总
    user_summary = f"""
=== LangGraph 状态管理演示汇总 ===

执行统计:
- 总步骤数: {step_counter}
- 处理历史: {len(processing_history)} 项
- 错误记录: {len(error_log)} 项
- 缓存数据: {len(result_cache)} 项

状态标志: {', '.join([k for k, v in flags.items() if v])}

最终输出: {state.get('output_data', '无输出')}

处理流程: {' -> '.join(processing_history[:5])}{'...' if len(processing_history) > 5 else ''}
"""
    
    print_result(user_summary)
    
    # 保存汇总到元数据
    metadata = state.get("metadata", {})
    metadata["final_summary"] = summary_report
    metadata["summary_generated_at"] = "2024-01-01T00:00:00Z"
    
    return {
        **state,
        "metadata": metadata,
        "current_step": "summarization"
    }

# 6. 条件路由函数
def should_continue_processing(state: AdvancedWorkflowState) -> Literal["continue", "end"]:
    """
    条件路由函数 - 决定是否继续处理
    
    这是LangGraph条件边的核心：
    - 返回值必须是字面量类型
    - 基于复杂状态决定路由
    - 考虑多种因素：步骤数、错误、标志位
    """
    flags = state.get("flags", {})
    step_counter = state.get("step_counter", 0)
    error_log = state.get("error_log", [])
    
    # 结束条件
    if flags.get("is_complete"):
        print("处理已完成，结束流程")
        return "end"
    
    if step_counter >= 10:
        print("达到最大步骤数，结束流程")
        return "end"
    
    if flags.get("has_errors") and step_counter >= 3:
        print("有错误且已处理3步，结束流程")
        return "end"
    
    # 继续条件
    if not flags.get("has_errors") and step_counter < 5:
        print("无错误且步骤未满，继续处理")
        return "continue"
    
    # 默认结束
    print("默认结束处理")
    return "end"

# 7. 构建状态管理流程图
def build_state_management_graph():
    """
    构建状态管理流程图
    
    展示复杂状态管理的完整流程：
    1. 状态初始化
    2. 状态验证
    3. 条件处理
    4. 状态更新
    5. 缓存管理
    6. 条件访问
    7. 状态汇总
    """
    print_step("构建状态管理流程图")
    
    # 创建状态图
    workflow: StateGraph = StateGraph(AdvancedWorkflowState)
    
    # 添加节点
    workflow.add_node("initialize", initialize_state)
    workflow.add_node("validate", validate_state)
    workflow.add_node("update_processing", update_processing_state)
    workflow.add_node("manage_cache", manage_state_cache)
    workflow.add_node("conditional_access", conditional_state_access)
    workflow.add_node("summarize", summarize_state)
    
    # 设置入口点
    workflow.set_entry_point("initialize")
    
    # 添加边 - initialize完成后继续到validate
    workflow.add_edge("initialize", "validate")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "validate",
        should_continue_processing,
        {
            "continue": "update_processing",
            "end": "summarize"
        }
    )
    
    workflow.add_conditional_edges(
        "update_processing",
        should_continue_processing,
        {
            "continue": "manage_cache",
            "end": "summarize"
        }
    )
    
    workflow.add_conditional_edges(
        "manage_cache",
        should_continue_processing,
        {
            "continue": "conditional_access",
            "end": "summarize"
        }
    )
    
    workflow.add_conditional_edges(
        "conditional_access",
        should_continue_processing,
        {
            "continue": "update_processing",  # 循环回到处理步骤
            "end": "summarize"
        }
    )
    
    # 添加结束边
    workflow.add_edge("summarize", END)
    
    # 编译状态图
    app = workflow.compile()
    
    print_result("状态管理流程图构建完成！")
    print("流程: initialize -> validate -> (条件路由) -> update_processing -> manage_cache -> conditional_access -> (循环或结束) -> summarize -> END")
    
    return app

# 8. 演示函数
def run_state_management_demo():
    """
    运行状态管理演示
    """
    print_step("开始LangGraph状态管理演示")
    
    # 构建状态图
    app = build_state_management_graph()
    
    # 准备初始状态（故意包含一些无效数据来测试验证）
    initial_state = AdvancedWorkflowState(
        user_info={},  # 故意为空，测试初始化和验证
        session_data={},
        processing_history=[],
        current_step="start",
        step_counter=0,
        flags={},
        input_data="这是一个状态管理演示的测试输入数据，用于展示LangGraph中复杂状态的处理流程。",
        processed_data=None,
        output_data=None,
        metadata={},
        result_cache={},
        error_log=[]
    )
    
    print(f"初始状态: {initial_state['input_data']}")
    
    try:
        # 运行工作流
        result = app.invoke(initial_state)
        
        print_step("状态管理工作流执行完成")
        
        # 显示最终状态的关键部分
        final_flags = result.get("flags", {})
        final_counter = result.get("step_counter", 0)
        final_step = result.get("current_step", "")
        final_output = result.get("output_data", "")
        
        print(f"最终步骤: {final_step}")
        print(f"总步骤数: {final_counter}")
        print(f"激活标志: {[k for k, v in final_flags.items() if v]}")
        print(f"最终输出: {final_output}")
        
    except Exception as e:
        print_error(f"状态管理演示失败: {e}")

def interactive_state_demo():
    """
    交互式状态管理演示

    详细流程：
    1. 用户输入测试数据
    2. 系统初始化状态
    3. 状态验证和处理
    4. 条件路由和状态更新
    5. 缓存管理和条件访问
    6. 状态汇总和输出
    """
    print_step("交互式状态管理演示")
    
    app = build_state_management_graph()
    
    print("请输入测试数据:")
    user_input = input("输入数据 (回车使用默认数据): ").strip()
    if not user_input:
        user_input = "这是默认的测试输入数据，用于演示LangGraph状态管理功能。"
    
    initial_state = AdvancedWorkflowState(
        user_info={
            "user_id": "interactive_user",
            "user_name": "交互式用户"
        },
        session_data={},
        processing_history=[],
        current_step="interactive_start",
        step_counter=0,
        flags={},
        input_data=user_input,
        processed_data=None,
        output_data=None,
        metadata={},
        result_cache={},
        error_log=[]
    )
    
    try:
        result = app.invoke(initial_state)
        print_step("交互式演示完成！")
        
        # 显示部分结果
        final_output = result.get("output_data", "")
        processing_history = result.get("processing_history", [])
        
        print(f"处理结果: {final_output}")
        print(f"处理步骤: {len(processing_history)} 步")
        
    except Exception as e:
        print_error(f"交互式演示失败: {e}")

# 主程序
if __name__ == "__main__":
    print("🎯 LangGraph 状态管理深度演示")
    print("=" * 50)
    print("本演示将展示:")
    print("1. 复杂状态定义和管理")
    print("2. 状态初始化和验证")
    print("3. 状态更新和缓存管理")
    print("4. 条件状态访问")
    print("5. 状态汇总和输出")
    print("=" * 50)
    
    while True:
        print("\n请选择演示模式:")
        print("1. 基础状态管理演示")
        print("2. 交互式状态演示")
        print("0. 退出")
        
        choice = input("请输入选择 (0-2): ").strip()
        
        if choice == "1":
            run_state_management_demo()
        elif choice == "2":
            interactive_state_demo()
        elif choice == "0":
            print("感谢使用LangGraph状态管理演示！")
            break
        else:
            print("无效选择，请重新输入")
        
        print("\n" + "-" * 50)