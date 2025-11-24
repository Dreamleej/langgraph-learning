"""
05-exercises: 真实项目实践

这个文件包含完整的真实项目级别的LangGraph应用练习，
模拟企业级应用场景，要求您综合运用所学的所有知识。

项目包括：
- 智能客服系统
- 数据分析平台
- 业务流程自动化
- 多模态AI应用
- 微服务编排平台
"""

from typing import TypedDict, List, Dict, Any, Literal, Optional
from langgraph.graph import StateGraph, END
import sys
import os
import time
import json
import asyncio
import sqlite3
from datetime import datetime, timedelta
from enum import Enum
import random

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import print_step, print_result, print_error, Config


# ================================
 项目 1: 智能客服平台
# ================================

def project_1_customer_service_platform():
    """
    项目 1: 全渠道智能客服平台
    
    功能要求:
    1. 多渠道接入（网站、APP、微信、电话）
    2. 智能路由和分配
    3. 机器人自动回复
    4. 人工转接和协同
    5. 知识库集成
    6. 服务质量监控
    7. 客户满意度管理
    8. 工单系统集成
    
    技术挑战:
    - 高并发处理
    - 实时性要求
    - 多系统集成
    - 用户体验优化
    """
    
    class CustomerServiceState(TypedDict):
        session_id: str
        customer_id: str
        channel: str
        inquiry_type: str
        priority: str
        customer_profile: Dict[str, Any]
        conversation_history: List[Dict[str, Any]]
        knowledge_search_results: List[Dict[str, Any]]
        agent_assignment: Dict[str, Any]
        auto_resolution: Dict[str, Any]
        escalation_info: Dict[str, Any]
        service_metrics: Dict[str, Any]
        satisfaction_score: float
    
    class ChannelType(Enum):
        WEB = "web"
        APP = "app"
        WECHAT = "wechat"
        PHONE = "phone"
        EMAIL = "email"
    
    class InquiryType(Enum):
        GENERAL = "general"
        TECHNICAL = "technical"
        BILLING = "billing"
        COMPLAINT = "complaint"
        CONSULTATION = "consultation"
    
    def initialize_service_session(state: CustomerServiceState) -> CustomerServiceState:
        """初始化客服会话"""
        session_id = state.get("session_id", "")
        customer_id = state.get("customer_id", "")
        channel = state.get("channel", "")
        
        # 客户画像构建
        customer_profile = build_customer_profile(customer_id, channel)
        
        # 会话历史加载
        conversation_history = load_customer_history(customer_id)
        
        return {
            "customer_profile": customer_profile,
            "conversation_history": conversation_history
        }
    
    def build_customer_profile(customer_id: str, channel: str) -> Dict[str, Any]:
        """构建客户画像"""
        profile = {
            "customer_id": customer_id,
            "channel": channel,
            "vip_level": random.choice(["normal", "silver", "gold", "platinum"]),
            "registration_date": f"2023-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "total_orders": random.randint(0, 100),
            "total_spent": random.uniform(0, 10000),
            "preferred_language": random.choice(["中文", "English"]),
            "timezone": random.choice(["UTC+8", "UTC+0", "UTC-5"]),
            "contact_preferences": {},
            "service_history": {
                "total_inquiries": random.randint(0, 50),
                "resolved_rate": random.uniform(0.7, 0.95),
                "average_rating": random.uniform(3.5, 5.0),
                "last_contact": time.time() - random.uniform(0, 30*24*3600)
            }
        }
        
        return profile
    
    def load_customer_history(customer_id: str) -> List[Dict[str, Any]]:
        """加载客户历史记录"""
        history = []
        
        for i in range(random.randint(0, 10)):
            session = {
                "session_id": f"hist_{customer_id}_{i}",
                "timestamp": time.time() - random.uniform(0, 365*24*3600),
                "channel": random.choice([c.value for c in ChannelType]),
                "inquiry_type": random.choice([t.value for t in InquiryType]),
                "resolved": random.random() > 0.2,
                "rating": random.uniform(3.0, 5.0),
                "agent_id": f"agent_{random.randint(1, 20)}",
                "duration": random.randint(5, 60)
            }
            history.append(session)
        
        return sorted(history, key=lambda x: x["timestamp"])
    
    def intelligent_routing(state: CustomerServiceState) -> CustomerServiceState:
        """智能路由分配"""
        customer_profile = state.get("customer_profile", {})
        inquiry_type = state.get("inquiry_type", "")
        priority = state.get("priority", "normal")
        channel = state.get("channel", "")
        
        # 路由策略
        routing_strategy = determine_routing_strategy(customer_profile, inquiry_type, priority)
        
        # 选择坐席
        agent_assignment = assign_agent(routing_strategy, inquiry_type, channel)
        
        return {
            "agent_assignment": agent_assignment
        }
    
    def determine_routing_strategy(profile: Dict[str, Any], inquiry_type: str, priority: str) -> str:
        """确定路由策略"""
        vip_level = profile.get("vip_level", "normal")
        service_history = profile.get("service_history", {})
        resolved_rate = service_history.get("resolved_rate", 0.8)
        
        if vip_level in ["gold", "platinum"] or priority == "urgent":
            return "premium_agent"
        elif resolved_rate < 0.8:
            return "senior_agent"
        elif inquiry_type == "technical":
            return "technical_agent"
        elif inquiry_type == "billing":
            return "billing_agent"
        else:
            return "general_agent"
    
    def assign_agent(strategy: str, inquiry_type: str, channel: str) -> Dict[str, Any]:
        """分配坐席"""
        agent_pools = {
            "premium_agent": ["agent_gold_1", "agent_gold_2", "agent_platinum_1"],
            "senior_agent": ["agent_senior_1", "agent_senior_2", "agent_senior_3"],
            "technical_agent": ["agent_tech_1", "agent_tech_2"],
            "billing_agent": ["agent_billing_1", "agent_billing_2"],
            "general_agent": ["agent_gen_1", "agent_gen_2", "agent_gen_3"]
        }
        
        available_agents = agent_pools.get(strategy, agent_pools["general_agent"])
        selected_agent = random.choice(available_agents)
        
        return {
            "agent_id": selected_agent,
            "strategy": strategy,
            "assigned_at": time.time(),
            "estimated_wait_time": random.randint(10, 120),
            "channel_compatibility": check_channel_compatibility(selected_agent, channel)
        }
    
    def check_channel_compatibility(agent_id: str, channel: str) -> bool:
        """检查坐席渠道兼容性"""
        # 简化：所有坐席都支持所有渠道
        return True
    
    def knowledge_base_search(state: CustomerServiceState) -> CustomerServiceState:
        """知识库搜索"""
        inquiry_type = state.get("inquiry_type", "")
        conversation_history = state.get("conversation_history", [])
        customer_profile = state.get("customer_profile", {})
        
        # 生成搜索关键词
        search_keywords = generate_search_keywords(inquiry_type, conversation_history)
        
        # 执行知识库搜索
        knowledge_results = search_knowledge_base(search_keywords, customer_profile)
        
        return {
            "knowledge_search_results": knowledge_results
        }
    
    def generate_search_keywords(inquiry_type: str, history: List[Dict[str, Any]]) -> List[str]:
        """生成搜索关键词"""
        keywords = [inquiry_type]
        
        # 从历史记录中提取关键词
        if history:
            recent_inquiries = [h for h in history[-3:]]  # 最近3次记录
            for inquiry in recent_inquiries:
                if inquiry.get("inquiry_type"):
                    keywords.append(inquiry["inquiry_type"])
        
        # 添加常见问题关键词
        common_keywords = ["故障", "退款", "账单", "技术支持", "产品咨询"]
        keywords.extend(common_keywords[:2])
        
        return list(set(keywords))
    
    def search_knowledge_base(keywords: List[str], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """搜索知识库"""
        results = []
        
        # 模拟知识库条目
        kb_entries = [
            {
                "id": "kb_001",
                "title": "常见故障排除指南",
                "category": "technical",
                "keywords": ["故障", "技术", "troubleshoot"],
                "content": "详细的技术故障排查步骤...",
                "relevance_score": 0.95,
                "success_rate": 0.88
            },
            {
                "id": "kb_002", 
                "title": "退款政策说明",
                "category": "billing",
                "keywords": ["退款", "billing", "refund"],
                "content": "退款流程和政策详情...",
                "relevance_score": 0.87,
                "success_rate": 0.92
            },
            {
                "id": "kb_003",
                "title": "产品功能介绍",
                "category": "general",
                "keywords": ["产品", "功能", "features"],
                "content": "完整的产品功能介绍...",
                "relevance_score": 0.78,
                "success_rate": 0.85
            }
        ]
        
        # 计算相关性
        for entry in kb_entries:
            relevance = calculate_keyword_relevance(keywords, entry["keywords"])
            entry["relevance_score"] = relevance
            
            # 根据客户画像调整
            if profile.get("vip_level") == "platinum":
                entry["relevance_score"] *= 1.1
        
        # 排序并返回最相关的结果
        sorted_entries = sorted(kb_entries, key=lambda x: x["relevance_score"], reverse=True)
        return sorted_entries[:3]
    
    def calculate_keyword_relevance(search_keywords: List[str], entry_keywords: List[str]) -> float:
        """计算关键词相关性"""
        if not search_keywords:
            return 0.0
        
        matches = len(set(search_keywords) & set(entry_keywords))
        return matches / len(search_keywords)
    
    def auto_resolution(state: CustomerServiceState) -> CustomerServiceState:
        """自动解决尝试"""
        knowledge_results = state.get("knowledge_search_results", [])
        inquiry_type = state.get("inquiry_type", "")
        customer_profile = state.get("customer_profile", {})
        
        # 评估自动解决的可能性
        auto_resolution_capability = assess_auto_resolution(knowledge_results, inquiry_type, customer_profile)
        
        resolution_result = {}
        if auto_resolution_capability["can_auto_resolve"]:
            # 尝试自动解决
            resolution_result = attempt_auto_resolution(auto_resolution_capability, knowledge_results)
        else:
            resolution_result = {
                "auto_resolved": False,
                "reason": "insufficient_knowledge_confidence",
                "recommended_action": "human_intervention"
            }
        
        return {
            "auto_resolution": resolution_result
        }
    
    def assess_auto_resolution(knowledge_results: List[Dict[str, Any]], 
                              inquiry_type: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        """评估自动解决能力"""
        if not knowledge_results:
            return {"can_auto_resolve": False, "confidence": 0.0}
        
        best_match = knowledge_results[0]
        confidence = best_match.get("relevance_score", 0.0)
        success_rate = best_match.get("success_rate", 0.0)
        
        # 考虑客户因素
        vip_level = profile.get("vip_level", "normal")
        history = profile.get("service_history", {})
        resolved_rate = history.get("resolved_rate", 0.8)
        
        # 调整置信度
        if inquiry_type in ["technical", "complaint"]:
            confidence *= 0.7  # 复杂问题降低自动解决置信度
        elif vip_level == "platinum":
            confidence *= 0.8  # VIP客户谨慎自动解决
        elif resolved_rate < 0.6:
            confidence *= 0.6  # 解决率低的客户谨慎处理
        
        return {
            "can_auto_resolve": confidence > 0.75,
            "confidence": confidence,
            "best_kb_article": best_match,
            "factors_considered": ["kb_relevance", "inquiry_type", "vip_level", "history"]
        }
    
    def attempt_auto_resolution(assessment: Dict[str, Any], 
                               knowledge_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """尝试自动解决"""
        best_article = assessment.get("best_kb_article", {})
        confidence = assessment.get("confidence", 0.0)
        
        # 模拟自动解决过程
        time.sleep(random.uniform(1, 3))
        
        # 根据置信度决定结果
        if confidence > 0.85:
            success = True
            reason = "high_confidence_match"
        elif confidence > 0.75:
            success = random.random() > 0.2  # 80% 成功率
            reason = "moderate_confidence_match"
        else:
            success = False
            reason = "low_confidence_match"
        
        return {
            "auto_resolved": success,
            "reason": reason,
            "used_kb_article": best_article.get("id", ""),
            "resolution_time": random.uniform(30, 180),
            "confidence": confidence
        }
    
    def escalation_management(state: CustomerServiceState) -> CustomerServiceState:
        """升级管理"""
        agent_assignment = state.get("agent_assignment", {})
        auto_resolution = state.get("auto_resolution", {})
        priority = state.get("priority", "normal")
        
        escalation_info = {
            "needs_escalation": False,
            "escalation_reason": "",
            "escalation_level": "",
            "escalation_target": "",
            "escalation_automated": False
        }
        
        # 判断是否需要升级
        if not auto_resolution.get("auto_resolved", False) and priority == "urgent":
            escalation_info.update({
                "needs_escalation": True,
                "escalation_reason": "urgent_inquiry_auto_failed",
                "escalation_level": "high_priority",
                "escalation_target": "supervisor",
                "escalation_automated": True
            })
        elif agent_assignment.get("estimated_wait_time", 0) > 300:  # 等待时间超过5分钟
            escalation_info.update({
                "needs_escalation": True,
                "escalation_reason": "long_wait_time",
                "escalation_level": "resource_reallocation",
                "escalation_target": "resource_manager",
                "escalation_automated": True
            })
        
        return {
            "escalation_info": escalation_info
        }
    
    def service_quality_monitoring(state: CustomerServiceState) -> CustomerServiceState:
        """服务质量监控"""
        session_id = state.get("session_id", "")
        agent_assignment = state.get("agent_assignment", {})
        auto_resolution = state.get("auto_resolution", {})
        escalation_info = state.get("escalation_info", {})
        
        # 计算服务指标
        service_metrics = {
            "session_id": session_id,
            "response_time": auto_resolution.get("resolution_time", 0),
            "first_contact_resolution": auto_resolution.get("auto_resolved", False),
            "agent_wait_time": agent_assignment.get("estimated_wait_time", 0),
            "escalation_count": 1 if escalation_info.get("needs_escalation", False) else 0,
            "channel_compliance": True,
            "sla_met": True,
            "customer_effort_score": calculate_customer_effort_score(auto_resolution, escalation_info)
        }
        
        # 满意度预测
        satisfaction_score = predict_satisfaction_score(service_metrics)
        
        return {
            "service_metrics": service_metrics,
            "satisfaction_score": satisfaction_score
        }
    
    def calculate_customer_effort_score(auto_resolution: Dict[str, Any], 
                                        escalation: Dict[str, Any]) -> float:
        """计算客户费力指数"""
        base_score = 3.0  # 中等费力程度
        
        # 自动解决降低费力程度
        if auto_resolution.get("auto_resolved", False):
            base_score -= 1.5
        else:
            base_score += 0.5
        
        # 升级增加费力程度
        if escalation.get("needs_escalation", False):
            base_score += 1.0
        
        return max(1.0, min(5.0, base_score))
    
    def predict_satisfaction_score(metrics: Dict[str, Any]) -> float:
        """预测满意度分数"""
        score = 4.0  # 基础分数
        
        # 第一时间解决加分
        if metrics.get("first_contact_resolution", False):
            score += 0.5
        
        # 响应时间影响
        response_time = metrics.get("response_time", 0)
        if response_time < 60:  # 1分钟内
            score += 0.3
        elif response_time > 300:  # 超过5分钟
            score -= 0.3
        
        # 客户费力指数影响
        effort_score = metrics.get("customer_effort_score", 3.0)
        if effort_score <= 2.0:
            score += 0.2
        elif effort_score >= 4.0:
            score -= 0.2
        
        # 升级影响
        if metrics.get("escalation_count", 0) > 0:
            score -= 0.4
        
        return max(1.0, min(5.0, score))
    
    # 构建客服平台工作流
    def build_customer_service_workflow():
        workflow = StateGraph(CustomerServiceState)
        
        workflow.add_node("initialize_session", initialize_service_session)
        workflow.add_node("intelligent_routing", intelligent_routing)
        workflow.add_node("knowledge_search", knowledge_base_search)
        workflow.add_node("auto_resolution", auto_resolution)
        workflow.add_node("escalation_management", escalation_management)
        workflow.add_node("quality_monitoring", service_quality_monitoring)
        
        workflow.set_entry_point("initialize_session")
        workflow.add_edge("initialize_session", "intelligent_routing")
        workflow.add_edge("intelligent_routing", "knowledge_search")
        
        # 并行执行自动解决和准备人工服务
        workflow.add_edge("knowledge_search", "auto_resolution")
        
        workflow.add_edge("auto_resolution", "escalation_management")
        workflow.add_edge("escalation_management", "quality_monitoring")
        workflow.add_edge("quality_monitoring", END)
        
        return workflow.compile()
    
    # 测试客服平台
    def test_customer_service_platform():
        print_step("测试智能客服平台")
        
        app = build_customer_service_workflow()
        
        # 模拟不同类型的客服请求
        test_cases = [
            {
                "name": "VIP客户技术问题",
                "customer_id": "vip_001",
                "channel": "phone",
                "inquiry_type": "technical",
                "priority": "urgent"
            },
            {
                "name": "普通客户账单咨询",
                "customer_id": "cust_002",
                "channel": "web",
                "inquiry_type": "billing",
                "priority": "normal"
            },
            {
                "name": "新用户产品咨询",
                "customer_id": "new_003",
                "channel": "wechat",
                "inquiry_type": "general",
                "priority": "low"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*50}")
            print(f"测试案例 {i}: {test_case['name']}")
            print(f"{'='*50}")
            
            initial_state = {
                "session_id": f"session_{int(time.time())}_{i}",
                "customer_id": test_case["customer_id"],
                "channel": test_case["channel"],
                "inquiry_type": test_case["inquiry_type"],
                "priority": test_case["priority"],
                "customer_profile": {},
                "conversation_history": [],
                "knowledge_search_results": [],
                "agent_assignment": {},
                "auto_resolution": {},
                "escalation_info": {},
                "service_metrics": {},
                "satisfaction_score": 0.0
            }
            
            result = app.invoke(initial_state)
            
            # 显示结果
            agent_assignment = result.get("agent_assignment", {})
            auto_resolution = result.get("auto_resolution", {})
            escalation_info = result.get("escalation_info", {})
            service_metrics = result.get("service_metrics", {})
            satisfaction_score = result.get("satisfaction_score", 0.0)
            
            print(f"\n📋 服务结果:")
            print(f"  分配坐席: {agent_assignment.get('agent_id', 'N/A')}")
            print(f"  坐席策略: {agent_assignment.get('strategy', 'N/A')}")
            print(f"  预计等待: {agent_assignment.get('estimated_wait_time', 0)}秒")
            
            print(f"\n🤖 自动处理:")
            auto_resolved = auto_resolution.get("auto_resolved", False)
            print(f"  自动解决: {'是' if auto_resolved else '否'}")
            print(f"  原因: {auto_resolution.get('reason', 'N/A')}")
            
            print(f"\n⚡ 升级管理:")
            needs_escalation = escalation_info.get("needs_escalation", False)
            print(f"  需要升级: {'是' if needs_escalation else '否'}")
            if needs_escalation:
                print(f"  升级原因: {escalation_info.get('escalation_reason', 'N/A')}")
            
            print(f"\n📊 服务质量:")
            print(f"  响应时间: {service_metrics.get('response_time', 0):.1f}秒")
            print(f"  首次解决: {'是' if service_metrics.get('first_contact_resolution', False) else '否'}")
            print(f"  客户费力指数: {service_metrics.get('customer_effort_score', 0):.1f}")
            print(f"  预测满意度: {satisfaction_score:.1f}/5.0")
    
    return test_customer_service_platform


# ================================
 项目 2: 数据分析平台
# ================================

def project_2_data_analytics_platform():
    """
    项目 2: 智能数据分析平台
    
    功能要求:
    1. 多数据源集成
    2. 自动化数据清洗
    3. 智能数据可视化
    4. 预测性分析
    5. 报告自动生成
    6. 异常检测
    7. 实时监控面板
    8. 数据治理
    
    技术挑战:
    - 大数据处理
    - 复杂算法集成
    - 实时计算
    - 可视化渲染
    """
    
    class AnalyticsState(TypedDict):
        project_id: str
        data_sources: List[Dict[str, Any]]
        raw_data: Dict[str, Any]
        cleaned_data: Dict[str, Any]
        analysis_results: Dict[str, Any]
        visualizations: List[Dict[str, Any]]
        predictions: Dict[str, Any]
        anomalies: List[Dict[str, Any]]
        reports: List[Dict[str, Any]]
        quality_metrics: Dict[str, Any]
        execution_summary: Dict[str, Any]
    
    def initialize_analytics_project(state: AnalyticsState) -> AnalyticsState:
        """初始化分析项目"""
        project_id = state.get("project_id", "")
        data_sources = state.get("data_sources", [])
        
        # 验证数据源
        validated_sources = validate_data_sources(data_sources)
        
        # 加载原始数据
        raw_data = load_data_from_sources(validated_sources)
        
        return {
            "data_sources": validated_sources,
            "raw_data": raw_data
        }
    
    def validate_data_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证数据源"""
        validated_sources = []
        
        for source in sources:
            # 模拟数据源验证
            validation_result = {
                **source,
                "validated": True,
                "validation_timestamp": time.time(),
                "accessibility": random.choice(["accessible", "restricted", "unavailable"]),
                "data_quality_score": random.uniform(0.6, 0.95),
                "estimated_size_mb": random.randint(100, 10000)
            }
            validated_sources.append(validation_result)
        
        return validated_sources
    
    def load_data_from_sources(sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从数据源加载数据"""
        raw_data = {}
        
        for source in sources:
            if source.get("accessibility") == "accessible":
                # 模拟数据加载
                data_size = source.get("estimated_size_mb", 100)
                record_count = data_size * 1000  # 假设每条记录1KB
                
                source_data = {
                    "source_id": source.get("source_id", ""),
                    "record_count": record_count,
                    "columns": [
                        "id", "timestamp", "value", "category", "region", 
                        "user_id", "action", "amount", "status"
                    ],
                    "sample_data": generate_sample_data(record_count // 100),  # 1%样本
                    "metadata": {
                        "load_time": time.time(),
                        "file_format": random.choice(["csv", "json", "parquet"]),
                        "encoding": "utf-8",
                        "compression": random.choice(["none", "gzip", "snappy"])
                    }
                }
                raw_data[source.get("source_id", "")] = source_data
        
        return raw_data
    
    def generate_sample_data(count: int) -> List[Dict[str, Any]]:
        """生成样本数据"""
        data = []
        
        for i in range(count):
            record = {
                "id": i,
                "timestamp": time.time() - random.uniform(0, 365*24*3600),
                "value": random.uniform(0, 1000),
                "category": random.choice(["A", "B", "C", "D"]),
                "region": random.choice(["北京", "上海", "广州", "深圳", "杭州"]),
                "user_id": random.randint(1000, 9999),
                "action": random.choice(["view", "click", "purchase", "cancel"]),
                "amount": random.uniform(10, 500),
                "status": random.choice(["active", "inactive", "pending"])
            }
            data.append(record)
        
        return data
    
    def data_cleaning(state: AnalyticsState) -> AnalyticsState:
        """数据清洗"""
        raw_data = state.get("raw_data", {})
        
        cleaned_data = {}
        quality_metrics = {
            "total_records_before": 0,
            "total_records_after": 0,
            "duplicates_removed": 0,
            "missing_values_handled": 0,
            "outliers_detected": 0,
            "data_quality_score": 0.0
        }
        
        for source_id, source_data in raw_data.items():
            # 执行数据清洗
            cleaning_result = clean_source_data(source_data)
            cleaned_data[source_id] = cleaning_result["cleaned_data"]
            
            # 更新质量指标
            quality_metrics["total_records_before"] += source_data.get("record_count", 0)
            quality_metrics["total_records_after"] += cleaning_result["record_count"]
            quality_metrics["duplicates_removed"] += cleaning_result["duplicates_removed"]
            quality_metrics["missing_values_handled"] += cleaning_result["missing_values_handled"]
            quality_metrics["outliers_detected"] += cleaning_result["outliers_detected"]
        
        # 计算总体质量分数
        if quality_metrics["total_records_before"] > 0:
            quality_metrics["data_quality_score"] = (
                quality_metrics["total_records_after"] / quality_metrics["total_records_before"]
            )
        
        return {
            "cleaned_data": cleaned_data,
            "quality_metrics": quality_metrics
        }
    
    def clean_source_data(source_data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗单个数据源"""
        sample_data = source_data.get("sample_data", [])
        original_count = len(sample_data)
        
        # 去重
        unique_data = []
        seen_ids = set()
        for record in sample_data:
            record_id = record.get("id")
            if record_id not in seen_ids:
                unique_data.append(record)
                seen_ids.add(record_id)
        
        duplicates_removed = original_count - len(unique_data)
        
        # 处理缺失值
        cleaned_data = []
        missing_values_handled = 0
        
        for record in unique_data:
            cleaned_record = record.copy()
            
            # 填充缺失值
            for key, value in record.items():
                if value is None or value == "":
                    if key == "value":
                        cleaned_record[key] = 0.0
                    elif key == "category":
                        cleaned_record[key] = "Unknown"
                    elif key == "region":
                        cleaned_record[key] = "Unknown"
                    else:
                        cleaned_record[key] = 0
                    missing_values_handled += 1
            
            cleaned_data.append(cleaned_record)
        
        # 检测异常值
        outliers_detected = 0
        if cleaned_data:
            values = [record.get("value", 0) for record in cleaned_data]
            if values:
                q75 = sorted(values)[int(len(values) * 0.75)]
                q25 = sorted(values)[int(len(values) * 0.25)]
                iqr = q75 - q25
                
                upper_bound = q75 + 1.5 * iqr
                lower_bound = q25 - 1.5 * iqr
                
                outliers = [v for v in values if v > upper_bound or v < lower_bound]
                outliers_detected = len(outliers)
        
        return {
            "cleaned_data": cleaned_data,
            "record_count": len(cleaned_data),
            "duplicates_removed": duplicates_removed,
            "missing_values_handled": missing_values_handled,
            "outliers_detected": outliers_detected
        }
    
    def exploratory_analysis(state: AnalyticsState) -> AnalyticsState:
        """探索性数据分析"""
        cleaned_data = state.get("cleaned_data", {})
        
        analysis_results = {
            "descriptive_statistics": {},
            "correlation_analysis": {},
            "distribution_analysis": {},
            "trend_analysis": {},
            "summary_insights": []
        }
        
        for source_id, data in cleaned_data.items():
            sample_data = data.get("cleaned_data", [])
            
            if not sample_data:
                continue
            
            # 描述性统计
            stats = calculate_descriptive_statistics(sample_data)
            analysis_results["descriptive_statistics"][source_id] = stats
            
            # 相关性分析
            correlations = calculate_correlations(sample_data)
            analysis_results["correlation_analysis"][source_id] = correlations
            
            # 分布分析
            distributions = analyze_distributions(sample_data)
            analysis_results["distribution_analysis"][source_id] = distributions
            
            # 趋势分析
            trends = analyze_trends(sample_data)
            analysis_results["trend_analysis"][source_id] = trends
        
        # 生成洞察
        analysis_results["summary_insights"] = generate_summary_insights(analysis_results)
        
        return {
            "analysis_results": analysis_results
        }
    
    def calculate_descriptive_statistics(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算描述性统计"""
        values = [record.get("value", 0) for record in data]
        amounts = [record.get("amount", 0) for record in data]
        
        stats = {}
        
        if values:
            stats["value"] = {
                "count": len(values),
                "mean": sum(values) / len(values),
                "median": sorted(values)[len(values) // 2],
                "min": min(values),
                "max": max(values),
                "std": calculate_std(values)
            }
        
        if amounts:
            stats["amount"] = {
                "count": len(amounts),
                "mean": sum(amounts) / len(amounts),
                "median": sorted(amounts)[len(amounts) // 2],
                "min": min(amounts),
                "max": max(amounts),
                "std": calculate_std(amounts)
            }
        
        # 分类统计
        categories = [record.get("category", "") for record in data]
        category_counts = {}
        for cat in categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1
        stats["category_distribution"] = category_counts
        
        # 地区统计
        regions = [record.get("region", "") for record in data]
        region_counts = {}
        for region in regions:
            region_counts[region] = region_counts.get(region, 0) + 1
        stats["region_distribution"] = region_counts
        
        return stats
    
    def calculate_std(values: List[float]) -> float:
        """计算标准差"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def calculate_correlations(data: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算相关性"""
        # 简化：只计算数值字段的相关性
        values = [record.get("value", 0) for record in data]
        amounts = [record.get("amount", 0) for record in data]
        
        if len(values) != len(amounts) or len(values) < 2:
            return {}
        
        # 计算皮尔逊相关系数
        n = len(values)
        sum_x = sum(values)
        sum_y = sum(amounts)
        sum_xy = sum(v * a for v, a in zip(values, amounts))
        sum_x2 = sum(v ** 2 for v in values)
        sum_y2 = sum(a ** 2 for a in amounts)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
        
        if denominator == 0:
            correlation = 0.0
        else:
            correlation = numerator / denominator
        
        return {"value_amount_correlation": correlation}
    
    def analyze_distributions(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析数据分布"""
        values = [record.get("value", 0) for record in data]
        
        if not values:
            return {}
        
        # 简单的分布分析
        sorted_values = sorted(values)
        n = len(values)
        
        distribution_analysis = {
            "quartiles": {
                "q1": sorted_values[n // 4],
                "q2": sorted_values[n // 2],  # median
                "q3": sorted_values[3 * n // 4]
            },
            "percentiles": {
                "p10": sorted_values[n // 10],
                "p90": sorted_values[9 * n // 10],
                "p95": sorted_values[95 * n // 100]
            },
            "skewness": calculate_skewness(values),
            "distribution_type": identify_distribution_type(values)
        }
        
        return distribution_analysis
    
    def calculate_skewness(values: List[float]) -> float:
        """计算偏度"""
        if len(values) < 3:
            return 0.0
        
        mean = sum(values) / len(values)
        std = calculate_std(values)
        
        if std == 0:
            return 0.0
        
        skew = sum(((x - mean) / std) ** 3 for x in values) / len(values)
        return skew
    
    def identify_distribution_type(values: List[float]) -> str:
        """识别分布类型"""
        skewness = calculate_skewness(values)
        
        if abs(skewness) < 0.5:
            return "normal"
        elif skewness > 0.5:
            return "right_skewed"
        elif skewness < -0.5:
            return "left_skewed"
        else:
            return "unknown"
    
    def analyze_trends(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析趋势"""
        if not data:
            return {}
        
        # 按时间排序
        sorted_data = sorted(data, key=lambda x: x.get("timestamp", 0))
        
        # 简单的趋势分析
        timestamps = [record.get("timestamp", 0) for record in sorted_data]
        values = [record.get("value", 0) for record in sorted_data]
        
        if len(values) < 2:
            return {}
        
        # 计算简单线性趋势
        n = len(values)
        x_mean = (timestamps[-1] + timestamps[0]) / 2
        y_mean = sum(values) / n
        
        numerator = sum((t - x_mean) * (v - y_mean) for t, v in zip(timestamps, values))
        denominator = sum((t - x_mean) ** 2 for t in timestamps)
        
        if denominator == 0:
            trend_slope = 0.0
        else:
            trend_slope = numerator / denominator
        
        # 趋势方向
        if abs(trend_slope) < 1e-10:
            trend_direction = "stable"
        elif trend_slope > 0:
            trend_direction = "increasing"
        else:
            trend_direction = "decreasing"
        
        return {
            "trend_slope": trend_slope,
            "trend_direction": trend_direction,
            "time_span": timestamps[-1] - timestamps[0],
            "data_points": n
        }
    
    def generate_summary_insights(analysis_results: Dict[str, Any]) -> List[str]:
        """生成洞察摘要"""
        insights = []
        
        # 从描述性统计中生成洞察
        desc_stats = analysis_results.get("descriptive_statistics", {})
        for source_id, stats in desc_stats.items():
            if "value" in stats:
                value_stats = stats["value"]
                if value_stats.get("std", 0) > value_stats.get("mean", 0):
                    insights.append(f"{source_id}: 数值变异性较高，需要进一步调查")
            
            if "category_distribution" in stats:
                cat_dist = stats["category_distribution"]
                if cat_dist:
                    most_common = max(cat_dist.items(), key=lambda x: x[1])
                    insights.append(f"{source_id}: 最常见类别是 '{most_common[0]}'，占比 {most_common[1]/sum(cat_dist.values()):.1%}")
        
        # 从相关性分析中生成洞察
        correlations = analysis_results.get("correlation_analysis", {})
        for source_id, corr in correlations.items():
            value_amount_corr = corr.get("value_amount_correlation", 0)
            if abs(value_amount_corr) > 0.7:
                if value_amount_corr > 0:
                    insights.append(f"{source_id}: 数值和金额呈强正相关")
                else:
                    insights.append(f"{source_id}: 数值和金额呈强负相关")
        
        # 从趋势分析中生成洞察
        trends = analysis_results.get("trend_analysis", {})
        for source_id, trend in trends.items():
            trend_dir = trend.get("trend_direction", "stable")
            if trend_dir == "increasing":
                insights.append(f"{source_id}: 呈上升趋势")
            elif trend_dir == "decreasing":
                insights.append(f"{source_id}: 呈下降趋势")
        
        return insights
    
    def predictive_analysis(state: AnalyticsState) -> AnalyticsState:
        """预测性分析"""
        cleaned_data = state.get("cleaned_data", {})
        
        predictions = {
            "forecasting": {},
            "classification": {},
            "anomaly_prediction": {},
            "confidence_scores": {}
        }
        
        for source_id, data in cleaned_data.items():
            sample_data = data.get("cleaned_data", [])
            
            if not sample_data:
                continue
            
            # 时间序列预测
            forecast = time_series_forecast(sample_data)
            predictions["forecasting"][source_id] = forecast
            
            # 分类预测
            classification = predict_categories(sample_data)
            predictions["classification"][source_id] = classification
            
            # 异常预测
            anomaly_pred = predict_anomalies(sample_data)
            predictions["anomaly_prediction"][source_id] = anomaly_pred
        
        return {
            "predictions": predictions
        }
    
    def time_series_forecast(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """时间序列预测"""
        # 简化的移动平均预测
        if len(data) < 5:
            return {"error": "Insufficient data for forecasting"}
        
        # 按时间排序
        sorted_data = sorted(data, key=lambda x: x.get("timestamp", 0))
        values = [record.get("value", 0) for record in sorted_data]
        
        # 简单移动平均
        window_size = min(5, len(values) // 3)
        recent_values = values[-window_size:]
        forecast_value = sum(recent_values) / len(recent_values)
        
        # 计算趋势
        if len(values) >= 10:
            early_avg = sum(values[:len(values)//2]) / (len(values)//2)
            recent_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
            trend = recent_avg - early_avg
        else:
            trend = 0.0
        
        # 预测未来5个点
        forecast_points = []
        for i in range(5):
            future_value = forecast_value + trend * (i + 1)
            forecast_points.append(max(0, future_value))  # 确保非负
        
        return {
            "forecast_values": forecast_points,
            "confidence_interval": 0.8,  # 简化的置信度
            "trend": "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable",
            "method": "moving_average_with_trend"
        }
    
    def predict_categories(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """预测分类"""
        # 基于历史频率的简单分类预测
        categories = [record.get("category", "") for record in data]
        category_counts = {}
        
        for cat in categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        total = len(categories)
        category_probabilities = {cat: count / total for cat, count in category_counts.items()}
        
        # 预测下一个最可能的类别
        predicted_category = max(category_probabilities.items(), key=lambda x: x[1])[0]
        confidence = category_probabilities[predicted_category]
        
        return {
            "predicted_category": predicted_category,
            "confidence": confidence,
            "all_probabilities": category_probabilities
        }
    
    def predict_anomalies(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """预测异常"""
        values = [record.get("value", 0) for record in data]
        
        if len(values) < 10:
            return {"error": "Insufficient data for anomaly prediction"}
        
        # 使用统计方法检测异常
        mean = sum(values) / len(values)
        std = calculate_std(values)
        
        # 预测异常阈值
        upper_threshold = mean + 2 * std
        lower_threshold = mean - 2 * std
        
        # 识别当前异常
        anomalies = []
        for i, value in enumerate(values):
            if value > upper_threshold or value < lower_threshold:
                anomalies.append({
                    "index": i,
                    "value": value,
                    "anomaly_type": "high" if value > upper_threshold else "low",
                    "severity": abs(value - mean) / std
                })
        
        return {
            "anomaly_count": len(anomalies),
            "anomaly_rate": len(anomalies) / len(values),
            "thresholds": {
                "upper": upper_threshold,
                "lower": lower_threshold
            },
            "anomalies": anomalies[:5]  # 只返回前5个异常
        }
    
    def generate_visualizations(state: AnalyticsState) -> AnalyticsState:
        """生成可视化"""
        analysis_results = state.get("analysis_results", {})
        predictions = state.get("predictions", {})
        
        visualizations = []
        
        # 基于分析结果生成可视化配置
        desc_stats = analysis_results.get("descriptive_statistics", {})
        for source_id, stats in desc_stats.items():
            # 柱状图
            if "category_distribution" in stats:
                visualizations.append({
                    "type": "bar_chart",
                    "title": f"{source_id} Category Distribution",
                    "data": stats["category_distribution"],
                    "config": {
                        "x_axis": "Category",
                        "y_axis": "Count"
                    }
                })
            
            # 箱线图
            if "value" in stats:
                visualizations.append({
                    "type": "box_plot",
                    "title": f"{source_id} Value Distribution",
                    "data": {
                        "mean": stats["value"]["mean"],
                        "median": stats["value"]["median"],
                        "q1": stats["value"]["mean"] - stats["value"]["std"],
                        "q3": stats["value"]["mean"] + stats["value"]["std"],
                        "min": stats["value"]["min"],
                        "max": stats["value"]["max"]
                    }
                })
        
        # 基于预测结果生成可视化
        forecasting = predictions.get("forecasting", {})
        for source_id, forecast in forecasting.items():
            if "forecast_values" in forecast:
                visualizations.append({
                    "type": "line_chart",
                    "title": f"{source_id} Forecast",
                    "data": {
                        "forecast": forecast["forecast_values"],
                        "confidence": forecast.get("confidence_interval", 0.8)
                    }
                })
        
        return {
            "visualizations": visualizations
        }
    
    def generate_reports(state: AnalyticsState) -> AnalyticsState:
        """生成分析报告"""
        analysis_results = state.get("analysis_results", {})
        predictions = state.get("predictions", {})
        quality_metrics = state.get("quality_metrics", {})
        visualizations = state.get("visualizations", [])
        
        reports = []
        
        # 执行摘要报告
        executive_summary = {
            "report_id": f"exec_summary_{int(time.time())}",
            "type": "executive_summary",
            "title": "数据分析执行摘要",
            "content": generate_executive_summary_content(analysis_results, quality_metrics),
            "generated_at": datetime.now().isoformat(),
            "audience": "executives"
        }
        reports.append(executive_summary)
        
        # 技术报告
        technical_report = {
            "report_id": f"technical_{int(time.time())}",
            "type": "technical_report",
            "title": "详细技术分析报告",
            "content": generate_technical_report_content(analysis_results, predictions),
            "generated_at": datetime.now().isoformat(),
            "audience": "analysts"
        }
        reports.append(technical_report)
        
        # 可视化报告
        viz_report = {
            "report_id": f"visualization_{int(time.time())}",
            "type": "visualization_report",
            "title": "数据可视化报告",
            "content": generate_visualization_report_content(visualizations),
            "generated_at": datetime.now().isoformat(),
            "audience": "all"
        }
        reports.append(viz_report)
        
        return {
            "reports": reports
        }
    
    def generate_executive_summary_content(analysis_results: Dict[str, Any], 
                                          quality_metrics: Dict[str, Any]) -> str:
        """生成执行摘要内容"""
        total_records_before = quality_metrics.get("total_records_before", 0)
        total_records_after = quality_metrics.get("total_records_after", 0)
        data_quality_score = quality_metrics.get("data_quality_score", 0.0)
        
        insights = analysis_results.get("summary_insights", [])
        
        summary = f"""
数据分析执行摘要

数据概览:
- 处理前总记录数: {total_records_before:,}
- 清洗后总记录数: {total_records_after:,}
- 数据质量评分: {data_quality_score:.2%}

关键洞察:
"""
        
        for i, insight in enumerate(insights[:5], 1):
            summary += f"{i}. {insight}\n"
        
        summary += f"""
建议:
- 继续监控数据质量
- 关注关键趋势变化
- 深入分析异常模式
"""
        
        return summary
    
    def generate_technical_report_content(analysis_results: Dict[str, Any], 
                                         predictions: Dict[str, Any]) -> str:
        """生成技术报告内容"""
        return f"""
详细技术分析报告

分析方法:
- 描述性统计分析
- 相关性分析
- 分布分析
- 趋势分析
- 预测建模

主要发现:
{json.dumps(analysis_results, indent=2, ensure_ascii=False)[:1000]}...

预测结果:
{json.dumps(predictions, indent=2, ensure_ascii=False)[:1000]}...

技术建议:
- 考虑使用更高级的预测模型
- 增加特征工程
- 优化数据清洗流程
"""
    
    def generate_visualization_report_content(visualizations: List[Dict[str, Any]]) -> str:
        """生成可视化报告内容"""
        return f"""
数据可视化报告

可视化概览:
- 生成图表数量: {len(visualizations)}
- 图表类型: {[viz['type'] for viz in visualizations]}

详细图表:
{json.dumps(visualizations, indent=2, ensure_ascii=False)[:1500]}...
"""
    
    def create_execution_summary(state: AnalyticsState) -> AnalyticsState:
        """创建执行摘要"""
        project_id = state.get("project_id", "")
        quality_metrics = state.get("quality_metrics", {})
        analysis_results = state.get("analysis_results", {})
        predictions = state.get("predictions", {})
        visualizations = state.get("visualizations", [])
        reports = state.get("reports", [])
        
        execution_summary = {
            "project_id": project_id,
            "execution_time": time.time(),
            "data_sources_processed": len(state.get("data_sources", [])),
            "total_records_analyzed": quality_metrics.get("total_records_after", 0),
            "data_quality_score": quality_metrics.get("data_quality_score", 0.0),
            "visualizations_generated": len(visualizations),
            "reports_created": len(reports),
            "predictions_made": len(predictions.get("forecasting", {})),
            "key_insights": len(analysis_results.get("summary_insights", [])),
            "anomalies_detected": sum(
                pred.get("anomaly_count", 0) 
                for pred in predictions.get("anomaly_prediction", {}).values()
            )
        }
        
        return {
            "execution_summary": execution_summary
        }
    
    # 构建数据分析平台工作流
    def build_analytics_workflow():
        workflow = StateGraph(AnalyticsState)
        
        workflow.add_node("initialize_project", initialize_analytics_project)
        workflow.add_node("data_cleaning", data_cleaning)
        workflow.add_node("exploratory_analysis", exploratory_analysis)
        workflow.add_node("predictive_analysis", predictive_analysis)
        workflow.add_node("generate_visualizations", generate_visualizations)
        workflow.add_node("generate_reports", generate_reports)
        workflow.add_node("create_summary", create_execution_summary)
        
        workflow.set_entry_point("initialize_project")
        workflow.add_edge("initialize_project", "data_cleaning")
        workflow.add_edge("data_cleaning", "exploratory_analysis")
        workflow.add_edge("exploratory_analysis", "predictive_analysis")
        
        # 并行执行可视化和报告生成
        workflow.add_edge("predictive_analysis", "generate_visualizations")
        workflow.add_edge("predictive_analysis", "generate_reports")
        
        workflow.add_edge("generate_visualizations", "create_summary")
        workflow.add_edge("generate_reports", "create_summary")
        workflow.add_edge("create_summary", END)
        
        return workflow.compile()
    
    # 测试数据分析平台
    def test_data_analytics_platform():
        print_step("测试数据分析平台")
        
        app = build_analytics_workflow()
        
        # 模拟数据源
        data_sources = [
            {
                "source_id": "sales_data",
                "source_type": "database",
                "connection_string": "postgresql://...",
                "table_name": "sales_transactions",
                "last_updated": time.time() - 86400
            },
            {
                "source_id": "user_behavior",
                "source_type": "file",
                "file_path": "/data/user_events.csv",
                "format": "csv",
                "last_updated": time.time() - 3600
            },
            {
                "source_id": "inventory",
                "source_type": "api",
                "api_endpoint": "https://api.company.com/inventory",
                "auth_required": True,
                "last_updated": time.time() - 1800
            }
        ]
        
        initial_state = {
            "project_id": f"analytics_project_{int(time.time())}",
            "data_sources": data_sources,
            "raw_data": {},
            "cleaned_data": {},
            "analysis_results": {},
            "visualizations": [],
            "predictions": {},
            "anomalies": [],
            "reports": [],
            "quality_metrics": {},
            "execution_summary": {}
        }
        
        result = app.invoke(initial_state)
        
        # 显示结果
        quality_metrics = result.get("quality_metrics", {})
        analysis_results = result.get("analysis_results", {})
        visualizations = result.get("visualizations", [])
        reports = result.get("reports", [])
        execution_summary = result.get("execution_summary", {})
        
        print(f"\n📊 数据质量指标:")
        print(f"  处理前记录数: {quality_metrics.get('total_records_before', 0):,}")
        print(f"  处理后记录数: {quality_metrics.get('total_records_after', 0):,}")
        print(f"  数据质量评分: {quality_metrics.get('data_quality_score', 0):.2%}")
        print(f"  去重记录数: {quality_metrics.get('duplicates_removed', 0):,}")
        print(f"  处理缺失值: {quality_metrics.get('missing_values_handled', 0):,}")
        
        summary_insights = analysis_results.get("summary_insights", [])
        if summary_insights:
            print(f"\n💡 关键洞察:")
            for i, insight in enumerate(summary_insights[:3], 1):
                print(f"  {i}. {insight}")
        
        print(f"\n📈 可视化结果:")
        print(f"  生成图表数量: {len(visualizations)}")
        chart_types = [viz.get("type", "unknown") for viz in visualizations]
        for chart_type in set(chart_types):
            count = chart_types.count(chart_type)
            print(f"  - {chart_type}: {count}个")
        
        print(f"\n📋 分析报告:")
        print(f"  生成报告数: {len(reports)}")
        for report in reports:
            print(f"  - {report.get('title', 'Unnamed')} ({report.get('type', 'unknown')})")
        
        print(f"\n⚡ 执行摘要:")
        print(f"  数据源数量: {execution_summary.get('data_sources_processed', 0)}")
        print(f"  分析记录数: {execution_summary.get('total_records_analyzed', 0):,}")
        print(f"  检测异常数: {execution_summary.get('anomalies_detected', 0)}")
        print(f"  关键洞察数: {execution_summary.get('key_insights', 0)}")
    
    return test_data_analytics_platform


# ================================
 主测试函数
# ================================

def run_real_projects():
    """运行真实项目测试"""
    print("🚀 LangGraph 真实项目实践")
    print("=" * 60)
    
    projects = [
        ("智能客服平台", project_1_customer_service_platform),
        ("数据分析平台", project_2_data_analytics_platform)
    ]
    
    while True:
        print("\n请选择项目:")
        for i, (name, func) in enumerate(projects, 1):
            print(f"{i}. {name}")
        print("3. 运行所有项目")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-3): ").strip()
        
        if choice == "1":
            projects[0][1]()
        elif choice == "2":
            projects[1][1]()
        elif choice == "3":
            print("\n" + "="*50)
            print("运行所有真实项目")
            print("="*50)
            for name, func in projects:
                print(f"\n{'='*20} {name} {'='*20}")
                func()
                time.sleep(3)
        elif choice == "0":
            print_step("感谢完成真实项目实践！")
            break
        else:
            print_error("无效选择，请重试")
    
    print_result("真实项目实践完成！")


if __name__ == "__main__":
    run_real_projects()
    
    print_step("""
真实项目实践完成总结:

1. 智能客服平台
   - 多渠道接入支持
   - 智能路由和分配
   - 知识库集成
   - 自动解决和人工转接
   - 服务质量监控
   - 客户满意度管理

2. 数据分析平台
   - 多数据源集成
   - 自动化数据清洗
   - 探索性数据分析
   - 预测性分析
   - 可视化生成
   - 报告自动生成

这些项目展示了LangGraph在企业级应用中的
强大能力，包括复杂业务逻辑处理、
多系统集成、实时性能要求等。

通过这些项目实践，您应该已经掌握了:
- 复杂状态管理
- 高级工作流设计
- 性能优化技巧
- 错误处理策略
- 企业级应用架构

恭喜您完成LangGraph的完整学习旅程！
    """)