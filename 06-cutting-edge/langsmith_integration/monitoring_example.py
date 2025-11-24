#!/usr/bin/env python3
"""
LangSmith监控和追踪示例
展示如何集成LangSmith进行工作流监控、调试和分析
"""

import os
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from langgraph.graph import StateGraph, START, END
from langsmith import Client, traceable
from langsmith.evaluation import evaluate
from langsmith.run_trees import RunTree
from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult

# 导入配置
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from config import get_llm


class LangSmithConfig:
    """LangSmith配置管理"""
    
    def __init__(self):
        self.api_key = os.getenv("LANGSMITH_API_KEY", "ls-kucVrtrSyaNjy8wqSjSjUg4NQqnDuHq9m")
        self.api_url = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        self.project_name = os.getenv("LANGSMITH_PROJECT", "langgraph-learning")
        self.enabled = os.getenv("LANGSMITH_ENABLED", "true").lower() == "true"
        
        # 初始化客户端
        if self.enabled:
            self.client = Client(
                api_key=self.api_key,
                api_url=self.api_url
            )
        else:
            self.client = None
    
    def get_client(self):
        """获取LangSmith客户端"""
        return self.client
    
    def is_enabled(self):
        """检查是否启用LangSmith"""
        return self.enabled and self.client is not None


class LangSmithCallbackHandler(BaseCallbackHandler):
    """LangSmith回调处理器"""
    
    def __init__(self, project_name: str = "langgraph-learning"):
        super().__init__()
        self.project_name = project_name
        self.runs = []
    
    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """LLM开始时调用"""
        print(f"🤖 LLM开始处理: {prompts[0][:50]}...")
        
        run_id = kwargs.get("run_id", str(uuid.uuid4()))
        self.runs.append({
            "run_id": run_id,
            "type": "llm",
            "start_time": datetime.now(),
            "prompts": prompts
        })
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """LLM结束时调用"""
        print(f"✅ LLM处理完成")
        
        run_id = kwargs.get("run_id")
        for run in self.runs:
            if run["run_id"] == run_id:
                run["end_time"] = datetime.now()
                run["response"] = response.generations[0][0].text if response.generations else ""
                break
    
    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """链开始时调用"""
        print(f"🔗 链开始: {serialized.get('name', 'Unknown')}")
        
        run_id = kwargs.get("run_id", str(uuid.uuid4()))
        self.runs.append({
            "run_id": run_id,
            "type": "chain",
            "start_time": datetime.now(),
            "chain_name": serialized.get('name', 'Unknown'),
            "inputs": inputs
        })
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """链结束时调用"""
        print(f"🔗 链结束")
        
        run_id = kwargs.get("run_id")
        for run in self.runs:
            if run["run_id"] == run_id:
                run["end_time"] = datetime.now()
                run["outputs"] = outputs
                break
    
    def get_runs(self) -> List[Dict[str, Any]]:
        """获取所有运行记录"""
        return self.runs
    
    def get_run_summary(self) -> Dict[str, Any]:
        """获取运行摘要"""
        summary = {
            "total_runs": len(self.runs),
            "llm_runs": len([r for r in self.runs if r["type"] == "llm"]),
            "chain_runs": len([r for r in self.runs if r["type"] == "chain"]),
            "total_duration": 0
        }
        
        for run in self.runs:
            if "start_time" in run and "end_time" in run:
                duration = (run["end_time"] - run["start_time"]).total_seconds()
                summary["total_duration"] += duration
        
        return summary


@traceable
def monitored_llm_call(prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """被监控的LLM调用"""
    print_step(f"执行监控的LLM调用: {prompt[:30]}...")
    
    llm = get_llm()
    
    # 添加上下文信息
    if context:
        enhanced_prompt = f"""
上下文信息: {context}

用户问题: {prompt}

请基于上下文回答用户问题:
"""
    else:
        enhanced_prompt = prompt
    
    start_time = time.time()
    
    try:
        response = llm.invoke(enhanced_prompt)
        end_time = time.time()
        
        return {
            "response": response.content,
            "prompt": enhanced_prompt,
            "duration": end_time - start_time,
            "success": True,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        end_time = time.time()
        
        return {
            "response": f"错误: {str(e)}",
            "prompt": enhanced_prompt,
            "duration": end_time - start_time,
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


def create_monitored_workflow(config: LangSmithConfig):
    """创建带监控的工作流"""
    
    from typing_extensions import TypedDict
    
    class MonitoringState(TypedDict):
        messages: List[Dict[str, str]]
        current_input: str
        response: str
        metadata: Dict[str, Any]
        performance_metrics: Dict[str, Any]
    
    def input_processing(state: MonitoringState) -> MonitoringState:
        """输入处理节点"""
        print_step("输入处理")
        
        current_input = state.get("current_input", "")
        
        # 分析输入
        input_analysis = {
            "length": len(current_input),
            "word_count": len(current_input.split()),
            "language": "zh" if any('\u4e00' <= char <= '\u9fff' for char in current_input) else "en",
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            **state,
            "metadata": {**state.get("metadata", {}), "input_analysis": input_analysis}
        }
    
    def ai_processing(state: MonitoringState) -> MonitoringState:
        """AI处理节点"""
        print_step("AI处理")
        
        current_input = state.get("current_input", "")
        metadata = state.get("metadata", {})
        
        # 执行被监控的LLM调用
        result = monitored_llm_call(current_input, metadata)
        
        # 更新性能指标
        performance_metrics = state.get("performance_metrics", {})
        performance_metrics.update({
            "ai_processing_duration": result.get("duration", 0),
            "ai_processing_success": result.get("success", False),
            "last_ai_call": result.get("timestamp")
        })
        
        return {
            **state,
            "response": result.get("response", ""),
            "performance_metrics": performance_metrics
        }
    
    def response_postprocessing(state: MonitoringState) -> MonitoringState:
        """响应后处理节点"""
        print_step("响应后处理")
        
        response = state.get("response", "")
        metadata = state.get("metadata", {})
        
        # 分析响应
        response_analysis = {
            "length": len(response),
            "word_count": len(response.split()),
            "sentiment": "positive",  # 简化的情感分析
            "timestamp": datetime.now().isoformat()
        }
        
        # 更新元数据
        updated_metadata = {
            **metadata,
            "response_analysis": response_analysis
        }
        
        return {
            **state,
            "metadata": updated_metadata
        }
    
    def performance_tracking(state: MonitoringState) -> MonitoringState:
        """性能追踪节点"""
        print_step("性能追踪")
        
        performance_metrics = state.get("performance_metrics", {})
        metadata = state.get("metadata", {})
        
        # 计算总体性能指标
        input_analysis = metadata.get("input_analysis", {})
        response_analysis = metadata.get("response_analysis", {})
        
        overall_metrics = {
            **performance_metrics,
            "total_processing_time": performance_metrics.get("ai_processing_duration", 0),
            "input_to_output_ratio": len(response_analysis.get("response", "")) / max(len(input_analysis.get("input", "")), 1),
            "processing_timestamp": datetime.now().isoformat()
        }
        
        return {
            **state,
            "performance_metrics": overall_metrics
        }
    
    # 构建工作流
    workflow = StateGraph(MonitoringState)
    
    # 添加节点
    workflow.add_node("input_processing", input_processing)
    workflow.add_node("ai_processing", ai_processing)
    workflow.add_node("response_postprocessing", response_postprocessing)
    workflow.add_node("performance_tracking", performance_tracking)
    
    # 添加边
    workflow.add_edge(START, "input_processing")
    workflow.add_edge("input_processing", "ai_processing")
    workflow.add_edge("ai_processing", "response_postprocessing")
    workflow.add_edge("response_postprocessing", "performance_tracking")
    workflow.add_edge("performance_tracking", END)
    
    return workflow.compile()


def print_step(step: str):
    """打印步骤信息"""
    print(f"🔍 {step}")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)


def demonstrate_basic_monitoring():
    """演示基础监控功能"""
    print("🔍 演示基础监控功能")
    print("=" * 60)
    
    # 创建配置
    config = LangSmithConfig()
    
    if not config.is_enabled():
        print("⚠️  LangSmith未启用，跳过监控演示")
        return
    
    # 创建回调处理器
    callback_handler = LangSmithCallbackHandler("langgraph-learning-demo")
    
    # 创建被监控的工作流
    workflow = create_monitored_workflow(config)
    
    # 测试输入
    test_inputs = [
        "什么是LangGraph？",
        "LangGraph有什么优势？",
        "如何监控LangGraph应用？"
    ]
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n📝 测试 {i}: {user_input}")
        
        # 初始状态
        initial_state = {
            "messages": [],
            "current_input": user_input,
            "response": "",
            "metadata": {},
            "performance_metrics": {}
        }
        
        # 运行工作流（带回调）
        start_time = time.time()
        config_params = {"callbacks": [callback_handler]}
        result = workflow.invoke(initial_state, config=config_params)
        end_time = time.time()
        
        # 显示结果
        response = result.get("response", "")
        performance = result.get("performance_metrics", {})
        
        print(f"🤖 回复: {response[:100]}...")
        print(f"⏱️  处理时间: {end_time - start_time:.2f}秒")
        print(f"📊 AI处理时间: {performance.get('ai_processing_duration', 0):.2f}秒")
        print(f"✅ 处理成功: {performance.get('ai_processing_success', False)}")
    
    # 显示运行摘要
    summary = callback_handler.get_run_summary()
    print(f"\n📊 运行摘要:")
    print(f"   总运行次数: {summary['total_runs']}")
    print(f"   LLM调用次数: {summary['llm_runs']}")
    print(f"   链运行次数: {summary['chain_runs']}")
    print(f"   总耗时: {summary['total_duration']:.2f}秒")


def demonstrate_traceable_functions():
    """演示可追踪函数"""
    print("\n🎯 演示可追踪函数")
    print("=" * 60)
    
    # 配置
    config = LangSmithConfig()
    
    if not config.is_enabled():
        print("⚠️  LangSmith未启用，跳过演示")
        return
    
    # 测试可追踪函数
    test_cases = [
        {"prompt": "解释什么是人工智能", "context": {"topic": "technology"}},
        {"prompt": "如何学习编程", "context": {"level": "beginner"}},
        {"prompt": "介绍LangGraph", "context": {"framework": "langchain"}}
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 测试 {i}: {test_case['prompt']}")
        
        result = monitored_llm_call(
            test_case["prompt"], 
            test_case["context"]
        )
        
        print(f"🤖 回复: {result['response'][:100]}...")
        print(f"⏱️  耗时: {result['duration']:.2f}秒")
        print(f"✅ 成功: {result['success']}")
        print(f"🕐 时间戳: {result['timestamp']}")


def demonstrate_evaluation_metrics():
    """演示评估指标"""
    print("\n📈 演示评估指标")
    print("=" * 60)
    
    # 配置
    config = LangSmithConfig()
    
    if not config.is_enabled() or not config.client:
        print("⚠️  LangSmith客户端未配置，跳过评估演示")
        return
    
    # 定义评估数据集
    dataset = [
        {
            "input": "什么是LangGraph？",
            "expected_output": "LangGraph是一个用于构建状态图、工作流和智能代理的框架"
        },
        {
            "input": "LangGraph有哪些优势？", 
            "expected_output": "LangGraph的优势包括状态管理、条件路由、并行处理等"
        }
    ]
    
    def run_evaluator(input_text: str):
        """运行评估器"""
        result = monitored_llm_call(input_text)
        return result.get("response", "")
    
    # 简单的评估函数
    def simple_evaluator(run, example):
        """简单评估函数"""
        output = run.outputs.get("output", "")
        expected = example.outputs.get("expected_output", "")
        
        # 计算相似度（简化版）
        output_words = set(output.lower().split())
        expected_words = set(expected.lower().split())
        
        if len(expected_words) == 0:
            similarity = 0.0
        else:
            common_words = output_words & expected_words
            similarity = len(common_words) / len(expected_words)
        
        return {"score": similarity}
    
    try:
        # 运行评估（这里只是演示，实际需要真实的LangSmith项目）
        print("📊 评估指标:")
        print("   - 准确性 (Accuracy)")
        print("   - 响应时间 (Response Time)")
        print("   - 成功率 (Success Rate)")
        print("   - 用户满意度 (User Satisfaction)")
        
        print("\n📝 评估结果（模拟）:")
        for i, example in enumerate(dataset, 1):
            input_text = example["input"]
            expected_output = example["expected_output"]
            
            # 运行评估
            actual_output = run_evaluator(input_text)
            
            # 计算指标
            output_words = set(actual_output.lower().split())
            expected_words = set(expected_output.lower().split())
            
            if len(expected_words) == 0:
                similarity = 0.0
            else:
                common_words = output_words & expected_words
                similarity = len(common_words) / len(expected_words)
            
            print(f"   测试 {i}:")
            print(f"     输入: {input_text}")
            print(f"     预期: {expected_output}")
            print(f"     实际: {actual_output[:100]}...")
            print(f"     相似度: {similarity:.2f}")
    
    except Exception as e:
        print(f"⚠️  评估过程中出现错误: {e}")


def demonstrate_error_tracking():
    """演示错误追踪"""
    print("\n🚨 演示错误追踪")
    print("=" * 60)
    
    # 配置
    config = LangSmithConfig()
    
    # 故意制造错误的测试
    error_test_cases = [
        {"prompt": "", "description": "空输入测试"},
        {"prompt": "x" * 10000, "description": "超长输入测试"},
        {"prompt": "故意触发的错误测试", "description": "异常处理测试"}
    ]
    
    for i, test_case in enumerate(error_test_cases, 1):
        print(f"\n🧪 错误测试 {i}: {test_case['description']}")
        
        try:
            result = monitored_llm_call(
                test_case["prompt"],
                {"test_type": test_case["description"]}
            )
            
            print(f"📊 结果:")
            print(f"   成功: {result['success']}")
            print(f"   耗时: {result['duration']:.2f}秒")
            
            if not result['success']:
                print(f"   错误: {result.get('error', 'Unknown error')}")
            else:
                print(f"   回复: {result['response'][:100]}...")
        
        except Exception as e:
            print(f"❌ 捕获到异常: {e}")
            print(f"   这展示了LangSmith如何追踪和处理异常")


if __name__ == "__main__":
    print("🔍 LangSmith 监控和追踪演示")
    print("=" * 60)
    
    try:
        # 检查环境变量
        print("🔧 配置检查:")
        config = LangSmithConfig()
        print(f"   LangSmith启用: {config.enabled}")
        print(f"   项目名称: {config.project_name}")
        print(f"   API URL: {config.api_url}")
        print(f"   客户端状态: {'已连接' if config.is_enabled() else '未连接'}")
        
        print("\n" + "=" * 60)
        
        # 演示各种功能
        demonstrate_basic_monitoring()
        demonstrate_traceable_functions()
        demonstrate_evaluation_metrics()
        demonstrate_error_tracking()
        
        print("\n✅ LangSmith集成演示完成！")
        print("💡 提示: 访问 https://smith.langchain.com 查看详细监控数据")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()