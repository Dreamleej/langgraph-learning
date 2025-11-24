"""
05-exercises: 高级问题解决

这个文件包含LangGraph高级问题的练习，挑战您的技术深度
和解决复杂问题的能力。

练习包括：
- 复杂状态管理
- 高级路由策略
- 性能优化
- 安全和监控
- 错误恢复
"""

from typing import TypedDict, List, Dict, Any, Literal, Optional
from langgraph.graph import StateGraph, END
import sys
import os
import time
import asyncio
import random
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import print_step, print_result, print_error

# ================================
 练习 1: 智能推荐系统
# ================================

def exercise_1_recommendation_system():
    """
    练习 1: 智能推荐系统
    
    要求:
    1. 实现基于用户行为的内容推荐
    2. 支持多种推荐算法（协同过滤、内容推荐等）
    3. 动态调整推荐策略
    4. 实时学习和优化
    5. A/B测试功能
    
    挑战点:
    - 复杂的用户画像建模
    - 实时性能要求
    - 冷启动问题处理
    - 推荐多样性控制
    """
    
    # 实现状态定义
    class RecommendationState(TypedDict):
        user_id: str
        request_context: Dict[str, Any]
        user_profile: Dict[str, Any]
        behavior_history: List[Dict[str, Any]]
        candidate_items: List[Dict[str, Any]]
        recommendation_strategy: str
        scored_items: List[Dict[str, Any]]
        final_recommendations: List[Dict[str, Any]]
        ab_test_group: str
        performance_metrics: Dict[str, Any]
    
    # 用户画像构建
    def build_user_profile(state: RecommendationState) -> RecommendationState:
        """构建用户画像"""
        user_id = state.get("user_id", "")
        behavior_history = state.get("behavior_history", [])
        
        # 模拟用户画像分析
        profile = {
            "user_id": user_id,
            "interests": [],
            "preferences": {},
            "activity_level": 0,
            "last_active": None,
            "demographics": {}
        }
        
        # 分析行为历史
        if behavior_history:
            # 提取兴趣标签
            all_tags = []
            for behavior in behavior_history:
                tags = behavior.get("tags", [])
                all_tags.extend(tags)
            
            # 统计标签频率
            tag_counts = {}
            for tag in all_tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # 选择高频标签作为兴趣
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            profile["interests"] = [tag for tag, count in sorted_tags[:5]]
            
            # 计算活跃度
            profile["activity_level"] = len(behavior_history)
            profile["last_active"] = max(behavior["timestamp"] for behavior in behavior_history)
        
        return {"user_profile": profile}
    
    # 协同过滤推荐
    def collaborative_filtering(state: RecommendationState) -> RecommendationState:
        """协同过滤算法"""
        user_profile = state.get("user_profile", {})
        candidate_items = state.get("candidate_items", [])
        
        # 模拟协同过滤
        similar_users = find_similar_users(user_profile["user_id"])
        scored_items = []
        
        for item in candidate_items:
            # 计算协同过滤评分
            cf_score = calculate_cf_score(item, similar_users)
            
            item_with_score = {
                **item,
                "cf_score": cf_score,
                "scoring_method": "collaborative_filtering"
            }
            scored_items.append(item_with_score)
        
        return {"scored_items": scored_items}
    
    # 内容推荐
    def content_based_recommendation(state: RecommendationState) -> RecommendationState:
        """基于内容的推荐"""
        user_profile = state.get("user_profile", {})
        candidate_items = state.get("candidate_items", [])
        scored_items = state.get("scored_items", [])
        
        for item in scored_items:
            # 计算内容相似度
            content_score = calculate_content_similarity(item, user_profile)
            item["content_score"] = content_score
        
        return {"scored_items": scored_items}
    
    def find_similar_users(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """查找相似用户"""
        # 模拟查找相似用户
        similar_users = []
        for i in range(limit):
            similar_user = {
                "user_id": f"user_{i}",
                "similarity": random.uniform(0.3, 0.9),
                "preferences": {}
            }
            similar_users.append(similar_user)
        return similar_users
    
    def calculate_cf_score(item: Dict[str, Any], similar_users: List[Dict[str, Any]]) -> float:
        """计算协同过滤评分"""
        base_score = random.uniform(0.1, 0.9)
        similarity_weight = sum(user["similarity"] for user in similar_users) / len(similar_users)
        return min(base_score * similarity_weight * 1.2, 1.0)
    
    def calculate_content_similarity(item: Dict[str, Any], user_profile: Dict[str, Any]) -> float:
        """计算内容相似度"""
        user_interests = user_profile.get("interests", [])
        item_tags = item.get("tags", [])
        
        # 计算标签重叠度
        common_tags = set(user_interests) & set(item_tags)
        if not item_tags:
            return 0.1
        
        similarity = len(common_tags) / len(item_tags)
        return min(similarity * 1.1, 1.0)
    
    def choose_recommendation_strategy(state: RecommendationState) -> RecommendationState:
        """选择推荐策略"""
        user_profile = state.get("user_profile", {})
        ab_test_group = random.choice(["control", "treatment"])
        
        # 根据用户特征选择策略
        activity_level = user_profile.get("activity_level", 0)
        interests = user_profile.get("interests", [])
        
        if activity_level < 5:  # 新用户
            strategy = "content_based"
        elif len(interests) > 10:  # 活跃用户
            strategy = "collaborative_filtering"
        else:  # 混合策略
            strategy = "hybrid"
        
        return {
            "recommendation_strategy": strategy,
            "ab_test_group": ab_test_group
        }
    
    def rank_recommendations(state: RecommendationState) -> RecommendationState:
        """排序推荐结果"""
        scored_items = state.get("scored_items", [])
        strategy = state.get("recommendation_strategy", "hybrid")
        
        # 根据策略计算最终分数
        for item in scored_items:
            cf_score = item.get("cf_score", 0)
            content_score = item.get("content_score", 0)
            
            if strategy == "collaborative_filtering":
                final_score = cf_score * 0.8 + content_score * 0.2
            elif strategy == "content_based":
                final_score = content_score * 0.8 + cf_score * 0.2
            else:  # hybrid
                final_score = cf_score * 0.6 + content_score * 0.4
            
            item["final_score"] = final_score
        
        # 排序并返回前N个
        sorted_items = sorted(scored_items, key=lambda x: x["final_score"], reverse=True)
        final_recommendations = sorted_items[:10]
        
        return {"final_recommendations": final_recommendations}
    
    def evaluate_performance(state: RecommendationState) -> RecommendationState:
        """评估推荐性能"""
        final_recommendations = state.get("final_recommendations", [])
        strategy = state.get("recommendation_strategy", "")
        ab_test_group = state.get("ab_test_group", "")
        
        # 模拟性能指标
        metrics = {
            "recommendation_count": len(final_recommendations),
            "avg_score": sum(item.get("final_score", 0) for item in final_recommendations) / len(final_recommendations),
            "diversity_score": calculate_diversity(final_recommendations),
            "coverage_score": random.uniform(0.6, 0.9),
            "response_time_ms": random.randint(50, 200),
            "strategy": strategy,
            "ab_test_group": ab_test_group
        }
        
        return {"performance_metrics": metrics}
    
    def calculate_diversity(recommendations: List[Dict[str, Any]]) -> float:
        """计算推荐多样性"""
        if len(recommendations) < 2:
            return 0.0
        
        # 简单的多样性计算：基于标签的差异
        all_tags = []
        for rec in recommendations:
            all_tags.extend(rec.get("tags", []))
        
        unique_tags = set(all_tags)
        diversity = len(unique_tags) / len(all_tags) if all_tags else 0
        return min(diversity, 1.0)
    
    # 构建推荐系统工作流
    def build_recommendation_workflow():
        workflow = StateGraph(RecommendationState)
        
        workflow.add_node("build_profile", build_user_profile)
        workflow.add_node("choose_strategy", choose_recommendation_strategy)
        workflow.add_node("collaborative_filtering", collaborative_filtering)
        workflow.add_node("content_based", content_based_recommendation)
        workflow.add_node("rank_recommendations", rank_recommendations)
        workflow.add_node("evaluate_performance", evaluate_performance)
        
        workflow.set_entry_point("build_profile")
        workflow.add_edge("build_profile", "choose_strategy")
        
        # 并行执行两种推荐算法
        workflow.add_edge("choose_strategy", "collaborative_filtering")
        workflow.add_edge("choose_strategy", "content_based")
        
        workflow.add_edge("collaborative_filtering", "rank_recommendations")
        workflow.add_edge("content_based", "rank_recommendations")
        
        workflow.add_edge("rank_recommendations", "evaluate_performance")
        workflow.add_edge("evaluate_performance", END)
        
        return workflow.compile()
    
    # 测试函数
    def test_recommendation_system():
        print_step("测试智能推荐系统")
        
        app = build_recommendation_workflow()
        
        # 模拟用户行为历史
        behavior_history = [
            {"item_id": "item1", "action": "view", "timestamp": time.time() - 86400, "tags": ["tech", "ai"]},
            {"item_id": "item2", "action": "like", "timestamp": time.time() - 43200, "tags": ["programming", "python"]},
            {"item_id": "item3", "action": "purchase", "timestamp": time.time() - 21600, "tags": ["education", "course"]},
        ]
        
        # 模拟候选物品
        candidate_items = [
            {"item_id": "item4", "title": "LangGraph教程", "tags": ["tech", "programming", "langgraph"]},
            {"item_id": "item5", "title": "Python高级课程", "tags": ["programming", "python", "education"]},
            {"item_id": "item6", "title": "AI实践指南", "tags": ["tech", "ai", "programming"]},
            {"item_id": "item7", "title": "机器学习基础", "tags": ["tech", "ai", "education"]},
        ]
        
        initial_state = {
            "user_id": "user123",
            "request_context": {"page": "homepage", "timestamp": time.time()},
            "behavior_history": behavior_history,
            "candidate_items": candidate_items,
            "user_profile": {},
            "scored_items": [],
            "final_recommendations": [],
            "recommendation_strategy": "",
            "ab_test_group": "",
            "performance_metrics": {}
        }
        
        result = app.invoke(initial_state)
        
        # 显示结果
        user_profile = result.get("user_profile", {})
        final_recommendations = result.get("final_recommendations", [])
        performance_metrics = result.get("performance_metrics", {})
        
        print(f"\n👤 用户画像:")
        print(f"  兴趣标签: {user_profile.get('interests', [])}")
        print(f"  活跃度: {user_profile.get('activity_level', 0)}")
        
        print(f"\n🎯 推荐策略: {result.get('recommendation_strategy', '')}")
        print(f"🧪 A/B测试组: {result.get('ab_test_group', '')}")
        
        print(f"\n📋 推荐结果:")
        for i, rec in enumerate(final_recommendations[:5], 1):
            score = rec.get("final_score", 0)
            title = rec.get("title", rec.get("item_id", ""))
            print(f"  {i}. {title} (评分: {score:.3f})")
        
        print(f"\n📊 性能指标:")
        print(f"  平均评分: {performance_metrics.get('avg_score', 0):.3f}")
        print(f"  多样性: {performance_metrics.get('diversity_score', 0):.3f}")
        print(f"  响应时间: {performance_metrics.get('response_time_ms', 0)}ms")
    
    return test_recommendation_system


# ================================
 练习 2: 实时数据流处理
# ================================

def exercise_2_stream_processing():
    """
    练习 2: 实时数据流处理
    
    要求:
    1. 处理高并发数据流
    2. 实现实时聚合和分析
    3. 支持动态规则引擎
    4. 异常检测和告警
    5. 背压处理机制
    
    挑战点:
    - 高性能要求
    - 数据一致性保证
    - 内存管理
    - 故障恢复
    """
    
    class StreamProcessingState(TypedDict):
        stream_id: str
        data_events: List[Dict[str, Any]]
        processing_rules: List[Dict[str, Any]]
        aggregated_results: Dict[str, Any]
        alerts: List[Dict[str, Any]]
        performance_stats: Dict[str, Any]
        buffer_status: Dict[str, Any]
        error_log: List[Dict[str, Any]]
    
    class EventType(Enum):
        METRIC = "metric"
        EVENT = "event"
        LOG = "log"
        ALERT = "alert"
    
    class ProcessingPriority(Enum):
        HIGH = 1
        MEDIUM = 2
        LOW = 3
    
    @dataclass
    class DataEvent:
        event_id: str
        event_type: EventType
        timestamp: float
        data: Dict[str, Any]
        priority: ProcessingPriority
        processed: bool = False
    
    # 数据缓冲管理
    def manage_buffer(state: StreamProcessingState) -> StreamProcessingState:
        """管理数据缓冲区"""
        data_events = state.get("data_events", [])
        
        # 缓冲区状态检查
        buffer_size = len(data_events)
        buffer_capacity = 1000  # 最大缓冲区大小
        
        buffer_status = {
            "current_size": buffer_size,
            "capacity": buffer_capacity,
            "utilization": buffer_size / buffer_capacity,
            "status": "normal"
        }
        
        # 背压处理
        if buffer_size > buffer_capacity * 0.8:
            buffer_status["status"] = "warning"
            # 实施背压策略
            processed_events = apply_backpressure(data_events)
            buffer_status["dropped_events"] = len(data_events) - len(processed_events)
        else:
            processed_events = data_events
        
        return {
            "data_events": processed_events,
            "buffer_status": buffer_status
        }
    
    def apply_backpressure(events: List[DataEvent]) -> List[DataEvent]:
        """应用背压处理"""
        # 按优先级排序
        sorted_events = sorted(events, key=lambda x: x.priority.value)
        
        # 保留高优先级和中等优先级的事件
        filtered_events = [e for e in sorted_events if e.priority.value <= ProcessingPriority.MEDIUM.value]
        
        # 如果还是太多，保留最新的事件
        if len(filtered_events) > 800:
            filtered_events = filtered_events[-800:]
        
        return filtered_events
    
    # 实时聚合
    def real_time_aggregation(state: StreamProcessingState) -> StreamProcessingState:
        """实时数据聚合"""
        data_events = state.get("data_events", [])
        
        aggregated_results = {
            "total_events": len(data_events),
            "event_types": {},
            "time_window": {},
            "key_metrics": {},
            "aggregation_timestamp": datetime.now().isoformat()
        }
        
        # 按事件类型统计
        for event in data_events:
            event_type = event.get("event_type", "unknown")
            aggregated_results["event_types"][event_type] = aggregated_results["event_types"].get(event_type, 0) + 1
        
        # 时间窗口聚合
        current_time = time.time()
        time_windows = {"1m": 60, "5m": 300, "1h": 3600}
        
        for window_name, window_seconds in time_windows.items():
            window_start = current_time - window_seconds
            window_events = [e for e in data_events if e.get("timestamp", 0) > window_start]
            aggregated_results["time_window"][window_name] = len(window_events)
        
        # 关键指标聚合
        metric_events = [e for e in data_events if e.get("event_type") == "metric"]
        if metric_events:
            for event in metric_events:
                metric_data = event.get("data", {})
                metric_name = metric_data.get("name", "unknown")
                metric_value = metric_data.get("value", 0)
                
                if metric_name not in aggregated_results["key_metrics"]:
                    aggregated_results["key_metrics"][metric_name] = {
                        "count": 0,
                        "sum": 0,
                        "avg": 0,
                        "min": float('inf'),
                        "max": float('-inf')
                    }
                
                metrics = aggregated_results["key_metrics"][metric_name]
                metrics["count"] += 1
                metrics["sum"] += metric_value
                metrics["avg"] = metrics["sum"] / metrics["count"]
                metrics["min"] = min(metrics["min"], metric_value)
                metrics["max"] = max(metrics["max"], metric_value)
        
        return {"aggregated_results": aggregated_results}
    
    # 规则引擎
    def apply_processing_rules(state: StreamProcessingState) -> StreamProcessingState:
        """应用处理规则"""
        data_events = state.get("data_events", [])
        processing_rules = state.get("processing_rules", [])
        alerts = state.get("alerts", [])
        
        for event in data_events:
            for rule in processing_rules:
                if evaluate_rule(event, rule):
                    alert = create_alert(event, rule)
                    alerts.append(alert)
        
        return {"alerts": alerts}
    
    def evaluate_rule(event: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """评估规则条件"""
        conditions = rule.get("conditions", [])
        
        for condition in conditions:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")
            
            event_value = get_nested_value(event, field)
            
            if not compare_values(event_value, operator, value):
                return False
        
        return True
    
    def get_nested_value(obj: Dict[str, Any], path: str) -> Any:
        """获取嵌套字典值"""
        keys = path.split(".")
        current = obj
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def compare_values(actual: Any, operator: str, expected: Any) -> bool:
        """比较值"""
        try:
            if operator == ">":
                return actual > expected
            elif operator == "<":
                return actual < expected
            elif operator == ">=":
                return actual >= expected
            elif operator == "<=":
                return actual <= expected
            elif operator == "==":
                return actual == expected
            elif operator == "!=":
                return actual != expected
            elif operator == "contains":
                return expected in str(actual)
            else:
                return False
        except:
            return False
    
    def create_alert(event: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """创建告警"""
        return {
            "alert_id": f"alert_{int(time.time())}_{random.randint(1000, 9999)}",
            "event_id": event.get("event_id", ""),
            "rule_name": rule.get("name", ""),
            "severity": rule.get("severity", "medium"),
            "message": rule.get("message", "Rule triggered"),
            "event_data": event,
            "timestamp": datetime.now().isoformat()
        }
    
    # 异常检测
    def detect_anomalies(state: StreamProcessingState) -> StreamProcessingState:
        """异常检测"""
        aggregated_results = state.get("aggregated_results", {})
        alerts = state.get("alerts", [])
        
        # 基于聚合结果的异常检测
        key_metrics = aggregated_results.get("key_metrics", {})
        
        for metric_name, metrics in key_metrics.items():
            # 检测异常值
            avg = metrics.get("avg", 0)
            max_val = metrics.get("max", 0)
            
            # 简单的异常检测规则
            if max_val > avg * 10:  # 最大值远大于平均值
                alert = {
                    "alert_id": f"anomaly_{metric_name}_{int(time.time())}",
                    "type": "anomaly_detection",
                    "metric": metric_name,
                    "reason": f"Max value ({max_val}) is much higher than average ({avg})",
                    "severity": "high",
                    "timestamp": datetime.now().isoformat()
                }
                alerts.append(alert)
        
        return {"alerts": alerts}
    
    # 性能统计
    def calculate_performance_stats(state: StreamProcessingState) -> StreamProcessingState:
        """计算性能统计"""
        data_events = state.get("data_events", [])
        aggregated_results = state.get("aggregated_results", {})
        alerts = state.get("alerts", [])
        buffer_status = state.get("buffer_status", {})
        
        start_time = time.time() - random.uniform(5, 30)  # 模拟处理开始时间
        end_time = time.time()
        processing_time = end_time - start_time
        
        performance_stats = {
            "processing_time_seconds": processing_time,
            "events_per_second": len(data_events) / processing_time if processing_time > 0 else 0,
            "total_events_processed": len(data_events),
            "alerts_generated": len(alerts),
            "buffer_utilization": buffer_status.get("utilization", 0),
            "memory_usage_mb": random.uniform(100, 500),
            "cpu_usage_percent": random.uniform(20, 80),
            "error_count": 0,
            "success_rate": 1.0
        }
        
        return {"performance_stats": performance_stats}
    
    # 构建流处理工作流
    def build_stream_processing_workflow():
        workflow = StateGraph(StreamProcessingState)
        
        workflow.add_node("manage_buffer", manage_buffer)
        workflow.add_node("aggregate", real_time_aggregation)
        workflow.add_node("apply_rules", apply_processing_rules)
        workflow.add_node("detect_anomalies", detect_anomalies)
        workflow.add_node("performance_stats", calculate_performance_stats)
        
        workflow.set_entry_point("manage_buffer")
        workflow.add_edge("manage_buffer", "aggregate")
        
        # 并行执行规则应用和异常检测
        workflow.add_edge("aggregate", "apply_rules")
        workflow.add_edge("aggregate", "detect_anomalies")
        
        workflow.add_edge("apply_rules", "performance_stats")
        workflow.add_edge("detect_anomalies", "performance_stats")
        workflow.add_edge("performance_stats", END)
        
        return workflow.compile()
    
    # 测试函数
    def test_stream_processing():
        print_step("测试实时数据流处理")
        
        app = build_stream_processing_workflow()
        
        # 生成模拟数据流
        current_time = time.time()
        data_events = []
        
        # 生成各种类型的事件
        for i in range(100):
            event = {
                "event_id": f"event_{i}",
                "event_type": random.choice(["metric", "event", "log"]),
                "timestamp": current_time - random.uniform(0, 300),
                "data": {
                    "name": f"metric_{i % 10}",
                    "value": random.uniform(10, 1000),
                    "source": f"source_{i % 5}"
                },
                "priority": random.choice(["high", "medium", "low"])
            }
            data_events.append(event)
        
        # 定义处理规则
        processing_rules = [
            {
                "name": "high_metric_value",
                "conditions": [
                    {"field": "event_type", "operator": "==", "value": "metric"},
                    {"field": "data.value", "operator": ">", "value": 800}
                ],
                "severity": "high",
                "message": "Metric value is unusually high"
            },
            {
                "name": "error_log_detection",
                "conditions": [
                    {"field": "event_type", "operator": "==", "value": "log"},
                    {"field": "data.level", "operator": "==", "value": "error"}
                ],
                "severity": "medium",
                "message": "Error log detected"
            }
        ]
        
        initial_state = {
            "stream_id": f"stream_{int(time.time())}",
            "data_events": data_events,
            "processing_rules": processing_rules,
            "aggregated_results": {},
            "alerts": [],
            "performance_stats": {},
            "buffer_status": {},
            "error_log": []
        }
        
        result = app.invoke(initial_state)
        
        # 显示结果
        aggregated_results = result.get("aggregated_results", {})
        alerts = result.get("alerts", [])
        performance_stats = result.get("performance_stats", {})
        buffer_status = result.get("buffer_status", {})
        
        print(f"\n📊 聚合结果:")
        print(f"  总事件数: {aggregated_results.get('total_events', 0)}")
        print(f"  事件类型分布: {aggregated_results.get('event_types', {})}")
        print(f"  时间窗口: {aggregated_results.get('time_window', {})}")
        
        key_metrics = aggregated_results.get("key_metrics", {})
        if key_metrics:
            print(f"\n📈 关键指标:")
            for metric, stats in list(key_metrics.items())[:3]:
                print(f"  {metric}: avg={stats.get('avg', 0):.2f}, min={stats.get('min', 0)}, max={stats.get('max', 0)}")
        
        print(f"\n🚨 告警信息:")
        print(f"  生成告警数: {len(alerts)}")
        for alert in alerts[:3]:
            print(f"  - {alert.get('severity', 'unknown')}: {alert.get('message', '')}")
        
        print(f"\n⚡ 性能统计:")
        print(f"  处理时间: {performance_stats.get('processing_time_seconds', 0):.3f}s")
        print(f"  事件/秒: {performance_stats.get('events_per_second', 0):.1f}")
        print(f"  缓冲区利用率: {buffer_status.get('utilization', 0):.1%}")
        print(f"  CPU使用率: {performance_stats.get('cpu_usage_percent', 0):.1f}%")
    
    return test_stream_processing


# ================================
 练习 3: 自适应学习系统
# ================================

def exercise_3_adaptive_learning():
    """
    练习 3: 自适应学习系统
    
    要求:
    1. 实现动态学习路径推荐
    2. 基于学习效果的难度调整
    3. 多维度学习评估
    4. 个性化内容推荐
    5. 学习进度跟踪和分析
    
    挑战点:
    - 学习效果评估算法
    - 难度适应性调整
    - 学习路径优化
    - 个性化建模
    """
    
    class AdaptiveLearningState(TypedDict):
        learner_id: str
        current_session: Dict[str, Any]
        learning_history: List[Dict[str, Any]]
        knowledge_model: Dict[str, Any]
        current_difficulty: float
        recommended_content: List[Dict[str, Any]]
        learning_path: List[Dict[str, Any]]
        performance_metrics: Dict[str, Any]
        adaptation_log: List[Dict[str, Any]]
    
    # 学习者画像建模
    def build_learner_profile(state: AdaptiveLearningState) -> AdaptiveLearningState:
        """构建学习者画像"""
        learner_id = state.get("learner_id", "")
        learning_history = state.get("learning_history", [])
        
        knowledge_model = {
            "learner_id": learner_id,
            "knowledge_domains": {},
            "skill_levels": {},
            "learning_style": {},
            "strengths": [],
            "weaknesses": [],
            "preferred_difficulty": 0.5,
            "engagement_level": 0.0,
            "completion_rate": 0.0
        }
        
        if learning_history:
            # 分析学习历史
            total_sessions = len(learning_history)
            completed_sessions = sum(1 for session in learning_history if session.get("completed", False))
            
            # 计算完成率
            knowledge_model["completion_rate"] = completed_sessions / total_sessions
            
            # 分析知识领域
            domain_scores = {}
            for session in learning_history:
                domain = session.get("domain", "general")
                score = session.get("performance_score", 0)
                if domain not in domain_scores:
                    domain_scores[domain] = []
                domain_scores[domain].append(score)
            
            # 计算各领域平均分数
            for domain, scores in domain_scores.items():
                avg_score = sum(scores) / len(scores)
                knowledge_model["knowledge_domains"][domain] = avg_score
                
                # 识别强项和弱项
                if avg_score > 0.8:
                    knowledge_model["strengths"].append(domain)
                elif avg_score < 0.5:
                    knowledge_model["weaknesses"].append(domain)
            
            # 分析参与度
            engagement_scores = [s.get("engagement_score", 0) for s in learning_history]
            knowledge_model["engagement_level"] = sum(engagement_scores) / len(engagement_scores)
            
            # 推断学习风格
            knowledge_model["learning_style"] = infer_learning_style(learning_history)
        
        return {"knowledge_model": knowledge_model}
    
    def infer_learning_style(history: List[Dict[str, Any]]) -> Dict[str, float]:
        """推断学习风格"""
        styles = {
            "visual": 0.0,
            "auditory": 0.0,
            "kinesthetic": 0.0,
            "reading": 0.0
        }
        
        for session in history:
            session_type = session.get("session_type", "")
            performance = session.get("performance_score", 0)
            
            if "video" in session_type:
                styles["visual"] += performance
            elif "audio" in session_type:
                styles["auditory"] += performance
            elif "interactive" in session_type:
                styles["kinesthetic"] += performance
            elif "text" in session_type:
                styles["reading"] += performance
        
        # 归一化
        total = sum(styles.values())
        if total > 0:
            for style in styles:
                styles[style] /= total
        
        return styles
    
    # 难度自适应
    def adaptive_difficulty_adjustment(state: AdaptiveLearningState) -> AdaptiveLearningState:
        """自适应难度调整"""
        knowledge_model = state.get("knowledge_model", {})
        current_session = state.get("current_session", {})
        learning_history = state.get("learning_history", [])
        
        # 当前难度
        current_difficulty = state.get("current_difficulty", 0.5)
        
        # 获取最近的表现
        recent_sessions = learning_history[-5:]  # 最近5次
        if len(recent_sessions) >= 3:
            recent_scores = [s.get("performance_score", 0) for s in recent_sessions]
            avg_recent_score = sum(recent_scores) / len(recent_scores)
            
            # 根据表现调整难度
            if avg_recent_score > 0.85:  # 表现很好，增加难度
                new_difficulty = min(current_difficulty + 0.1, 1.0)
                reason = "high_performance"
            elif avg_recent_score < 0.5:  # 表现较差，降低难度
                new_difficulty = max(current_difficulty - 0.1, 0.1)
                reason = "low_performance"
            else:  # 表现适中，保持难度
                new_difficulty = current_difficulty
                reason = "stable_performance"
            
            # 考虑学习者的偏好
            preferred_difficulty = knowledge_model.get("preferred_difficulty", 0.5)
            new_difficulty = 0.7 * new_difficulty + 0.3 * preferred_difficulty
            
            adaptation_log = state.get("adaptation_log", [])
            adaptation_log.append({
                "timestamp": datetime.now().isoformat(),
                "old_difficulty": current_difficulty,
                "new_difficulty": new_difficulty,
                "reason": reason,
                "recent_performance": avg_recent_score
            })
            
            return {
                "current_difficulty": new_difficulty,
                "adaptation_log": adaptation_log
            }
        
        return {}
    
    # 学习内容推荐
    def recommend_learning_content(state: AdaptiveLearningState) -> AdaptiveLearningState:
        """推荐学习内容"""
        knowledge_model = state.get("knowledge_model", {})
        current_difficulty = state.get("current_difficulty", 0.5)
        
        # 生成推荐内容
        recommended_content = []
        
        # 基于弱点推荐
        weaknesses = knowledge_model.get("weaknesses", [])
        for domain in weaknesses:
            content = {
                "content_id": f"content_{domain}_{int(time.time())}",
                "domain": domain,
                "type": "tutorial",
                "difficulty": current_difficulty * 0.8,  # 从稍低难度开始
                "estimated_time": random.randint(15, 45),
                "learning_objectives": [f"improve_{domain}"],
                "priority": "high"
            }
            recommended_content.append(content)
        
        # 基于强项推荐进阶内容
        strengths = knowledge_model.get("strengths", [])
        for domain in strengths:
            content = {
                "content_id": f"advanced_{domain}_{int(time.time())}",
                "domain": domain,
                "type": "advanced_exercise",
                "difficulty": min(current_difficulty * 1.2, 1.0),
                "estimated_time": random.randint(20, 60),
                "learning_objectives": [f"advance_{domain}"],
                "priority": "medium"
            }
            recommended_content.append(content)
        
        # 基于学习风格推荐
        learning_style = knowledge_model.get("learning_style", {})
        preferred_style = max(learning_style.items(), key=lambda x: x[1])[0] if learning_style else "visual"
        
        style_based_content = {
            "content_id": f"style_based_{preferred_style}_{int(time.time())}",
            "domain": "general",
            "type": f"{preferred_style}_content",
            "difficulty": current_difficulty,
            "estimated_time": random.randint(10, 30),
            "learning_objectives": ["engagement_improvement"],
            "priority": "low"
        }
        recommended_content.append(style_based_content)
        
        return {"recommended_content": recommended_content}
    
    # 学习路径规划
    def generate_learning_path(state: AdaptiveLearningState) -> AdaptiveLearningState:
        """生成学习路径"""
        recommended_content = state.get("recommended_content", [])
        knowledge_model = state.get("knowledge_model", {})
        
        # 按优先级和难度排序内容
        priority_order = {"high": 3, "medium": 2, "low": 1}
        sorted_content = sorted(
            recommended_content,
            key=lambda x: (priority_order.get(x["priority"], 0), x["difficulty"])
        )
        
        # 生成学习路径
        learning_path = []
        current_time = time.time()
        
        for i, content in enumerate(sorted_content):
            step = {
                "step_number": i + 1,
                "content": content,
                "estimated_duration": content.get("estimated_time", 30),
                "prerequisites": [],
                "learning_outcomes": content.get("learning_objectives", []),
                "scheduled_start": current_time + sum(step.get("estimated_duration", 0) for step in learning_path)
            }
            learning_path.append(step)
        
        return {"learning_path": learning_path}
    
    # 性能指标计算
    def calculate_learning_metrics(state: AdaptiveLearningState) -> AdaptiveLearningState:
        """计算学习性能指标"""
        learning_history = state.get("learning_history", [])
        knowledge_model = state.get("knowledge_model", {})
        learning_path = state.get("learning_path", [])
        
        performance_metrics = {
            "total_learning_time": sum(s.get("duration", 0) for s in learning_history),
            "average_session_score": 0,
            "improvement_rate": 0,
            "knowledge_growth": {},
            "engagement_trend": [],
            "goal_completion_rate": 0
        }
        
        if learning_history:
            # 平均分数
            scores = [s.get("performance_score", 0) for s in learning_history]
            performance_metrics["average_session_score"] = sum(scores) / len(scores)
            
            # 改进率
            if len(scores) >= 2:
                early_average = sum(scores[:len(scores)//2]) / (len(scores)//2)
                recent_average = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
                performance_metrics["improvement_rate"] = (recent_average - early_average) / early_average if early_average > 0 else 0
            
            # 知识成长
            domain_scores = knowledge_model.get("knowledge_domains", {})
            for domain, score in domain_scores.items():
                performance_metrics["knowledge_growth"][domain] = {
                    "current_level": score,
                    "target_level": min(score + 0.2, 1.0),
                    "improvement_needed": max(0, 1.0 - score)
                }
            
            # 参与度趋势
            engagement_scores = [s.get("engagement_score", 0) for s in learning_history[-10:]]
            performance_metrics["engagement_trend"] = engagement_scores
        
        # 目标完成率
        if learning_path:
            total_steps = len(learning_path)
            completed_steps = sum(1 for s in learning_history if s.get("completed", False))
            performance_metrics["goal_completion_rate"] = completed_steps / total_steps if total_steps > 0 else 0
        
        return {"performance_metrics": performance_metrics}
    
    # 构建自适应学习工作流
    def build_adaptive_learning_workflow():
        workflow = StateGraph(AdaptiveLearningState)
        
        workflow.add_node("build_profile", build_learner_profile)
        workflow.add_node("adjust_difficulty", adaptive_difficulty_adjustment)
        workflow.add_node("recommend_content", recommend_learning_content)
        workflow.add_node("generate_path", generate_learning_path)
        workflow.add_node("calculate_metrics", calculate_learning_metrics)
        
        workflow.set_entry_point("build_profile")
        workflow.add_edge("build_profile", "adjust_difficulty")
        workflow.add_edge("adjust_difficulty", "recommend_content")
        workflow.add_edge("recommend_content", "generate_path")
        workflow.add_edge("generate_path", "calculate_metrics")
        workflow.add_edge("calculate_metrics", END)
        
        return workflow.compile()
    
    # 测试函数
    def test_adaptive_learning():
        print_step("测试自适应学习系统")
        
        app = build_adaptive_learning_workflow()
        
        # 生成模拟学习历史
        learning_history = []
        for i in range(20):
            session = {
                "session_id": f"session_{i}",
                "domain": random.choice(["mathematics", "programming", "science", "language"]),
                "session_type": random.choice(["video", "interactive", "text", "audio"]),
                "duration": random.randint(10, 60),
                "performance_score": random.uniform(0.3, 0.95),
                "engagement_score": random.uniform(0.4, 0.9),
                "completed": random.random() > 0.1,
                "timestamp": time.time() - random.uniform(0, 30*24*3600)
            }
            learning_history.append(session)
        
        current_session = {
            "session_id": f"current_session_{int(time.time())}",
            "start_time": time.time(),
            "domain": "programming"
        }
        
        initial_state = {
            "learner_id": "learner_123",
            "current_session": current_session,
            "learning_history": learning_history,
            "knowledge_model": {},
            "current_difficulty": 0.5,
            "recommended_content": [],
            "learning_path": [],
            "performance_metrics": {},
            "adaptation_log": []
        }
        
        result = app.invoke(initial_state)
        
        # 显示结果
        knowledge_model = result.get("knowledge_model", {})
        current_difficulty = result.get("current_difficulty", 0.5)
        recommended_content = result.get("recommended_content", [])
        learning_path = result.get("learning_path", [])
        performance_metrics = result.get("performance_metrics", {})
        adaptation_log = result.get("adaptation_log", [])
        
        print(f"\n👤 学习者画像:")
        print(f"  完成率: {knowledge_model.get('completion_rate', 0):.1%}")
        print(f"  参与度: {knowledge_model.get('engagement_level', 0):.1%}")
        print(f"  强项: {knowledge_model.get('strengths', [])}")
        print(f"  弱项: {knowledge_model.get('weaknesses', [])}")
        
        learning_style = knowledge_model.get('learning_style', {})
        if learning_style:
            preferred_style = max(learning_style.items(), key=lambda x: x[1])[0]
            print(f"  学习风格: {preferred_style}")
        
        print(f"\n🎯 当前难度: {current_difficulty:.2f}")
        
        if adaptation_log:
            latest_adaptation = adaptation_log[-1]
            print(f"  难度调整: {latest_adaptation.get('reason', '')} ({latest_adaptation.get('old_difficulty', 0):.2f} → {latest_adaptation.get('new_difficulty', 0):.2f})")
        
        print(f"\n📚 推荐内容:")
        for content in recommended_content[:5]:
            priority = content.get("priority", "medium")
            domain = content.get("domain", "general")
            content_type = content.get("type", "tutorial")
            print(f"  - {domain} ({content_type}) - {priority} priority")
        
        print(f"\n🗺️ 学习路径:")
        print(f"  总步骤: {len(learning_path)}")
        estimated_total_time = sum(step.get("estimated_duration", 0) for step in learning_path)
        print(f"  预计总时长: {estimated_total_time} 分钟")
        
        print(f"\n📊 性能指标:")
        print(f"  平均分数: {performance_metrics.get('average_session_score', 0):.2f}")
        print(f"  改进率: {performance_metrics.get('improvement_rate', 0):.1%}")
        print(f"  目标完成率: {performance_metrics.get('goal_completion_rate', 0):.1%}")
        
        knowledge_growth = performance_metrics.get("knowledge_growth", {})
        if knowledge_growth:
            print(f"  知识成长:")
            for domain, growth in list(knowledge_growth.items())[:3]:
                current = growth.get("current_level", 0)
                print(f"    {domain}: {current:.2f}")
    
    return test_adaptive_learning


# ================================
 主测试函数
# ================================

def run_advanced_exercises():
    """运行所有高级练习"""
    print("🎯 LangGraph 高级问题解决练习")
    print("=" * 60)
    
    exercises = [
        ("智能推荐系统", exercise_1_recommendation_system),
        ("实时数据流处理", exercise_2_stream_processing),
        ("自适应学习系统", exercise_3_adaptive_learning)
    ]
    
    while True:
        print("\n请选择高级练习:")
        for i, (name, func) in enumerate(exercises, 1):
            print(f"{i}. {name}")
        print("4. 运行所有练习")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-4): ").strip()
        
        if choice == "1":
            exercises[0][1]()
        elif choice == "2":
            exercises[1][1]()
        elif choice == "3":
            exercises[2][1]()
        elif choice == "4":
            print("\n" + "="*50)
            print("运行所有高级练习")
            print("="*50)
            for name, func in exercises:
                print(f"\n{'='*20} {name} {'='*20}")
                func()
                time.sleep(2)
        elif choice == "0":
            print_step("感谢完成高级练习！")
            break
        else:
            print_error("无效选择，请重试")
    
    print_result("高级问题解决练习完成！")


if __name__ == "__main__":
    run_advanced_exercises()
    
    print_step("""
高级练习完成总结:

1. 智能推荐系统
   - 实现了用户画像建模
   - 支持多种推荐算法
   - 包含A/B测试功能
   - 性能评估和优化

2. 实时数据流处理
   - 高并发数据处理
   - 背压机制
   - 异常检测和告警
   - 性能监控

3. 自适应学习系统
   - 学习者画像分析
   - 难度自适应调整
   - 个性化内容推荐
   - 学习路径优化

这些练习展示了LangGraph在处理复杂业务逻辑、
高性能要求和智能化应用方面的强大能力。
    """)