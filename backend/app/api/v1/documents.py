"""
文档管理 API
提供文档的 CRUD 操作
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.core.database import get_db
from app.models.database import Document, Chapter
from app.models.schemas import (
    DocumentCreate,
    DocumentUpdate,
    DocumentBase,
    DocumentWithChapters,
    DocumentListResponse,
    ChapterBase,
    MessageResponse
)
from app.models.params import PaginationParams
from app.models.responses import paginated_response


router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("", response_model=DocumentBase, status_code=201)
def create_document(
    doc_in: DocumentCreate,
    db: Session = Depends(get_db)
):
    """
    创建新文档
    
    Args:
        doc_in: 文档创建数据
        db: 数据库会话
        
    Returns:
        创建的文档信息
    """
    db_doc = Document(
        id=str(uuid.uuid4()),
        title=doc_in.title
    )
    
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    return db_doc


@router.get("/{doc_id}", response_model=DocumentWithChapters)
def get_document(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    获取文档详情（包含章节列表）
    
    Args:
        doc_id: 文档 ID
        db: 数据库会话
        
    Returns:
        文档信息及其章节列表
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 获取排序后的章节
    # 获取排序后的章节
    # 使用 chapters 模块中的 build_chapter_tree 进行树形排序
    from app.api.v1.chapters import build_chapter_tree
    
    raw_chapters = db.query(Chapter).filter(
        Chapter.doc_id == doc_id
    ).all()
    
    sorted_chapters = build_chapter_tree(raw_chapters)
    
    return DocumentWithChapters(
        id=doc.id,
        title=doc.title,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        chapters=[
            ChapterBase(
                id=c.id,
                doc_id=c.doc_id,
                title=c.title,
                order_index=c.order_index,
                level=c.level,
                parent_id=c.parent_id,
                created_at=c.created_at,
                updated_at=c.updated_at
            )
            for c in sorted_chapters
        ]
    )


@router.put("/{doc_id}", response_model=DocumentBase)
def update_document(
    doc_id: str,
    doc_in: DocumentUpdate,
    db: Session = Depends(get_db)
):
    """
    更新文档
    
    Args:
        doc_id: 文档 ID
        doc_in: 更新数据
        db: 数据库会话
        
    Returns:
        更新后的文档信息
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    if doc_in.title is not None:
        doc.title = doc_in.title
    
    db.commit()
    db.refresh(doc)
    
    return doc


@router.delete("/{doc_id}", response_model=MessageResponse)
def delete_document(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    删除文档（级联删除所有章节）
    
    Args:
        doc_id: 文档 ID
        db: 数据库会话
        
    Returns:
        删除成功消息
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    db.delete(doc)
    db.commit()
    
    return MessageResponse(
        message=f"文档 '{doc.title}' 及其所有章节已删除",
        success=True
    )


@router.get("", response_model=DocumentListResponse)
def list_documents(
    page: int = Query(1, ge=1, le=10000, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    获取文档列表（分页）
    
    Args:
        page: 页码（从 1 开始）
        page_size: 每页记录数(1-100)
        db: 数据库会话
        
    Returns:
        分页的文档列表
    """
    # 验证分页参数
    pagination = PaginationParams(page=page, size=page_size)
    
    # 计算偏移量
    offset = pagination.get_offset()
    limit = pagination.get_limit()
    
    # 查询总数
    total = db.query(Document).count()
    
    # 查询文档列表
    docs = db.query(Document).offset(offset).limit(limit).all()
    
    # 为每个文档查询章节
    # 为每个文档查询章节
    # 延迟导入以避免循环依赖
    from app.api.v1.chapters import build_chapter_tree

    items = []
    for doc in docs:
        raw_chapters = db.query(Chapter).filter(
            Chapter.doc_id == doc.id
        ).all()
        
        sorted_chapters = build_chapter_tree(raw_chapters)
        
        items.append(DocumentWithChapters(
            id=doc.id,
            title=doc.title,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            chapters=[
                ChapterBase(
                    id=c.id,
                    doc_id=c.doc_id,
                    title=c.title,
                    order_index=c.order_index,
                    level=c.level,
                    parent_id=c.parent_id,
                    created_at=c.created_at,
                    updated_at=c.updated_at
                )
                for c in sorted_chapters
            ]
        ))
    
    return DocumentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )
