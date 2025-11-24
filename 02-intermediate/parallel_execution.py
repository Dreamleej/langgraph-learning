"""
02-intermediate: 并行执行处理

本示例展示LangGraph中并行执行的技术，包括任务分叉、
并行处理和结果合并等高级特性。

学习要点：
1. 并行节点定义
2. 数据分叉和合并
3. 异步任务处理
4. 性能优化策略
"""

from typing import TypedDict, Literal, Dict, List, Any
from langgraph.graph import StateGraph, END
import sys
import os
import time
import asyncio
import concurrent.futures
import random

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import print_step, print_result, print_error

# 1. 状态定义
class ParallelState(TypedDict):
    """
    并行执行工作流状态
    """
    input_data: Dict[str, Any]
    parallel_results: Dict[str, Any]
    merged_result: Dict[str, Any]
    execution_times: Dict[str, float]
    task_status: Dict[str, str]
    total_time: float

class DataProcessingState(TypedDict):
    """
    数据处理并行状态
    """
    raw_data: List[Dict[str, Any]]
    processed_chunks: List[Dict[str, Any]]
    analysis_results: Dict[str, Any]
    final_report: str
    processing_stats: Dict[str, Any]

class AnalysisState(TypedDict):
    """
    分析并行状态
    """
    source_data: Dict[str, Any]
    sentiment_result: Dict[str, Any]
    classification_result: Dict[str, Any]
    extraction_result: Dict[str, Any]
    combined_analysis: Dict[str, Any]

# 2. 并行处理函数

