"""
AI 章节处理 API
提供基于 AI 的章节内容修改功能

核心功能:
1. 直接修改章节的 Content JSON
2. 自动重新渲染为 HTML
3. 支持批量修改多个 Block
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid

from app.core.database import get_db
from app.models.database import Chapter
from app.models.content_models import Content, StyleSheet, Block
from app.services.wangeditor_renderer import WangEditorRenderer  # 使用 WangEditor 兼容渲染器


router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


class ContentUpdateRequest(BaseModel):
    """直接更新 Content JSON 的请求模型"""
    content: Dict[str, Any] = Field(..., description="新的 Content JSON")
    stylesheet: Optional[Dict[str, Any]] = Field(None, description="新的 StyleSheet JSON(可选)")


class BlockUpdateRequest(BaseModel):
    """更新单个 Block 的请求模型"""
    block_id: str = Field(..., description="要更新的 Block ID")
    updates: Dict[str, Any] = Field(..., description="要更新的字段")


class BatchBlockUpdateRequest(BaseModel):
    """批量更新 Block 的请求模型"""
    updates: List[BlockUpdateRequest] = Field(..., description="Block 更新列表")


@router.put("/chapters/{chapter_id}/content")
def update_chapter_content(
    chapter_id: str,
    request: ContentUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    直接更新章节的 Content 和 StyleSheet JSON
    
    用途:
    1. AI 修改章节内容后直接更新 JSON
    2. 批量修改多个 Block
    3. 高级编辑功能
    
    流程:
    1. 接收新的 Content + StyleSheet JSON
    2. 验证 JSON 格式
    3. 保存到数据库
    4. 重新渲染为 HTML 并更新
    
    Args:
        chapter_id: 章节 ID
        request: 包含新 Content 和 StyleSheet 的请求
        db: 数据库会话
        
    Returns:
        更新后的章节信息
    """
    # 查询章节
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    try:
        # 验证并转换为 Pydantic 模型
        content = Content(**request.content)
        
        # 如果提供了新的 stylesheet,使用新的;否则保留原有的
        if request.stylesheet:
            stylesheet = StyleSheet(**request.stylesheet)
        else:
            stylesheet = StyleSheet(**chapter.stylesheet)
        
        # 使用 WangEditor 兼容渲染器生成新的 HTML
        renderer = WangEditorRenderer(content, stylesheet)
        new_html = renderer.render()
        
        # 更新数据库
        chapter.content = content.model_dump()
        chapter.stylesheet = stylesheet.model_dump()
        chapter.html_content = new_html
        
        db.commit()
        db.refresh(chapter)
        
        return {
            "success": True,
            "message": "章节内容已更新",
            "chapter_id": chapter.id,
            "html_preview": new_html[:200] + "..." if len(new_html) > 200 else new_html
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"更新失败: {str(e)}"
        )


@router.patch("/chapters/{chapter_id}/blocks")
def update_chapter_blocks(
    chapter_id: str,
    request: BatchBlockUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    批量更新章节中的特定 Block
    
    用途:
    1. AI 修改特定段落的文本
    2. 批量调整样式
    3. 精确修改表格单元格内容
    
    流程:
    1. 读取当前 Content JSON
    2. 根据 block_id 定位并更新指定的 Block
    3. 重新渲染为 HTML
    4. 保存到数据库
    
    Args:
        chapter_id: 章节 ID
        request: 包含 Block 更新列表的请求
        db: 数据库会话
        
    Returns:
        更新结果
    """
    # 查询章节
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    try:
        # 解析当前 Content
        content = Content(**chapter.content)
        stylesheet = StyleSheet(**chapter.stylesheet)
        
        # 创建 block_id 到 block 的映射
        block_map = {block.id: block for block in content.blocks}
        
        # 应用更新
        updated_count = 0
        for update_req in request.updates:
            if update_req.block_id in block_map:
                block = block_map[update_req.block_id]
                
                # 更新 Block 的字段
                for key, value in update_req.updates.items():
                    if hasattr(block, key):
                        setattr(block, key, value)
                        updated_count += 1
        
        # 重新渲染 HTML
        renderer = WangEditorRenderer(content, stylesheet)
        new_html = renderer.render()
        
        # 更新数据库
        chapter.content = content.model_dump()
        chapter.html_content = new_html
        
        db.commit()
        db.refresh(chapter)
        
        return {
            "success": True,
            "message": f"成功更新 {updated_count} 个字段",
            "chapter_id": chapter.id,
            "updated_blocks": len(request.updates)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"更新失败: {str(e)}"
        )


@router.post("/chapters/{chapter_id}/ai-enhance")
def ai_enhance_chapter(
    chapter_id: str,
    db: Session = Depends(get_db)
):
    """
    AI 增强章节内容(示例接口)
    
    这是一个示例接口,展示如何集成 AI 功能
    实际使用时需要接入真实的 AI 服务
    
    功能示例:
    1. 自动润色文本
    2. 优化段落结构
    3. 生成摘要
    4. 翻译内容
    
    Args:
        chapter_id: 章节 ID
        db: 数据库会话
        
    Returns:
        AI 处理结果
    """
    # 查询章节
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    try:
        # 解析 Content
        content = Content(**chapter.content)
        
        # TODO: 这里接入真实的 AI 服务
        # 示例: 将所有段落文本转为大写(仅作演示)
        for block in content.blocks:
            if hasattr(block, 'text'):
                # 这里可以调用 AI API 进行文本处理
                # block.text = ai_service.enhance(block.text)
                pass
        
        return {
            "success": True,
            "message": "AI 增强完成(示例)",
            "chapter_id": chapter.id,
            "note": "这是一个示例接口,需要接入真实的 AI 服务"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"AI 处理失败: {str(e)}"
        )


@router.get("/chapters/{chapter_id}/structure")
def get_chapter_structure(
    chapter_id: str,
    db: Session = Depends(get_db)
):
    """
    获取章节的结构化信息
    
    用途:
    1. AI 分析章节结构
    2. 生成目录
    3. 内容摘要
    
    Args:
        chapter_id: 章节 ID
        db: 数据库会话
        
    Returns:
        章节结构信息
    """
    # 查询章节
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    try:
        # 解析 Content
        content = Content(**chapter.content)
        
        # 提取结构信息
        structure = {
            "total_blocks": len(content.blocks),
            "block_types": {},
            "headings": [],
            "paragraphs_count": 0,
            "tables_count": 0,
            "images_count": 0,
            "total_text_length": 0
        }
        
        for block in content.blocks:
            # 统计 Block 类型
            block_type = block.type
            structure["block_types"][block_type] = structure["block_types"].get(block_type, 0) + 1
            
            # 提取标题
            if block.type == "heading":
                structure["headings"].append({
                    "level": block.level,
                    "text": block.text,
                    "id": block.id
                })
            
            # 统计各类型数量
            if block.type == "paragraph":
                structure["paragraphs_count"] += 1
            elif block.type == "table":
                structure["tables_count"] += 1
            elif block.type == "image":
                structure["images_count"] += 1
            
            # 统计文本长度
            if hasattr(block, 'text'):
                structure["total_text_length"] += len(block.text)
        
        return {
            "success": True,
            "chapter_id": chapter.id,
            "structure": structure
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"分析失败: {str(e)}"
        )
