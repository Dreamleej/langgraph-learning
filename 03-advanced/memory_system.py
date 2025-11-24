"""
03-advanced: 记忆系统实现

本示例展示如何在LangGraph中实现高级记忆系统，
包括短期记忆、长期记忆、上下文管理和智能检索。

学习要点：
1. 短期记忆和长期记忆
2. 上下文窗口管理
3. 记忆检索和更新
4. 智能遗忘机制
"""

from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
import sys
import os
import json
import time
import hashlib
from datetime import datetime, timedelta
import sqlite3
import re

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import print_step, print_result, print_error

# 1. 状态定义
class MemoryState(TypedDict):
    """
    记忆系统状态
    """
    current_input: str
    short_term_memory: List[Dict[str, Any]]
    long_term_memory: List[Dict[str, Any]]
    context_window: List[Dict[str, Any]]
    memory_summary: Dict[str, Any]
    user_id: str
    session_id: str
    retrieval_results: List[Dict[str, Any]]
    memory_stats: Dict[str, Any]

class MemoryItem(TypedDict):
    """
    记忆项结构
    """
    id: str
    content: str
    timestamp: str
    importance: float
    tags: List[str]
    user_id: str
    session_id: str
    access_count: int
    last_accessed: str
    embedding: Optional[List[float]]  # 简化的向量嵌入

# 2. 记忆存储系统

