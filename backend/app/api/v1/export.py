"""
导出功能 API
提供章节和文档的导出功能
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.database import Chapter, Document
from app.services.docx_exporter import DocxExporter


router = APIRouter(prefix="/api/v1/export", tags=["export"])


@router.get("/chapters/{chapter_id}/docx")
def export_chapter_to_docx(
    chapter_id: str,
    db: Session = Depends(get_db)
):
    """
    导出章节为 Word 文档
    
    Args:
        chapter_id: 章节 ID
        db: 数据库会话
        
    Returns:
        .docx 文件流
    """
    # 查询章节
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    # 创建导出器
    exporter = DocxExporter(chapter.content, chapter.stylesheet)
    file_stream = exporter.export()
    
    # 返回文件
    return Response(
        content=file_stream.read(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{chapter.title}.docx"'
        }
    )


@router.get("/documents/{doc_id}/docx")
def export_document_to_docx(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    导出整个文档为 Word 文件（合并所有章节）
    
    Args:
        doc_id: 文档 ID
        db: 数据库会话
        
    Returns:
        .docx 文件流
    """
    # 查询文档
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 查询所有章节（按顺序）
    chapters = db.query(Chapter).filter(
        Chapter.doc_id == doc_id
    ).order_by(Chapter.order_index.asc()).all()
    
    if not chapters:
        raise HTTPException(status_code=400, detail="文档没有章节")
    
    # 合并所有章节的 Content 和 StyleSheet
    merged_content = {"blocks": []}
    merged_stylesheet = {
        "styleId": f"merged-{doc_id}",
        "appliesTo": "document",
        "rules": []
    }
    
    for chapter in chapters:
        # 添加章节标题作为一级标题
        merged_content["blocks"].append({
            "id": f"chapter-title-{chapter.id}",
            "type": "heading",
            "level": 1,
            "text": chapter.title,
            "marks": []
        })
        
        # 合并章节内容
        chapter_blocks = chapter.content.get("blocks", [])
        merged_content["blocks"].extend(chapter_blocks)
        
        # 合并样式规则
        chapter_rules = chapter.stylesheet.get("rules", [])
        merged_stylesheet["rules"].extend(chapter_rules)
    
    # 创建导出器
    exporter = DocxExporter(merged_content, merged_stylesheet)
    file_stream = exporter.export()
    
    # 返回文件
    return Response(
        content=file_stream.read(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{doc.title}.docx"'
        }
    )
