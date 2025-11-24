"""
04-real-world/workflow: 业务流程自动化

这是一个企业级工作流自动化系统，展示了LangGraph在处理复杂业务流程
、审批决策、多系统集成等方面的实际应用。

特性：
- 复杂业务流程编排
- 多条件分支和并行处理
- 审批和决策流程
- 异常处理和恢复
- 实时监控和报告
"""

from typing import TypedDict, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
import sys
import os
import json
import time
import sqlite3
from datetime import datetime, timedelta
import random
import uuid

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils import print_step, print_result, print_error, Config

# 1. 状态定义

class WorkflowState(TypedDict):
    """
    工作流状态
    """
    workflow_id: str
    workflow_type: str
    initiator: str
    request_data: Dict[str, Any]
    approval_steps: List[Dict[str, Any]]
    current_step: int
    step_results: List[Dict[str, Any]]
    parallel_tasks: List[Dict[str, Any]]
    notifications: List[Dict[str, Any]]
    final_result: Dict[str, Any]
    audit_log: List[Dict[str, Any]]
    error_log: List[Dict[str, Any]]

class TaskStatus:
    """任务状态常量"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class WorkflowType:
    """工作流类型常量"""
    PURCHASE_APPROVAL = "purchase_approval"
    LEAVE_REQUEST = "leave_request"
    EXPENSE_CLAIM = "expense_claim"
    PROJECT_APPROVAL = "project_approval"
    INCIDENT_RESPONSE = "incident_response"

# 2. 数据库管理

class WorkflowDB:
    """
    工作流数据库管理
    """
    
    def __init__(self, db_path: str = "workflow.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 工作流实例表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_instances (
                workflow_id TEXT PRIMARY KEY,
                workflow_type TEXT,
                initiator TEXT,
                status TEXT,
                request_data TEXT,
                current_step INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                completed_at TEXT
            )
        ''')
        
        # 审批步骤表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS approval_steps (
                step_id TEXT PRIMARY KEY,
                workflow_id TEXT,
                step_name TEXT,
                approver TEXT,
                status TEXT,
                decision TEXT,
                comments TEXT,
                assigned_at TEXT,
                completed_at TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflow_instances (workflow_id)
            )
        ''')
        
        # 任务执行表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_executions (
                task_id TEXT PRIMARY KEY,
                workflow_id TEXT,
                task_name TEXT,
                task_type TEXT,
                status TEXT,
                input_data TEXT,
                output_data TEXT,
                execution_time REAL,
                error_message TEXT,
                started_at TEXT,
                completed_at TEXT
            )
        ''')
        
        # 通知记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id TEXT PRIMARY KEY,
                workflow_id TEXT,
                recipient TEXT,
                message TEXT,
                notification_type TEXT,
                status TEXT,
                sent_at TEXT,
                read_at TEXT
            )
        ''')
        
        # 审计日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT,
                actor TEXT,
                action TEXT,
                details TEXT,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_workflow(self, workflow_id: str, workflow_type: str, 
                       initiator: str, request_data: Dict[str, Any]):
        """创建工作流实例"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO workflow_instances 
            (workflow_id, workflow_type, initiator, status, request_data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            workflow_id, workflow_type, initiator, TaskStatus.PENDING,
            json.dumps(request_data), datetime.now().isoformat(), datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def update_workflow_status(self, workflow_id: str, status: str, current_step: int = None):
        """更新工作流状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if current_step is not None:
            cursor.execute('''
                UPDATE workflow_instances 
                SET status = ?, current_step = ?, updated_at = ?
                WHERE workflow_id = ?
            ''', (status, current_step, datetime.now().isoformat(), workflow_id))
        else:
            cursor.execute('''
                UPDATE workflow_instances 
                SET status = ?, updated_at = ?
                WHERE workflow_id = ?
            ''', (status, datetime.now().isoformat(), workflow_id))
        
        conn.commit()
        conn.close()
    
    def log_audit(self, workflow_id: str, actor: str, action: str, details: str):
        """记录审计日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_log (workflow_id, actor, action, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (workflow_id, actor, action, details, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

# 3. 业务逻辑组件

class ApprovalEngine:
    """审批引擎"""
    
    def __init__(self):
        self.approval_rules = {
            WorkflowType.PURCHASE_APPROVAL: {
                "steps": [
                    {"name": "manager_approval", "approver": "manager", "required": True},
                    {"name": "finance_approval", "approver": "finance", "condition": "amount > 5000"},
                    {"name": "director_approval", "approver": "director", "condition": "amount > 10000"}
                ]
            },
            WorkflowType.LEAVE_REQUEST: {
                "steps": [
                    {"name": "supervisor_approval", "approver": "supervisor", "required": True},
                    {"name": "hr_approval", "approver": "hr", "condition": "days > 3"}
                ]
            },
            WorkflowType.EXPENSE_CLAIM: {
                "steps": [
                    {"name": "manager_review", "approver": "manager", "required": True},
                    {"name": "finance_review", "approver": "finance", "condition": "amount > 2000"}
                ]
            }
        }
    
    def generate_approval_steps(self, workflow_type: str, request_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成审批步骤"""
        rules = self.approval_rules.get(workflow_type, {})
        steps = []
        
        for step_rule in rules.get("steps", []):
            should_include = True
            
            # 检查条件
            if "condition" in step_rule:
                condition = step_rule["condition"]
                if "amount" in condition:
                    amount = request_data.get("amount", 0)
                    threshold = int(condition.split(">")[1].strip())
                    should_include = amount > threshold
                elif "days" in condition:
                    days = request_data.get("days", 0)
                    threshold = int(condition.split(">")[1].strip())
                    should_include = days > threshold
            
            if should_include:
                step = {
                    "step_id": str(uuid.uuid4()),
                    "name": step_rule["name"],
                    "approver": step_rule["approver"],
                    "required": step_rule.get("required", False),
                    "status": TaskStatus.PENDING,
                    "assigned_at": datetime.now().isoformat()
                }
                steps.append(step)
        
        return steps

class TaskExecutor:
    """任务执行器"""
    
    def __init__(self):
        self.task_handlers = {
            "email_notification": self.send_email_notification,
            "data_validation": self.validate_data,
            "system_integration": self.integrate_with_system,
            "document_generation": self.generate_document,
            "report_creation": self.create_report
        }
    
    def execute_task(self, task_name: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        start_time = time.time()
        
        try:
            if task_name in self.task_handlers:
                result = self.task_handlers[task_name](task_data)
                execution_time = time.time() - start_time
                
                return {
                    "status": TaskStatus.COMPLETED,
                    "result": result,
                    "execution_time": execution_time,
                    "completed_at": datetime.now().isoformat()
                }
            else:
                raise ValueError(f"未知任务类型: {task_name}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            
            return {
                "status": TaskStatus.FAILED,
                "error": str(e),
                "execution_time": execution_time,
                "completed_at": datetime.now().isoformat()
            }
    
    def send_email_notification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送邮件通知"""
        recipient = data.get("recipient", "")
        subject = data.get("subject", "")
        message = data.get("message", "")
        
        # 模拟邮件发送
        print(f"📧 发送邮件到 {recipient}: {subject}")
        time.sleep(random.uniform(0.5, 2.0))
        
        return {
            "recipient": recipient,
            "subject": subject,
            "sent_at": datetime.now().isoformat(),
            "message_id": str(uuid.uuid4())
        }
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """数据验证"""
        validation_rules = data.get("validation_rules", {})
        data_to_validate = data.get("data", {})
        
        validation_results = {}
        all_passed = True
        
        for field, rule in validation_rules.items():
            value = data_to_validate.get(field)
            
            if "required" in rule and rule["required"]:
                if not value:
                    validation_results[field] = {"status": "failed", "reason": "required field missing"}
                    all_passed = False
                else:
                    validation_results[field] = {"status": "passed"}
            
            if "type" in rule and value:
                expected_type = rule["type"]
                if expected_type == "number" and not isinstance(value, (int, float)):
                    validation_results[field] = {"status": "failed", "reason": "wrong type"}
                    all_passed = False
                elif expected_type == "string" and not isinstance(value, str):
                    validation_results[field] = {"status": "failed", "reason": "wrong type"}
                    all_passed = False
        
        return {
            "validation_passed": all_passed,
            "results": validation_results,
            "validated_at": datetime.now().isoformat()
        }
    
    def integrate_with_system(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """系统集成"""
        system_name = data.get("system_name", "")
        integration_data = data.get("data", {})
        
        # 模拟系统调用
        print(f"🔗 集成系统: {system_name}")
        time.sleep(random.uniform(1.0, 3.0))
        
        return {
            "system": system_name,
            "integration_id": str(uuid.uuid4()),
            "status": "success",
            "response_data": {"status": "processed", "id": str(uuid.uuid4())}
        }
    
    def generate_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成文档"""
        doc_type = data.get("doc_type", "")
        content = data.get("content", {})
        
        # 模拟文档生成
        print(f"📄 生成文档: {doc_type}")
        time.sleep(random.uniform(0.8, 2.0))
        
        document_id = str(uuid.uuid4())
        
        return {
            "document_id": document_id,
            "doc_type": doc_type,
            "generated_at": datetime.now().isoformat(),
            "file_path": f"/documents/{document_id}.pdf"
        }
    
    def create_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建报告"""
        report_type = data.get("report_type", "")
        report_data = data.get("data", {})
        
        # 模拟报告创建
        print(f"📊 创建报告: {report_type}")
        time.sleep(random.uniform(1.0, 2.5))
        
        report_id = str(uuid.uuid4()
)
        
        return {
            "report_id": report_id,
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "summary": f"报告已生成，包含 {len(report_data)} 项数据"
        }

class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self.notification_channels = ["email", "sms", "push", "slack"]
    
    def send_notification(self, recipient: str, message: str, 
                         notification_type: str = "info", channels: List[str] = None):
        """发送通知"""
        if channels is None:
            channels = ["email"]
        
        notifications = []
        
        for channel in channels:
            if channel in self.notification_channels:
                notification = {
                    "notification_id": str(uuid.uuid4()),
                    "recipient": recipient,
                    "message": message,
                    "channel": channel,
                    "type": notification_type,
                    "status": "sent",
                    "sent_at": datetime.now().isoformat()
                }
                notifications.append(notification)
                
                print(f"📢 通过 {channel} 发送通知给 {recipient}")
        
        return notifications

# 4. 工作流节点

def initialize_workflow(state: WorkflowState) -> WorkflowState:
    """初始化工作流"""
    print_step("初始化工作流")
    
    workflow_type = state.get("workflow_type", "")
    initiator = state.get("initiator", "")
    request_data = state.get("request_data", {})
    
    workflow_id = str(uuid.uuid4())
    
    # 生成审批步骤
    approval_engine = ApprovalEngine()
    approval_steps = approval_engine.generate_approval_steps(workflow_type, request_data)
    
    # 初始化数据库
    db = WorkflowDB()
    db.create_workflow(workflow_id, workflow_type, initiator, request_data)
    db.log_audit(workflow_id, "system", "workflow_created", f"工作流 {workflow_type} 已创建")
    
    print(f"工作流初始化完成 - ID: {workflow_id}")
    print(f"审批步骤数: {len(approval_steps)}")
    
    return {
        "workflow_id": workflow_id,
        "approval_steps": approval_steps,
        "current_step": 0,
        "step_results": [],
        "notifications": [],
        "audit_log": []
    }

def validate_request(state: WorkflowState) -> WorkflowState:
    """验证请求"""
    print_step("验证请求数据")
    
    workflow_id = state.get("workflow_id", "")
    request_data = state.get("request_data", {})
    workflow_type = state.get("workflow_type", "")
    
    # 定义验证规则
    validation_rules = {}
    
    if workflow_type == WorkflowType.PURCHASE_APPROVAL:
        validation_rules = {
            "item_name": {"required": True, "type": "string"},
            "amount": {"required": True, "type": "number"},
            "vendor": {"required": True, "type": "string"},
            "quantity": {"required": True, "type": "number"}
        }
    elif workflow_type == WorkflowType.LEAVE_REQUEST:
        validation_rules = {
            "employee_name": {"required": True, "type": "string"},
            "start_date": {"required": True, "type": "string"},
            "end_date": {"required": True, "type": "string"},
            "reason": {"required": True, "type": "string"}
        }
    
    # 执行验证
    task_executor = TaskExecutor()
    validation_result = task_executor.execute_task("data_validation", {
        "validation_rules": validation_rules,
        "data": request_data
    })
    
    # 记录结果
    step_results = state.get("step_results", [])
    step_results.append({
        "step": "validation",
        "result": validation_result,
        "timestamp": datetime.now().isoformat()
    })
    
    # 记录审计日志
    db = WorkflowDB()
    db.log_audit(workflow_id, "system", "validation_completed", 
               f"验证结果: {validation_result['status']}")
    
    print(f"验证完成: {validation_result['status']}")
    
    return {
        "step_results": step_results
    }

def execute_parallel_tasks(state: WorkflowState) -> WorkflowState:
    """执行并行任务"""
    print_step("执行并行任务")
    
    workflow_id = state.get("workflow_id", "")
    workflow_type = state.get("workflow_type", "")
    request_data = state.get("request_data", "")
    
    # 定义并行任务
    parallel_tasks = []
    task_executor = TaskExecutor()
    
    # 基于工作流类型定义不同的并行任务
    if workflow_type == WorkflowType.PURCHASE_APPROVAL:
        tasks = [
            {
                "name": "vendor_check",
                "handler": "system_integration",
                "data": {"system_name": "vendor_system", "vendor": request_data.get("vendor")}
            },
            {
                "name": "budget_check",
                "handler": "system_integration", 
                "data": {"system_name": "budget_system", "amount": request_data.get("amount")}
            },
            {
                "name": "generate_purchase_order",
                "handler": "document_generation",
                "data": {"doc_type": "purchase_order", "content": request_data}
            }
        ]
    elif workflow_type == WorkflowType.LEAVE_REQUEST:
        tasks = [
            {
                "name": "check_leave_balance",
                "handler": "system_integration",
                "data": {"system_name": "hr_system", "employee": request_data.get("employee_name")}
            },
            {
                "name": "check_team_schedule",
                "handler": "system_integration",
                "data": {"system_name": "schedule_system", "dates": [request_data.get("start_date"), request_data.get("end_date")]}
            }
        ]
    else:
        tasks = []
    
    # 并行执行任务
    task_results = []
    for task in tasks:
        print(f"执行任务: {task['name']}")
        result = task_executor.execute_task(task["handler"], task["data"])
        task_results.append({
            "task_name": task["name"],
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
    
    parallel_tasks.extend(task_results)
    
    # 记录审计日志
    db = WorkflowDB()
    db.log_audit(workflow_id, "system", "parallel_tasks_completed", 
               f"执行了 {len(tasks)} 个并行任务")
    
    print(f"并行任务执行完成: {len(task_results)} 个任务")
    
    return {
        "parallel_tasks": parallel_tasks
    }

def process_approval_steps(state: WorkflowState) -> WorkflowState:
    """处理审批步骤"""
    print_step("处理审批步骤")
    
    workflow_id = state.get("workflow_id", "")
    approval_steps = state.get("approval_steps", [])
    current_step = state.get("current_step", 0)
    request_data = state.get("request_data", {})
    
    step_results = state.get("step_results", [])
    notifications = state.get("notifications", [])
    
    if current_step >= len(approval_steps):
        print("所有审批步骤已完成")
        return state
    
    # 处理当前步骤
    current_approval_step = approval_steps[current_step]
    step_name = current_approval_step["name"]
    approver = current_approval_step["approver"]
    
    print(f"处理审批步骤: {step_name} - 审批人: {approver}")
    
    # 模拟审批决策
    time.sleep(random.uniform(1.0, 3.0))
    
    # 基于规则做出审批决策
    approval_decision = "approved"
    approval_comments = "审批通过"
    
    # 模拟一些审批被拒绝的情况
    if random.random() < 0.2:  # 20% 概率拒绝
        approval_decision = "rejected"
        approval_comments = "需要更多信息，请补充相关文档"
    
    # 更新审批步骤状态
    current_approval_step["status"] = TaskStatus.COMPLETED if approval_decision == "approved" else TaskStatus.REJECTED
    current_approval_step["decision"] = approval_decision
    current_approval_step["comments"] = approval_comments
    current_approval_step["completed_at"] = datetime.now().isoformat()
    
    # 记录审批结果
    step_results.append({
        "step": step_name,
        "approver": approver,
        "decision": approval_decision,
        "comments": approval_comments,
        "timestamp": datetime.now().isoformat()
    })
    
    # 发送通知
    notification_manager = NotificationManager()
    notification_message = f"您的申请已{approval_decision} - {approval_comments}"
    
    # 更新工作流状态
    db = WorkflowDB()
    if approval_decision == "rejected":
        db.update_workflow_status(workflow_id, TaskStatus.REJECTED, current_step)
        db.log_audit(workflow_id, approver, "approval_rejected", f"拒绝了步骤 {step_name}")
    else:
        db.log_audit(workflow_id, approver, "approval_approved", f"批准了步骤 {step_name}")
    
    print(f"审批步骤完成: {approval_decision}")
    
    return {
        "approval_steps": approval_steps,
        "step_results": step_results,
        "current_step": current_step + 1 if approval_decision == "approved" else current_step
    }

def check_completion_conditions(state: WorkflowState) -> WorkflowState:
    """检查完成条件"""
    print_step("检查完成条件")
    
    approval_steps = state.get("approval_steps", [])
    current_step = state.get("current_step", 0)
    workflow_id = state.get("workflow_id", "")
    
    # 检查是否有被拒绝的步骤
    rejected_steps = [step for step in approval_steps if step.get("status") == TaskStatus.REJECTED]
    
    if rejected_steps:
        final_status = TaskStatus.REJECTED
        final_result = {
            "status": "rejected",
            "reason": "审批被拒绝",
            "rejected_steps": [step["name"] for step in rejected_steps],
            "completed_at": datetime.now().isoformat()
        }
    elif current_step >= len(approval_steps):
        final_status = TaskStatus.COMPLETED
        final_result = {
            "status": "approved",
            "reason": "所有审批步骤完成",
            "approved_steps": [step["name"] for step in approval_steps],
            "completed_at": datetime.now().isoformat()
        }
    else:
        final_status = TaskStatus.IN_PROGRESS
        final_result = {
            "status": "in_progress",
            "current_step": current_step,
            "remaining_steps": len(approval_steps) - current_step
        }
    
    # 更新数据库状态
    if final_status in [TaskStatus.COMPLETED, TaskStatus.REJECTED]:
        db = WorkflowDB()
        db.update_workflow_status(workflow_id, final_status, current_step)
    
    print(f"完成条件检查: {final_result['status']}")
    
    return {
        "final_result": final_result
    }

def generate_final_report(state: WorkflowState) -> WorkflowState:
    """生成最终报告"""
    print_step("生成最终报告")
    
    workflow_id = state.get("workflow_id", "")
    workflow_type = state.get("workflow_type", "")
    initiator = state.get("initiator", "")
    request_data = state.get("request_data", {})
    step_results = state.get("step_results", [])
    parallel_tasks = state.get("parallel_tasks", [])
    final_result = state.get("final_result", {})
    
    # 创建最终报告
    task_executor = TaskExecutor()
    report_data = {
        "workflow_id": workflow_id,
        "workflow_type": workflow_type,
        "initiator": initiator,
        "request_data": request_data,
        "step_results": step_results,
        "parallel_tasks": parallel_tasks,
        "final_result": final_result,
        "report_generated_at": datetime.now().isoformat()
    }
    
    report_result = task_executor.execute_task("report_creation", {
        "report_type": f"{workflow_type}_summary",
        "data": report_data
    })
    
    print("最终报告生成完成")
    
    return {
        "final_result": {
            **final_result,
            "report": report_result.get("result", {})
        }
    }

def send_notifications(state: WorkflowState) -> WorkflowState:
    """发送通知"""
    print_step("发送通知")
    
    workflow_id = state.get("workflow_id", "")
    initiator = state.get("initiator", "")
    final_result = state.get("final_result", {})
    workflow_type = state.get("workflow_type", "")
    
    notifications = []
    notification_manager = NotificationManager()
    
    # 根据最终状态发送不同的通知
    if final_result.get("status") == "approved":
        message = f"您的工作流 {workflow_type} 已批准，ID: {workflow_id}"
        notification_type = "success"
    elif final_result.get("status") == "rejected":
        message = f"您的工作流 {workflow_type} 已被拒绝，原因: {final_result.get('reason', '')}"
        notification_type = "error"
    else:
        message = f"您的工作流 {workflow_type} 正在处理中，ID: {workflow_id}"
        notification_type = "info"
    
    # 发送给发起人
    initiator_notifications = notification_manager.send_notification(
        initiator, message, notification_type
    )
    notifications.extend(initiator_notifications)
    
    print(f"通知发送完成: {len(notifications)} 条通知")
    
    return {
        "notifications": notifications
    }

# 5. 路由函数

def route_after_validation(state: WorkflowState) -> Literal["parallel_tasks", "reject"]:
    """验证后的路由"""
    step_results = state.get("step_results", [])
    
    if step_results:
        validation_result = step_results[-1].get("result", {})
        if validation_result.get("status") == "failed":
            print("路由: reject (验证失败)")
            return "reject"
    
    print("路由: parallel_tasks (验证成功)")
    return "parallel_tasks"

def route_after_parallel_tasks(state: WorkflowState) -> Literal["approval", "complete"]:
    """并行任务后的路由"""
    parallel_tasks = state.get("parallel_tasks", [])
    
    # 检查是否所有并行任务都成功
    failed_tasks = [task for task in parallel_tasks 
                   if task.get("result", {}).get("status") == "failed"]
    
    if failed_tasks:
        print("路由: complete (有任务失败，直接完成)")
        return "complete"
    
    print("路由: approval (并行任务成功，进入审批)")
    return "approval"

def route_after_approval(state: WorkflowState) -> Literal["next_approval", "complete"]:
    """审批后的路由"""
    approval_steps = state.get("approval_steps", [])
    current_step = state.get("current_step", 0)
    
    # 检查当前审批步骤的结果
    if current_step > 0 and approval_steps[current_step - 1].get("status") == TaskStatus.REJECTED:
        print("路由: complete (审批被拒绝)")
        return "complete"
    
    # 检查是否还有待审批的步骤
    if current_step < len(approval_steps):
        print("路由: next_approval (继续下一步审批)")
        return "next_approval"
    
    print("路由: complete (所有审批完成)")
    return "complete"

# 6. 构建工作流

def build_business_automation_workflow():
    """构建业务自动化工作流"""
    print_step("构建业务自动化工作流")
    
    workflow = StateGraph(WorkflowState)
    
    # 添加节点
    workflow.add_node("initialize", initialize_workflow)
    workflow.add_node("validate", validate_request)
    workflow.add_node("parallel_tasks", execute_parallel_tasks)
    workflow.add_node("approval", process_approval_steps)
    workflow.add_node("check_completion", check_completion_conditions)
    workflow.add_node("generate_report", generate_final_report)
    workflow.add_node("notifications", send_notifications)
    
    # 设置入口点
    workflow.set_entry_point("initialize")
    
    # 添加边
    workflow.add_edge("initialize", "validate")
    
    # 验证后的条件路由
    workflow.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "parallel_tasks": "parallel_tasks",
            "reject": "generate_report"
        }
    )
    
    # 并行任务后的条件路由
    workflow.add_conditional_edges(
        "parallel_tasks",
        route_after_parallel_tasks,
        {
            "approval": "approval",
            "complete": "generate_report"
        }
    )
    
    # 审批后的条件路由
    workflow.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "next_approval": "approval",
            "complete": "generate_report"
        }
    )
    
    workflow.add_edge("generate_report", "check_completion")
    workflow.add_edge("check_completion", "notifications")
    workflow.add_edge("notifications", END)
    
    return workflow.compile()

# 7. 演示函数

def demo_purchase_approval():
    """演示采购审批工作流"""
    print_step("采购审批工作流演示")
    
    app = build_business_automation_workflow()
    
    initial_state = {
        "workflow_type": WorkflowType.PURCHASE_APPROVAL,
        "initiator": "张三",
        "request_data": {
            "item_name": "笔记本电脑",
            "amount": 8000,
            "vendor": "科技供应商A",
            "quantity": 2,
            "purpose": "研发部门使用"
        },
        "approval_steps": [],
        "current_step": 0,
        "step_results": [],
        "parallel_tasks": [],
        "notifications": [],
        "final_result": {},
        "audit_log": [],
        "error_log": []
    }
    
    print(f"\n开始处理采购审批:")
    print(f"  项目: {initial_state['request_data']['item_name']}")
    print(f"  金额: ¥{initial_state['request_data']['amount']}")
    print(f"  供应商: {initial_state['request_data']['vendor']}")
    
    result = app.invoke(initial_state)
    
    # 显示结果
    final_result = result.get("final_result", {})
    print(f"\n📋 审批结果:")
    print(f"  状态: {final_result.get('status', 'unknown')}")
    print(f"  原因: {final_result.get('reason', '')}")
    print(f"  完成时间: {final_result.get('completed_at', '')}")
    
    # 显示审批步骤
    step_results = result.get("step_results", [])
    approval_steps = [r for r in step_results if "approver" in r]
    if approval_steps:
        print(f"\n📝 审批记录:")
        for step in approval_steps:
            print(f"  {step['step']}: {step['decision']} ({step['approver']})")
    
    # 显示通知
    notifications = result.get("notifications", [])
    if notifications:
        print(f"\n📢 发送通知: {len(notifications)} 条")

def demo_leave_request():
    """演示请假申请工作流"""
    print_step("请假申请工作流演示")
    
    app = build_business_automation_workflow()
    
    initial_state = {
        "workflow_type": WorkflowType.LEAVE_REQUEST,
        "initiator": "李四",
        "request_data": {
            "employee_name": "李四",
            "start_date": "2024-12-20",
            "end_date": "2024-12-25",
            "reason": "家庭事务",
            "days": 5
        },
        "approval_steps": [],
        "current_step": 0,
        "step_results": [],
        "parallel_tasks": [],
        "notifications": [],
        "final_result": {},
        "audit_log": [],
        "error_log": []
    }
    
    print(f"\n开始处理请假申请:")
    print(f"  员工: {initial_state['request_data']['employee_name']}")
    print(f"  时间: {initial_state['request_data']['start_date']} 至 {initial_state['request_data']['end_date']}")
    print(f"  天数: {initial_state['request_data']['days']} 天")
    
    result = app.invoke(initial_state)
    
    # 显示结果
    final_result = result.get("final_result", {})
    print(f"\n📋 申请结果:")
    print(f"  状态: {final_result.get('status', 'unknown')}")
    print(f"  原因: {final_result.get('reason', '')}")

def demo_workflow_statistics():
    """演示工作流统计"""
    print_step("工作流统计信息")
    
    # 模拟运行多个工作流以生成统计数据
    workflows = [
        demo_purchase_approval,
        demo_leave_request
    ]
    
    print(f"\n📊 工作流统计信息:")
    print(f"  支持的工作流类型:")
    print(f"    - {WorkflowType.PURCHASE_APPROVAL}: 采购审批")
    print(f"    - {WorkflowType.LEAVE_REQUEST}: 请假申请")
    print(f"    - {WorkflowType.EXPENSE_CLAIM}: 费用报销")
    print(f"    - {WorkflowType.PROJECT_APPROVAL}: 项目审批")
    print(f"    - {WorkflowType.INCIDENT_RESPONSE}: 事件响应")
    
    print(f"\n  工作流特性:")
    print(f"    ✅ 多步骤审批")
    print(f"    ✅ 并行任务执行")
    print(f"    ✅ 条件分支路由")
    print(f"    ✅ 异常处理")
    print(f"    ✅ 实时通知")
    print(f"    ✅ 审计日志")
    print(f"    ✅ 报告生成")

# 主程序
if __name__ == "__main__":
    print("⚙️ LangGraph 业务流程自动化系统")
    print("=" * 60)
    
    while True:
        print("\n请选择演示:")
        print("1. 采购审批工作流")
        print("2. 请假申请工作流")
        print("3. 工作流统计信息")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-3): ").strip()
        
        if choice == "1":
            demo_purchase_approval()
        elif choice == "2":
            demo_leave_request()
        elif choice == "3":
            demo_workflow_statistics()
        elif choice == "0":
            print_step("感谢使用业务流程自动化系统！")
            break
        else:
            print_error("无效选择，请重试")
    
    print_result("业务流程自动化演示完成！")