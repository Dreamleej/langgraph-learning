#!/usr/bin/env python3
"""
模板应用演示
展示如何使用模板引擎快速构建LangGraph应用
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from template_engine import TemplateManager, print_step
from utils.config import get_llm


def register_bot_functions(manager: TemplateManager):
    """注册聊天机器人相关函数"""
    
    def analyze_input(state):
        """分析用户输入"""
        print_step("分析用户输入")
        current_input = state.get("current_input", "")
        
        # 简单的输入分析
        analysis = {
            "length": len(current_input),
            "word_count": len(current_input.split()),
            "has_question": "?" in current_input,
            "has_numbers": any(char.isdigit() for char in current_input),
            "language": "zh" if any('\u4e00' <= char <= '\u9fff' for char in current_input) else "en"
        }
        
        return {
            **state,
            "input_analysis": analysis,
            "context": {**state.get("context", {}), "last_analysis": analysis}
        }
    
    def recognize_intent(state):
        """识别用户意图"""
        print_step("识别用户意图")
        current_input = state.get("current_input", "")
        analysis = state.get("input_analysis", {})
        
        # 简单的意图识别逻辑
        input_lower = current_input.lower()
        
        if any(word in input_lower for word in ["你好", "hello", "hi"]):
            intent = "greeting"
        elif analysis.get("has_question", False):
            intent = "question"
        elif any(word in input_lower for word in ["谢谢", "thank", "thanks"]):
            intent = "gratitude"
        elif any(word in input_lower for word in ["再见", "bye", "goodbye"]):
            intent = "farewell"
        else:
            intent = "general_chat"
        
        return {
            **state,
            "intent": intent
        }
    
    def retrieve_context(state):
        """检索相关上下文"""
        print_step("检索上下文")
        intent = state.get("intent", "")
        messages = state.get("messages", [])
        
        # 简单的上下文检索
        relevant_context = []
        
        # 根据意图检索相关历史消息
        if intent == "greeting":
            relevant_context = [{"type": "greeting_template", "content": "你好！很高兴见到你！"}]
        elif intent == "question":
            # 查找相关的问答历史
            for msg in messages[-5:]:
                if msg.get("role") == "assistant" and "问题" in msg.get("content", ""):
                    relevant_context.append(msg)
        
        return {
            **state,
            "retrieved_context": relevant_context
        }
    
    def generate_response(state):
        """生成回复"""
        print_step("生成回复")
        current_input = state.get("current_input", "")
        intent = state.get("intent", "")
        context = state.get("retrieved_context", [])
        
        # 使用LLM生成回复
        llm = get_llm()
        
        prompt = f"""
你是一个智能助手。请根据以下信息生成合适的回复：

用户输入: {current_input}
识别意图: {intent}
相关上下文: {context}

