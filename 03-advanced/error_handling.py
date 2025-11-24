"""
03-advanced: 错误处理和恢复

本示例展示LangGraph中高级错误处理机制，
包括异常捕获、自动重试、断路器模式和优雅降级。

学习要点：
1. 异常捕获和处理
2. 自动重试和回退
3. 断路器模式
4. 错误恢复策略
"""

from typing import TypedDict, List, Dict, Any, Optional, Callable
from langgraph.graph import StateGraph, END
import sys
import os
import time
import random
import logging
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
import json

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import print_step, print_result, print_error

# 1. 错误处理状态定义
class ErrorHandlingState(TypedDict):
    """
    错误处理工作流状态
    """
    task_data: Dict[str, Any]
    current_step: str
    error_history: List[Dict[str, Any]]
    retry_count: int
    circuit_breaker_status: Dict[str, Any]
    fallback_data: Dict[str, Any]
    final_result: Dict[str, Any]
    error_stats: Dict[str, Any]

class CircuitState(Enum):
    """断路器状态"""
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 断路状态
    HALF_OPEN = "half_open"  # 半开状态

class CircuitBreaker:
    """
    断路器实现
    """
    
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
    
    def call(self, func: Callable, *args, **kwargs):
        """调用受保护的函数"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """是否应该尝试重置断路器"""
        if self.last_failure_time is None:
            return False
        return (datetime.now() - self.last_failure_time).seconds >= self.recovery_timeout
    
    def _on_success(self):
        """成功时的处理"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """失败时的处理"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def get_status(self) -> Dict[str, Any]:
        """获取断路器状态"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }

# 2. 重试装饰器和工具

def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, 
          exceptions: tuple = (Exception,)):
    """
    重试装饰器
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (backoff ** attempt)
                        print(f"重试第 {attempt + 1} 次，等待 {wait_time:.1f}s 后继续...")
                        time.sleep(wait_time)
                    else:
                        print(f"重试 {max_attempts} 次后仍然失败")
            
            raise last_exception
        return wrapper
    return decorator

class ErrorHandler:
    """
    错误处理器
    """
    
    def __init__(self):
        self.circuit_breakers = {}
        self.error_log = []
    
    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """获取或创建断路器"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """记录错误"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        self.error_log.append(error_entry)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计"""
        if not self.error_log:
            return {"total_errors": 0}
        
        error_types = {}
        for error in self.error_log:
            error_type = error["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.error_log),
            "error_types": error_types,
            "recent_errors": [error for error in self.error_log[-5:]]
        }

# 全局错误处理器
error_handler = ErrorHandler()

# 3. 模拟外部服务和处理节点

