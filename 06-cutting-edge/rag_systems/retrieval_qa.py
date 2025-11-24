#!/usr/bin/env python3
"""
RAG检索增强问答系统
展示如何使用LangGraph构建智能检索增强生成系统
"""

import os
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid
import re

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import numpy as np
from typing_extensions import TypedDict

# 导入配置
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from config import get_llm


class Document:
    """文档类"""
    
    def __init__(self, content: str, metadata: Dict[str, Any] = None):
        self.content = content
        self.metadata = metadata or {}
        self.id = self._generate_id()
        self.embedding = None
        self.chunks = []
    
    def _generate_id(self) -> str:
        """生成文档ID"""
        content_hash = hashlib.md5(self.content.encode()).hexdigest()
        return f"doc_{content_hash[:12]}"
    
    def chunk_document(self, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """将文档分割为块"""
        if not self.content:
            return []
        
        # 简单的分块策略
        words = self.content.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk = " ".join(chunk_words)
            chunks.append(chunk)
            
            if len(chunk_words) < chunk_size - overlap:
                break
        
        self.chunks = chunks
        return chunks
    
    def __str__(self):
        return f"Document(id={self.id}, content_length={len(self.content)})"


class VectorStore:
    """简单的向量存储"""
    
    def __init__(self):
        self.documents = {}  # doc_id -> Document
        self.embeddings = {}  # chunk_id -> embedding
        self.chunk_mapping = {}  # chunk_id -> doc_id
        self.index = {}  # 用于快速检索的索引
    
    def add_document(self, document: Document):
        """添加文档"""
        self.documents[document.id] = document
        
        # 生成分块
        chunks = document.chunk_document()
        
        # 为每个块生成简单的嵌入（这里用词频向量简化）
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document.id}_chunk_{i}"
            embedding = self._simple_embedding(chunk)
            
            self.embeddings[chunk_id] = embedding
            self.chunk_mapping[chunk_id] = document.id
    
    def _simple_embedding(self, text: str) -> np.ndarray:
        """简单的文本嵌入（使用词频）"""
        # 简化的TF-IDF风格嵌入
        words = re.findall(r'\w+', text.lower())
        word_count = len(words)
        
        if word_count == 0:
            return np.zeros(100)
        
        # 创建固定维度的向量
        embedding = np.zeros(100)
        
        # 基于词的简单哈希映射到向量维度
        for word in words:
            hash_val = hash(word) % 100
            embedding[hash_val] += 1 / word_count
        
        # 归一化
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    def similarity_search(self, query: str, k: int = 5) -> List[Tuple[str, float]]:
        """相似度搜索"""
        query_embedding = self._simple_embedding(query)
        similarities = []
        
        for chunk_id, chunk_embedding in self.embeddings.items():
            # 计算余弦相似度
            similarity = np.dot(query_embedding, chunk_embedding)
            similarities.append((chunk_id, similarity))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:k]
    
    def get_document_by_chunk(self, chunk_id: str) -> Optional[Document]:
        """通过块ID获取文档"""
        doc_id = self.chunk_mapping.get(chunk_id)
        return self.documents.get(doc_id)
    
    def get_relevant_context(self, query: str, k: int = 3) -> str:
        """获取相关上下文"""
        search_results = self.similarity_search(query, k)
        
        context_parts = []
        for chunk_id, similarity in search_results:
            doc = self.get_document_by_chunk(chunk_id)
            if doc:
                # 提取对应的块
                chunk_index = int(chunk_id.split("_chunk_")[-1])
                if chunk_index < len(doc.chunks):
                    context_parts.append(f"[来源: {doc.metadata.get('title', '未知')}]\n{doc.chunks[chunk_index]}")
        
        return "\n\n".join(context_parts)


