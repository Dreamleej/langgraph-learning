# 📝 模板应用框架

## 📋 概述

本模块提供了一个可配置、可扩展的LangGraph应用模板框架，让开发者能够快速构建和部署AI工作流应用。

## 🎯 核心特性

### 🔧 模板引擎
- **YAML配置**: 使用YAML文件定义工作流模板
- **动态加载**: 运行时加载和构建工作流
- **函数注册**: 支持动态函数注册和调用
- **条件路由**: 基于条件的智能路由

### 🏗️ 组件系统
- **节点模板**: 可重用的处理节点
- **边模板**: 灵活的数据流连接
- **状态模式**: 动态状态类型定义
- **检查点**: 支持状态持久化

### 🎨 开发体验
- **热重载**: 模板变更即时生效
- **类型安全**: 强类型状态定义
- **错误处理**: 完善的异常处理机制
- **调试支持**: 详细的执行日志

## 🚀 快速开始

### 1. 基础使用

```python
from template_apps.template_engine import TemplateManager

# 创建模板管理器
manager = TemplateManager()

# 加载模板
template_name = manager.load_template_from_file("chatbot_template.yaml")

# 构建工作流
workflow = manager.build_workflow(template_name)

# 运行工作流
result = workflow.invoke(initial_state)
```

### 2. 自定义函数

```python
def my_processing_function(state):
    """自定义处理函数"""
    input_data = state.get("input_data")
    
    # 处理逻辑
    processed_data = process(input_data)
    
    return {"processed_data": processed_data}

# 注册函数
manager.engine.register_function("my_function", my_processing_function)
```

### 3. 模板配置

```yaml
name: "my_template"
description: "我的自定义模板"

state_schema:
  input_data:
    type: "dict"
  processed_data:
    type: "dict"
    default: {}

nodes:
  - name: "process_data"
    function_path: "my_function"
    parameters:
      param1: "value1"

edges:
  - from: START
    to: "process_data"
  - from: "process_data"
    to: END
```

## 📁 文件结构

```
template_apps/
├── template_engine.py    # 核心模板引擎
├── demo.py              # 使用演示
├── chatbot_template.yaml # 聊天机器人模板
├── workflow_template.yaml # 通用工作流模板
├── __init__.py
└── README.md
```

## 🔧 核心组件

### TemplateEngine

模板引擎的核心类，负责：
- 解析YAML模板文件
- 构建LangGraph工作流
- 管理函数注册

```python
class YamlTemplateEngine(TemplateEngine):
    def load_template(self, template_path: str) -> WorkflowTemplate
    def build_workflow(self, template: WorkflowTemplate) -> StateGraph
    def validate_template(self, template: WorkflowTemplate) -> bool
```

### TemplateManager

模板管理器，提供高级API：

```python
manager = TemplateManager()

# 加载模板
template_name = manager.load_template_from_file("template.yaml")

# 构建工作流
workflow = manager.build_workflow(template_name)

# 获取模板信息
info = manager.get_template_info(template_name)
```

### 模板配置结构

#### WorkflowTemplate
```python
@dataclass
class WorkflowTemplate:
    name: str                    # 模板名称
    description: str             # 模板描述
    state_schema: Dict[str, Any] # 状态模式定义
    nodes: List[NodeTemplate]    # 节点列表
    edges: List[EdgeTemplate]    # 边列表
    checkpoint_config: Dict      # 检查点配置
    entry_point: Optional[str]   # 入口点
    exit_points: List[str]       # 出口点
```

#### NodeTemplate
```python
@dataclass
class NodeTemplate:
    name: str                     # 节点名称
    description: str              # 节点描述
    function_path: str            # 函数路径
    parameters: Dict[str, Any]    # 参数配置
    conditions: Dict[str, Any]    # 条件配置
    retry_config: Dict[str, Any]  # 重试配置
```

## 🎨 使用示例

### 示例1: 聊天机器人模板

```yaml
name: "chatbot"
description: "智能聊天机器人"

state_schema:
  messages:
    type: "list"
  current_input:
    type: "str"
  intent:
    type: "str"
  response:
    type: "str"

nodes:
  - name: "analyze_input"
    function_path: "bot_nodes.analyze_input"
  - name: "generate_response"
    function_path: "bot_nodes.generate_response"

edges:
  - from: START
    to: "analyze_input"
  - from: "analyze_input"
    to: "generate_response"
  - from: "generate_response"
    to: END
```

### 示例2: 业务流程模板

```yaml
name: "business_workflow"
description: "业务处理流程"

state_schema:
  input_data:
    type: "dict"
  validation_result:
    type: "dict"
  processed_data:
    type: "dict"

nodes:
  - name: "validate"
    function_path: "workflow.validate_data"
  - name: "process"
    function_path: "workflow.process_data"

edges:
  - from: START
    to: "validate"
  - from: "validate"
    to: "process"
    condition: "conditions.is_valid"
  - from: "process"
    to: END
```

## 🔌 高级功能

### 条件路由

```yaml
edges:
  - from: "decision_node"
    to: "option_a"
    condition: "conditions.choose_option_a"
  - from: "decision_node"
    to: "option_b"
    condition: "conditions.choose_option_b"
```

### 重试配置

```yaml
nodes:
  - name: "unreliable_node"
    function_path: "nodes.process_data"
    retry_config:
      max_retries: 3
      delay: 1.0
      backoff: "exponential"
```

### 检查点配置

```yaml
checkpoint_config:
  enabled: true
  persist_history: true
  checkpoint_interval: 10
```

## 🎯 最佳实践

### 1. 模板设计
- 保持模板简洁和模块化
- 使用描述性的节点和边名称
- 合理设计状态模式

### 2. 函数开发
- 函数接收state参数并返回字典
- 处理异常情况
- 添加适当的日志

### 3. 配置管理
- 使用参数化配置
- 避免硬编码值
- 支持环境变量

### 4. 测试策略
- 为每个模板编写单元测试
- 测试边界条件
- 验证错误处理

## 🚀 部署建议

### 开发环境
```bash
cd 06-cutting-edge/template_apps
python demo.py
```

### 生产部署
```python
from template_apps.template_engine import TemplateManager

# 初始化
manager = TemplateManager()
manager.load_template_from_file("production_template.yaml")

# 构建应用
app = manager.build_workflow("production_template")

# 部署服务
deploy_app(app)
```

## 📊 性能优化

### 函数缓存
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(param):
    # 计算密集型操作
    return result
```

### 并行处理
```python
async def parallel_processing(state):
    tasks = []
    for item in state.get("items", []):
        tasks.append(process_item(item))
    
    results = await asyncio.gather(*tasks)
    return {"processed_items": results}
```

## 🔍 调试技巧

### 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 状态检查点
```python
# 在关键节点保存状态
def checkpoint_node(state):
    print(f"Checkpoint state: {state}")
    return state
```

### 错误追踪
```python
def error_handling_node(state):
    try:
        return process_data(state)
    except Exception as e:
        logger.error(f"Processing error: {e}")
        return {"error": str(e), "status": "failed"}
```

## 🎉 总结

模板应用框架提供了：

✅ **快速开发**: 通过配置快速构建应用  
✅ **代码复用**: 可重用的模板和组件  
✅ **灵活配置**: 支持复杂的业务逻辑  
✅ **易于维护**: 清晰的结构和良好的文档  
✅ **生产就绪**: 完善的错误处理和监控  

这让LangGraph应用开发变得更加高效和标准化！