@retry(max_attempts=3, delay=1.0, backoff=2.0)
def unreliable_service_call(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    模拟不可靠的服务调用
    """
    # 模拟失败率
    if random.random() < 0.3:  # 30% 失败率
        raise Exception("服务暂时不可用")
    
    # 模拟处理延迟
    time.sleep(random.uniform(0.5, 2.0))
    
    return {
        "status": "success",
        "processed_data": data,
        "processing_time": random.uniform(0.5, 2.0),
        "timestamp": datetime.now().isoformat()
    }

def circuit_breaker_service_call(service_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    使用断路器的服务调用
    """
    circuit_breaker = error_handler.get_circuit_breaker(service_name)
    
    def call_service():
        # 模拟服务调用
        if random.random() < 0.4:  # 40% 失败率
            raise Exception(f"服务 {service_name} 调用失败")
        
        time.sleep(random.uniform(0.3, 1.5))
        return {
            "service": service_name,
            "status": "success",
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        result = circuit_breaker.call(call_service)
        return result
    except Exception as e:
        error_handler.log_error(e, {"service": service_name, "data": data})
        raise e

# 4. 错误处理节点

def data_preprocessing(state: ErrorHandlingState) -> ErrorHandlingState:
    """
    数据预处理节点
    """
    print_step("数据预处理")
    
    task_data = state.get("task_data", {})
    error_history = state.get("error_history", [])
    
    try:
        # 验证数据
        if not task_data.get("input"):
            raise ValueError("输入数据为空")
        
        # 模拟处理
        processed_data = {
            **task_data,
            "preprocessed": True,
            "preprocessing_timestamp": datetime.now().isoformat()
        }
        
        print_result("数据预处理完成")
        
        return {
            "task_data": processed_data,
            "current_step": "preprocessing"
        }
        
    except Exception as e:
        error_entry = {
            "step": "preprocessing",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        error_history.append(error_entry)
        error_handler.log_error(e, {"step": "preprocessing", "data": task_data})
        
        print_error(f"数据预处理失败: {e}")
        
        return {
            "error_history": error_history,
            "current_step": "preprocessing_error"
        }

def primary_processing(state: ErrorHandlingState) -> ErrorHandlingState:
    """
    主要处理节点
    """
    print_step("主要处理")
    
    task_data = state.get("task_data", {})
    error_history = state.get("error_history", [])
    retry_count = state.get("retry_count", 0)
    
    try:
        # 使用重试机制的服务调用
        result = unreliable_service_call(task_data)
        
        processed_data = {
            **task_data,
            "primary_result": result,
            "processing_timestamp": datetime.now().isoformat()
        }
        
        print_result("主要处理完成")
        
        return {
            "task_data": processed_data,
            "current_step": "primary_processing",
            "retry_count": 0  # 重置重试计数
        }
        
    except Exception as e:
        print_error(f"主要处理失败: {e}")
        
        error_entry = {
            "step": "primary_processing",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "retry_count": retry_count
        }
        error_history.append(error_entry)
        error_handler.log_error(e, {"step": "primary_processing", "retry_count": retry_count})
        
        return {
            "error_history": error_history,
            "current_step": "primary_processing_error",
            "retry_count": retry_count + 1
        }

def secondary_processing(state: ErrorHandlingState) -> ErrorHandlingState:
    """
    备用处理节点
    """
    print_step("备用处理")
    
    task_data = state.get("task_data", {})
    error_history = state.get("error_history", [])
    
    try:
        # 使用断路器保护的服务调用
        result = circuit_breaker_service_call("secondary_service", task_data)
        
        processed_data = {
            **task_data,
            "secondary_result": result,
            "processing_timestamp": datetime.now().isoformat(),
            "processing_mode": "fallback"
        }
        
        print_result("备用处理完成")
        
        return {
            "task_data": processed_data,
            "current_step": "secondary_processing"
        }
        
    except Exception as e:
        print_error(f"备用处理失败: {e}")
        
        error_entry = {
            "step": "secondary_processing",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        error_history.append(error_entry)
        error_handler.log_error(e, {"step": "secondary_processing"})
        
        return {
            "error_history": error_history,
            "current_step": "secondary_processing_error"
        }

def fallback_processing(state: ErrorHandlingState) -> ErrorHandlingState:
    """
    降级处理节点
    """
    print_step("降级处理")
    
    task_data = state.get("task_data", {})
    fallback_data = state.get("fallback_data", {})
    
    # 提供基本的降级服务
    basic_result = {
        "status": "degraded",
        "message": "使用降级服务",
        "basic_functionality": True,
        "limited_features": True,
        "timestamp": datetime.now().isoformat()
    }
    
    processed_data = {
        **task_data,
        "fallback_result": basic_result,
        "processing_mode": "degraded",
        "timestamp": datetime.now().isoformat()
    }
    
    # 更新降级数据
    new_fallback_data = {
        **fallback_data,
        "last_used": datetime.now().isoformat(),
        "usage_count": fallback_data.get("usage_count", 0) + 1
    }
    
    print_result("降级处理完成")
    
    return {
        "task_data": processed_data,
        "fallback_data": new_fallback_data,
        "current_step": "fallback_processing"
    }

def error_analysis(state: ErrorHandlingState) -> ErrorHandlingState:
    """
    错误分析节点
    """
    print_step("错误分析")
    
    error_history = state.get("error_history", [])
    circuit_breaker_status = {}
    
    # 收集所有断路器状态
    for service_name, circuit_breaker in error_handler.circuit_breakers.items():
        circuit_breaker_status[service_name] = circuit_breaker.get_status()
    
    # 分析错误模式
    error_stats = error_handler.get_error_stats()
    
    print(f"错误分析完成:")
    print(f"  - 总错误数: {error_stats.get('total_errors', 0)}")
    print(f"  - 错误类型: {error_stats.get('error_types', {})}")
    print(f"  - 断路器状态: {list(circuit_breaker_status.keys())}")
    
    return {
        "circuit_breaker_status": circuit_breaker_status,
        "error_stats": error_stats,
        "current_step": "error_analysis"
    }

def recovery_strategy(state: ErrorHandlingState) -> ErrorHandlingState:
    """
    恢复策略节点
    """
    print_step("执行恢复策略")
    
    error_history = state.get("error_history", [])
    retry_count = state.get("retry_count", 0)
    current_step = state.get("current_step", "")
    
    # 根据错误历史决定恢复策略
    if current_step == "primary_processing_error" and retry_count < 3:
        recovery_action = "retry_primary"
        message = "将重试主要处理"
    elif len(error_history) > 5:
        recovery_action = "use_secondary"
        message = "错误过多，切换到备用处理"
    else:
        recovery_action = "use_fallback"
        message = "使用降级处理"
    
    print(f"恢复策略: {message}")
    
    return {
        "current_step": f"recovery_{recovery_action}"
    }

def final_result_generation(state: ErrorHandlingState) -> ErrorHandlingState:
    """
    最终结果生成节点
    """
    print_step("生成最终结果")
    
    task_data = state.get("task_data", {})
    error_history = state.get("error_history", [])
    circuit_breaker_status = state.get("circuit_breaker_status", {})
    error_stats = state.get("error_stats", {})
    
    # 确定最终结果
    final_result = {}
    
    if "primary_result" in task_data:
        final_result = {
            "status": "success",
            "processing_mode": "primary",
            "result": task_data["primary_result"]
        }
    elif "secondary_result" in task_data:
        final_result = {
            "status": "success",
            "processing_mode": "secondary",
            "result": task_data["secondary_result"]
        }
    elif "fallback_result" in task_data:
        final_result = {
            "status": "degraded",
            "processing_mode": "fallback",
            "result": task_data["fallback_result"]
        }
    else:
        final_result = {
            "status": "failed",
            "error": "所有处理方式都失败",
            "error_count": len(error_history)
        }
    
    final_result.update({
        "processing_summary": {
            "total_errors": len(error_history),
            "circuit_breakers": list(circuit_breaker_status.keys()),
            "error_types": error_stats.get("error_types", {}),
            "final_timestamp": datetime.now().isoformat()
        }
    })
    
    print_result("最终结果生成完成")
    print(f"处理状态: {final_result['status']}")
    print(f"处理模式: {final_result.get('processing_mode', 'unknown')}")
    
    return {
        "final_result": final_result
    }

# 5. 路由函数

def route_after_preprocessing(state: ErrorHandlingState) -> Literal["primary", "error"]:
    """
    预处理后的路由
    """
    current_step = state.get("current_step", "")
    
    if current_step == "preprocessing":
        print("路由: primary (预处理成功)")
        return "primary"
    else:
        print("路由: error (预处理失败)")
        return "error"

def route_after_primary(state: ErrorHandlingState) -> Literal["success", "retry", "secondary"]:
    """
    主要处理后的路由
    """
    current_step = state.get("current_step", "")
    retry_count = state.get("retry_count", 0)
    
    if current_step == "primary_processing":
        print("路由: success (主要处理成功)")
        return "success"
    elif retry_count < 3:
        print("路由: retry (重试主要处理)")
        return "retry"
    else:
        print("路由: secondary (切换到备用处理)")
        return "secondary"

def route_after_secondary(state: ErrorHandlingState) -> Literal["success", "fallback"]:
    """
    备用处理后的路由
    """
    current_step = state.get("current_step", "")
    
    if current_step == "secondary_processing":
        print("路由: success (备用处理成功)")
        return "success"
    else:
        print("路由: fallback (降级处理)")
        return "fallback"

def route_after_recovery(state: ErrorHandlingState) -> Literal["primary", "secondary", "fallback"]:
    """
    恢复策略后的路由
    """
    current_step = state.get("current_step", "")
    
    if "retry_primary" in current_step:
        print("路由: primary (重试主要处理)")
        return "primary"
    elif "use_secondary" in current_step:
        print("路由: secondary (使用备用处理)")
        return "secondary"
    else:
        print("路由: fallback (使用降级处理)")
        return "fallback"

# 6. 构建错误处理工作流

def build_error_handling_workflow():
    """构建错误处理工作流"""
    print_step("构建错误处理工作流")
    
    workflow = StateGraph(ErrorHandlingState)
    
    # 添加节点
    workflow.add_node("preprocessing", data_preprocessing)
    workflow.add_node("primary_processing", primary_processing)
    workflow.add_node("secondary_processing", secondary_processing)
    workflow.add_node("fallback_processing", fallback_processing)
    workflow.add_node("error_analysis", error_analysis)
    workflow.add_node("recovery_strategy", recovery_strategy)
    workflow.add_node("final_result", final_result_generation)
    
    # 设置入口点
    workflow.set_entry_point("preprocessing")
    
    # 添加边
    workflow.add_conditional_edges(
        "preprocessing",
        route_after_preprocessing,
        {
            "primary": "primary_processing",
            "error": "error_analysis"
        }
    )
    
    workflow.add_conditional_edges(
        "primary_processing",
        route_after_primary,
        {
            "success": "final_result",
            "retry": "primary_processing",
            "secondary": "secondary_processing"
        }
    )
    
    workflow.add_conditional_edges(
        "secondary_processing",
        route_after_secondary,
        {
            "success": "final_result",
            "fallback": "fallback_processing"
        }
    )
    
    workflow.add_edge("fallback_processing", "final_result")
    workflow.add_edge("error_analysis", "recovery_strategy")
    workflow.add_conditional_edges(
        "recovery_strategy",
        route_after_recovery,
        {
            "primary": "primary_processing",
            "secondary": "secondary_processing",
            "fallback": "fallback_processing"
        }
    )
    
    workflow.add_edge("final_result", END)
    
    return workflow.compile()

# 7. 演示函数

def demo_error_handling():
    """演示错误处理"""
    print_step("错误处理演示")
    
    app = build_error_handling_workflow()
    
    initial_state = {
        "task_data": {
            "input": "测试数据",
            "parameters": {"timeout": 10}
        },
        "current_step": "",
        "error_history": [],
        "retry_count": 0,
        "circuit_breaker_status": {},
        "fallback_data": {},
        "final_result": {},
        "error_stats": {}
    }
    
    print("开始错误处理演示...")
    
    start_time = time.time()
    result = app.invoke(initial_state)
    end_time = time.time()
    
    print(f"\n执行完成，总耗时: {end_time - start_time:.2f}s")
    
    # 显示最终结果
    final_result = result.get("final_result", {})
    print(f"\n最终结果:")
    for key, value in final_result.items():
        print(f"  {key}: {value}")
    
    # 显示错误统计
    error_stats = result.get("error_stats", {})
    if error_stats:
        print(f"\n错误统计:")
        print(f"  总错误数: {error_stats.get('total_errors', 0)}")
        print(f"  错误类型: {error_stats.get('error_types', {})}")

def demo_circuit_breaker():
    """演示断路器"""
    print_step("断路器演示")
    
    # 测试断路器
    for i in range(10):
        try:
            result = circuit_breaker_service_call("test_service", {"request": i})
            print(f"请求 {i+1}: 成功")
        except Exception as e:
            print(f"请求 {i+1}: 失败 - {e}")
        
        # 显示断路器状态
        circuit_breaker = error_handler.get_circuit_breaker("test_service")
        status = circuit_breaker.get_status()
        print(f"  断路器状态: {status['state']} (失败次数: {status['failure_count']})")
        
        time.sleep(0.5)

def demo_retry_mechanism():
    """演示重试机制"""
    print_step("重试机制演示")
    
    try:
        # 这会失败并重试
        result = unreliable_service_call({"test": "data"})
        print(f"重试成功: {result}")
    except Exception as e:
        print(f"重试失败: {e}")

# 主程序
if __name__ == "__main__":
    print("🛡️ LangGraph 错误处理学习程序")
    print("=" * 60)
    
    while True:
        print("\n请选择演示:")
        print("1. 完整错误处理工作流")
        print("2. 断路器机制")
        print("3. 重试机制")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-3): ").strip()
        
        if choice == "1":
            demo_error_handling()
        elif choice == "2":
            demo_circuit_breaker()
        elif choice == "3":
            demo_retry_mechanism()
        elif choice == "0":
            print_step("感谢学习错误处理！")
            break
        else:
            print_error("无效选择，请重试")
    
    print_result("错误处理学习完成！")