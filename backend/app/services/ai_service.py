"""
AI 编辑服务
提供 AI 辅助写作功能
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import json
import httpx
import logging
import time
from app.core.config import settings

# 配置日志
logger = logging.getLogger(__name__)


class AIEditRequest(BaseModel):
    """AI 编辑请求"""
    action: str = Field(..., description="操作类型: rewrite(重写), improve(改进), expand(扩展), summarize(总结), translate(翻译)")
    text: str = Field(..., description="要处理的文本")
    context: Optional[str] = Field(None, description="上下文信息")
    language: str = Field(default="zh", description="目标语言")
    style: Optional[str] = Field(None, description="写作风格: formal(正式), casual(随意), professional(专业)")


class AIEditResponse(BaseModel):
    """AI 编辑响应"""
    success: bool
    original_text: str
    edited_text: str
    action: str
    suggestions: Optional[List[str]] = None


class AIService:
    """
    AI 服务类
    
    使用 OpenAI 兼容格式，支持多种 AI 服务:
    - OpenAI GPT
    - Azure OpenAI
    - DeepSeek
    - 通义千问
    - 文心一言
    等
    """
    
    def __init__(self):
        """初始化 AI 服务"""
        self.api_key = settings.AI_API_KEY
        self.base_url = settings.AI_BASE_URL
        self.model = settings.AI_MODEL
        self.max_tokens = settings.AI_MAX_TOKENS
        self.temperature = settings.AI_TEMPERATURE
        self.timeout = settings.AI_TIMEOUT
        
        # 检查是否配置了 API 密钥
        self.enabled = bool(self.api_key and self.api_key != "your_api_key_here" and self.api_key.strip())
        
        if not self.enabled:
            logger.warning("AI 服务未配置: 缺少有效 API Key")
        else:
            logger.info(f"AI 服务已初始化: Model={self.model}")
        

    
    def _build_prompt(self, action: str, text: str, context: Optional[str] = None, style: Optional[str] = None) -> str:
        """
        构建提示词
        
        Args:
            action: 操作类型
            text: 要处理的文本
            context: 上下文
            style: 写作风格
            
        Returns:
            提示词
        """
        prompts = {
            "rewrite": f"请重写以下文本，使其更加清晰流畅，保持原意但改变表达方式：\n\n{text}",
            "improve": f"请改进以下文本，提升表达质量、准确性和专业性：\n\n{text}",
            "expand": f"请扩展以下文本，添加更多细节、例子和说明，使内容更加丰富：\n\n{text}",
            "summarize": f"请总结以下文本的核心要点，提炼关键信息：\n\n{text}",
            "translate": f"请将以下文本翻译成中文，保持原文的语气和风格：\n\n{text}",
            "polish": f"请润色以下文本，使语言更加优雅、流畅、有文采：\n\n{text}",
            "simplify": f"请简化以下文本，使其更加通俗易懂，适合普通读者阅读：\n\n{text}",
        }
        
        if action == "custom":
            # 如果是自定义操作，style 字段被复用为用户指令
            instruction = style if style else "请处理以下文本"
            base_prompt = f"{instruction}：\n\n{text}"
        else:
            base_prompt = prompts.get(action, f"请处理以下文本：\n\n{text}")
        
        # 添加上下文
        if context:
            base_prompt = f"上下文：{context}\n\n{base_prompt}"
        
        # 添加风格要求
        if style:
            style_desc = {
                "formal": "请使用正式、严谨的语言风格",
                "casual": "请使用轻松、随意的语言风格",
                "professional": "请使用专业、权威的语言风格"
            }
            if style in style_desc:
                base_prompt += f"\n\n{style_desc[style]}"
        
        return base_prompt
    
    async def edit_text_stream(self, request: AIEditRequest):
        """
        流式生成编辑内容 (SSE)
        """
        start_time = time.time()
        logger.info(f"AI Stream Request: action={request.action}, text_len={len(request.text)}")
        
        if not self.enabled:
            # 模拟流式输出
            logger.warning("AI Disabled, using mock response")
            mock_text = "AI 服务未配置。请在 .env 文件中配置 AI_API_KEY 以启用真实服务。" # ...
            # (keep mock logic same or simplify, but user didn't ask to change mock)
            import asyncio
            for char in mock_text:
                yield f"data: {json.dumps({'text': char, 'finish_reason': None})}\n\n"
                await asyncio.sleep(0.05)
            yield f"data: {json.dumps({'text': '', 'finish_reason': 'stop'})}\n\n"
            return
            
        prompt = self._build_prompt(request.action, request.text, request.context, request.style)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "你是一个专业的写作助手。请直接输出结果。"},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": self.max_tokens,
                        "temperature": self.temperature,
                        "stream": True
                    }
                ) as response:
                    if response.status_code != 200:
                        error_msg = await response.aread()
                        logger.error(f"AI API Error {response.status_code}: {error_msg}")
                        yield f"data: {json.dumps({'error': f'API Error: {response.status_code}'})}\n\n"
                        return

                    chunk_count = 0
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                yield f"data: {json.dumps({'text': '', 'finish_reason': 'stop'})}\n\n"
                                break
                            try:
                                data = json.loads(data_str)
                                delta = data["choices"][0]["delta"]
                                content = delta.get("content", "")
                                if content:
                                    chunk_count += 1
                                    yield f"data: {json.dumps({'text': content, 'finish_reason': None})}\n\n"
                            except Exception:
                                continue
                                
                    duration = time.time() - start_time
                    logger.info(f"AI Stream Success: chars={chunk_count}, duration={duration:.2f}s")
                    
        except Exception as e:
            logger.error(f"AI Stream Exception: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    
    async def generate_continuation(
        self, 
        context: str, 
        length: int = 200
    ) -> str:
        """
        生成续写内容
        
        Args:
            context: 上下文
            length: 生成长度
            
        Returns:
            生成的文本
            
        Raises:
            Exception: 当 AI 服务未配置或调用失败时
        """
        if not self.enabled:
            raise Exception("AI 服务未配置，无法生成续写内容")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个专业的写作助手，擅长续写内容。请基于上下文生成连贯的续写内容。"
                        },
                        {
                            "role": "user",
                            "content": f"请基于以下内容续写约{length}字：\n\n{context}"
                        }
                    ],
                    "max_tokens": length * 2,
                    "temperature": 0.8
                }
            )
        
        if response.status_code != 200:
            raise Exception(f"AI API 调用失败 (HTTP {response.status_code}): {response.text}")
        
        try:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, ValueError) as e:
            raise Exception(f"AI API 响应格式错误: {str(e)}")
    



# 全局 AI 服务实例
ai_service = AIService()