请生成一个友好、有帮助的回复：
"""
        
        try:
            response = llm.invoke(prompt)
            generated_response = response.content
        except Exception as e:
            generated_response = f"抱歉，我暂时无法处理您的请求。错误：{str(e)}"
        
        return {
            **state,
            "response": generated_response
        }
    
    def refine_response(state):
        """完善回复"""
        print_step("完善回复")
        response = state.get("response", "")
        intent = state.get("intent", "")
        
        # 根据意图调整回复风格
        if intent == "greeting":
            refined_response = response + " 😊"
        elif intent == "farewell":
            refined_response = response + " 期待下次再见！"
        else:
            refined_response = response
        
        return {
            **state,
            "response": refined_response
        }
    
    def update_context(state):
        """更新上下文"""
        print_step("更新上下文")
        current_input = state.get("current_input", "")
        response = state.get("response", "")
        messages = state.get("messages", [])
        
        # 添加新消息到历史
        new_messages = messages + [
            {"role": "user", "content": current_input, "timestamp": "now"},
            {"role": "assistant", "content": response, "timestamp": "now"}
        ]
        
        return {
            **state,
            "messages": new_messages,
            "context": {**state.get("context", {}), "last_intent": state.get("intent", "")}
        }
    
    def should_retrieve_context(state):
        """条件：是否需要检索上下文"""
        intent = state.get("intent", "")
        return "context_retrieval" if intent in ["question", "greeting"] else "response_generation"
    
    def is_validation_passed(state):
        """验证是否通过"""
        validation_result = state.get("validation_result", {})
        return "data_preprocessing" if validation_result.get("valid", True) else "notification"
    
    def has_business_result(state):
        """是否有业务结果"""
        processed_data = state.get("processed_data", {})
        return "quality_check" if processed_data else "notification"
    
    def quality_passed(state):
        """质量检查是否通过"""
        quality_result = state.get("quality_result", {})
        return "result_formatting" if quality_result.get("score", 0) >= 0.8 else "notification"
    
    def business_failed(state):
        """业务逻辑失败"""
        workflow_status = state.get("workflow_status", "")
        return "notification" if "failed" in workflow_status else None
    
    def quality_failed(state):
        """质量检查失败"""
        quality_result = state.get("quality_result", {})
        return "notification" if quality_result.get("score", 0) < 0.8 else None
    
    def is_validation_failed(state):
        """验证是否失败"""
        validation_result = state.get("validation_result", {})
        return "notification" if not validation_result.get("valid", True) else None
    
    # 注册所有函数
    manager.engine.register_function("template_apps.bot_nodes.analyze_input", analyze_input)
    manager.engine.register_function("template_apps.bot_nodes.recognize_intent", recognize_intent)
    manager.engine.register_function("template_apps.bot_nodes.retrieve_context", retrieve_context)
    manager.engine.register_function("template_apps.bot_nodes.generate_response", generate_response)
    manager.engine.register_function("template_apps.bot_nodes.refine_response", refine_response)
    manager.engine.register_function("template_apps.bot_nodes.update_context", update_context)
    
    # 注册条件函数
    manager.engine.register_function("template_apps.bot_conditions.should_retrieve_context", should_retrieve_context)
    manager.engine.register_function("template_apps.workflow_conditions.is_validation_passed", is_validation_passed)
    manager.engine.register_function("template_apps.workflow_conditions.has_business_result", has_business_result)
    manager.engine.register_function("template_apps.workflow_conditions.quality_passed", quality_passed)
    manager.engine.register_function("template_apps.workflow_conditions.business_failed", business_failed)
    manager.engine.register_function("template_apps.workflow_conditions.quality_failed", quality_failed)
    manager.engine.register_function("template_apps.workflow_conditions.is_validation_failed", is_validation_failed)


def register_workflow_functions(manager: TemplateManager):
    """注册工作流相关函数"""
    
    def validate_data(state):
        """验证数据"""
        print_step("验证数据")
        input_data = state.get("input_data", {})
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 检查必需字段
        required_fields = ["id", "type"]
        for field in required_fields:
            if field not in input_data:
                validation_result["valid"] = False
                validation_result["errors"].append(f"缺少必需字段: {field}")
        
        return {
            **state,
            "validation_result": validation_result
        }
    
    def preprocess_data(state):
        """预处理数据"""
        print_step("预处理数据")
        input_data = state.get("input_data", {})
        
        processed_data = {}
        for key, value in input_data.items():
            # 简单的预处理
            if isinstance(value, str):
                processed_data[key] = value.strip()
            else:
                processed_data[key] = value
        
        return {
            **state,
            "processed_data": processed_data,
            "workflow_status": "preprocessed"
        }
    
    def execute_business_logic(state):
        """执行业务逻辑"""
        print_step("执行业务逻辑")
        processed_data = state.get("processed_data", {})
        
        # 模拟业务处理
        business_result = {
            "processed_id": f"PROC_{processed_data.get('id', 'UNKNOWN')}",
            "processed_type": processed_data.get("type", "unknown"),
            "processing_time": "now",
            "status": "completed"
        }
        
        return {
            **state,
            "business_result": business_result,
            "workflow_status": "business_completed"
        }
    
    def quality_check(state):
        """质量检查"""
        print_step("质量检查")
        business_result = state.get("business_result", {})
        
        # 模拟质量检查
        quality_score = 0.9 if business_result.get("status") == "completed" else 0.6
        
        quality_result = {
            "score": quality_score,
            "passed": quality_score >= 0.8,
            "checks": ["data_integrity", "business_logic", "performance"]
        }
        
        return {
            **state,
            "quality_result": quality_result
        }
    
    def format_results(state):
        """格式化结果"""
        print_step("格式化结果")
        business_result = state.get("business_result", {})
        quality_result = state.get("quality_result", {})
        
        formatted_result = {
            "success": True,
            "data": business_result,
            "quality": quality_result,
            "timestamp": "now"
        }
        
        return {
            **state,
            "formatted_result": formatted_result,
            "workflow_status": "completed"
        }
    
    def send_notification(state):
        """发送通知"""
        print_step("发送通知")
        workflow_status = state.get("workflow_status", "")
        formatted_result = state.get("formatted_result", {})
        validation_result = state.get("validation_result", {})
        
        notification = {
            "type": "email",
            "status": workflow_status,
            "recipient": "admin@example.com",
            "content": f"工作流{workflow_status}完成"
        }
        
        if not validation_result.get("valid", True):
            notification["content"] = "工作流验证失败"
        
        return {
            **state,
            "notification_sent": notification
        }
    
    # 注册函数
    manager.engine.register_function("template_apps.workflow_nodes.validate_data", validate_data)
    manager.engine.register_function("template_apps.workflow_nodes.preprocess_data", preprocess_data)
    manager.engine.register_function("template_apps.workflow_nodes.execute_business_logic", execute_business_logic)
    manager.engine.register_function("template_apps.workflow_nodes.quality_check", quality_check)
    manager.engine.register_function("template_apps.workflow_nodes.format_results", format_results)
    manager.engine.register_function("template_apps.workflow_nodes.send_notification", send_notification)


def demo_chatbot_template():
    """演示聊天机器人模板"""
    print("🤖 演示聊天机器人模板")
    print("=" * 60)
    
    # 创建模板管理器
    manager = TemplateManager()
    
    # 注册函数
    register_bot_functions(manager)
    
    # 加载模板
    template_path = os.path.join(os.path.dirname(__file__), "chatbot_template.yaml")
    template_name = manager.load_template_from_file(template_path)
    
    # 构建工作流
    workflow = manager.build_workflow(template_name)
    
    # 测试对话
    test_inputs = [
        "你好，我想了解一下LangGraph",
        "LangGraph有什么优势？",
        "谢谢你的介绍！"
    ]
    
    for user_input in test_inputs:
        print(f"\n👤 用户: {user_input}")
        
        # 初始状态
        initial_state = {
            "messages": [],
            "current_input": user_input,
            "intent": "unknown",
            "response": "",
            "user_profile": {},
            "context": {}
        }
        
        # 运行工作流
        config = {"configurable": {"thread_id": "demo_chat"}}
        result = workflow.invoke(initial_state, config=config)
        
        response = result.get("response", "")
        intent = result.get("intent", "")
        
        print(f"🤖 助手: {response}")
        print(f"🎯 意图: {intent}")


def demo_workflow_template():
    """演示工作流模板"""
    print("\n📋 演示工作流模板")
    print("=" * 60)
    
    # 创建模板管理器
    manager = TemplateManager()
    
    # 注册函数
    register_workflow_functions(manager)
    
    # 加载模板
    template_path = os.path.join(os.path.dirname(__file__), "workflow_template.yaml")
    template_name = manager.load_template_from_file(template_path)
    
    # 构建工作流
    workflow = manager.build_workflow(template_name)
    
    # 测试数据
    test_data = {
        "id": "test_001",
        "type": "order",
        "content": "这是一个测试订单"
    }
    
    print(f"📥 输入数据: {test_data}")
    
    # 初始状态
    initial_state = {
        "input_data": test_data,
        "processed_data": {},
        "validation_result": {},
        "workflow_status": "initialized",
        "errors": [],
        "metadata": {}
    }
    
    # 运行工作流
    config = {"configurable": {"thread_id": "demo_workflow"}}
    result = workflow.invoke(initial_state, config=config)
    
    print(f"📤 工作流状态: {result.get('workflow_status', '')}")
    formatted_result = result.get("formatted_result", {})
    print(f"📊 格式化结果: {formatted_result}")
    
    notification = result.get("notification_sent", {})
    if notification:
        print(f"📧 通知已发送: {notification.get('content', '')}")


if __name__ == "__main__":
    print("🚀 LangGraph 模板应用演示")
    print("=" * 60)
    
    try:
        # 演示聊天机器人模板
        demo_chatbot_template()
        
        # 演示工作流模板
        demo_workflow_template()
        
        print("\n✅ 所有演示完成！")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()