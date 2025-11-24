# 🔍 LangSmith集成

## 📋 概述

本模块展示如何将LangSmith集成到LangGraph应用中，实现全面的监控、追踪和分析功能。

## 🎯 核心功能

### 🔧 监控与追踪
- **实时监控**: 追踪所有LangGraph执行
- **性能分析**: 详细的时间分析和瓶颈识别
- **错误追踪**: 完整的异常处理和错误报告
- **可视化仪表板**: 实时性能指标展示

### 📊 评估与优化
- **自动评估**: 基于预设指标的自动评估
- **A/B测试**: 对比不同配置的性能
- **趋势分析**: 长期性能趋势监控
- **质量监控**: 输出质量持续监控

### 🔄 集成特性
- **无缝集成**: 最小化代码变更
- **回调处理**: 自定义回调逻辑
- **数据持久化**: 执行数据持久化存储
- **API访问**: 完整的API访问能力

## 🚀 快速开始

### 1. 环境配置

```bash
# 设置环境变量
export LANGSMITH_API_KEY="your-api-key"
export LANGSMITH_PROJECT="your-project-name"
export LANGSMITH_ENABLED="true"
```

### 2. 基础集成

```python
from langsmith_integration.monitoring_example import LangSmithConfig, monitored_llm_call

# 创建配置
config = LangSmithConfig()

# 使用可追踪函数
result = monitored_llm_call("你的问题", {"context": "相关上下文"})
```

### 3. 启动监控仪表板

```bash
cd 06-cutting-edge/langsmith_integration
python dashboard.py
```

访问 http://localhost:8001 查看监控仪表板。

## 📁 文件结构

```
langsmith_integration/
├── monitoring_example.py  # 基础监控示例
├── dashboard.py          # 监控仪表板
├── __init__.py
└── README.md
```

## 🔧 核心组件

### LangSmithConfig

配置管理类，处理LangSmith相关配置：

```python
config = LangSmithConfig()

print(f"API Key: {config.api_key}")
print(f"Project: {config.project_name}")
print(f"Enabled: {config.enabled}")
```

### @traceable装饰器

用于标记需要追踪的函数：

```python
@traceable
def my_function(input_data):
    # 函数逻辑
    return result
```

### LangSmithCallbackHandler

自定义回调处理器：

```python
handler = LangSmithCallbackHandler("my-project")

# 在LLM调用中使用
llm.invoke(prompt, callbacks=[handler])
```

### PerformanceMonitor

性能监控器，收集和分析性能数据：

```python
monitor = PerformanceMonitor()

# 记录请求
monitor.record_request(success=True, response_time=1.5)

# 获取指标
metrics = monitor.get_metrics()
```

## 🎨 使用示例

### 示例1: 基础监控

```python
from langsmith_integration.monitoring_example import create_monitored_workflow

# 创建被监控的工作流
config = LangSmithConfig()
workflow = create_monitored_workflow(config)

# 运行工作流（自动追踪）
result = workflow.invoke(initial_state)
```

### 示例2: 自定义追踪

```python
from langsmith import traceable

@traceable(name="custom_processor")
def custom_processing(data):
    # 自定义处理逻辑
    return processed_data

# 自动被LangSmith追踪
result = custom_processing(input_data)
```

### 示例3: 评估配置

```python
from langsmith.evaluation import evaluate

def evaluator(run, example):
    # 自定义评估逻辑
    output = run.outputs.get("output")
    expected = example.outputs.get("expected")
    
    # 计算相似度等指标
    return {"score": similarity_score}

# 运行评估
results = evaluate(
    my_dataset,
    my_llm,
    evaluator=evaluator,
    experiment_prefix="my-evaluation"
)
```

## 📊 监控仪表板

### 实时指标

- **总请求数**: 处理的请求总数
- **成功率**: 请求成功百分比
- **平均响应时间**: 所有请求的平均处理时间
- **错误率**: 请求失败百分比

### 可视化图表

- **响应时间趋势**: 响应时间变化图表
- **成功率趋势**: 成功率变化图表
- **错误分布**: 错误类型分布图
- **吞吐量分析**: 处理能力分析图

### 功能特性

- **实时更新**: WebSocket实时数据推送
- **交互式图表**: Chart.js交互式图表
- **响应式设计**: 适配各种屏幕尺寸
- **数据导出**: 支持数据导出功能

## 🔌 高级功能

### 自定义指标

