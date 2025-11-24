"""
配置文件和工具函数
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

class Config:
    """配置类"""
    
    # 硅基流动 API 配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")
    
    # 模型配置
    MODEL_NAME = "Qwen/Qwen3-Next-80B-A3B-Instruct"
    
    # LangSmith 配置
    LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "langgraph-learning")

def get_openai_client():
    """获取 OpenAI 客户端"""
    if not Config.OPENAI_API_KEY:
        raise ValueError("未设置 OPENAI_API_KEY 环境变量")
    
    return OpenAI(
        api_key=Config.OPENAI_API_KEY,
        base_url=Config.OPENAI_BASE_URL
    )

def print_step(message: str):
    """打印步骤信息"""
    print(f"\n{'='*50}")
    print(f"🔄 {message}")
    print('='*50)

def print_result(message: str):
    """打印结果信息"""
    print(f"\n{'✅'*20}")
    print(f"✅ {message}")
    print(f"{'✅'*20}")

def print_error(message: str):
    """打印错误信息"""
    print(f"\n{'❌'*20}")
    print(f"❌ {message}")
    print(f"{'❌'*20}")