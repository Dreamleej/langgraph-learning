#!/usr/bin/env python3
"""
LangSmith监控仪表板
提供实时的性能监控和可视化界面
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import threading
from collections import defaultdict, deque

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from langsmith import Client
from .monitoring_example import LangSmithConfig, LangSmithCallbackHandler


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_failed": 0,
            "total_response_time": 0.0,
            "avg_response_time": 0.0,
            "max_response_time": 0.0,
            "min_response_time": float('inf')
        }
        
        # 时间序列数据（保留最近1000个数据点）
        self.time_series = deque(maxlen=1000)
        
        # 错误统计
        self.error_stats = defaultdict(int)
        
        # 锁用于线程安全
        self.lock = threading.Lock()
    
    def record_request(self, success: bool, response_time: float, error: str = None):
        """记录请求指标"""
        with self.lock:
            now = datetime.now()
            
            # 更新基础指标
            self.metrics["requests_total"] += 1
            
            if success:
                self.metrics["requests_success"] += 1
            else:
                self.metrics["requests_failed"] += 1
                if error:
                    self.error_stats[error] += 1
            
            # 更新响应时间指标
            self.metrics["total_response_time"] += response_time
            self.metrics["avg_response_time"] = self.metrics["total_response_time"] / self.metrics["requests_total"]
            self.metrics["max_response_time"] = max(self.metrics["max_response_time"], response_time)
            self.metrics["min_response_time"] = min(self.metrics["min_response_time"], response_time)
            
            # 添加时间序列数据
            self.time_series.append({
                "timestamp": now.isoformat(),
                "response_time": response_time,
                "success": success,
                "error": error
            })
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""
        with self.lock:
            return {
                **self.metrics,
                "success_rate": self.metrics["requests_success"] / max(self.metrics["requests_total"], 1),
                "error_rate": self.metrics["requests_failed"] / max(self.metrics["requests_total"], 1),
                "error_stats": dict(self.error_stats),
                "recent_requests": len(self.time_series)
            }
    
    def get_recent_time_series(self, minutes: int = 30) -> List[Dict[str, Any]]:
        """获取最近的时间序列数据"""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            
            return [
                point for point in self.time_series
                if datetime.fromisoformat(point["timestamp"]) >= cutoff_time
            ]
    
    def reset_metrics(self):
        """重置指标"""
        with self.lock:
            self.metrics = {
                "requests_total": 0,
                "requests_success": 0,
                "requests_failed": 0,
                "total_response_time": 0.0,
                "avg_response_time": 0.0,
                "max_response_time": 0.0,
                "min_response_time": float('inf')
            }
            self.error_stats.clear()
            self.time_series.clear()


# 全局监控器实例
monitor = PerformanceMonitor()


class LangSmithDashboard:
    """LangSmith仪表板"""
    
    def __init__(self):
        self.config = LangSmithConfig()
        self.active_connections: List[WebSocket] = []
    
    def get_langsmith_data(self) -> Dict[str, Any]:
        """从LangSmith获取数据"""
        if not self.config.is_enabled():
            return {"error": "LangSmith未启用"}
        
        try:
            client = self.config.get_client()
            
            # 获取项目信息
            # 注意：这些API调用需要真实的LangSmith项目
            # 这里返回模拟数据用于演示
            
            return {
                "project_name": self.config.project_name,
                "status": "connected",
                "last_updated": datetime.now().isoformat(),
                "runs_count": monitor.metrics["requests_total"],
                "success_rate": monitor.metrics["success_rate"],
                "avg_duration": monitor.metrics["avg_response_time"]
            }
        
        except Exception as e:
            return {
                "error": f"获取LangSmith数据失败: {str(e)}",
                "status": "error",
                "last_updated": datetime.now().isoformat()
            }


# 创建FastAPI应用
app = FastAPI(
    title="LangSmith 监控仪表板",
    description="实时监控LangGraph应用的性能和状态",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建仪表板实例
dashboard = LangSmithDashboard()


@app.get("/", response_class=HTMLResponse)
async def dashboard_page():
    """仪表板主页"""
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LangSmith 监控仪表板</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }
        .metric-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .chart-container {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-connected { background-color: #4caf50; }
        .status-error { background-color: #f44336; }
        .status-warning { background-color: #ff9800; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 LangSmith 监控仪表板</h1>
            <p>实时监控 LangGraph 应用性能</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">总请求数</div>
                <div class="metric-value" id="requests-total">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">成功率</div>
                <div class="metric-value" id="success-rate">0%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">平均响应时间</div>
                <div class="metric-value" id="avg-response-time">0ms</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">连接状态</div>
                <div class="metric-value" id="connection-status">
                    <span class="status-indicator status-connected"></span>
                    <span id="status-text">连接中</span>
                </div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>响应时间趋势</h3>
            <canvas id="responseTimeChart"></canvas>
        </div>
        
        <div class="chart-container">
            <h3>请求成功率</h3>
            <canvas id="successRateChart"></canvas>
        </div>
    </div>

    <script>
        // WebSocket连接
        const ws = new WebSocket(`ws://${window.location.host}/ws/dashboard`);
        
        // 图表配置
        const responseTimeCtx = document.getElementById('responseTimeChart').getContext('2d');
        const responseTimeChart = new Chart(responseTimeCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '响应时间 (ms)',
                    data: [],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        
        const successRateCtx = document.getElementById('successRateChart').getContext('2d');
        const successRateChart = new Chart(successRateCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '成功率 (%)',
                    data: [],
                    borderColor: '#4caf50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
        
        // 更新指标
        function updateMetrics(data) {
            document.getElementById('requests-total').textContent = data.requests_total || 0;
            document.getElementById('success-rate').textContent = 
                ((data.success_rate || 0) * 100).toFixed(1) + '%';
            document.getElementById('avg-response-time').textContent = 
                Math.round((data.avg_response_time || 0) * 1000) + 'ms';
            
            // 更新连接状态
            const statusText = document.getElementById('status-text');
            const statusIndicator = document.querySelector('.status-indicator');
            
            if (data.langsmith_status === 'connected') {
                statusText.textContent = '已连接';
                statusIndicator.className = 'status-indicator status-connected';
            } else if (data.langsmith_status === 'error') {
                statusText.textContent = '错误';
                statusIndicator.className = 'status-indicator status-error';
            } else {
                statusText.textContent = '连接中';
                statusIndicator.className = 'status-indicator status-warning';
            }
        }
        
        // 更新图表
        function updateCharts(timeSeriesData) {
            const now = new Date();
            const labels = timeSeriesData.map((_, index) => {
                const time = new Date(now - (timeSeriesData.length - index) * 1000);
                return time.toLocaleTimeString();
            });
            
            const responseTimes = timeSeriesData.map(point => 
                point.success ? point.response_time * 1000 : null
            );
            
            responseTimeChart.data.labels = labels;
            responseTimeChart.data.datasets[0].data = responseTimes;
            responseTimeChart.update();
            
            // 计算移动成功率
            const successRates = [];
            for (let i = 0; i < timeSeriesData.length; i++) {
                const window = timeSeriesData.slice(Math.max(0, i - 9), i + 1);
                const successCount = window.filter(point => point.success).length;
                successRates.push((successCount / window.length) * 100);
            }
            
            successRateChart.data.labels = labels;
            successRateChart.data.datasets[0].data = successRates;
            successRateChart.update();
        }
        
        // WebSocket消息处理
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            updateMetrics(data);
            updateCharts(data.recent_time_series || []);
        };
        
        // 定期请求数据
        setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({type: 'get_metrics'}));
            }
        }, 5000);
    </script>
</body>
</html>
    """
    return html_content