def simulate_processing_task(task_name: str, duration_range: tuple = (1, 3)) -> Dict[str, Any]:
    """
    模拟处理任务
    """
    start_time = time.time()
    duration = random.uniform(*duration_range)
    
    print(f"🔄 开始执行 {task_name} (预计 {duration:.1f}s)")
    
    # 模拟处理时间
    time.sleep(duration)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    result = {
        "task_name": task_name,
        "status": "completed",
        "execution_time": execution_time,
        "output": f"{task_name} 的处理结果",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    print(f"✅ 完成执行 {task_name} (耗时 {execution_time:.1f}s)")
    
    return result

def data_analyzer(data: Dict[str, Any]) -> Dict[str, Any]:
    """数据分析任务"""
    time.sleep(random.uniform(0.5, 1.5))
    
    numeric_values = [v for v in data.values() if isinstance(v, (int, float))]
    text_values = [v for v in data.values() if isinstance(v, str)]
    
    return {
        "analysis_type": "data_analysis",
        "numeric_count": len(numeric_values),
        "text_count": len(text_values),
        "total_items": len(data),
        "numeric_sum": sum(numeric_values) if numeric_values else 0,
        "numeric_avg": sum(numeric_values) / len(numeric_values) if numeric_values else 0
    }

def sentiment_analyzer(text_data: Dict[str, Any]) -> Dict[str, Any]:
    """情感分析任务"""
    time.sleep(random.uniform(1.0, 2.0))
    
    texts = [v for v in text_data.values() if isinstance(v, str)]
    
    # 模拟情感分析
    sentiments = []
    for text in texts:
        if len(text) % 3 == 0:
            sentiment = "positive"
        elif len(text) % 3 == 1:
            sentiment = "neutral"
        else:
            sentiment = "negative"
        sentiments.append(sentiment)
    
    return {
        "analysis_type": "sentiment_analysis",
        "analyzed_texts": len(texts),
        "sentiments": sentiments,
        "positive_count": sentiments.count("positive"),
        "negative_count": sentiments.count("negative"),
        "neutral_count": sentiments.count("neutral")
    }

def keyword_extractor(text_data: Dict[str, Any]) -> Dict[str, Any]:
    """关键词提取任务"""
    time.sleep(random.uniform(0.8, 1.8))
    
    # 模拟关键词提取
    all_text = " ".join([str(v) for v in text_data.values()])
    words = all_text.split()
    
    # 简单的关键词提取（取前5个最长的词）
    keywords = sorted(set(words), key=len, reverse=True)[:5]
    
    return {
        "analysis_type": "keyword_extraction",
        "total_words": len(words),
        "unique_words": len(set(words)),
        "extracted_keywords": keywords,
        "keyword_count": len(keywords)
    }

# 3. 并行执行节点

def parallel_data_processing(state: ParallelState) -> ParallelState:
    """
    并行数据处理节点
    """
    print_step("开始并行数据处理")
    
    input_data = state.get("input_data", {})
    parallel_results = state.get("parallel_results", {})
    execution_times = state.get("execution_times", {})
    
    # 定义并行任务
    tasks = {
        "task1": lambda: simulate_processing_task("数据清洗", (1, 2)),
        "task2": lambda: simulate_processing_task("数据转换", (0.5, 1.5)),
        "task3": lambda: simulate_processing_task("数据验证", (0.8, 1.2))
    }
    
    # 使用ThreadPoolExecutor执行并行任务
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # 提交所有任务
        future_to_task = {
            executor.submit(task_func): task_name 
            for task_name, task_func in tasks.items()
        }
        
        # 收集结果
        for future in concurrent.futures.as_completed(future_to_task):
            task_name = future_to_task[future]
            try:
                result = future.result()
                parallel_results[task_name] = result
                execution_times[task_name] = result["execution_time"]
            except Exception as exc:
                print(f"任务 {task_name} 执行失败: {exc}")
                parallel_results[task_name] = {"status": "failed", "error": str(exc)}
                execution_times[task_name] = 0.0
    
    print(f"并行处理完成，共执行 {len(parallel_results)} 个任务")
    
    return {
        "parallel_results": parallel_results,
        "execution_times": execution_times,
        "task_status": {k: v.get("status", "unknown") for k, v in parallel_results.items()}
    }

def parallel_analysis(state: ParallelState) -> ParallelState:
    """
    并行分析节点
    """
    print_step("开始并行分析")
    
    input_data = state.get("input_data", {})
    parallel_results = state.get("parallel_results", {})
    execution_times = state.get("execution_times", {})
    
    # 并行分析任务
    analysis_tasks = {
        "data_analysis": lambda: data_analyzer(input_data),
        "sentiment_analysis": lambda: sentiment_analyzer(input_data),
        "keyword_extraction": lambda: keyword_extractor(input_data)
    }
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_task = {
            executor.submit(task_func): task_name 
            for task_name, task_func in analysis_tasks.items()
        }
        
        for future in concurrent.futures.as_completed(future_to_task):
            task_name = future_to_task[future]
            try:
                result = future.result()
                parallel_results[task_name] = result
                execution_times[task_name] = time.time()  # 记录完成时间
            except Exception as exc:
                print(f"分析任务 {task_name} 失败: {exc}")
                parallel_results[task_name] = {"analysis_type": task_name, "error": str(exc)}
    
    print(f"并行分析完成")
    
    return {
        "parallel_results": parallel_results,
        "execution_times": execution_times
    }

def results_merger(state: ParallelState) -> ParallelState:
    """
    结果合并节点
    """
    print_step("合并并行结果")
    
    parallel_results = state.get("parallel_results", {})
    execution_times = state.get("execution_times", {})
    
    # 合并所有结果
    merged_result = {
        "summary": {
            "total_tasks": len(parallel_results),
            "successful_tasks": len([r for r in parallel_results.values() 
                                   if r.get("status") == "completed"]),
            "failed_tasks": len([r for r in parallel_results.values() 
                                if r.get("status") == "failed"]),
            "total_execution_time": sum(execution_times.values())
        },
        "detailed_results": parallel_results,
        "performance_metrics": {
            "average_task_time": sum(execution_times.values()) / len(execution_times) 
                                 if execution_times else 0,
            "fastest_task": min(execution_times.items(), key=lambda x: x[1]) 
                           if execution_times else ("none", 0),
            "slowest_task": max(execution_times.items(), key=lambda x: x[1]) 
                           if execution_times else ("none", 0)
        }
    }
    
    print_result(f"结果合并完成")
    print(f"  - 总任务数: {merged_result['summary']['total_tasks']}")
    print(f"  - 成功任务: {merged_result['summary']['successful_tasks']}")
    print(f"  - 失败任务: {merged_result['summary']['failed_tasks']}")
    print(f"  - 总耗时: {merged_result['summary']['total_execution_time']:.2f}s")
    
    return {
        "merged_result": merged_result
    }

# 4. 数据处理并行节点

def data_splitter(state: DataProcessingState) -> DataProcessingState:
    """
    数据分割节点
    """
    print_step("分割数据以进行并行处理")
    
    raw_data = state.get("raw_data", [])
    
    # 将数据分成多个块
    chunk_size = max(1, len(raw_data) // 3)
    chunks = [raw_data[i:i + chunk_size] for i in range(0, len(raw_data), chunk_size)]
    
    print(f"原始数据: {len(raw_data)} 条记录")
    print(f"分割成 {len(chunks)} 个块")
    
    return {
        "processed_chunks": chunks
    }

def parallel_chunk_processor(state: DataProcessingState) -> DataProcessingState:
    """
    并行块处理节点
    """
    print_step("并行处理数据块")
    
    chunks = state.get("processed_chunks", [])
    processed_results = []
    
    def process_chunk(chunk: List[Dict[str, Any]], chunk_id: int) -> Dict[str, Any]:
        """处理单个数据块"""
        start_time = time.time()
        
        # 模拟处理逻辑
        processed_items = []
        for item in chunk:
            processed_item = {
                **item,
                "processed": True,
                "chunk_id": chunk_id,
                "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            processed_items.append(processed_item)
        
        time.sleep(random.uniform(0.5, 1.5))  # 模拟处理时间
        
        end_time = time.time()
        
        return {
            "chunk_id": chunk_id,
            "processed_items": processed_items,
            "item_count": len(processed_items),
            "processing_time": end_time - start_time
        }
    
    # 并行处理所有块
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(process_chunk, chunk, i) 
            for i, chunk in enumerate(chunks)
        ]
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            processed_results.append(result)
            print(f"块 {result['chunk_id']} 处理完成: {result['item_count']} 条记录")
    
    return {
        "processed_chunks": processed_results
    }

def parallel_analyzer(state: DataProcessingState) -> DataProcessingState:
    """
    并行分析节点
    """
    print_step("并行分析处理结果")
    
    chunks = state.get("processed_chunks", [])
    analysis_results = {}
    
    # 定义分析任务
    def analyze_statistics(chunks):
        """统计分析"""
        all_items = []
        for chunk in chunks:
            all_items.extend(chunk.get("processed_items", []))
        
        return {
            "total_items": len(all_items),
            "unique_chunks": len(set(item.get("chunk_id") for item in all_items)),
            "processing_times": [chunk.get("processing_time", 0) for chunk in chunks]
        }
    
    def analyze_quality(chunks):
        """质量分析"""
        total_items = sum(chunk.get("item_count", 0) for chunk in chunks)
        processing_times = [chunk.get("processing_time", 0) for chunk in chunks]
        
        return {
            "total_items_processed": total_items,
            "average_processing_time": sum(processing_times) / len(processing_times) if processing_times else 0,
            "processing_efficiency": total_items / sum(processing_times) if sum(processing_times) > 0 else 0
        }
    
    def analyze_performance(chunks):
        """性能分析"""
        return {
            "total_chunks": len(chunks),
            "processing_times": [chunk.get("processing_time", 0) for chunk in chunks],
            "fastest_chunk": min(chunks, key=lambda x: x.get("processing_time", float('inf'))),
            "slowest_chunk": max(chunks, key=lambda x: x.get("processing_time", 0))
        }
    
    # 并行执行分析任务
    analysis_tasks = {
        "statistics": lambda: analyze_statistics(chunks),
        "quality": lambda: analyze_quality(chunks),
        "performance": lambda: analyze_performance(chunks)
    }
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_task = {
            executor.submit(task_func): task_name 
            for task_name, task_func in analysis_tasks.items()
        }
        
        for future in concurrent.futures.as_completed(future_to_task):
            task_name = future_to_task[future]
            try:
                result = future.result()
                analysis_results[task_name] = result
                print(f"分析任务 {task_name} 完成")
            except Exception as exc:
                print(f"分析任务 {task_name} 失败: {exc}")
                analysis_results[task_name] = {"error": str(exc)}
    
    return {
        "analysis_results": analysis_results
    }

def report_generator(state: DataProcessingState) -> DataProcessingState:
    """
    报告生成节点
    """
    print_step("生成处理报告")
    
    chunks = state.get("processed_chunks", [])
    analysis_results = state.get("analysis_results", {})
    
    # 生成报告
    report_lines = [
        "=== 并行数据处理报告 ===",
        f"处理的数据块数量: {len(chunks)}",
        ""
    ]
    
    # 统计信息
    if "statistics" in analysis_results:
        stats = analysis_results["statistics"]
        report_lines.extend([
            "【统计信息】",
            f"- 总处理项目数: {stats.get('total_items', 0)}",
            f"- 涉及数据块数: {stats.get('unique_chunks', 0)}",
            ""
        ])
    
    # 质量信息
    if "quality" in analysis_results:
        quality = analysis_results["quality"]
        report_lines.extend([
            "【质量信息】",
            f"- 处理效率: {quality.get('processing_efficiency', 0):.2f} items/s",
            f"- 平均处理时间: {quality.get('average_processing_time', 0):.2f}s",
            ""
        ])
    
    # 性能信息
    if "performance" in analysis_results:
        perf = analysis_results["performance"]
        report_lines.extend([
            "【性能信息】",
            f"- 总数据块: {perf.get('total_chunks', 0)}",
            f"- 最快块处理时间: {perf.get('fastest_chunk', {}).get('processing_time', 0):.2f}s",
            f"- 最慢块处理时间: {perf.get('slowest_chunk', {}).get('processing_time', 0):.2f}s",
            ""
        ])
    
    report_lines.append("=== 报告结束 ===")
    
    final_report = "\n".join(report_lines)
    
    print_result("报告生成完成")
    
    return {
        "final_report": final_report,
        "processing_stats": {
            "chunks_processed": len(chunks),
            "total_analysis_tasks": len(analysis_results),
            "report_lines": len(report_lines)
        }
    }

# 5. 构建并行执行工作流

def build_basic_parallel_workflow():
    """构建基础并行工作流"""
    print_step("构建基础并行工作流")
    
    workflow = StateGraph(ParallelState)
    
    workflow.add_node("parallel_process", parallel_data_processing)
    workflow.add_node("merge", results_merger)
    
    workflow.set_entry_point("parallel_process")
    workflow.add_edge("parallel_process", "merge")
    workflow.add_edge("merge", END)
    
    return workflow.compile()

def build_analysis_parallel_workflow():
    """构建分析并行工作流"""
    print_step("构建分析并行工作流")
    
    workflow = StateGraph(ParallelState)
    
    workflow.add_node("parallel_analysis", parallel_analysis)
    workflow.add_node("merge", results_merger)
    
    workflow.set_entry_point("parallel_analysis")
    workflow.add_edge("parallel_analysis", "merge")
    workflow.add_edge("merge", END)
    
    return workflow.compile()

def build_data_processing_parallel_workflow():
    """构建数据处理并行工作流"""
    print_step("构建数据处理并行工作流")
    
    workflow = StateGraph(DataProcessingState)
    
    workflow.add_node("split", data_splitter)
    workflow.add_node("parallel_process", parallel_chunk_processor)
    workflow.add_node("parallel_analyze", parallel_analyzer)
    workflow.add_node("generate_report", report_generator)
    
    workflow.set_entry_point("split")
    workflow.add_edge("split", "parallel_process")
    workflow.add_edge("parallel_process", "parallel_analyze")
    workflow.add_edge("parallel_analyze", "generate_report")
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()

# 6. 演示函数

def demo_basic_parallel():
    """演示基础并行处理"""
    print_step("基础并行处理演示")
    
    app = build_basic_parallel_workflow()
    
    initial_state = {
        "input_data": {
            "text1": "这是一段测试文本",
            "number1": 42,
            "text2": "另一段文本内容",
            "number2": 100,
            "text3": "更多的文本数据"
        },
        "parallel_results": {},
        "merged_result": {},
        "execution_times": {},
        "task_status": {},
        "total_time": 0.0
    }
    
    start_time = time.time()
    result = app.invoke(initial_state)
    end_time = time.time()
    
    print_result(f"基础并行处理完成，总耗时: {end_time - start_time:.2f}s")
    
    # 显示详细结果
    merged = result.get("merged_result", {})
    if "summary" in merged:
        summary = merged["summary"]
        print(f"任务执行情况:")
        print(f"  - 总任务: {summary.get('total_tasks', 0)}")
        print(f"  - 成功: {summary.get('successful_tasks', 0)}")
        print(f"  - 失败: {summary.get('failed_tasks', 0)}")

def demo_analysis_parallel():
    """演示并行分析"""
    print_step("并行分析演示")
    
    app = build_analysis_parallel_workflow()
    
    initial_state = {
        "input_data": {
            "product_review": "这个产品真的很棒，质量很好，推荐购买！",
            "customer_feedback": "服务态度很好，但是配送速度有待提高",
            "technical_issue": "系统运行正常，性能表现优秀",
            "price_comment": "价格合理，性价比高"
        },
        "parallel_results": {},
        "merged_result": {},
        "execution_times": {}
    }
    
    start_time = time.time()
    result = app.invoke(initial_state)
    end_time = time.time()
    
    print_result(f"并行分析完成，总耗时: {end_time - start_time:.2f}s")
    
    # 显示分析结果
    parallel_results = result.get("parallel_results", {})
    for task_name, result_data in parallel_results.items():
        print(f"\n{task_name}:")
        for key, value in result_data.items():
            print(f"  {key}: {value}")

def demo_data_processing_parallel():
    """演示数据处理并行"""
    print_step("数据处理并行演示")
    
    app = build_data_processing_parallel_workflow()
    
    # 生成测试数据
    raw_data = [
        {"id": i, "value": random.randint(1, 100), "category": f"cat_{i % 5}"}
        for i in range(15)
    ]
    
    initial_state = {
        "raw_data": raw_data,
        "processed_chunks": [],
        "analysis_results": {},
        "final_report": "",
        "processing_stats": {}
    }
    
    print(f"输入数据: {len(raw_data)} 条记录")
    
    start_time = time.time()
    result = app.invoke(initial_state)
    end_time = time.time()
    
    print_result(f"数据处理并行完成，总耗时: {end_time - start_time:.2f}s")
    
    # 显示报告
    report = result.get("final_report", "")
    if report:
        print("\n" + "="*50)
        print(report)
        print("="*50)

def performance_comparison():
    """性能对比演示"""
    print_step("并行vs串行性能对比")
    
    # 模拟任务
    def simulate_task(duration):
        time.sleep(duration)
        return f"任务完成，耗时 {duration}s"
    
    # 串行执行
    print("执行串行处理...")
    serial_start = time.time()
    serial_results = []
    for i in range(3):
        result = simulate_task(random.uniform(0.5, 1.5))
        serial_results.append(result)
    serial_end = time.time()
    serial_time = serial_end - serial_start
    
    print(f"串行执行完成，耗时: {serial_time:.2f}s")
    
    # 并行执行
    print("\n执行并行处理...")
    parallel_start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(simulate_task, random.uniform(0.5, 1.5)) for _ in range(3)]
        parallel_results = [future.result() for future in concurrent.futures.as_completed(futures)]
    parallel_end = time.time()
    parallel_time = parallel_end - parallel_start
    
    print(f"并行执行完成，耗时: {parallel_time:.2f}s")
    
    # 性能对比
    speedup = serial_time / parallel_time if parallel_time > 0 else 0
    print(f"\n性能对比:")
    print(f"  串行时间: {serial_time:.2f}s")
    print(f"  并行时间: {parallel_time:.2f}s")
    print(f"  加速比: {speedup:.2f}x")
    print(f"  效率提升: {((speedup - 1) * 100):.1f}%")

# 主程序
if __name__ == "__main__":
    print("⚡ LangGraph 并行执行学习程序")
    print("=" * 60)
    
    while True:
        print("\n请选择演示:")
        print("1. 基础并行处理")
        print("2. 并行分析")
        print("3. 数据处理并行")
        print("4. 性能对比")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-4): ").strip()
        
        if choice == "1":
            demo_basic_parallel()
        elif choice == "2":
            demo_analysis_parallel()
        elif choice == "3":
            demo_data_processing_parallel()
        elif choice == "4":
            performance_comparison()
        elif choice == "0":
            print_step("感谢学习并行执行！")
            break
        else:
            print_error("无效选择，请重试")
    
    print_result("并行执行学习完成！")