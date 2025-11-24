#!/usr/bin/env python3
"""
模板应用引擎
提供可配置、可扩展的LangGraph应用模板
"""

import json
import yaml
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import importlib
import inspect
from pathlib import Path

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict


@dataclass
class NodeTemplate:
    """节点模板配置"""
    name: str
    description: str
    function_path: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    conditions: Dict[str, Any] = field(default_factory=dict)
    retry_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EdgeTemplate:
    """边模板配置"""
    from_node: str
    to_node: str
    condition: Optional[str] = None
    weight: float = 1.0


@dataclass
class WorkflowTemplate:
    """工作流模板配置"""
    name: str
    description: str
    state_schema: Dict[str, Any]
    nodes: List[NodeTemplate]
    edges: List[EdgeTemplate]
    checkpoint_config: Dict[str, Any] = field(default_factory=dict)
    entry_point: Optional[str] = None
    exit_points: List[str] = field(default_factory=list)


class TemplateEngine(ABC):
    """模板引擎抽象基类"""
    
    @abstractmethod
    def load_template(self, template_path: str) -> WorkflowTemplate:
        """加载模板"""
        pass
    
    @abstractmethod
    def build_workflow(self, template: WorkflowTemplate) -> StateGraph:
        """构建工作流"""
        pass
    
    @abstractmethod
    def validate_template(self, template: WorkflowTemplate) -> bool:
        """验证模板"""
        pass


