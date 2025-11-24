"""
03-advanced: 自定义工具和集成

本示例展示如何在LangGraph中开发和集成自定义工具，
包括API集成、数据库连接、文件处理和外部服务调用。

学习要点：
1. 工具设计和实现
2. API集成
3. 数据库连接
4. 外部服务调用
"""

from typing import TypedDict, List, Dict, Any, Optional, Callable
from langgraph.graph import StateGraph, END
import sys
import os
import json
import time
import requests
import sqlite3
import csv
from datetime import datetime
import hashlib
import base64
from abc import ABC, abstractmethod

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import print_step, print_result, print_error, Config

# 1. 状态定义
class ToolState(TypedDict):
    """
    工具工作流状态
    """
    task_type: str
    input_data: Dict[str, Any]
    tool_results: Dict[str, Any]
    api_responses: List[Dict[str, Any]]
    database_results: List[Dict[str, Any]]
    file_results: List[Dict[str, Any]]
    combined_output: Dict[str, Any]
    tool_execution_log: List[Dict[str, Any]]
    error_log: List[Dict[str, Any]]

class ToolConfig(TypedDict):
    """
    工具配置
    """
    name: str
    description: str
    parameters: Dict[str, Any]
    enabled: bool
    timeout: int

# 2. 基础工具抽象类

class BaseTool(ABC):
    """
    基础工具抽象类
    """
    
    def __init__(self, name: str, description: str, config: Dict[str, Any] = None):
        self.name = name
        self.description = description
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.timeout = self.config.get("timeout", 30)
        self.execution_count = 0
        self.last_execution = None
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        pass
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        return True
    
    def log_execution(self, input_data: Dict[str, Any], output_data: Dict[str, Any], 
                      execution_time: float, success: bool):
        """记录执行日志"""
        self.execution_count += 1
        self.last_execution = datetime.now().isoformat()
        
        log_entry = {
            "tool_name": self.name,
            "timestamp": self.last_execution,
            "execution_time": execution_time,
            "success": success,
            "input_size": len(str(input_data)),
            "output_size": len(str(output_data)) if success else 0
        }
        
        return log_entry
    
    def get_stats(self) -> Dict[str, Any]:
        """获取工具统计信息"""
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "execution_count": self.execution_count,
            "last_execution": self.last_execution,
            "timeout": self.timeout
        }

# 3. 具体工具实现

class WeatherAPITool(BaseTool):
    """
    天气API工具
    """
    
    def __init__(self):
        super().__init__(
            name="weather_api",
            description="获取天气信息",
            config={"timeout": 10, "api_key": "demo_key"}
        )
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取天气信息"""
        if not self.validate_input(input_data):
            raise ValueError("输入数据无效")
        
        start_time = time.time()
        
        try:
            city = input_data.get("city", "Beijing")
            
            # 模拟API调用（实际项目中调用真实API）
            # 这里使用模拟数据
            mock_weather_data = {
                "city": city,
                "temperature": random.randint(-10, 35),
                "humidity": random.randint(30, 90),
                "weather": random.choice(["晴", "多云", "雨", "雪"]),
                "wind_speed": random.uniform(0, 20),
                "timestamp": datetime.now().isoformat()
            }
            
            # 模拟网络延迟
            time.sleep(random.uniform(0.5, 2.0))
            
            execution_time = time.time() - start_time
            success = True
            
            log_entry = self.log_execution(input_data, mock_weather_data, execution_time, success)
            
            return {
                "status": "success",
                "data": mock_weather_data,
                "source": "weather_api",
                "execution_log": log_entry
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = {
                "status": "error",
                "error": str(e),
                "source": "weather_api"
            }
            
            log_entry = self.log_execution(input_data, error_result, execution_time, False)
            error_result["execution_log"] = log_entry
            
            return error_result
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入"""
        return "city" in input_data or "location" in input_data

