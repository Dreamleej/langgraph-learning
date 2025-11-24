#!/usr/bin/env python3
"""
多模态AI代理
展示如何使用LangGraph构建处理文本、图像、音频的多模态AI系统
"""

import os
import json
import base64
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid
import mimetypes
import io
from dataclasses import dataclass

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict

# 导入配置
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from config import get_llm


@dataclass
class MediaContent:
    """媒体内容类"""
    content: Union[str, bytes]  # 文本或二进制数据
    media_type: str  # text, image, audio, video
    format: str  # 具体格式，如 jpeg, png, mp3, wav
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_text(self) -> bool:
        return self.media_type == "text"
    
    @property
    def is_image(self) -> bool:
        return self.media_type == "image"
    
    @property
    def is_audio(self) -> bool:
        return self.media_type == "audio"


class MultimodalState(TypedDict):
    """多模态系统状态"""
    input_media: List[MediaContent]
    processed_media: Dict[str, Any]
    analysis_results: Dict[str, Any]
    cross_modal_insights: Dict[str, Any]
    final_response: str
    confidence: float
    metadata: Dict[str, Any]


class MediaProcessor:
    """媒体处理器"""
    
    def __init__(self):
        self.llm = get_llm()
        self.processing_history = []
    
    def process_text(self, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理文本内容"""
        print_step("处理文本内容")
        
        # 文本分析
        analysis = {
            "type": "text",
            "length": len(content),
            "word_count": len(content.split()),
            "language": self._detect_language(content),
            "sentiment": self._analyze_sentiment(content),
            "keywords": self._extract_keywords(content),
            "summary": self._generate_summary(content),
            "entities": self._extract_entities(content),
            "metadata": metadata or {}
        }
        
        return analysis
    
    def process_image(self, image_data: bytes, format: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理图像内容"""
        print_step("处理图像内容")
        
        # 模拟图像处理（实际应用中会使用计算机视觉模型）
        analysis = {
            "type": "image",
            "format": format,
            "size": len(image_data),
            "description": self._describe_image(image_data),
            "objects": self._detect_objects(image_data),
            "scenes": self._detect_scenes(image_data),
            "colors": self._analyze_colors(image_data),
            "text_content": self._extract_text_from_image(image_data),
            "metadata": metadata or {}
        }
        
        return analysis
    
    def process_audio(self, audio_data: bytes, format: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理音频内容"""
        print_step("处理音频内容")
        
        # 模拟音频处理（实际应用中会使用音频处理模型）
        analysis = {
            "type": "audio",
            "format": format,
            "size": len(audio_data),
            "duration": self._estimate_duration(audio_data),
            "transcription": self._transcribe_audio(audio_data),
            "speech_emotion": self._analyze_speech_emotion(audio_data),
            "speaker_count": self._detect_speakers(audio_data),
            "language": self._detect_audio_language(audio_data),
            "metadata": metadata or {}
        }
        
        return analysis
    
    def _detect_language(self, text: str) -> str:
        """检测文本语言"""
        # 简化的语言检测
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        if chinese_chars > len(text) * 0.3:
            return "zh"
        else:
            return "en"
    
    def _analyze_sentiment(self, text: str) -> str:
        """分析文本情感"""
        positive_words = ["好", "棒", "优秀", "perfect", "good", "great", "excellent"]
        negative_words = ["差", "糟糕", "不好", "bad", "terrible", "poor"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        words = text.split()
        # 过滤停用词
        stop_words = {'的', '是', '在', '有', '和', 'the', 'is', 'a', 'an', 'and'}
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        return keywords[:10]
    
    def _generate_summary(self, text: str) -> str:
        """生成文本摘要"""
        # 简单的摘要生成
        sentences = text.split('。')
        if len(sentences) <= 2:
            return text
        
        # 返回前两个句子作为摘要
        summary = '。'.join(sentences[:2]) + '。'
        return summary
    
    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """提取实体"""
        # 简化的实体提取
        entities = []
        
        # 查找可能的实体模式
        import re
        
        # 时间模式
        time_pattern = r'\d{4}年|\d{1,2}月|\d{1,2}日'
        times = re.findall(time_pattern, text)
        for time in times:
            entities.append({"type": "TIME", "value": time})
        
        # 数字模式
        number_pattern = r'\d+%'
        percentages = re.findall(number_pattern, text)
        for pct in percentages:
            entities.append({"type": "PERCENTAGE", "value": pct})
        
        return entities
    
    def _describe_image(self, image_data: bytes) -> str:
        """描述图像内容"""
        # 模拟图像描述
        return "这是一张包含丰富视觉元素的图像，可能包含人物、物体或场景。"
    
    def _detect_objects(self, image_data: bytes) -> List[str]:
        """检测图像中的物体"""
        # 模拟物体检测
        return ["人物", "建筑", "自然景观", "物品"]
    
    def _detect_scenes(self, image_data: bytes) -> List[str]:
        """检测图像场景"""
        # 模拟场景检测
        return ["室内", "室外", "城市", "自然"]
    
    def _analyze_colors(self, image_data: bytes) -> Dict[str, Any]:
        """分析图像颜色"""
        # 模拟颜色分析
        return {
            "dominant_colors": ["蓝色", "绿色", "红色"],
            "brightness": "中等",
            "contrast": "高"
        }
    
    def _extract_text_from_image(self, image_data: bytes) -> str:
        """从图像中提取文字"""
        # 模拟OCR
        return "图像中包含一些文字内容"
    
    def _estimate_duration(self, audio_data: bytes) -> float:
        """估计音频时长"""
        # 简化的时长估算
        size_mb = len(audio_data) / (1024 * 1024)
        # 假设压缩比为10:1，音频质量128kbps
        estimated_seconds = (size_mb * 8 * 1024 * 1024) / 128000
        return estimated_seconds
    
    def _transcribe_audio(self, audio_data: bytes) -> str:
        """音频转录"""
        # 模拟语音识别
        return "这是从音频中转录出的文本内容，包含了语音的主要信息。"
    
    def _analyze_speech_emotion(self, audio_data: bytes) -> str:
        """分析语音情感"""
        # 模拟情感分析
        return "neutral"
    
    def _detect_speakers(self, audio_data: bytes) -> int:
        """检测说话人数量"""
        # 模拟说话人检测
        return 1
    
    def _detect_audio_language(self, audio_data: bytes) -> str:
        """检测音频语言"""
        # 模拟语言检测
        return "zh"


class CrossModalAnalyzer:
    """跨模态分析器"""
    
    def __init__(self):
        self.llm = get_llm()
    
    def analyze_cross_modal(self, processed_media: Dict[str, Any]) -> Dict[str, Any]:
        """跨模态分析"""
        print_step("执行跨模态分析")
        
        # 收集各种媒体的分析结果
        media_types = []
        content_summary = []
        
        for media_id, analysis in processed_media.items():
            media_type = analysis.get("type", "unknown")
            media_types.append(media_type)
            
            if media_type == "text":
                summary = analysis.get("summary", "")
                content_summary.append(f"文本内容: {summary}")
            elif media_type == "image":
                description = analysis.get("description", "")
                objects = analysis.get("objects", [])
                content_summary.append(f"图像描述: {description}, 包含物体: {', '.join(objects)}")
            elif media_type == "audio":
                transcription = analysis.get("transcription", "")
                content_summary.append(f"音频转录: {transcription}")
        
        # 生成跨模态洞察
        cross_modal_insights = {
            "media_types": media_types,
            "content_summary": content_summary,
            "consistency_analysis": self._analyze_consistency(processed_media),
            "complementary_info": self._extract_complementary_info(processed_media),
            "overall_theme": self._identify_overall_theme(processed_media),
            "key_insights": self._generate_key_insights(processed_media)
        }
        
        return cross_modal_insights
    
    def _analyze_consistency(self, processed_media: Dict[str, Any]) -> Dict[str, Any]:
        """分析多模态内容的一致性"""
        consistency_score = 0.85  # 模拟一致性分数
        
        return {
            "score": consistency_score,
            "level": "high" if consistency_score > 0.7 else "medium" if consistency_score > 0.4 else "low",
            "conflicts": [],
            "agreements": ["主题一致", "情感相符"]
        }
    
    def _extract_complementary_info(self, processed_media: Dict[str, Any]) -> List[str]:
        """提取互补信息"""
        return [
            "图像提供了视觉上下文",
            "文本补充了详细信息",
            "音频传达了情感色彩"
        ]
    
    def _identify_overall_theme(self, processed_media: Dict[str, Any]) -> str:
        """识别整体主题"""
        # 简化的主题识别
        return "多模态内容展示了丰富的信息，各个模态相互补充，形成了完整的表达。"
    
    def _generate_key_insights(self, processed_media: Dict[str, Any]) -> List[str]:
        """生成关键洞察"""
        return [
            "多模态内容提供了更丰富的信息维度",
            "不同模态之间具有良好的互补性",
            "整体表达更加立体和完整"
        ]


class MultimodalAgent:
    """多模态AI代理"""
    
    def __init__(self):
        self.media_processor = MediaProcessor()
        self.cross_modal_analyzer = CrossModalAnalyzer()
        self.conversation_history = []
    
    def create_multimodal_workflow(self) -> StateGraph:
        """创建多模态工作流"""
        
        def media_preprocessing(state: MultimodalState) -> MultimodalState:
            """媒体预处理"""
            print_step("预处理输入媒体")
            
            input_media = state.get("input_media", [])
            processed_media = {}
            
            for i, media in enumerate(input_media):
                media_id = f"media_{i}"
                
                if media.is_text:
                    result = self.media_processor.process_text(media.content, media.metadata)
                elif media.is_image:
                    result = self.media_processor.process_image(media.content, media.format, media.metadata)
                elif media.is_audio:
                    result = self.media_processor.process_audio(media.content, media.format, media.metadata)
                else:
                    result = {"type": "unknown", "error": "不支持的媒体类型"}
                
                processed_media[media_id] = result
            
            return {
                **state,
                "processed_media": processed_media
            }
        
        def content_analysis(state: MultimodalState) -> MultimodalState:
            """内容分析"""
            print_step("深度分析内容")
            
            processed_media = state.get("processed_media", {})
            analysis_results = {}
            
            for media_id, analysis in processed_media.items():
                # 为每种媒体类型进行深度分析
                media_type = analysis.get("type", "unknown")
                
                if media_type == "text":
                    analysis_results[media_id] = self._deep_analyze_text(analysis)
                elif media_type == "image":
                    analysis_results[media_id] = self._deep_analyze_image(analysis)
                elif media_type == "audio":
                    analysis_results[media_id] = self._deep_analyze_audio(analysis)
            
            return {
                **state,
                "analysis_results": analysis_results
            }
        
        def cross_modal_integration(state: MultimodalState) -> MultimodalState:
            """跨模态整合"""
            print_step("跨模态信息整合")
            
            processed_media = state.get("processed_media", {})
            cross_modal_insights = self.cross_modal_analyzer.analyze_cross_modal(processed_media)
            
            return {
                **state,
                "cross_modal_insights": cross_modal_insights
            }
        
        def response_generation(state: MultimodalState) -> MultimodalState:
            """生成最终响应"""
            print_step("生成多模态响应")
            
            processed_media = state.get("processed_media", {})
            analysis_results = state.get("analysis_results", {})
            cross_modal_insights = state.get("cross_modal_insights", {})
            
            # 构建综合响应
            response_parts = []
            
            # 媒体类型概览
            media_types = cross_modal_insights.get("media_types", [])
            response_parts.append(f"📊 处理了 {len(media_types)} 种媒体类型: {', '.join(media_types)}")
            
            # 各媒体分析结果
            for media_id, analysis in processed_media.items():
                media_type = analysis.get("type", "unknown")
                if media_type == "text":
                    summary = analysis.get("summary", "")
                    response_parts.append(f"📝 文本分析: {summary}")
                elif media_type == "image":
                    description = analysis.get("description", "")
                    response_parts.append(f"🖼️ 图像分析: {description}")
                elif media_type == "audio":
                    transcription = analysis.get("transcription", "")
                    response_parts.append(f"🎵 音频转录: {transcription}")
            
            # 跨模态洞察
            overall_theme = cross_modal_insights.get("overall_theme", "")
            response_parts.append(f"🔍 整体洞察: {overall_theme}")
            
            # 关键洞察
            key_insights = cross_modal_insights.get("key_insights", [])
            if key_insights:
                response_parts.append("💡 关键发现:")
                for insight in key_insights:
                    response_parts.append(f"   • {insight}")
            
            final_response = "\n\n".join(response_parts)
            
            # 计算置信度
            confidence = self._calculate_overall_confidence(processed_media, cross_modal_insights)
            
            return {
                **state,
                "final_response": final_response,
                "confidence": confidence
            }
        
        # 构建工作流
        workflow = StateGraph(MultimodalState)
        
        # 添加节点
        workflow.add_node("media_preprocessing", media_preprocessing)
        workflow.add_node("content_analysis", content_analysis)
        workflow.add_node("cross_modal_integration", cross_modal_integration)
        workflow.add_node("response_generation", response_generation)
        
        # 添加边
        workflow.add_edge(START, "media_preprocessing")
        workflow.add_edge("media_preprocessing", "content_analysis")
        workflow.add_edge("content_analysis", "cross_modal_integration")
        workflow.add_edge("cross_modal_integration", "response_generation")
        workflow.add_edge("response_generation", END)
        
        # 使用内存检查点
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    def _deep_analyze_text(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """深度文本分析"""
        return {
            **analysis,
            "readability_score": 0.8,
            "complexity_level": "medium",
            "topic_relevance": 0.9
        }
    
    def _deep_analyze_image(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """深度图像分析"""
        return {
            **analysis,
            "visual_complexity": "high",
            "aesthetic_score": 0.75,
            "content_quality": 0.85
        }
    
    def _deep_analyze_audio(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """深度音频分析"""
        return {
            **analysis,
            "audio_quality": "good",
            "speech_clarity": 0.8,
            "emotional_expression": "neutral"
        }
    
    def _calculate_overall_confidence(self, processed_media: Dict[str, Any], cross_modal_insights: Dict[str, Any]) -> float:
        """计算整体置信度"""
        base_confidence = 0.7
        
        # 基于媒体数量
        media_count = len(processed_media)
        if media_count >= 3:
            base_confidence += 0.1
        
        # 基于一致性分析
        consistency = cross_modal_insights.get("consistency_analysis", {})
        consistency_score = consistency.get("score", 0.5)
        base_confidence += consistency_score * 0.2
        
        return min(base_confidence, 1.0)
    
    def process_multimodal_input(self, media_inputs: List[MediaContent]) -> Dict[str, Any]:
        """处理多模态输入"""
        workflow = self.create_multimodal_workflow()
        
        initial_state = {
            "input_media": media_inputs,
            "processed_media": {},
            "analysis_results": {},
            "cross_modal_insights": {},
            "final_response": "",
            "confidence": 0.0,
            "metadata": {"timestamp": datetime.now().isoformat()}
        }
        
        # 运行工作流
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        result = workflow.invoke(initial_state, config=config)
        
        # 保存到对话历史
        self.conversation_history.append({
            "input_media_count": len(media_inputs),
            "media_types": [m.media_type for m in media_inputs],
            "response": result.get("final_response", ""),
            "confidence": result.get("confidence", 0.0),
            "timestamp": datetime.now().isoformat()
        })
        
        return result


def print_step(step: str):
    """打印步骤信息"""
    print(f"🎨 {step}")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)


def demo_multimodal_agent():
    """演示多模态代理"""
    print("🎨 多模态AI代理演示")
    print("=" * 60)
    
    # 创建多模态代理
    agent = MultimodalAgent()
    
    # 准备测试数据
    test_cases = [
        {
            "name": "纯文本输入",
            "media": [
                MediaContent(
                    content="LangGraph是一个强大的AI工作流框架，它让开发者能够构建复杂的智能应用。通过图形化的方式定义节点和边，可以实现清晰的可视化工作流设计。",
                    media_type="text",
                    format="plain"
                )
            ]
        },
        {
            "name": "图文混合输入",
            "media": [
                MediaContent(
                    content="这张图片展示了LangGraph的工作流架构图。",
                    media_type="text",
                    format="plain"
                ),
                MediaContent(
                    content=b"fake_image_data_for_demo",  # 模拟图像数据
                    media_type="image",
                    format="jpeg",
                    metadata={"description": "LangGraph架构图"}
                )
            ]
        },
        {
            "name": "全模态输入",
            "media": [
                MediaContent(
                    content="这是一个包含文本、图像和音频的多模态示例。",
                    media_type="text",
                    format="plain"
                ),
                MediaContent(
                    content=b"fake_image_data_for_demo",
                    media_type="image",
                    format="png"
                ),
                MediaContent(
                    content=b"fake_audio_data_for_demo",
                    media_type="audio",
                    format="wav"
                )
            ]
        }
    ]
    
    # 执行测试
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🎯 测试案例 {i}: {test_case['name']}")
        print("=" * 40)
        
        # 处理多模态输入
        result = agent.process_multimodal_input(test_case['media'])
        
        # 显示结果
        final_response = result.get("final_response", "")
        confidence = result.get("confidence", 0.0)
        processed_media = result.get("processed_media", {})
        
        print(f"🤖 分析结果:")
        print(final_response)
        print(f"\n📊 置信度: {confidence:.1%}")
        print(f"📁 处理的媒体: {len(processed_media)} 种")
        
        # 显示详细分析
        for media_id, analysis in processed_media.items():
            media_type = analysis.get("type", "unknown")
            print(f"   • {media_type}: {analysis.get('format', 'unknown')}")
    
    print(f"\n📈 对话历史: {len(agent.conversation_history)} 次交互")


if __name__ == "__main__":
    try:
        demo_multimodal_agent()
        print("\n✅ 多模态代理演示完成！")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()