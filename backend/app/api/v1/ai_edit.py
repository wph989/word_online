"""
AI 编辑 API
提供 AI 辅助写作的 REST API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from app.core.database import get_db
from app.models.database import Chapter
from app.services.ai_service import ai_service, AIEditRequest, AIEditResponse
from app.services.html_parser import HtmlParser
from app.services.wangeditor_renderer import WangEditorRenderer
from app.models.content_models import Content, StyleSheet


router = APIRouter(prefix="/api/v1/ai/edit", tags=["ai-edit"])


class TextEditRequest(BaseModel):
    """文本编辑请求"""
    text: str = Field(..., description="要编辑的文本")
    action: str = Field(..., description="操作类型")
    context: Optional[str] = Field(None, description="上下文")
    style: Optional[str] = Field(None, description="写作风格")


class SelectionEditRequest(BaseModel):
    """选区编辑请求"""
    chapter_id: str = Field(..., description="章节 ID")
    block_id: str = Field(..., description="Block ID")
    selection_start: int = Field(..., description="选区开始位置")
    selection_end: int = Field(..., description="选区结束位置")
    action: str = Field(..., description="操作类型")


class ContinuationRequest(BaseModel):
    """续写请求"""
    chapter_id: str = Field(..., description="章节 ID")
    context_length: int = Field(default=500, description="上下文长度")
    length: int = Field(default=200, description="生成长度")


@router.post("/text", response_model=AIEditResponse)
async def edit_text(request: TextEditRequest):
    """
    编辑文本
    
    支持的操作:
    - rewrite: 重写
    - improve: 改进
    - expand: 扩展
    - summarize: 总结
    - translate: 翻译
    - polish: 润色
    - simplify: 简化
    """
    ai_request = AIEditRequest(
        action=request.action,
        text=request.text,
        context=request.context,
        style=request.style
    )
    
    result = await ai_service.edit_text(ai_request)
    return result
    
    
@router.post("/stream/text")
async def stream_edit_text(request: TextEditRequest):
    """
    流式编辑文本 (SSE)
    """
    from fastapi.responses import StreamingResponse
    
    ai_request = AIEditRequest(
        action=request.action,
        text=request.text,
        context=request.context,
        style=request.style
    )
    
    return StreamingResponse(
        ai_service.edit_text_stream(ai_request),
        media_type="text/event-stream"
    )


@router.post("/selection")
async def edit_selection(
    request: SelectionEditRequest,
    db: Session = Depends(get_db)
):
    """
    编辑选中的文本
    
    流程:
    1. 获取章节内容
    2. 定位到指定 Block
    3. 提取选中的文本
    4. 使用 AI 编辑
    5. 更新 Block
    6. 重新渲染 HTML
    """
    # 获取章节
    chapter = db.query(Chapter).filter(Chapter.id == request.chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    # 解析 Content
    content = Content(**chapter.content)
    
    # 查找 Block
    target_block = None
    for block in content.blocks:
        if block.id == request.block_id:
            target_block = block
            break
    
    if not target_block:
        raise HTTPException(status_code=404, detail="Block 不存在")
    
    # 提取选中的文本
    if not hasattr(target_block, 'text'):
        raise HTTPException(status_code=400, detail="该 Block 不支持文本编辑")
    
    original_text = target_block.text
    selected_text = original_text[request.selection_start:request.selection_end]
    
    # 使用 AI 编辑
    ai_request = AIEditRequest(
        action=request.action,
        text=selected_text,
        context=original_text
    )
    ai_result = await ai_service.edit_text(ai_request)
    
    # 更新文本
    new_text = (
        original_text[:request.selection_start] +
        ai_result.edited_text +
        original_text[request.selection_end:]
    )
    target_block.text = new_text
    
    # 重新渲染
    stylesheet = StyleSheet(**chapter.stylesheet)
    renderer = WangEditorRenderer(content, stylesheet)
    new_html = renderer.render()
    
    # 保存
    chapter.content = content.model_dump()
    chapter.html_content = new_html
    db.commit()
    db.refresh(chapter)
    
    return {
        "success": True,
        "message": "编辑成功",
        "original_text": selected_text,
        "edited_text": ai_result.edited_text,
        "new_html": new_html
    }


@router.post("/continuation")
async def generate_continuation(
    request: ContinuationRequest,
    db: Session = Depends(get_db)
):
    """
    生成续写内容
    
    流程:
    1. 获取章节最后的内容作为上下文
    2. 使用 AI 生成续写
    3. 添加到章节末尾
    """
    # 获取章节
    chapter = db.query(Chapter).filter(Chapter.id == request.chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    # 获取上下文（最后的文本）
    content = Content(**chapter.content)
    context_text = ""
    
    # 从最后几个 Block 提取文本
    for block in reversed(content.blocks[-5:]):  # 最后 5 个 Block
        if hasattr(block, 'text') and block.text:
            context_text = block.text + "\n" + context_text
            if len(context_text) >= request.context_length:
                break
    
    # 生成续写
    continuation = await ai_service.generate_continuation(
        context=context_text,
        length=request.length
    )
    
    return {
        "success": True,
        "continuation": continuation,
        "context": context_text[:200] + "..."
    }





@router.get("/actions")
def get_available_actions():
    """获取可用的 AI 操作列表"""
    return {
        "actions": [
            {
                "id": "rewrite",
                "name": "重写",
                "description": "重新表述内容，使其更加清晰",
                "icon": "🔄"
            },
            {
                "id": "improve",
                "name": "改进",
                "description": "提升文本质量和表达",
                "icon": "✨"
            },
            {
                "id": "expand",
                "name": "扩展",
                "description": "添加更多细节和说明",
                "icon": "📝"
            },
            {
                "id": "summarize",
                "name": "总结",
                "description": "提炼核心要点",
                "icon": "📋"
            },
            {
                "id": "polish",
                "name": "润色",
                "description": "优化语言表达",
                "icon": "💎"
            },
            {
                "id": "simplify",
                "name": "简化",
                "description": "使内容更易理解",
                "icon": "🎯"
            },
            {
                "id": "translate",
                "name": "翻译",
                "description": "翻译成其他语言",
                "icon": "🌐"
            }
        ]
    }
