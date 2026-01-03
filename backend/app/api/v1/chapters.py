"""
章节管理 API
提供章节的 CRUD 操作

核心逻辑:
1. 保存: HTML -> HtmlParser -> Content + StyleSheet JSON
2. 回显: Content + StyleSheet JSON -> HtmlRenderer -> HTML
3. AI 修改: 修改 JSON -> HtmlRenderer -> 新 HTML
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.core.database import get_db
from app.models.database import Chapter
from app.models.schemas import (
    ChapterCreate,
    ChapterUpdate,
    ChapterBase,
    ChapterDetail,
    ChapterHtmlResponse,
    MessageResponse
)
from app.models.content_models import Content, StyleSheet
from app.services.html_parser import HtmlParser
from app.services.wangeditor_renderer import WangEditorRenderer  # 使用 WangEditor 兼容渲染器


router = APIRouter(prefix="/api/v1/chapters", tags=["chapters"])


@router.post("", response_model=ChapterBase, status_code=201)
def create_chapter(
    chapter_in: ChapterCreate,
    db: Session = Depends(get_db)
):
    """
    创建新章节
    
    流程:
    1. 接收前端传来的 HTML
    2. 使用 HtmlParser 解析为 Content + StyleSheet
    3. 同时保存原始 HTML 和解析后的 JSON
    
    Args:
        chapter_in: 章节创建数据(包含 HTML)
        db: 数据库会话
        
    Returns:
        创建的章节基础信息
    """
    # 使用新版解析器解析 HTML
    parser = HtmlParser(chapter_in.html_content)
    content, stylesheet = parser.parse()
    
    # 创建章节记录
    db_chapter = Chapter(
        id=str(uuid.uuid4()),
        doc_id=chapter_in.doc_id,
        title=chapter_in.title,
        html_content=chapter_in.html_content,  # 保存原始 HTML(备份用)
        content=content.model_dump(),  # 结构化数据(用于 AI 处理)
        stylesheet=stylesheet.model_dump(),  # 样式数据(独立存储)
        order_index=chapter_in.order_index
    )
    
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)
    
    return db_chapter


@router.get("/{chapter_id}", response_model=ChapterHtmlResponse)
def get_chapter(
    chapter_id: str,
    db: Session = Depends(get_db)
):
    """
    获取章节详情(返回从 JSON 重新生成的 HTML)
    
    流程:
    1. 从数据库读取 Content + StyleSheet JSON
    2. 使用 HtmlRenderer 渲染为 HTML
    3. 返回给前端编辑器
    
    优势:
    - AI 可以修改 JSON 数据
    - 修改后自动重新渲染
    - 保证数据与样式分离
    
    Args:
        chapter_id: 章节 ID
        db: 数据库会话
        
    Returns:
        章节信息(包含从 JSON 渲染的 HTML)
    """
    # 查询章节
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    # 从 JSON 重新生成 HTML (AI 修改后必须重新渲染)
    try:
        # 将字典转换为 Pydantic 模型
        content = Content(**chapter.content)
        stylesheet = StyleSheet(**chapter.stylesheet)
        
        # 使用 WangEditor 兼容渲染器生成 HTML
        renderer = WangEditorRenderer(content, stylesheet)
        html_content = renderer.render()
        
        print(f"✅ 成功从 JSON 渲染 HTML,长度: {len(html_content)}")
        
    except Exception as e:
        # 如果渲染失败,降级使用原始 HTML
        print(f"❌ 渲染失败,使用原始 HTML: {e}")
        import traceback
        traceback.print_exc()
        html_content = chapter.html_content or ""
    
    # 构建响应
    return ChapterHtmlResponse(
        id=chapter.id,
        doc_id=chapter.doc_id,
        title=chapter.title,
        order_index=chapter.order_index,
        created_at=chapter.created_at,
        updated_at=chapter.updated_at,
        html_content=html_content
    )


@router.get("/{chapter_id}/json", response_model=ChapterDetail)
def get_chapter_json(
    chapter_id: str,
    db: Session = Depends(get_db)
):
    """
    获取章节的 JSON 数据(Content 和 StyleSheet)
    
    用途:
    1. AI 处理章节内容
    2. 调试和查看结构化数据
    3. 高级编辑功能
    
    Args:
        chapter_id: 章节 ID
        db: 数据库会话
        
    Returns:
        章节详细信息(包含 Content 和 StyleSheet JSON)
    """
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    return ChapterDetail(
        id=chapter.id,
        doc_id=chapter.doc_id,
        title=chapter.title,
        order_index=chapter.order_index,
        created_at=chapter.created_at,
        updated_at=chapter.updated_at,
        content=chapter.content,
        stylesheet=chapter.stylesheet
    )


@router.put("/{chapter_id}", response_model=ChapterBase)
def update_chapter(
    chapter_id: str,
    chapter_in: ChapterUpdate,
    db: Session = Depends(get_db)
):
    """
    更新章节
    
    支持两种更新方式:
    1. 传递 HTML: 重新解析为 JSON
    2. 直接修改 JSON: 通过其他 API(如 AI 修改接口)
    
    Args:
        chapter_id: 章节 ID
        chapter_in: 更新数据
        db: 数据库会话
        
    Returns:
        更新后的章节信息
    """
    # 查询章节
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    # 如果有新的 HTML 内容,重新解析
    if chapter_in.html_content is not None:
        parser = HtmlParser(chapter_in.html_content)
        content, stylesheet = parser.parse()
        
        chapter.html_content = chapter_in.html_content
        chapter.content = content.model_dump()
        chapter.stylesheet = stylesheet.model_dump()
    
    # 更新其他字段
    if chapter_in.title is not None:
        chapter.title = chapter_in.title
    
    if chapter_in.order_index is not None:
        chapter.order_index = chapter_in.order_index
    
    db.commit()
    db.refresh(chapter)
    
    return chapter


@router.delete("/{chapter_id}", response_model=MessageResponse)
def delete_chapter(
    chapter_id: str,
    db: Session = Depends(get_db)
):
    """
    删除章节
    
    Args:
        chapter_id: 章节 ID
        db: 数据库会话
        
    Returns:
        删除成功消息
    """
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    db.delete(chapter)
    db.commit()
    
    return MessageResponse(
        message=f"章节 '{chapter.title}' 已删除",
        success=True
    )


@router.get("", response_model=List[ChapterBase])
def list_chapters(
    doc_id: str = None,
    db: Session = Depends(get_db)
):
    """
    获取章节列表
    
    Args:
        doc_id: 文档 ID(可选,用于筛选)
        db: 数据库会话
        
    Returns:
        章节列表
    """
    query = db.query(Chapter)
    
    # 如果指定了文档 ID,进行筛选
    if doc_id:
        query = query.filter(Chapter.doc_id == doc_id)
    
    # 按排序索引排序
    chapters = query.order_by(Chapter.order_index.asc()).all()
    
    return chapters