class MemoryStorage:
    """
    记忆存储系统
    """
    
    def __init__(self, db_path: str = "memory.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT,
                timestamp TEXT,
                importance REAL,
                tags TEXT,
                user_id TEXT,
                session_id TEXT,
                access_count INTEGER,
                last_accessed TEXT,
                embedding TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_summary (
                user_id TEXT,
                session_id TEXT,
                summary TEXT,
                timestamp TEXT,
                PRIMARY KEY (user_id, session_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_memory(self, memory_item: MemoryItem) -> bool:
        """存储记忆项"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO memories 
                (id, content, timestamp, importance, tags, user_id, session_id, access_count, last_accessed, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory_item["id"],
                memory_item["content"],
                memory_item["timestamp"],
                memory_item["importance"],
                json.dumps(memory_item["tags"]),
                memory_item["user_id"],
                memory_item["session_id"],
                memory_item["access_count"],
                memory_item["last_accessed"],
                json.dumps(memory_item.get("embedding", []))
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"存储记忆失败: {e}")
            return False
    
    def retrieve_memories(self, user_id: str, query: str = "", limit: int = 10) -> List[MemoryItem]:
        """检索记忆"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if query:
                # 简单的关键词搜索
                cursor.execute('''
                    SELECT id, content, timestamp, importance, tags, user_id, session_id, 
                           access_count, last_accessed, embedding
                    FROM memories 
                    WHERE user_id = ? AND content LIKE ?
                    ORDER BY importance DESC, timestamp DESC
                    LIMIT ?
                ''', (user_id, f"%{query}%", limit))
            else:
                cursor.execute('''
                    SELECT id, content, timestamp, importance, tags, user_id, session_id,
                           access_count, last_accessed, embedding
                    FROM memories 
                    WHERE user_id = ?
                    ORDER BY importance DESC, timestamp DESC
                    LIMIT ?
                ''', (user_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            memories = []
            for row in rows:
                memory = {
                    "id": row[0],
                    "content": row[1],
                    "timestamp": row[2],
                    "importance": row[3],
                    "tags": json.loads(row[4]) if row[4] else [],
                    "user_id": row[5],
                    "session_id": row[6],
                    "access_count": row[7],
                    "last_accessed": row[8],
                    "embedding": json.loads(row[9]) if row[9] else None
                }
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            print(f"检索记忆失败: {e}")
            return []
    
    def update_access_count(self, memory_id: str) -> bool:
        """更新访问次数"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE memories 
                SET access_count = access_count + 1, last_accessed = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), memory_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"更新访问次数失败: {e}")
            return False

# 3. 记忆管理节点

def calculate_importance(content: str, context: Dict[str, Any] = None) -> float:
    """计算内容重要性"""
    importance = 0.5  # 基础重要性
    
    # 基于长度的加分
    length_bonus = min(len(content) / 200, 0.3)
    importance += length_bonus
    
    # 基于关键词的加分
    important_keywords = ["重要", "紧急", "关键", "必须", "记住", "important", "urgent", "critical"]
    keyword_count = sum(1 for keyword in important_keywords if keyword.lower() in content.lower())
    importance += keyword_count * 0.1
    
    # 基于提问的加分（问题通常更重要）
    if "?" in content or "？" in content:
        importance += 0.2
    
    # 基于情感的加分（情感表达可能重要）
    emotion_keywords = ["开心", "难过", "生气", "担心", "happy", "sad", "angry", "worried"]
    emotion_count = sum(1 for keyword in emotion_keywords if keyword.lower() in content.lower())
    importance += emotion_count * 0.1
    
    return min(importance, 1.0)

def extract_tags(content: str) -> List[str]:
    """从内容中提取标签"""
    tags = []
    
    # 简单的标签提取
    if "工作" in content or "work" in content.lower():
        tags.append("工作")
    if "学习" in content or "study" in content.lower():
        tags.append("学习")
    if "家庭" in content or "family" in content.lower():
        tags.append("家庭")
    if "健康" in content or "health" in content.lower():
        tags.append("健康")
    if "技术" in content or "tech" in content.lower():
        tags.append("技术")
    
    # 提取时间相关的标签
    if "今天" in content or "today" in content.lower():
        tags.append("今天")
    if "明天" in content or "tomorrow" in content.lower():
        tags.append("明天")
    if "昨天" in content or "yesterday" in content.lower():
        tags.append("昨天")
    
    return list(set(tags))  # 去重

def store_short_term_memory(state: MemoryState) -> MemoryState:
    """
    存储短期记忆
    """
    print_step("存储短期记忆")
    
    current_input = state.get("current_input", "")
    short_term_memory = state.get("short_term_memory", [])
    user_id = state.get("user_id", "default")
    session_id = state.get("session_id", "default")
    
    if not current_input.strip():
        return state
    
    # 创建记忆项
    memory_id = hashlib.md5(f"{current_input}_{time.time()}".encode()).hexdigest()
    
    memory_item = {
        "id": memory_id,
        "content": current_input,
        "timestamp": datetime.now().isoformat(),
        "importance": calculate_importance(current_input),
        "tags": extract_tags(current_input),
        "user_id": user_id,
        "session_id": session_id,
        "access_count": 0,
        "last_accessed": datetime.now().isoformat(),
        "embedding": [hash(current_input) % 100 / 100.0]  # 简化的嵌入
    }
    
    # 添加到短期记忆
    short_term_memory.append(memory_item)
    
    print(f"已存储短期记忆: {current_input[:50]}...")
    print(f"重要性评分: {memory_item['importance']:.2f}")
    print(f"标签: {memory_item['tags']}")
    
    return {
        "short_term_memory": short_term_memory
    }

def consolidate_long_term_memory(state: MemoryState) -> MemoryState:
    """
    整合到长期记忆
    """
    print_step("整合到长期记忆")
    
    short_term_memory = state.get("short_term_memory", [])
    long_term_memory = state.get("long_term_memory", [])
    memory_storage = MemoryStorage()
    
    # 将重要的短期记忆转移到长期记忆
    consolidated_count = 0
    for memory_item in short_term_memory:
        if memory_item["importance"] > 0.6:  # 重要性阈值
            # 存储到数据库
            if memory_storage.store_memory(memory_item):
                long_term_memory.append(memory_item)
                consolidated_count += 1
    
    print(f"已整合 {consolidated_count} 条记忆到长期记忆")
    
    # 清空短期记忆
    return {
        "short_term_memory": [],
        "long_term_memory": long_term_memory[-50:]  # 保留最近50条长期记忆
    }

def retrieve_relevant_memories(state: MemoryState) -> MemoryState:
    """
    检索相关记忆
    """
    print_step("检索相关记忆")
    
    current_input = state.get("current_input", "")
    user_id = state.get("user_id", "default")
    long_term_memory = state.get("long_term_memory", [])
    
    memory_storage = MemoryStorage()
    
    # 从数据库检索相关记忆
    retrieved_memories = memory_storage.retrieve_memories(user_id, current_input, limit=5)
    
    # 更新访问次数
    for memory in retrieved_memories:
        memory_storage.update_access_count(memory["id"])
    
    # 合并长期记忆和检索记忆
    all_memories = long_term_memory + retrieved_memories
    
    # 简单的相关性排序
    def calculate_relevance(memory_item):
        content = memory_item["content"]
        common_words = set(content.lower().split()) & set(current_input.lower().split())
        return len(common_words)
    
    all_memories.sort(key=calculate_relevance, reverse=True)
    
    # 保留最相关的记忆
    relevant_memories = all_memories[:10]
    
    print(f"检索到 {len(retrieved_memories)} 条相关记忆")
    print(f"总共相关记忆: {len(relevant_memories)} 条")
    
    return {
        "retrieval_results": relevant_memories
    }

def manage_context_window(state: MemoryState) -> MemoryState:
    """
    管理上下文窗口
    """
    print_step("管理上下文窗口")
    
    current_input = state.get("current_input", "")
    retrieval_results = state.get("retrieval_results", [])
    context_window = state.get("context_window", [])
    
    # 上下文窗口大小限制
    max_context_size = 5
    
    # 构建新的上下文窗口
    new_context = []
    
    # 添加当前输入
    new_context.append({
        "type": "current",
        "content": current_input,
        "timestamp": datetime.now().isoformat(),
        "source": "input"
    })
    
    # 添加相关的历史记忆
    for memory in retrieval_results[:max_context_size - 1]:
        new_context.append({
            "type": "memory",
            "content": memory["content"],
            "timestamp": memory["timestamp"],
            "source": "long_term_memory",
            "importance": memory["importance"],
            "tags": memory["tags"]
        })
    
    # 如果上下文太大，移除最旧的条目
    if len(new_context) > max_context_size:
        new_context = new_context[-max_context_size:]
    
    print(f"上下文窗口包含 {len(new_context)} 条记录")
    
    return {
        "context_window": new_context
    }

def intelligent_forgetting(state: MemoryState) -> MemoryState:
    """
    智能遗忘机制
    """
    print_step("执行智能遗忘")
    
    long_term_memory = state.get("long_term_memory", [])
    user_id = state.get("user_id", "default")
    
    if len(long_term_memory) < 20:  # 记忆数量较少，不需要遗忘
        return state
    
    # 遗忘策略
    current_time = datetime.now()
    forgotten_count = 0
    
    # 1. 遗忘时间过久且不重要的记忆
    filtered_memory = []
    for memory in long_term_memory:
        memory_time = datetime.fromisoformat(memory["timestamp"])
        days_old = (current_time - memory_time).days
        
        # 遗忘条件：超过30天且重要性低于0.3且访问次数少于2次
        if days_old > 30 and memory["importance"] < 0.3 and memory["access_count"] < 2:
            forgotten_count += 1
            continue
        
        filtered_memory.append(memory)
    
    # 2. 如果记忆仍然太多，保留最重要的
    if len(filtered_memory) > 50:
        filtered_memory.sort(key=lambda x: (x["importance"], x["access_count"]), reverse=True)
        filtered_memory = filtered_memory[:50]
        forgotten_count += len(long_term_memory) - len(filtered_memory)
    
    print(f"智能遗忘完成，遗忘了 {forgotten_count} 条记忆")
    print(f"保留记忆: {len(filtered_memory)} 条")
    
    return {
        "long_term_memory": filtered_memory
    }

def generate_memory_summary(state: MemoryState) -> MemoryState:
    """
    生成记忆摘要
    """
    print_step("生成记忆摘要")
    
    short_term_memory = state.get("short_term_memory", [])
    long_term_memory = state.get("long_term_memory", [])
    context_window = state.get("context_window", [])
    user_id = state.get("user_id", "default")
    session_id = state.get("session_id", "default")
    
    # 统计信息
    total_memories = len(short_term_memory) + len(long_term_memory)
    
    # 标签统计
    all_tags = []
    for memory in short_term_memory + long_term_memory:
        all_tags.extend(memory.get("tags", []))
    tag_counts = {}
    for tag in all_tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # 重要性统计
    importances = [memory["importance"] for memory in short_term_memory + long_term_memory]
    avg_importance = sum(importances) / len(importances) if importances else 0
    
    # 访问统计
    total_access = sum(memory["access_count"] for memory in long_term_memory)
    
    summary = {
        "user_id": user_id,
        "session_id": session_id,
        "total_memories": total_memories,
        "short_term_count": len(short_term_memory),
        "long_term_count": len(long_term_memory),
        "context_window_size": len(context_window),
        "tag_distribution": tag_counts,
        "average_importance": avg_importance,
        "total_access_count": total_access,
        "most_common_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5],
        "generated_at": datetime.now().isoformat()
    }
    
    print_result("记忆摘要生成完成")
    print(f"  总记忆数: {summary['total_memories']}")
    print(f"  平均重要性: {summary['average_importance']:.2f}")
    print(f"  常用标签: {dict(summary['most_common_tags'])}")
    
    return {
        "memory_summary": summary
    }

def update_memory_stats(state: MemoryState) -> MemoryState:
    """
    更新记忆统计
    """
    print_step("更新记忆统计")
    
    short_term_memory = state.get("short_term_memory", [])
    long_term_memory = state.get("long_term_memory", [])
    context_window = state.get("context_window", [])
    retrieval_results = state.get("retrieval_results", [])
    
    stats = {
        "short_term_count": len(short_term_memory),
        "long_term_count": len(long_term_memory),
        "context_window_size": len(context_window),
        "retrieval_count": len(retrieval_results),
        "total_stored": len(short_term_memory) + len(long_term_memory),
        "last_updated": datetime.now().isoformat()
    }
    
    return {
        "memory_stats": stats
    }

# 4. 构建记忆系统工作流

def build_memory_workflow():
    """构建记忆系统工作流"""
    print_step("构建记忆系统工作流")
    
    workflow = StateGraph(MemoryState)
    
    # 添加节点
    workflow.add_node("store_short_term", store_short_term_memory)
    workflow.add_node("retrieve_relevant", retrieve_relevant_memories)
    workflow.add_node("manage_context", manage_context_window)
    workflow.add_node("consolidate_long_term", consolidate_long_term_memory)
    workflow.add_node("intelligent_forget", intelligent_forgetting)
    workflow.add_node("generate_summary", generate_memory_summary)
    workflow.add_node("update_stats", update_memory_stats)
    
    # 设置入口点
    workflow.set_entry_point("store_short_term")
    
    # 添加边
    workflow.add_edge("store_short_term", "retrieve_relevant")
    workflow.add_edge("retrieve_relevant", "manage_context")
    workflow.add_edge("manage_context", "consolidate_long_term")
    workflow.add_edge("consolidate_long_term", "intelligent_forget")
    workflow.add_edge("intelligent_forget", "generate_summary")
    workflow.add_edge("generate_summary", "update_stats")
    workflow.add_edge("update_stats", END)
    
    return workflow.compile()

# 5. 演示函数

def demo_basic_memory():
    """演示基础记忆功能"""
    print_step("基础记忆功能演示")
    
    app = build_memory_workflow()
    
    initial_state = {
        "current_input": "我需要记住明天有一个重要的会议",
        "short_term_memory": [],
        "long_term_memory": [],
        "context_window": [],
        "memory_summary": {},
        "user_id": "user123",
        "session_id": "session001",
        "retrieval_results": [],
        "memory_stats": {}
    }
    
    print("第一次输入...")
    result1 = app.invoke(initial_state)
    
    print("\n第二次输入...")
    state2 = {
        "current_input": "那个会议需要准备什么材料？",
        "short_term_memory": [],
        "long_term_memory": result1.get("long_term_memory", []),
        "context_window": [],
        "memory_summary": {},
        "user_id": "user123",
        "session_id": "session001",
        "retrieval_results": [],
        "memory_stats": {}
    }
    result2 = app.invoke(state2)
    
    print_result("基础记忆演示完成")
    
    # 显示最终统计
    stats = result2.get("memory_stats", {})
    print(f"最终统计: {stats}")

def demo_memory_retrieval():
    """演示记忆检索"""
    print_step("记忆检索演示")
    
    app = build_memory_workflow()
    
    # 先存储一些记忆
    memories = [
        "我喜欢在周末看电影",
        "明天要学习LangGraph",
        "工作项目需要在本周完成",
        "昨天和朋友吃了火锅",
        "今天天气很好，适合出去走走"
    ]
    
    for memory_text in memories:
        print(f"\n存储记忆: {memory_text}")
        state = {
            "current_input": memory_text,
            "short_term_memory": [],
            "long_term_memory": [],
            "context_window": [],
            "memory_summary": {},
            "user_id": "user456",
            "session_id": "session002",
            "retrieval_results": [],
            "memory_stats": {}
        }
        app.invoke(state)
    
    # 测试检索
    print("\n" + "="*50)
    print("测试记忆检索")
    print("="*50)
    
    query_state = {
        "current_input": "我明天有什么计划？",
        "short_term_memory": [],
        "long_term_memory": [],
        "context_window": [],
        "memory_summary": {},
        "user_id": "user456",
        "session_id": "session002",
        "retrieval_results": [],
        "memory_stats": {}
    }
    
    result = app.invoke(query_state)
    
    retrieval_results = result.get("retrieval_results", [])
    print(f"\n检索到 {len(retrieval_results)} 条相关记忆:")
    for i, memory in enumerate(retrieval_results, 1):
        print(f"{i}. {memory['content']} (重要性: {memory['importance']:.2f})")

def demo_memory_management():
    """演示记忆管理"""
    print_step("记忆管理演示")
    
    app = build_memory_workflow()
    
    # 模拟大量记忆输入
    print("模拟大量记忆输入...")
    for i in range(25):
        memory_text = f"这是第{i+1}条记忆，内容包含一些{'重要' if i % 5 == 0 else '普通'}的信息"
        
        state = {
            "current_input": memory_text,
            "short_term_memory": [],
            "long_term_memory": [],
            "context_window": [],
            "memory_summary": {},
            "user_id": "user789",
            "session_id": "session003",
            "retrieval_results": [],
            "memory_stats": {}
        }
        result = app.invoke(state)
        
        if i % 10 == 9:
            print(f"已存储 {i+1} 条记忆，长期记忆: {len(result.get('long_term_memory', []))} 条")
    
    print_result("记忆管理演示完成")

# 主程序
if __name__ == "__main__":
    print("🧠 LangGraph 记忆系统学习程序")
    print("=" * 60)
    
    while True:
        print("\n请选择演示:")
        print("1. 基础记忆功能")
        print("2. 记忆检索")
        print("3. 记忆管理")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-3): ").strip()
        
        if choice == "1":
            demo_basic_memory()
        elif choice == "2":
            demo_memory_retrieval()
        elif choice == "3":
            demo_memory_management()
        elif choice == "0":
            print_step("感谢学习记忆系统！")
            break
        else:
            print_error("无效选择，请重试")
    
    print_result("记忆系统学习完成！")