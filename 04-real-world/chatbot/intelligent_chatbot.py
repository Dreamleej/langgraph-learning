"""
04-real-world/chatbot: 智能对话系统

这是一个完整的多轮对话系统，展示了LangGraph在构建智能客服
和对话助手方面的实际应用。

特性：
- 记忆能力和上下文理解
- 意图识别和智能路由
- 情感分析
- 多轮对话状态管理
- 个性化回复生成
"""

from typing import TypedDict, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
import sys
import os
import json
import time
import sqlite3
from datetime import datetime, timedelta
import re
import random

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils import print_step, print_result, print_error, Config

# 1. 状态定义
class ChatbotState(TypedDict):
    """
    聊天机器人状态
    """
    user_id: str
    session_id: str
    current_message: str
    conversation_history: List[Dict[str, Any]]
    user_profile: Dict[str, Any]
    intent: str
    entities: Dict[str, Any]
    emotion: str
    context: Dict[str, Any]
    response: str
    next_action: str
    memory_items: List[Dict[str, Any]]
    bot_mood: str

class IntentType:
    """意图类型常量"""
    GREETING = "greeting"
    QUESTION = "question"
    REQUEST = "request"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"
    GOODBYE = "goodbye"
    UNKNOWN = "unknown"

class EmotionType:
    """情感类型常量"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    ANGRY = "angry"
    HAPPY = "happy"
    SAD = "sad"

# 2. 数据库管理

class ConversationDB:
    """
    对话数据库管理
    """
    
    def __init__(self, db_path: str = "chatbot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                preferences TEXT,
                first_seen TEXT,
                last_seen TEXT,
                conversation_count INTEGER DEFAULT 0
            )
        ''')
        
        # 对话会话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                start_time TEXT,
                end_time TEXT,
                message_count INTEGER DEFAULT 0,
                sentiment_score REAL DEFAULT 0.0
            )
        ''')
        
        # 对话历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                user_id TEXT,
                message_type TEXT,
                content TEXT,
                intent TEXT,
                emotion TEXT,
                timestamp TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        ''')
        
        # 记忆表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                content TEXT,
                memory_type TEXT,
                importance REAL,
                created_at TEXT,
                accessed_count INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_user(self, user_id: str, username: str = None, preferences: Dict = None):
        """保存用户信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, preferences, first_seen, last_seen, conversation_count)
            VALUES (?, ?, ?, 
                COALESCE((SELECT first_seen FROM users WHERE user_id = ?), ?),
                ?,
                COALESCE((SELECT conversation_count FROM users WHERE user_id = ?), 0) + 1
            )
        ''', (user_id, username, json.dumps(preferences or {}), 
              user_id, datetime.now().isoformat(), datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
    
    def save_session(self, session_id: str, user_id: str):
        """保存会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO sessions (session_id, user_id, start_time, end_time, message_count, sentiment_score)
            VALUES (?, ?, 
                COALESCE((SELECT start_time FROM sessions WHERE session_id = ?), ?),
                COALESCE((SELECT end_time FROM sessions WHERE session_id = ?), ?),
                COALESCE((SELECT message_count FROM sessions WHERE session_id = ?), 0),
                COALESCE((SELECT sentiment_score FROM sessions WHERE session_id = ?), 0.0)
            )
        ''', (session_id, user_id, session_id, datetime.now().isoformat(), 
              session_id, datetime.now().isoformat(), session_id, session_id))
        
        conn.commit()
        conn.close()
    
    def save_message(self, session_id: str, user_id: str, message_type: str, 
                     content: str, intent: str, emotion: str):
        """保存消息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO messages (session_id, user_id, message_type, content, intent, emotion, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, user_id, message_type, content, intent, emotion, datetime.now().isoformat()))
        
        # 更新会话的消息计数
        cursor.execute('''
            UPDATE sessions SET message_count = message_count + 1, end_time = ?
            WHERE session_id = ?
        ''', (datetime.now().isoformat(), session_id))
        
        conn.commit()
        conn.close()
    
    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取对话历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT content, message_type, intent, emotion, timestamp
            FROM messages
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "content": row[0],
                "type": row[1],
                "intent": row[2],
                "emotion": row[3],
                "timestamp": row[4]
            }
            for row in reversed(rows)  # 按时间正序返回
        ]

# 3. 核心处理函数

class IntentClassifier:
    """意图分类器"""
    
    def __init__(self):
        self.intent_patterns = {
            IntentType.GREETING: [
                r"你好|hello|hi|嗨|您好",
                r"早上好|下午好|晚上好",
                r"在吗|在不在"
            ],
            IntentType.QUESTION: [
                r"什么|怎么|为什么|如何|哪些",
                r"\?|？",
                r"请问|想问|咨询"
            ],
            IntentType.REQUEST: [
                r"帮我|请|能否|可以",
                r"需要|想要|希望",
                r"做一下|处理一下|解决一下"
            ],
            IntentType.COMPLAINT: [
                r"不满|投诉|抱怨|糟糕",
                r"问题|错误|失败|不好",
                r"太差了|不满意|搞砸了"
            ],
            IntentType.COMPLIMENT: [
                r"很好|不错|棒|优秀",
                r"感谢|谢谢|多谢",
                r"厉害|太好了|满意"
            ],
            IntentType.GOODBYE: [
                r"再见|拜拜|bye|see you",
                r"结束|完事了|就这样",
                r"下次聊|回聊"
            ]
        }
    
    def classify(self, message: str) -> str:
        """分类意图"""
        message_lower = message.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        
        return IntentType.UNKNOWN

class EmotionAnalyzer:
    """情感分析器"""
    
    def __init__(self):
        self.emotion_words = {
            EmotionType.POSITIVE: ["好", "棒", "喜欢", "开心", "满意", "优秀", "perfect", "great", "good"],
            EmotionType.NEGATIVE: ["差", "糟", "坏", "讨厌", "烦", "生气", "bad", "terrible", "awful"],
            EmotionType.ANGRY: ["愤怒", "气死", "受不了", "太过分", "angry", "furious", "mad"],
            EmotionType.HAPPY: ["高兴", "快乐", "幸福", "开心", "happy", "joyful", "excited"],
            EmotionType.SAD: ["难过", "伤心", "沮丧", "失望", "sad", "disappointed", "depressed"]
        }
    
    def analyze(self, message: str) -> str:
        """分析情感"""
        message_lower = message.lower()
        
        scores = {}
        for emotion, words in self.emotion_words.items():
            score = sum(1 for word in words if word in message_lower)
            scores[emotion] = score
        
        if not scores or max(scores.values()) == 0:
            return EmotionType.NEUTRAL
        
        return max(scores.items(), key=lambda x: x[1])[0]

class EntityExtractor:
    """实体提取器"""
    
    def extract(self, message: str) -> Dict[str, Any]:
        """提取实体"""
        entities = {}
        
        # 提取时间相关实体
        time_patterns = {
            "今天": r"今天|today",
            "明天": r"明天|tomorrow",
            "昨天": r"昨天|yesterday",
            "本周": r"这周|本周|this week",
            "下周": r"下周|next week"
        }
        
        for entity_type, pattern in time_patterns.items():
            if re.search(pattern, message.lower()):
                entities[entity_type] = True
        
        # 提取数字
        numbers = re.findall(r'\d+', message)
        if numbers:
            entities["numbers"] = [int(n) for n in numbers]
        
        # 提取问题类型
        if "价格" in message or "多少钱" in message or "cost" in message.lower():
            entities["question_type"] = "pricing"
        elif "功能" in message or "用途" in message or "feature" in message.lower():
            entities["question_type"] = "feature"
        elif "技术" in message or "实现" in message or "technical" in message.lower():
            entities["question_type"] = "technical"
        
        return entities

class ResponseGenerator:
    """回复生成器"""
    
    def __init__(self):
        self.response_templates = {
            IntentType.GREETING: [
                "您好！很高兴为您服务，有什么可以帮助您的吗？",
                "你好！我是智能助手，请问有什么需要帮助的？",
                "嗨！欢迎来到我们的服务，我能为您做些什么？"
            ],
            IntentType.QUESTION: {
                "pricing": [
                    "关于价格问题，我们的服务非常实惠。具体的价格方案需要根据您的需求来定制。",
                    "我们的价格是根据服务内容和使用量来计算的，您能告诉我具体需求吗？"
                ],
                "feature": [
                    "关于功能方面，我们提供完整的服务解决方案。您想了解哪个具体功能呢？",
                    "我们的功能非常丰富，包括智能分析、自动化处理等。您对哪个功能感兴趣？"
                ],
                "technical": [
                    "技术实现方面我们采用最先进的架构。您遇到了什么技术问题吗？",
                    "关于技术细节，我可以为您详细解答。请告诉我您想了解的具体技术点。"
                ],
                "default": [
                    "这是一个很好的问题！让我来为您详细解答。",
                    "我理解您的问题。让我为您提供准确的信息。",
                    "关于您的问题，我需要更多信息来给出准确的回答。"
                ]
            },
            IntentType.REQUEST: [
                "好的，我来帮您处理这个请求。请提供更多详细信息。",
                "收到您的请求！我会尽快为您处理，请稍等片刻。",
                "没问题！我已经记录您的请求，现在开始处理。"
            ],
            IntentType.COMPLAINT: [
                "很抱歉给您带来不便。我会立即为您解决问题，请您稍等。",
                "我理解您的不满，让我来帮您解决这个问题。",
                "非常抱歉有这样的体验。我会尽全力帮您改善情况。"
            ],
            IntentType.COMPLIMENT: [
                "谢谢您的认可！您的满意是我们最大的动力。",
                "非常感谢您的赞美！我们会继续努力提供更好的服务。",
                "很高兴能帮到您！有任何其他需要都可以随时告诉我。"
            ],
            IntentType.GOODBYE: [
                "再见！感谢您的使用，期待下次为您服务。",
                "拜拜！祝您有美好的一天！",
                "再见！如果需要帮助，随时欢迎您回来。"
            ],
            IntentType.UNKNOWN: [
                "抱歉，我可能没有完全理解您的问题。能请您再详细说明一下吗？",
                "我需要更多信息来帮助您。您能具体描述一下您的问题吗？",
                "让我确认一下您的意思...您是想了解什么内容呢？"
            ]
        }
        
        self.emotion_responses = {
            EmotionType.HAPPY: "看到您这么开心我也很高兴！",
            EmotionType.SAD: "我理解您的感受，让我来帮您。",
            EmotionType.ANGRY: "请冷静下来，我会全力帮您解决问题。",
            EmotionType.NEGATIVE: "我理解您的心情，让我们一起找到解决方案。"
        }
    
    def generate(self, intent: str, emotion: str, entities: Dict[str, Any], 
                 context: Dict[str, Any]) -> str:
        """生成回复"""
        # 基础回复模板
        if intent in self.response_templates:
            templates = self.response_templates[intent]
            
            if isinstance(templates, dict):
                question_type = entities.get("question_type", "default")
                template = templates.get(question_type, templates.get("default", templates["default"][0]))
            else:
                template = random.choice(templates) if isinstance(templates, list) else templates
        else:
            template = random.choice(self.response_templates[IntentType.UNKNOWN])
        
        # 添加情感回应
        emotion_response = ""
        if emotion in self.emotion_responses and emotion != EmotionType.NEUTRAL:
            emotion_response = self.emotion_responses[emotion] + " "
        
        # 个性化回复
        personal_response = ""
        if context.get("user_name"):
            personal_response = f"{context['user_name']}，"
        
        # 组合回复
        response = f"{personal_response}{emotion_response}{template}"
        
        # 添加额外信息
        if entities:
            if "numbers" in entities:
                response += f" 我注意到您提到了数字：{', '.join(map(str, entities['numbers']))}。"
        
        return response

# 4. 对话工作流节点

def initialize_conversation(state: ChatbotState) -> ChatbotState:
    """初始化对话"""
    print_step("初始化对话")
    
    user_id = state.get("user_id", "default_user")
    session_id = state.get("session_id", f"session_{int(time.time())}")
    current_message = state.get("current_message", "")
    
    # 初始化数据库连接
    db = ConversationDB()
    
    # 保存用户和会话信息
    db.save_user(user_id)
    db.save_session(session_id, user_id)
    
    # 获取用户历史对话
    conversation_history = db.get_conversation_history(user_id)
    
    # 保存用户消息
    conversation_db = ConversationDB()
    conversation_db.save_message(session_id, user_id, "user", current_message, "", "")
    
    print(f"对话初始化完成 - 用户: {user_id}, 会话: {session_id}")
    
    return {
        "conversation_history": conversation_history,
        "user_id": user_id,
        "session_id": session_id
    }

def analyze_message(state: ChatbotState) -> ChatbotState:
    """分析消息"""
    print_step("分析用户消息")
    
    current_message = state.get("current_message", "")
    
    # 意图识别
    intent_classifier = IntentClassifier()
    intent = intent_classifier.classify(current_message)
    
    # 情感分析
    emotion_analyzer = EmotionAnalyzer()
    emotion = emotion_analyzer.analyze(current_message)
    
    # 实体提取
    entity_extractor = EntityExtractor()
    entities = entity_extractor.extract(current_message)
    
    print(f"分析结果 - 意图: {intent}, 情感: {emotion}, 实体: {entities}")
    
    return {
        "intent": intent,
        "emotion": emotion,
        "entities": entities
    }

def manage_context(state: ChatbotState) -> ChatbotState:
    """管理上下文"""
    print_step("管理对话上下文")
    
    conversation_history = state.get("conversation_history", [])
    intent = state.get("intent", "")
    entities = state.get("entities", {})
    emotion = state.get("emotion", "")
    user_id = state.get("user_id", "")
    
    # 构建上下文
    context = {
        "recent_messages": conversation_history[-3:],  # 最近3条消息
        "user_id": user_id,
        "current_intent": intent,
        "entities": entities,
        "emotion": emotion,
        "message_count": len(conversation_history)
    }
    
    # 从历史中提取用户信息
    if conversation_history:
        last_messages = [msg for msg in conversation_history if msg["type"] == "user"]
        if last_messages:
            # 简单的用户偏好分析
            topics = []
            for msg in last_messages[-5:]:  # 最近5条用户消息
                if msg["intent"] != "":
                    topics.append(msg["intent"])
            
            if topics:
                context["user_interests"] = topics
                context["favorite_topics"] = max(set(topics), key=topics.count)
    
    print(f"上下文管理完成 - 消息数: {len(conversation_history)}")
    
    return {
        "context": context
    }

def retrieve_memory(state: ChatbotState) -> ChatbotState:
    """检索记忆"""
    print_step("检索相关记忆")
    
    user_id = state.get("user_id", "")
    intent = state.get("intent", "")
    entities = state.get("entities", {})
    
    # 模拟记忆检索（实际项目中会查询真实的记忆数据库）
    memory_items = []
    
    # 基于意图检索相关记忆
    if intent == IntentType.QUESTION:
        memory_items.append({
            "type": "faq",
            "content": "用户之前询问过类似的问题",
            "relevance": 0.8
        })
    
    if intent == IntentType.COMPLAINT:
        memory_items.append({
            "type": "previous_complaint",
            "content": "用户之前有过投诉记录",
            "relevance": 0.9
        })
    
    # 基于实体检索
    if "question_type" in entities:
        memory_items.append({
            "type": "topic_history",
            "content": f"用户之前询问过{entities['question_type']}相关问题",
            "relevance": 0.7
        })
    
    print(f"检索到 {len(memory_items)} 条相关记忆")
    
    return {
        "memory_items": memory_items
    }

def generate_response(state: ChatbotState) -> ChatbotState:
    """生成回复"""
    print_step("生成回复")
    
    intent = state.get("intent", "")
    emotion = state.get("emotion", "")
    entities = state.get("entities", {})
    context = state.get("context", {})
    memory_items = state.get("memory_items", [])
    
    # 生成回复
    response_generator = ResponseGenerator()
    response = response_generator.generate(intent, emotion, entities, context)
    
    # 如果有相关记忆，添加记忆相关内容
    if memory_items:
        high_relevance_memories = [m for m in memory_items if m.get("relevance", 0) > 0.7]
        if high_relevance_memories:
            response += " 我记得您之前也关心过这个问题。"
    
    print(f"生成回复: {response[:50]}...")
    
    return {
        "response": response
    }

def save_conversation(state: ChatbotState) -> ChatbotState:
    """保存对话"""
    print_step("保存对话记录")
    
    user_id = state.get("user_id", "")
    session_id = state.get("session_id", "")
    response = state.get("response", "")
    intent = state.get("intent", "")
    emotion = state.get("emotion", "")
    
    # 保存机器人回复
    db = ConversationDB()
    db.save_message(session_id, user_id, "bot", response, intent, emotion)
    
    # 更新对话历史
    conversation_history = state.get("conversation_history", [])
    conversation_history.append({
        "type": "user",
        "content": state.get("current_message", ""),
        "intent": intent,
        "emotion": emotion,
        "timestamp": datetime.now().isoformat()
    })
    conversation_history.append({
        "type": "bot",
        "content": response,
        "timestamp": datetime.now().isoformat()
    })
    
    print("对话记录保存完成")
    
    return {
        "conversation_history": conversation_history
    }

def determine_next_action(state: ChatbotState) -> ChatbotState:
    """确定下一步动作"""
    print_step("确定下一步动作")
    
    intent = state.get("intent", "")
    emotion = state.get("emotion", "")
    entities = state.get("entities", {})
    
    # 确定下一步动作
    if intent == IntentType.GOODBYE:
        next_action = "end_conversation"
    elif emotion == EmotionType.ANGRY:
        next_action = "escalate_to_human"
    elif intent == IntentType.REQUEST and entities.get("question_type") == "technical":
        next_action = "technical_support"
    elif intent == IntentType.COMPLAINT:
        next_action = "follow_up_required"
    else:
        next_action = "continue_conversation"
    
    print(f"下一步动作: {next_action}")
    
    return {
        "next_action": next_action
    }

# 5. 构建聊天机器人工作流

def build_chatbot_workflow():
    """构建聊天机器人工作流"""
    print_step("构建聊天机器人工作流")
    
    workflow = StateGraph(ChatbotState)
    
    # 添加节点
    workflow.add_node("initialize", initialize_conversation)
    workflow.add_node("analyze", analyze_message)
    workflow.add_node("manage_context", manage_context)
    workflow.add_node("retrieve_memory", retrieve_memory)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("save_conversation", save_conversation)
    workflow.add_node("determine_action", determine_next_action)
    
    # 设置入口点
    workflow.set_entry_point("initialize")
    
    # 添加边
    workflow.add_edge("initialize", "analyze")
    workflow.add_edge("analyze", "manage_context")
    workflow.add_edge("manage_context", "retrieve_memory")
    workflow.add_edge("retrieve_memory", "generate_response")
    workflow.add_edge("generate_response", "save_conversation")
    workflow.add_edge("save_conversation", "determine_action")
    
    # 条件边 - 根据下一步动作决定路由
    workflow.add_conditional_edges(
        "determine_action",
        lambda state: state.get("next_action", "continue_conversation"),
        {
            "end_conversation": END,
            "escalate_to_human": END,
            "continue_conversation": END,
            "technical_support": END,
            "follow_up_required": END
        }
    )
    
    return workflow.compile()

# 6. 演示和交互函数

def demo_conversation():
    """演示对话功能"""
    print_step("智能对话系统演示")
    
    app = build_chatbot_workflow()
    
    print("\n🤖 智能聊天机器人已启动")
    print("💡 输入 'quit' 退出对话")
    print("🎯 支持的对话类型：问候、提问、请求、投诉、感谢、再见")
    print("=" * 50)
    
    user_id = "demo_user"
    session_id = f"session_{int(time.time())}"
    
    while True:
        try:
            # 获取用户输入
            user_message = input("\n👤 您: ").strip()
            
            if user_message.lower() in ['quit', '退出', 'bye', '再见']:
                print("\n🤖 机器人: 再见！感谢您的使用！")
                break
            
            if not user_message:
                continue
            
            # 构建状态
            state = {
                "user_id": user_id,
                "session_id": session_id,
                "current_message": user_message,
                "conversation_history": [],
                "user_profile": {},
                "intent": "",
                "entities": {},
                "emotion": "",
                "context": {},
                "response": "",
                "next_action": "",
                "memory_items": [],
                "bot_mood": "friendly"
            }
            
            # 执行工作流
            result = app.invoke(state)
            
            # 显示机器人回复
            bot_response = result.get("response", "抱歉，我现在无法回应。")
            print(f"\n🤖 机器人: {bot_response}")
            
            # 显示分析结果（调试用）
            if os.getenv("DEBUG_MODE", "false").lower() == "true":
                print(f"\n🔍 调试信息:")
                print(f"  意图: {result.get('intent', '')}")
                print(f"  情感: {result.get('emotion', '')}")
                print(f"  实体: {result.get('entities', {})}")
                print(f"  下一步动作: {result.get('next_action', '')}")
            
        except KeyboardInterrupt:
            print("\n\n🤖 机器人: 再见！期待下次与您对话！")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            print("🤖 机器人: 抱歉，出现了技术问题，请稍后再试。")

def test_intent_classification():
    """测试意图分类"""
    print_step("测试意图分类功能")
    
    classifier = IntentClassifier()
    
    test_messages = [
        "你好，请问在吗？",
        "这个产品多少钱？",
        "帮我查一下订单状态",
        "你们的服务太差了",
        "你们的客服真的很棒",
        "再见，下次聊"
    ]
    
    print("\n意图分类测试结果:")
    for message in test_messages:
        intent = classifier.classify(message)
        print(f"  \"{message}\" -> {intent}")

def test_emotion_analysis():
    """测试情感分析"""
    print_step("测试情感分析功能")
    
    analyzer = EmotionAnalyzer()
    
    test_messages = [
        "我今天真的很开心！",
        "这个产品太糟糕了，我很生气",
        "我觉得很难过",
        "还行吧，一般般"
    ]
    
    print("\n情感分析测试结果:")
    for message in test_messages:
        emotion = analyzer.analyze(message)
        print(f"  \"{message}\" -> {emotion}")

# 主程序
if __name__ == "__main__":
    print("💬 LangGraph 智能对话系统")
    print("=" * 60)
    
    while True:
        print("\n请选择功能:")
        print("1. 启动对话机器人")
        print("2. 测试意图分类")
        print("3. 测试情感分析")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-3): ").strip()
        
        if choice == "1":
            demo_conversation()
        elif choice == "2":
            test_intent_classification()
        elif choice == "3":
            test_emotion_analysis()
        elif choice == "0":
            print_step("感谢使用智能对话系统！")
            break
        else:
            print_error("无效选择，请重试")
    
    print_result("智能对话系统演示完成！")