class DatabaseTool(BaseTool):
    """
    数据库工具
    """
    
    def __init__(self, db_path: str = "tools_demo.db"):
        super().__init__(
            name="database_tool",
            description="数据库操作工具",
            config={"timeout": 15}
        )
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT,
                category TEXT,
                price REAL,
                stock INTEGER,
                created_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                email TEXT,
                role TEXT,
                created_at TEXT
            )
        ''')
        
        # 插入示例数据
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            products = [
                ("笔记本电脑", "电子产品", 5999.99, 50),
                ("无线鼠标", "电子产品", 199.99, 200),
                ("机械键盘", "电子产品", 899.99, 100),
                ("显示器", "电子产品", 2499.99, 30),
                ("USB集线器", "电子产品", 99.99, 150)
            ]
            
            cursor.executemany(
                "INSERT INTO products (name, category, price, stock, created_at) VALUES (?, ?, ?, ?, ?)",
                [(name, category, price, stock, datetime.now().isoformat()) for name, category, price, stock in products]
            )
        
        conn.commit()
        conn.close()
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据库操作"""
        if not self.validate_input(input_data):
            raise ValueError("输入数据无效")
        
        start_time = time.time()
        
        try:
            operation = input_data.get("operation", "query")
            
            if operation == "query":
                result = self._query_data(input_data)
            elif operation == "insert":
                result = self._insert_data(input_data)
            elif operation == "update":
                result = self._update_data(input_data)
            elif operation == "delete":
                result = self._delete_data(input_data)
            else:
                raise ValueError(f"不支持的操作: {operation}")
            
            execution_time = time.time() - start_time
            success = True
            
            log_entry = self.log_execution(input_data, result, execution_time, success)
            
            return {
                "status": "success",
                "data": result,
                "source": "database_tool",
                "operation": operation,
                "execution_log": log_entry
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = {
                "status": "error",
                "error": str(e),
                "source": "database_tool"
            }
            
            log_entry = self.log_execution(input_data, error_result, execution_time, False)
            error_result["execution_log"] = log_entry
            
            return error_result
    
    def _query_data(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """查询数据"""
        table = input_data.get("table", "products")
        condition = input_data.get("condition", "")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if condition:
            query = f"SELECT * FROM {table} WHERE {condition}"
            cursor.execute(query)
        else:
            cursor.execute(f"SELECT * FROM {table}")
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        conn.close()
        
        return [
            dict(zip(columns, row))
            for row in rows
        ]
    
    def _insert_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """插入数据"""
        table = input_data.get("table", "products")
        data = input_data.get("data", {})
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        columns = list(data.keys())
        placeholders = ["?"] * len(columns)
        values = list(data.values())
        
        if table == "products":
            values.append(datetime.now().isoformat())  # created_at
            columns.append("created_at")
        
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        cursor.execute(query, values)
        
        last_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {"inserted_id": last_id, "affected_rows": 1}
    
    def _update_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新数据"""
        table = input_data.get("table", "products")
        data = input_data.get("data", {})
        condition = input_data.get("condition", "id = 1")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        values = list(data.values())
        
        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        cursor.execute(query, values)
        
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        
        return {"affected_rows": affected_rows}
    
    def _delete_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """删除数据"""
        table = input_data.get("table", "products")
        condition = input_data.get("condition", "1 = 0")  # 默认不删除
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = f"DELETE FROM {table} WHERE {condition}"
        cursor.execute(query)
        
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        
        return {"affected_rows": affected_rows}
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入"""
        return "operation" in input_data

class FileProcessingTool(BaseTool):
    """
    文件处理工具
    """
    
    def __init__(self, work_dir: str = "files"):
        super().__init__(
            name="file_processing",
            description="文件处理工具",
            config={"timeout": 20}
        )
        self.work_dir = work_dir
        os.makedirs(work_dir, exist_ok=True)
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行文件操作"""
        if not self.validate_input(input_data):
            raise ValueError("输入数据无效")
        
        start_time = time.time()
        
        try:
            operation = input_data.get("operation", "read")
            
            if operation == "read":
                result = self._read_file(input_data)
            elif operation == "write":
                result = self._write_file(input_data)
            elif operation == "analyze":
                result = self._analyze_file(input_data)
            elif operation == "convert":
                result = self._convert_file(input_data)
            else:
                raise ValueError(f"不支持的操作: {operation}")
            
            execution_time = time.time() - start_time
            success = True
            
            log_entry = self.log_execution(input_data, result, execution_time, success)
            
            return {
                "status": "success",
                "data": result,
                "source": "file_processing",
                "operation": operation,
                "execution_log": log_entry
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = {
                "status": "error",
                "error": str(e),
                "source": "file_processing"
            }
            
            log_entry = self.log_execution(input_data, error_result, execution_time, False)
            error_result["execution_log"] = log_entry
            
            return error_result
    
    def _read_file(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """读取文件"""
        filename = input_data.get("filename", "")
        filepath = os.path.join(self.work_dir, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "filename": filename,
            "content": content,
            "size": len(content),
            "lines": len(content.split('\n'))
        }
    
    def _write_file(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """写入文件"""
        filename = input_data.get("filename", "")
        content = input_data.get("content", "")
        filepath = os.path.join(self.work_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "filename": filename,
            "filepath": filepath,
            "size": len(content),
            "written_at": datetime.now().isoformat()
        }
    
    def _analyze_file(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析文件"""
        filename = input_data.get("filename", "")
        filepath = os.path.join(self.work_dir, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")
        
        # 文件基本信息
        stat = os.stat(filepath)
        
        analysis = {
            "filename": filename,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": os.path.splitext(filename)[1],
            "encoding": "utf-8"
        }
        
        # 如果是文本文件，进行内容分析
        if filename.endswith(('.txt', '.csv', '.json', '.md')):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            words = content.split()
            
            analysis.update({
                "content_length": len(content),
                "line_count": len(lines),
                "word_count": len(words),
                "character_count": len(content),
                "avg_line_length": sum(len(line) for line in lines) / len(lines) if lines else 0
            })
        
        return analysis
    
    def _convert_file(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换文件格式"""
        source_filename = input_data.get("source_filename", "")
        target_format = input_data.get("target_format", "txt")
        
        source_filepath = os.path.join(self.work_dir, source_filename)
        if not os.path.exists(source_filepath):
            raise FileNotFoundError(f"源文件不存在: {source_filepath}")
        
        # 读取源文件
        with open(source_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 生成目标文件名
        base_name = os.path.splitext(source_filename)[0]
        target_filename = f"{base_name}.{target_format}"
        target_filepath = os.path.join(self.work_dir, target_filename)
        
        # 简单的格式转换
        if target_format == "json":
            converted_content = json.dumps({"content": content}, ensure_ascii=False, indent=2)
        elif target_format == "csv":
            lines = content.split('\n')
            converted_content = '\n'.join([f'"{line}"' for line in lines if line])
        else:
            converted_content = content  # 默认不转换
        
        # 写入目标文件
        with open(target_filepath, 'w', encoding='utf-8') as f:
            f.write(converted_content)
        
        return {
            "source_filename": source_filename,
            "target_filename": target_filename,
            "target_format": target_format,
            "converted_size": len(converted_content),
            "converted_at": datetime.now().isoformat()
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入"""
        return "operation" in input_data

class LLMIntegrationTool(BaseTool):
    """
    LLM集成工具
    """
    
    def __init__(self):
        super().__init__(
            name="llm_integration",
            description="LLM模型调用工具",
            config={"timeout": 60}
        )
        # 注意：这里使用硅基流动API
        self.api_base = Config.OPENAI_BASE_URL
        self.api_key = Config.OPENAI_API_KEY
        self.model = Config.MODEL_NAME
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """调用LLM模型"""
        if not self.validate_input(input_data):
            raise ValueError("输入数据无效")
        
        start_time = time.time()
        
        try:
            prompt = input_data.get("prompt", "")
            max_tokens = input_data.get("max_tokens", 1000)
            temperature = input_data.get("temperature", 0.7)
            
            # 模拟LLM调用（实际项目中使用真实的API调用）
            # 这里返回模拟结果
            mock_response = f"""
基于您的输入"{prompt[:50]}..."，我生成了以下响应：

这是一个模拟的LLM响应。在实际项目中，这里会调用硅基流动的Qwen模型来生成真实的响应。

模拟响应参数：
- 模型: {self.model}
- 最大令牌数: {max_tokens}
- 温度: {temperature}
- 响应时间: {time.time() - start_time:.2f}s
            """.strip()
            
            execution_time = time.time() - start_time
            success = True
            
            log_entry = self.log_execution(input_data, {"response": mock_response}, execution_time, success)
            
            return {
                "status": "success",
                "data": {
                    "response": mock_response,
                    "model": self.model,
                    "usage": {
                        "prompt_tokens": len(prompt.split()),
                        "completion_tokens": len(mock_response.split()),
                        "total_tokens": len(prompt.split()) + len(mock_response.split())
                    }
                },
                "source": "llm_integration",
                "execution_log": log_entry
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = {
                "status": "error",
                "error": str(e),
                "source": "llm_integration"
            }
            
            log_entry = self.log_execution(input_data, error_result, execution_time, False)
            error_result["execution_log"] = log_entry
            
            return error_result
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入"""
        return "prompt" in input_data and input_data["prompt"].strip()

# 4. 工具管理器

class ToolManager:
    """
    工具管理器
    """
    
    def __init__(self):
        self.tools = {}
        self.execution_history = []
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具"""
        self.register_tool(WeatherAPITool())
        self.register_tool(DatabaseTool())
        self.register_tool(FileProcessingTool())
        self.register_tool(LLMIntegrationTool())
    
    def register_tool(self, tool: BaseTool):
        """注册工具"""
        self.tools[tool.name] = tool
        print(f"工具已注册: {tool.name}")
    
    def execute_tool(self, tool_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        if tool_name not in self.tools:
            raise ValueError(f"工具不存在: {tool_name}")
        
        tool = self.tools[tool_name]
        if not tool.enabled:
            raise ValueError(f"工具已禁用: {tool_name}")
        
        # 执行工具
        result = tool.execute(input_data)
        
        # 记录执行历史
        execution_record = {
            "tool_name": tool_name,
            "timestamp": datetime.now().isoformat(),
            "input_data": input_data,
            "result": result,
            "success": result.get("status") == "success"
        }
        
        self.execution_history.append(execution_record)
        
        return result
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """获取工具统计"""
        stats = {}
        for tool_name, tool in self.tools.items():
            stats[tool_name] = tool.get_stats()
        
        stats["total_executions"] = len(self.execution_history)
        stats["successful_executions"] = sum(1 for record in self.execution_history if record["success"])
        
        return stats
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "enabled": tool.enabled,
                "execution_count": tool.execution_count
            }
            for tool in self.tools.values()
        ]

# 5. 工作流节点

def api_tool_execution(state: ToolState) -> ToolState:
    """API工具执行节点"""
    print_step("执行API工具")
    
    task_data = state.get("input_data", {})
    api_responses = state.get("api_responses", [])
    tool_execution_log = state.get("tool_execution_log", [])
    
    tool_manager = ToolManager()
    
    # 执行天气API工具
    if task_data.get("use_weather_api", False):
        city = task_data.get("city", "北京")
        weather_input = {"city": city}
        
        result = tool_manager.execute_tool("weather_api", weather_input)
        api_responses.append(result)
        
        if result.get("status") == "success":
            log_entry = result.get("execution_log", {})
            tool_execution_log.append(log_entry)
            print(f"天气API调用成功: {result['data']['city']}")
        else:
            print_error(f"天气API调用失败: {result.get('error')}")
    
    return {
        "api_responses": api_responses,
        "tool_execution_log": tool_execution_log
    }

def database_tool_execution(state: ToolState) -> ToolState:
    """数据库工具执行节点"""
    print_step("执行数据库工具")
    
    task_data = state.get("input_data", {})
    database_results = state.get("database_results", [])
    tool_execution_log = state.get("tool_execution_log", [])
    
    tool_manager = ToolManager()
    
    # 执行数据库查询
    if task_data.get("query_database", False):
        table = task_data.get("table", "products")
        condition = task_data.get("condition", "")
        
        db_input = {
            "operation": "query",
            "table": table,
            "condition": condition
        }
        
        result = tool_manager.execute_tool("database_tool", db_input)
        database_results.append(result)
        
        if result.get("status") == "success":
            log_entry = result.get("execution_log", {})
            tool_execution_log.append(log_entry)
            data = result.get("data", [])
            print(f"数据库查询成功，返回 {len(data)} 条记录")
        else:
            print_error(f"数据库查询失败: {result.get('error')}")
    
    return {
        "database_results": database_results,
        "tool_execution_log": tool_execution_log
    }

def file_tool_execution(state: ToolState) -> ToolState:
    """文件工具执行节点"""
    print_step("执行文件工具")
    
    task_data = state.get("input_data", {})
    file_results = state.get("file_results", [])
    tool_execution_log = state.get("tool_execution_log", [])
    
    tool_manager = ToolManager()
    
    # 创建示例文件
    if task_data.get("create_sample_file", False):
        filename = "sample_data.txt"
        content = f"""
这是一个示例文件，用于演示文件处理工具。

创建时间: {datetime.now().isoformat()}
内容: 包含一些示例文本
行数: 5行
字符数: 约100个字符

LangGraph工具系统演示
        """.strip()
        
        file_input = {
            "operation": "write",
            "filename": filename,
            "content": content
        }
        
        result = tool_manager.execute_tool("file_processing", file_input)
        file_results.append(result)
        
        if result.get("status") == "success":
            log_entry = result.get("execution_log", {})
            tool_execution_log.append(log_entry)
            print(f"文件创建成功: {filename}")
        else:
            print_error(f"文件创建失败: {result.get('error')}")
    
    # 分析文件
    if task_data.get("analyze_file", False):
        filename = task_data.get("filename_to_analyze", "sample_data.txt")
        
        analyze_input = {
            "operation": "analyze",
            "filename": filename
        }
        
        result = tool_manager.execute_tool("file_processing", analyze_input)
        file_results.append(result)
        
        if result.get("status") == "success":
            log_entry = result.get("execution_log", {})
            tool_execution_log.append(log_entry)
            data = result.get("data", {})
            print(f"文件分析成功: {data.get('size', 0)} 字节")
        else:
            print_error(f"文件分析失败: {result.get('error')}")
    
    return {
        "file_results": file_results,
        "tool_execution_log": tool_execution_log
    }

def llm_tool_execution(state: ToolState) -> ToolState:
    """LLM工具执行节点"""
    print_step("执行LLM工具")
    
    task_data = state.get("input_data", {})
    tool_results = state.get("tool_results", {})
    tool_execution_log = state.get("tool_execution_log", [])
    
    tool_manager = ToolManager()
    
    # 调用LLM工具
    if task_data.get("use_llm", False):
        prompt = task_data.get("prompt", "请介绍一下LangGraph框架的特点和用途。")
        max_tokens = task_data.get("max_tokens", 500)
        
        llm_input = {
            "prompt": prompt,
            "max_tokens": max_tokens
        }
        
        result = tool_manager.execute_tool("llm_integration", llm_input)
        tool_results["llm_result"] = result
        
        if result.get("status") == "success":
            log_entry = result.get("execution_log", {})
            tool_execution_log.append(log_entry)
            print(f"LLM调用成功")
        else:
            print_error(f"LLM调用失败: {result.get('error')}")
    
    return {
        "tool_results": tool_results,
        "tool_execution_log": tool_execution_log
    }

def combine_results(state: ToolState) -> ToolState:
    """合并结果节点"""
    print_step("合并工具执行结果")
    
    api_responses = state.get("api_responses", [])
    database_results = state.get("database_results", [])
    file_results = state.get("file_results", [])
    tool_results = state.get("tool_results", {})
    tool_execution_log = state.get("tool_execution_log", [])
    
    # 统计成功和失败的工具执行
    successful_tools = []
    failed_tools = []
    
    all_results = api_responses + database_results + file_results + list(tool_results.values())
    
    for result in all_results:
        if result.get("status") == "success":
            successful_tools.append(result.get("source", "unknown"))
        else:
            failed_tools.append(result.get("source", "unknown"))
    
    combined_output = {
        "summary": {
            "total_tools_executed": len(all_results),
            "successful_tools": len(successful_tools),
            "failed_tools": len(failed_tools),
            "success_rate": len(successful_tools) / len(all_results) if all_results else 0
        },
        "successful_tools": successful_tools,
        "failed_tools": failed_tools,
        "detailed_results": {
            "api_responses": api_responses,
            "database_results": database_results,
            "file_results": file_results,
            "llm_results": tool_results.get("llm_result", {})
        },
        "execution_statistics": {
            "total_log_entries": len(tool_execution_log),
            "execution_times": [log.get("execution_time", 0) for log in tool_execution_log],
            "generated_at": datetime.now().isoformat()
        }
    }
    
    print_result(f"结果合并完成")
    print(f"  - 成功工具: {len(successful_tools)}")
    print(f"  - 失败工具: {len(failed_tools)}")
    print(f"  - 成功率: {combined_output['summary']['success_rate']:.1%}")
    
    return {
        "combined_output": combined_output
    }

# 6. 构建工具集成工作流

def build_tool_integration_workflow():
    """构建工具集成工作流"""
    print_step("构建工具集成工作流")
    
    workflow = StateGraph(ToolState)
    
    # 添加节点
    workflow.add_node("execute_api_tools", api_tool_execution)
    workflow.add_node("execute_database_tools", database_tool_execution)
    workflow.add_node("execute_file_tools", file_tool_execution)
    workflow.add_node("execute_llm_tools", llm_tool_execution)
    workflow.add_node("combine_results", combine_results)
    
    # 设置入口点
    workflow.set_entry_point("execute_api_tools")
    
    # 并行执行所有工具
    workflow.add_edge("execute_api_tools", "execute_database_tools")
    workflow.add_edge("execute_api_tools", "execute_file_tools")
    workflow.add_edge("execute_api_tools", "execute_llm_tools")
    
    # 等待所有工具执行完成后合并结果
    workflow.add_edge("execute_database_tools", "combine_results")
    workflow.add_edge("execute_file_tools", "combine_results")
    workflow.add_edge("execute_llm_tools", "combine_results")
    
    workflow.add_edge("combine_results", END)
    
    return workflow.compile()

# 7. 演示函数

def demo_api_tools():
    """演示API工具"""
    print_step("API工具演示")
    
    tool_manager = ToolManager()
    
    # 测试天气API
    print("\n测试天气API工具:")
    result = tool_manager.execute_tool("weather_api", {"city": "上海"})
    print(f"结果: {result}")
    
    print("\n测试LLM工具:")
    result = tool_manager.execute_tool("llm_integration", {
        "prompt": "什么是人工智能？",
        "max_tokens": 200
    })
    print(f"结果状态: {result.get('status')}")

def demo_database_tools():
    """演示数据库工具"""
    print_step("数据库工具演示")
    
    tool_manager = ToolManager()
    
    # 测试数据库查询
    print("\n测试数据库查询:")
    result = tool_manager.execute_tool("database_tool", {
        "operation": "query",
        "table": "products",
        "condition": "price > 500"
    })
    
    if result.get("status") == "success":
        data = result.get("data", [])
        print(f"查询到 {len(data)} 条记录")
        for item in data[:3]:  # 只显示前3条
            print(f"  - {item}")
    else:
        print_error(f"查询失败: {result.get('error')}")

def demo_file_tools():
    """演示文件工具"""
    print_step("文件工具演示")
    
    tool_manager = ToolManager()
    
    # 创建文件
    print("\n创建示例文件:")
    content = "LangGraph是一个强大的框架\n用于构建基于状态的工作流\n支持复杂的AI应用场景"
    
    result = tool_manager.execute_tool("file_processing", {
        "operation": "write",
        "filename": "langgraph_demo.txt",
        "content": content
    })
    
    if result.get("status") == "success":
        print("文件创建成功")
        
        # 分析文件
        print("\n分析文件:")
        result = tool_manager.execute_tool("file_processing", {
            "operation": "analyze",
            "filename": "langgraph_demo.txt"
        })
        
        if result.get("status") == "success":
            analysis = result.get("data", {})
            print(f"文件大小: {analysis.get('size', 0)} 字节")
            print(f"行数: {analysis.get('line_count', 0)}")
            print(f"词数: {analysis.get('word_count', 0)}")

def demo_complete_tool_workflow():
    """演示完整的工具工作流"""
    print_step("完整工具工作流演示")
    
    app = build_tool_integration_workflow()
    
    initial_state = {
        "task_type": "multi_tool_demo",
        "input_data": {
            "use_weather_api": True,
            "city": "深圳",
            "query_database": True,
            "table": "products",
            "condition": "category = '电子产品'",
            "create_sample_file": True,
            "analyze_file": True,
            "use_llm": True,
            "prompt": "请总结一下现代编程语言的特点。",
            "max_tokens": 300
        },
        "tool_results": {},
        "api_responses": [],
        "database_results": [],
        "file_results": [],
        "combined_output": {},
        "tool_execution_log": [],
        "error_log": []
    }
    
    print("开始执行完整工具工作流...")
    
    start_time = time.time()
    result = app.invoke(initial_state)
    end_time = time.time()
    
    print_result(f"工作流执行完成，总耗时: {end_time - start_time:.2f}s")
    
    # 显示详细结果
    combined = result.get("combined_output", {})
    summary = combined.get("summary", {})
    
    print(f"\n执行摘要:")
    print(f"  总工具数: {summary.get('total_tools_executed', 0)}")
    print(f"  成功工具: {summary.get('successful_tools', 0)}")
    print(f"  失败工具: {summary.get('failed_tools', 0)}")
    print(f"  成功率: {summary.get('success_rate', 0):.1%}")
    
    # 显示工具列表
    tool_manager = ToolManager()
    tools = tool_manager.list_tools()
    
    print(f"\n可用工具:")
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']} (执行{tool['execution_count']}次)")

# 主程序
if __name__ == "__main__":
    print("🔧 LangGraph 自定义工具学习程序")
    print("=" * 60)
    
    while True:
        print("\n请选择演示:")
        print("1. API工具演示")
        print("2. 数据库工具演示")
        print("3. 文件工具演示")
        print("4. 完整工具工作流")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-4): ").strip()
        
        if choice == "1":
            demo_api_tools()
        elif choice == "2":
            demo_database_tools()
        elif choice == "3":
            demo_file_tools()
        elif choice == "4":
            demo_complete_tool_workflow()
        elif choice == "0":
            print_step("感谢学习自定义工具！")
            break
        else:
            print_error("无效选择，请重试")
    
    print_result("自定义工具学习完成！")