```python
class CustomMetrics:
    def calculate_metrics(self, state):
        # 自定义指标计算
        return {
            "custom_score": self.calculate_score(state),
            "efficiency": self.calculate_efficiency(state)
        }

# 在工作流中使用
def metrics_node(state):
    metrics = CustomMetrics()
    return {"performance": metrics.calculate_metrics(state)}
```

### 错误追踪

```python
@traceable
def error_prone_function(input_data):
    try:
        # 可能出错的操作
        result = risky_operation(input_data)
        return {"success": True, "data": result}
    
    except Exception as e:
        # 自动追踪错误
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
```

### 性能优化

```python
@traceable
def optimized_processing(data):
    start_time = time.time()
    
    # 执行处理
    result = process_data(data)
    
    end_time = time.time()
    
    # 记录性能指标
    return {
        "result": result,
        "processing_time": end_time - start_time,
        "data_size": len(str(data))
    }
```

## 🎯 最佳实践

### 1. 配置管理

```python
# 使用环境变量管理配置
LANGSMITH_API_KEY=your-key
LANGSMITH_PROJECT=your-project
LANGSMITH_ENABLED=true
```

### 2. 错误处理

```python
@traceable
def robust_function(input_data):
    try:
        return process_input(input_data)
    except Exception as e:
        # 记录错误上下文
        logger.error(f"处理失败: {e}", extra={"input": input_data})
        raise
```

### 3. 性能监控

```python
@traceable
def performance_aware_function(data):
    with performance_monitor.timer("function_execution"):
        # 执行操作
        return expensive_operation(data)
```

### 4. 数据安全

```python
@traceable
def secure_function(sensitive_data):
    # 脱敏处理
    sanitized_data = sanitize_input(sensitive_data)
    
    # 处理脱敏后的数据
    result = process_sanitized_data(sanitized_data)
    
    return result
```

## 📈 监控指标

### 基础指标
- **请求数量**: 总请求数、成功请求数、失败请求数
- **响应时间**: 平均响应时间、最大/最小响应时间
- **成功率**: 请求成功百分比
- **吞吐量**: 每秒处理的请求数

### 质量指标
- **相关性**: 输出与输入的相关性
- **一致性**: 多次执行的一致性
- **准确性**: 输出准确性评分
- **满意度**: 用户满意度指标

### 业务指标
- **转化率**: 业务转化成功率
- **留存率**: 用户留存率
- **活跃度**: 系统活跃度指标
- **成本效益**: 成本效益分析

## 🔍 故障排查

### 常见问题

1. **连接问题**
   ```bash
   # 检查API密钥
   echo $LANGSMITH_API_KEY
   
   # 测试连接
   python -c "from langsmith import Client; print('Connected')"
   ```

2. **性能问题**
   ```python
   # 启用详细日志
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **数据问题**
   ```python
   # 验证数据格式
   def validate_data(data):
       assert isinstance(data, dict)
       assert "input" in data
       return True
   ```

### 调试技巧

```python
# 启用调试模式
import os
os.environ["LANGSMITH_TRACING"] = "true"

# 添加调试信息
@traceable
def debug_function(data):
    print(f"Debug: Input data = {data}")
    result = process_data(data)
    print(f"Debug: Output result = {result}")
    return result
```

## 🚀 部署建议

### 生产环境配置

```python
# 生产环境配置
PROD_CONFIG = {
    "langsmith": {
        "enabled": True,
        "project": "production-app",
        "sample_rate": 0.1,  # 10%采样率
        "tracing": "full"
    }
}
```

### 监控告警

```python
# 设置告警阈值
ALERT_THRESHOLDS = {
    "response_time": 2.0,  # 2秒
    "error_rate": 0.05,    # 5%
    "success_rate": 0.95   # 95%
}
```

### 扩展性考虑

```python
# 分布式追踪
from langsmith.tracing import DistributedTracer

tracer = DistributedTracer(service_name="my-app")

@tracer.trace
def distributed_function(data):
    # 跨服务追踪
    return process_with_other_services(data)
```

## 🎉 总结

LangSmith集成提供了：

✅ **全面监控**: 完整的执行追踪和性能分析  
✅ **实时仪表板**: 直观的可视化监控界面  
✅ **自动化评估**: 智能的质量评估系统  
✅ **故障诊断**: 快速定位和解决问题  
✅ **生产就绪**: 企业级的监控和追踪解决方案  

这为LangGraph应用提供了完整的可观测性能力！