@app.get("/api/metrics")
async def get_metrics():
    """获取监控指标"""
    local_metrics = monitor.get_metrics()
    langsmith_data = dashboard.get_langsmith_data()
    
    return {
        **local_metrics,
        "langsmith_project": langsmith_data.get("project_name"),
        "langsmith_status": langsmith_data.get("status", "unknown"),
        "recent_time_series": monitor.get_recent_time_series(30)
    }


@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket仪表板端点"""
    await websocket.accept()
    dashboard.active_connections.append(websocket)
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "get_metrics":
                # 发送最新指标
                metrics_data = await get_metrics()
                await websocket.send_text(json.dumps(metrics_data))
    
    except WebSocketDisconnect:
        dashboard.active_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket错误: {e}")
        if websocket in dashboard.active_connections:
            dashboard.active_connections.remove(websocket)


@app.post("/api/simulate-request")
async def simulate_request():
    """模拟请求用于测试"""
    import random
    
    # 模拟请求
    success = random.random() > 0.1  # 90%成功率
    response_time = random.uniform(0.1, 2.0)  # 0.1-2秒响应时间
    error = None if success else random.choice([
        "Timeout Error", "API Error", "Validation Error", "Network Error"
    ])
    
    # 记录指标
    monitor.record_request(success, response_time, error)
    
    return {
        "success": success,
        "response_time": response_time,
        "error": error
    }


@app.get("/api/test")
async def test_endpoint():
    """测试端点"""
    import time
    
    start_time = time.time()
    
    try:
        # 模拟一些处理
        time.sleep(0.1)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # 记录成功请求
        monitor.record_request(True, response_time)
        
        return {
            "status": "success",
            "message": "测试成功",
            "response_time": response_time
        }
    
    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        
        # 记录失败请求
        monitor.record_request(False, response_time, str(e))
        
        return {
            "status": "error",
            "message": str(e),
            "response_time": response_time
        }


def start_dashboard(host: str = "0.0.0.0", port: int = 8001):
    """启动监控仪表板"""
    print("🚀 启动LangSmith监控仪表板...")
    print(f"📊 仪表板地址: http://{host}:{port}")
    print(f"📡 WebSocket地址: ws://{host}:{port}/ws/dashboard")
    print(f"🔍 API地址: http://{host}:{port}/api/metrics")
    print(f"🧪 测试地址: http://{host}:{port}/api/test")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    start_dashboard()