class RAGState(TypedDict):
    """RAG系统状态"""
    query: str
    context: str
    relevant_docs: List[Dict[str, Any]]
    response: str
    confidence: float
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class RAGSystem:
    """RAG检索增强生成系统"""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.llm = get_llm()
        self.conversation_history = []
    
    def add_knowledge(self, content: str, title: str = "", source: str = ""):
        """添加知识文档"""
        metadata = {"title": title, "source": source, "added_at": datetime.now().isoformat()}
        document = Document(content, metadata)
        self.vector_store.add_document(document)
        
        print(f"📚 添加文档: {title or '未知标题'} ({len(content)} 字符)")
    
    def create_rag_workflow(self) -> StateGraph:
        """创建RAG工作流"""
        
        def query_understanding(state: RAGState) -> RAGState:
            """查询理解"""
            print_step("理解查询意图")
            query = state.get("query", "")
            
            # 简单的查询分析
            query_analysis = {
                "original_query": query,
                "query_length": len(query),
                "word_count": len(query.split()),
                "query_type": self._classify_query(query),
                "keywords": self._extract_keywords(query)
            }
            
            return {
                **state,
                "metadata": {**state.get("metadata", {}), "query_analysis": query_analysis}
            }
        
        def knowledge_retrieval(state: RAGState) -> RAGState:
            """知识检索"""
            print_step("检索相关知识")
            query = state.get("query", "")
            
            # 执行相似度搜索
            search_results = self.vector_store.similarity_search(query, k=5)
            
            # 构建相关文档列表
            relevant_docs = []
            context_parts = []
            sources = []
            
            for chunk_id, similarity in search_results:
                if similarity > 0.1:  # 相似度阈值
                    doc = self.vector_store.get_document_by_chunk(chunk_id)
                    if doc:
                        chunk_index = int(chunk_id.split("_chunk_")[-1])
                        if chunk_index < len(doc.chunks):
                            chunk_content = doc.chunks[chunk_index]
                            
                            relevant_docs.append({
                                "content": chunk_content,
                                "source": doc.metadata.get("title", "未知"),
                                "similarity": similarity,
                                "doc_id": doc.id
                            })
                            
                            context_parts.append(chunk_content)
                            sources.append({
                                "title": doc.metadata.get("title", "未知"),
                                "source": doc.metadata.get("source", ""),
                                "similarity": similarity
                            })
            
            context = "\n\n".join(context_parts)
            
            return {
                **state,
                "context": context,
                "relevant_docs": relevant_docs,
                "sources": sources
            }
        
        def answer_generation(state: RAGState) -> RAGState:
            """生成回答"""
            print_step("生成回答")
            query = state.get("query", "")
            context = state.get("context", "")
            
            # 构建提示词
            if context:
                prompt = f"""
基于以下知识库内容回答用户问题：

知识库内容：
{context}

用户问题：{query}

请基于提供的知识库内容回答问题。如果知识库中没有相关信息，请明确说明。
回答要求：
1. 准确基于提供的知识库内容
2. 条理清晰，重点突出
3. 如果信息不足，请诚实说明
4. 引用具体的来源信息

回答：
"""
            else:
                prompt = f"""
用户问题：{query}

抱歉，知识库中没有找到与您问题相关的信息。请尝试：
1. 使用更具体的关键词
2. 检查拼写是否正确
3. 尝试相关问题

如果您需要更多信息，请具体说明您的需求。
"""
            
            try:
                response = self.llm.invoke(prompt)
                generated_response = response.content
                
                # 计算置信度
                confidence = self._calculate_confidence(state, generated_response)
                
            except Exception as e:
                generated_response = f"生成回答时出现错误：{str(e)}"
                confidence = 0.0
            
            return {
                **state,
                "response": generated_response,
                "confidence": confidence
            }
        
        def response_refinement(state: RAGState) -> RAGState:
            """回答优化"""
            print_step("优化回答")
            response = state.get("response", "")
            sources = state.get("sources", [])
            confidence = state.get("confidence", 0.0)
            
            # 如果有来源信息，添加引用
            if sources and confidence > 0.5:
                source_list = []
                for i, source in enumerate(sources[:3], 1):
                    source_list.append(f"{i}. {source['title']} (相似度: {source['similarity']:.2f})")
                
                refined_response = f"{response}\n\n📚 参考来源:\n" + "\n".join(source_list)
            else:
                refined_response = response
            
            # 添加置信度提示
            if confidence < 0.7:
                refined_response += f"\n\n⚠️ 回答置信度: {confidence:.1%}，建议结合其他信息验证。"
            
            return {
                **state,
                "response": refined_response
            }
        
        # 构建工作流
        workflow = StateGraph(RAGState)
        
        # 添加节点
        workflow.add_node("query_understanding", query_understanding)
        workflow.add_node("knowledge_retrieval", knowledge_retrieval)
        workflow.add_node("answer_generation", answer_generation)
        workflow.add_node("response_refinement", response_refinement)
        
        # 添加边
        workflow.add_edge(START, "query_understanding")
        workflow.add_edge("query_understanding", "knowledge_retrieval")
        workflow.add_edge("knowledge_retrieval", "answer_generation")
        workflow.add_edge("answer_generation", "response_refinement")
        workflow.add_edge("response_refinement", END)
        
        # 使用内存检查点
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    def _classify_query(self, query: str) -> str:
        """分类查询类型"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["什么是", "介绍", "定义", "概念"]):
            return "definition"
        elif any(word in query_lower for word in ["如何", "怎么", "步骤", "方法"]):
            return "how_to"
        elif any(word in query_lower for word in ["为什么", "原因", "原理"]):
            return "why"
        elif any(word in query_lower for word in ["比较", "区别", "优缺点"]):
            return "comparison"
        else:
            return "general"
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        words = re.findall(r'\w+', query.lower())
        # 过滤停用词（简化版）
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '如果', '那么', '的', '了', '着', '过', '将', '会', '能', '可以', '应该', '需要', 'the', 'is', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        return keywords[:10]  # 返回前10个关键词
    
    def _calculate_confidence(self, state: RAGState, response: str) -> float:
        """计算回答置信度"""
        base_confidence = 0.5
        
        # 基于检索结果调整
        relevant_docs = state.get("relevant_docs", [])
        if relevant_docs:
            max_similarity = max(doc.get("similarity", 0) for doc in relevant_docs)
            base_confidence += max_similarity * 0.3
        
        # 基于上下文长度调整
        context = state.get("context", "")
        if len(context) > 100:
            base_confidence += 0.1
        
        # 基于回答长度调整
        if len(response) > 50:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def query(self, question: str) -> Dict[str, Any]:
        """执行查询"""
        workflow = self.create_rag_workflow()
        
        initial_state = {
            "query": question,
            "context": "",
            "relevant_docs": [],
            "response": "",
            "confidence": 0.0,
            "sources": [],
            "metadata": {}
        }
        
        # 运行工作流
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        result = workflow.invoke(initial_state, config=config)
        
        # 保存到对话历史
        self.conversation_history.append({
            "query": question,
            "response": result.get("response", ""),
            "confidence": result.get("confidence", 0.0),
            "timestamp": datetime.now().isoformat()
        })
        
        return result


def print_step(step: str):
    """打印步骤信息"""
    print(f"🔍 {step}")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)


def demo_rag_system():
    """演示RAG系统"""
    print("🔍 RAG检索增强问答系统演示")
    print("=" * 60)
    
    # 创建RAG系统
    rag_system = RAGSystem()
    
    # 添加知识库
    knowledge_base = [
        {
            "title": "LangGraph介绍",
            "content": """
