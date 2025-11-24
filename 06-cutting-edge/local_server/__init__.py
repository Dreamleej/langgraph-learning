"""
本地服务器部署模块

本模块展示如何将LangGraph工作流部署为Web服务。
"""

from .main import app, chat_app

__all__ = ["app", "chat_app"]