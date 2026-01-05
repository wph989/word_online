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
    ChapterMoveRequest,
    MessageResponse
)
from app.models.content_models import Content, StyleSheet
from app.services.html_parser import HtmlParser
from app.services.wangeditor_renderer import WangEditorRenderer  # 使用 WangEditor 兼容渲染器


router = APIRouter(prefix="/api/v1/chapters", tags=["chapters"])


def build_chapter_tree(chapters: List[Chapter], parent_id: str = None) -> List[Chapter]:
    """
    递归构建章节树，按层级和顺序排序
    
    Args:
        chapters: 所有章节列表
        parent_id: 父章节ID（None表示顶级章节）
        
    Returns:
        排序后的章节列表（深度优先遍历）
    """
    result = []
    
    # 找出当前层级的章节并按 order_index 排序
    current_level = [
        ch for ch in chapters 
        if ch.parent_id == parent_id
    ]
    current_level.sort(key=lambda x: x.order_index)
    
    # 递归添加每个章节及其子章节
    for chapter in current_level:
        result.append(chapter)
        # 递归添加子章节
        children = build_chapter_tree(chapters, chapter.id)
        result.extend(children)
    
    return result



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
        parent_id=chapter_in.parent_id,  # 父章节ID
        level=chapter_in.level,  # 章节层级
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
        level=chapter.level,
        parent_id=chapter.parent_id,
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
    
    if chapter_in.parent_id is not None:
        chapter.parent_id = chapter_in.parent_id
    
    if chapter_in.level is not None:
        chapter.level = chapter_in.level
    
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
        message=f"章节 '{chapter.title}' 及其子章节已删除",
        success=True
    )


@router.post("/{chapter_id}/move", response_model=ChapterBase)
def move_chapter(
    chapter_id: str,
    move_req: ChapterMoveRequest,
    db: Session = Depends(get_db)
):
    """
    移动/重排序章节
    """
    # 1. 获取目标章节
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    # 2. 验证新的父章节
    new_parent_id = move_req.new_parent_id
    new_level = 1
    
    if new_parent_id:
        if new_parent_id == chapter_id:
            raise HTTPException(status_code=400, detail="不能将章节移动到自己下面")
            
        new_parent = db.query(Chapter).filter(Chapter.id == new_parent_id).first()
        if not new_parent:
            raise HTTPException(status_code=404, detail="目标父章节不存在")
        
        # 检查是否移动到了自己的子孙章节下
        # 简单的循环检查（更严谨应该递归或使用 CTE，但此处假设层级不深）
        ancestor = new_parent
        while ancestor.parent_id:
            if ancestor.parent_id == chapter_id:
                raise HTTPException(status_code=400, detail="不能将章节移动到自己的子章节下")
            ancestor = db.query(Chapter).filter(Chapter.id == ancestor.parent_id).first()
            if not ancestor:
                break
                
        new_level = new_parent.level + 1

    # 3. 准备数据
    old_parent_id = chapter.parent_id
    old_index = chapter.order_index
    new_index = move_req.new_index
    
    # 4. 执行移动
    if old_parent_id == new_parent_id:
        # 情况 A: 同级重排序
        if new_index == old_index:
            return chapter # 无变化
            
        if new_index < old_index:
            # 向上移动：中间的兄弟向下挤 (+1)
            # 范围：[new_index, old_index - 1]
            db.query(Chapter).filter(
                Chapter.doc_id == chapter.doc_id,
                Chapter.parent_id == old_parent_id,
                Chapter.order_index >= new_index,
                Chapter.order_index < old_index
            ).update({Chapter.order_index: Chapter.order_index + 1}, synchronize_session=False)
        else:
            # 向下移动：中间的兄弟向上挤 (-1)
            # 范围：[old_index + 1, new_index]
            db.query(Chapter).filter(
                Chapter.doc_id == chapter.doc_id,
                Chapter.parent_id == old_parent_id,
                Chapter.order_index > old_index,
                Chapter.order_index <= new_index
            ).update({Chapter.order_index: Chapter.order_index - 1}, synchronize_session=False)
            
        chapter.order_index = new_index
        
    else:
        # 情况 B: 跨父级移动
        
        # B1. 从旧父级移除：旧兄弟填补空缺 (index > old_index 的都 -1)
        db.query(Chapter).filter(
            Chapter.doc_id == chapter.doc_id,
            Chapter.parent_id == old_parent_id,
            Chapter.order_index > old_index
        ).update({Chapter.order_index: Chapter.order_index - 1}, synchronize_session=False)
        
        # B2. 插入新父级：新兄弟腾出位置 (index >= new_index 的都 +1)
        db.query(Chapter).filter(
            Chapter.doc_id == chapter.doc_id,
            Chapter.parent_id == new_parent_id,
            Chapter.order_index >= new_index
        ).update({Chapter.order_index: Chapter.order_index + 1}, synchronize_session=False)
        
        # B3. 更新自身
        level_diff = new_level - chapter.level
        chapter.parent_id = new_parent_id
        chapter.order_index = new_index
        chapter.level = new_level
        
        # B4. 递归更新所有子孙章节的 level
        if level_diff != 0:
            def update_children_level(parent_id, diff):
                children = db.query(Chapter).filter(Chapter.parent_id == parent_id).all()
                for child in children:
                    child.level += diff
                    update_children_level(child.id, diff)
            
            update_children_level(chapter.id, level_diff)

    db.commit()
    db.refresh(chapter)
    return chapter


@router.get("", response_model=List[ChapterBase])
def list_chapters(
    doc_id: str = None,
    db: Session = Depends(get_db)
):
    """
    获取章节列表（按层级结构排序）
    
    返回的章节列表按照父子关系和 order_index 排序：
    - 先显示顶级章节（parent_id=NULL）
    - 每个章节后面紧跟其子章节
    - 同级章节按 order_index 排序
    
    Args:
        doc_id: 文档 ID(可选,用于筛选)
        db: 数据库会话
        
    Returns:
        章节列表（层级结构展开后的列表）
    """
    query = db.query(Chapter)
    
    # 如果指定了文档 ID,进行筛选
    if doc_id:
        query = query.filter(Chapter.doc_id == doc_id)
    
    # 获取所有章节
    all_chapters = query.all()
    
    # 使用递归函数构建层级树并展开为列表
    chapters = build_chapter_tree(all_chapters)
    
    return chapters