LangGraph是LangChain生态系统中的一个重要组件，专门用于构建状态图和工作流。
它提供了一种声明式的方式来定义复杂的AI应用流程，支持条件路由、并行执行、
状态管理和错误处理等高级特性。LangGraph特别适合构建需要多步骤处理的AI应用，
如对话系统、决策流程和自动化工作流。它的核心优势在于可视化的流程定义和强大的状态管理能力。
""",
            "source": "LangGraph官方文档"
        },
        {
            "title": "LangGraph的核心概念",
            "content": """
LangGraph的核心概念包括节点（Node）、边（Edge）和状态（State）。
节点代表处理单元，可以是LLM调用、工具使用或数据处理；边定义了节点之间的连接关系；
状态是在整个工作流中传递的数据。LangGraph还支持条件边（Conditional Edge），
可以根据运行时状态动态选择下一个节点。此外，它还提供了检查点（Checkpoint）机制，
支持状态的持久化和恢复。
""",
            "source": "LangGraph教程"
        },
        {
            "title": "RAG系统原理",
            "content": """
检索增强生成（Retrieval-Augmented Generation，RAG）是一种结合了信息检索和文本生成的AI系统架构。
RAG系统首先从知识库中检索相关的文档片段，然后将这些片段作为上下文提供给LLM生成回答。
这种架构解决了传统LLM的两个主要问题：知识更新滞后和幻觉现象。RAG系统通过实时检索最新的相关信息，
大大提高了回答的准确性和可信度。典型的RAG系统包括文档预处理、向量化、相似度检索和上下文增强生成等步骤。
""",
            "source": "AI技术文档"
        }
    ]
    
    # 添加知识到系统
    for knowledge in knowledge_base:
        rag_system.add_knowledge(
            content=knowledge["content"],
            title=knowledge["title"],
            source=knowledge["source"]
        )
    
    print(f"📚 知识库加载完成，共 {len(knowledge_base)} 个文档")
    
    # 测试查询
    test_queries = [
        "什么是LangGraph？",
        "LangGraph有哪些核心概念？",
        "RAG系统的工作原理是什么？",
        "如何使用LangGraph构建应用？",
        "LangGraph和传统LLM有什么区别？"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🎯 查询 {i}: {query}")
        print("-" * 40)
        
        result = rag_system.query(query)
        
        response = result.get("response", "")
        confidence = result.get("confidence", 0.0)
        relevant_docs = result.get("relevant_docs", [])
        
        print(f"🤖 回答: {response}")
        print(f"📊 置信度: {confidence:.1%}")
        
        if relevant_docs:
            print(f"📚 检索到 {len(relevant_docs)} 个相关文档片段")
            for j, doc in enumerate(relevant_docs[:2], 1):
                print(f"   {j}. {doc['source']} (相似度: {doc['similarity']:.2f})")
    
    print(f"\n📈 对话历史: {len(rag_system.conversation_history)} 次交互")


if __name__ == "__main__":
    try:
        demo_rag_system()
        print("\n✅ RAG系统演示完成！")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()