class YamlTemplateEngine(TemplateEngine):
    """YAML模板引擎"""
    
    def __init__(self):
        self.function_registry = {}
    
    def register_function(self, name: str, func: Callable):
        """注册函数"""
        self.function_registry[name] = func
    
    def load_template(self, template_path: str) -> WorkflowTemplate:
        """从YAML文件加载模板"""
        with open(template_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return self._parse_template_data(data)
    
    def _parse_template_data(self, data: Dict[str, Any]) -> WorkflowTemplate:
        """解析模板数据"""
        # 解析节点
        nodes = []
        for node_data in data.get('nodes', []):
            node = NodeTemplate(
                name=node_data['name'],
                description=node_data.get('description', ''),
                function_path=node_data['function_path'],
                parameters=node_data.get('parameters', {}),
                conditions=node_data.get('conditions', {}),
                retry_config=node_data.get('retry_config', {})
            )
            nodes.append(node)
        
        # 解析边
        edges = []
        for edge_data in data.get('edges', []):
            edge = EdgeTemplate(
                from_node=edge_data['from'],
                to_node=edge_data['to'],
                condition=edge_data.get('condition'),
                weight=edge_data.get('weight', 1.0)
            )
            edges.append(edge)
        
        return WorkflowTemplate(
            name=data['name'],
            description=data.get('description', ''),
            state_schema=data.get('state_schema', {}),
            nodes=nodes,
            edges=edges,
            checkpoint_config=data.get('checkpoint_config', {}),
            entry_point=data.get('entry_point'),
            exit_points=data.get('exit_points', [])
        )
    
    def build_workflow(self, template: WorkflowTemplate) -> StateGraph:
        """从模板构建工作流"""
        print_step(f"构建工作流: {template.name}")
        
        # 创建动态状态类型
        StateType = self._create_state_type(template.state_schema)
        
        # 创建工作流
        workflow = StateGraph(StateType)
        
        # 加载并注册节点函数
        for node_template in template.nodes:
            func = self._load_function(node_template.function_path)
            
            # 创建包装函数处理参数
            wrapped_func = self._wrap_function(func, node_template)
            
            workflow.add_node(node_template.name, wrapped_func)
        
        # 添加边
        for edge_template in template.edges:
            if edge_template.condition:
                # 条件边
                condition_func = self._load_condition(edge_template.condition)
                workflow.add_conditional_edges(
                    edge_template.from_node,
                    condition_func,
                    {edge_template.to_node: edge_template.to_node, END: END}
                )
            else:
                # 普通边
                workflow.add_edge(edge_template.from_node, edge_template.to_node)
        
        # 设置入口点
        entry_point = template.entry_point or template.nodes[0].name
        workflow.set_entry_point(entry_point)
        
        # 设置出口点
        for exit_point in template.exit_points:
            workflow.add_edge(exit_point, END)
        
        # 配置检查点
        if template.checkpoint_config.get('enabled', True):
            memory = MemorySaver()
            return workflow.compile(checkpointer=memory)
        
        return workflow.compile()
    
    def _create_state_type(self, schema: Dict[str, Any]):
        """创建动态状态类型"""
        fields = {}
        
        for field_name, field_config in schema.items():
            if isinstance(field_config, dict):
                field_type = field_config.get('type', 'str')
                default_value = field_config.get('default')
                
                # 简单类型映射
                type_mapping = {
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict
                }
                
                python_type = type_mapping.get(field_type, str)
                if default_value is not None:
                    fields[field_name] = (python_type, default_value)
                else:
                    fields[field_name] = python_type
            else:
                fields[field_name] = str
        
        return TypedDict(f"DynamicState", fields)
    
    def _load_function(self, function_path: str) -> Callable:
        """动态加载函数"""
        if function_path in self.function_registry:
            return self.function_registry[function_path]
        
        # 支持模块路径和函数名
        try:
            module_path, func_name = function_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            
            self.function_registry[function_path] = func
            return func
        except (ImportError, AttributeError) as e:
            raise ValueError(f"无法加载函数 {function_path}: {e}")
    
    def _load_condition(self, condition_path: str) -> Callable:
        """加载条件函数"""
        return self._load_function(condition_path)
    
    def _wrap_function(self, func: Callable, node_template: NodeTemplate) -> Callable:
        """包装函数以处理参数和重试"""
        def wrapped_function(state):
            try:
                # 合并参数
                params = {
                    **node_template.parameters,
                    **{k: v for k, v in state.items() if k in inspect.signature(func).parameters}
                }
                
                # 调用原函数
                result = func(**params)
                
                # 如果返回结果是字典，更新状态
                if isinstance(result, dict):
                    return {**state, **result}
                else:
                    # 如果是其他类型，包装成字典
                    return {**state, f"{node_template.name}_result": result}
                
            except Exception as e:
                print(f"节点 {node_template.name} 执行失败: {e}")
                
                # 重试逻辑
                retry_count = node_template.retry_config.get('max_retries', 0)
                if retry_count > 0:
                    # 这里可以实现更复杂的重试逻辑
                    pass
                
                # 返回错误状态
                return {
                    **state,
                    f"{node_template.name}_error": str(e),
                    f"{node_template.name}_status": "failed"
                }
        
        return wrapped_function
    
    def validate_template(self, template: WorkflowTemplate) -> bool:
        """验证模板配置"""
        try:
            # 检查必需字段
            if not template.name or not template.nodes:
                return False
            
            # 检查节点函数是否存在
            for node in template.nodes:
                self._load_function(node.function_path)
            
            # 检查边引用的节点是否存在
            node_names = {node.name for node in template.nodes}
            for edge in template.edges:
                if edge.from_node not in node_names or edge.to_node not in node_names:
                    return False
            
            return True
        except Exception:
            return False


class TemplateManager:
    """模板管理器"""
    
    def __init__(self):
        self.engine = YamlTemplateEngine()
        self.templates = {}
    
    def load_template_from_file(self, template_path: str, name: str = None) -> str:
        """从文件加载模板"""
        template = self.engine.load_template(template_path)
        
        if not self.engine.validate_template(template):
            raise ValueError(f"模板验证失败: {template_path}")
        
        template_name = name or template.name
        self.templates[template_name] = template
        
        print_step(f"成功加载模板: {template_name}")
        return template_name
    
    def build_workflow(self, template_name: str) -> StateGraph:
        """构建工作流"""
        if template_name not in self.templates:
            raise ValueError(f"模板不存在: {template_name}")
        
        template = self.templates[template_name]
        return self.engine.build_workflow(template)
    
    def list_templates(self) -> List[str]:
        """列出所有模板"""
        return list(self.templates.keys())
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """获取模板信息"""
        if template_name not in self.templates:
            raise ValueError(f"模板不存在: {template_name}")
        
        template = self.templates[template_name]
        return {
            "name": template.name,
            "description": template.description,
            "node_count": len(template.nodes),
            "edge_count": len(template.edges),
            "entry_point": template.entry_point,
            "exit_points": template.exit_points
        }


def print_step(step: str):
    """打印步骤信息"""
    print(f"🔧 {step}")
    print("-" * 50)


# 预定义的常用函数
def simple_llm_call(prompt: str, **kwargs) -> Dict[str, Any]:
    """简单的LLM调用"""
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
    from config import get_llm
    
    llm = get_llm()
    response = llm.invoke(prompt)
    
    return {
        "llm_response": response.content,
        "prompt_used": prompt
    }


def text_processing(text: str, operation: str = "clean") -> Dict[str, Any]:
    """文本处理"""
    if operation == "clean":
        cleaned_text = text.strip().lower()
        return {"processed_text": cleaned_text}
    elif operation == "count":
        word_count = len(text.split())
        return {"word_count": word_count, "char_count": len(text)}
    elif operation == "extract_keywords":
        # 简单的关键词提取
        words = text.lower().split()
        keywords = list(set([word for word in words if len(word) > 3]))
        return {"keywords": keywords[:10]}  # 返回前10个关键词
    else:
        return {"original_text": text}


def decision_logic(condition_field: str, threshold: float = 0.5) -> str:
    """决策逻辑"""
    # 这里应该从状态中获取condition_field的值
    # 为了演示，我们返回一个简单的决策
    import random
    score = random.random()
    
    if score > threshold:
        return "approved"
    else:
        return "rejected"


if __name__ == "__main__":
    # 注册预定义函数
    manager = TemplateManager()
    manager.engine.register_function("simple_llm_call", simple_llm_call)
    manager.engine.register_function("text_processing", text_processing)
    manager.engine.register_function("decision_logic", decision_logic)
    
    print("🚀 模板应用引擎已准备就绪")
    print(f"📋 可用函数: {list(manager.engine.function_registry.keys())}")
    print("🔧 使用 manager.load_template_from_file() 来加载模板")