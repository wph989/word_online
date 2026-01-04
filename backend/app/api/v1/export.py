"""
导出功能 API
提供章节和文档的 DOCX 导出功能

接口说明:
1. GET /api/v1/export/chapters/{chapter_id}/docx - 导出单个章节
2. GET /api/v1/export/documents/{doc_id}/docx - 导出整个文档(合并所有章节)
3. POST /api/v1/export/batch/docx - 批量导出多个章节
"""

from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging
from urllib.parse import quote

from app.core.database import get_db
from app.models.database import Chapter, Document, DocumentSettings
from app.services.docx_exporter import DocxExporter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/export", tags=["export"])


class BatchExportRequest(BaseModel):
    """批量导出请求"""
    chapter_ids: List[str]
    document_title: Optional[str] = "合并文档"


@router.get("/chapters/{chapter_id}/docx")
def export_chapter_to_docx(
    chapter_id: str,
    db: Session = Depends(get_db),
    include_title: bool = Query(True, description="是否在文档开头包含章节标题")
):
    """
    导出章节为 Word 文档（自动包含所有子章节）
    
    Args:
        chapter_id: 章节 ID
        db: 数据库会话
        include_title: 是否包含章节标题作为一级标题
        
    Returns:
        .docx 文件流
        
    Raises:
        404: 章节不存在
        500: 导出失败
    """
    try:
        # 查询章节
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail=f"章节不存在: {chapter_id}")
        
        logger.info(f"开始导出章节: {chapter.title} (ID: {chapter_id})")
        
        # 递归收集该章节及其所有子章节
        def collect_chapter_tree(parent_chapter):
            """递归收集章节及其子章节"""
            chapters = [parent_chapter]
            
            # 查询子章节（按 order_index 排序）
            children = db.query(Chapter).filter(
                Chapter.parent_id == parent_chapter.id
            ).order_by(Chapter.order_index.asc()).all()
            
            # 递归收集每个子章节
            for child in children:
                chapters.extend(collect_chapter_tree(child))
            
            return chapters
        
        # 收集所有章节（父章节 + 所有子孙章节）
        all_chapters = collect_chapter_tree(chapter)
        logger.info(f"收集到 {len(all_chapters)} 个章节（包含子章节）")
        
        # 合并所有章节的内容
        merged_content = {"blocks": []}
        merged_stylesheet = {
            "styleId": f"chapter-export-{chapter_id}",
            "appliesTo": "document",
            "rules": []
        }
        
        for idx, ch in enumerate(all_chapters):
            # 添加章节标题（根据层级调整标题级别）
            if include_title or idx > 0:  # 第一个章节根据参数决定，子章节总是包含标题
                # 计算标题级别：父章节用 level，子章节用 level+1（但不超过6）
                title_level = min(ch.level, 6)
                
                merged_content["blocks"].append({
                    "id": f"chapter-title-{ch.id}",
                    "type": "heading",
                    "level": title_level,
                    "text": ch.title,
                    "marks": []
                })
            
            # 合并章节内容
            chapter_blocks = ch.content.get("blocks", []) if isinstance(ch.content, dict) else []
            merged_content["blocks"].extend(chapter_blocks)
            
            # 合并样式规则
            chapter_rules = ch.stylesheet.get("rules", []) if isinstance(ch.stylesheet, dict) else []
            merged_stylesheet["rules"].extend(chapter_rules)
        
        logger.info(f"合并后总 Blocks 数量: {len(merged_content['blocks'])}")
        
        # 查询文档配置
        doc_settings = db.query(DocumentSettings).filter(
            DocumentSettings.doc_id == chapter.doc_id
        ).first()
        
        settings_dict = None
        if doc_settings:
            settings_dict = {
                'margin_top': doc_settings.margin_top,
                'margin_bottom': doc_settings.margin_bottom,
                'margin_left': doc_settings.margin_left,
                'margin_right': doc_settings.margin_right,
                'heading_styles': doc_settings.heading_styles
            }
        
        # 创建导出器（传入文档配置）
        exporter = DocxExporter(merged_content, merged_stylesheet, settings_dict)
        file_stream = exporter.export()
        
        # 生成文件名(移除非法字符)
        safe_filename = "".join(c for c in chapter.title if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_filename:
            safe_filename = f"chapter_{chapter_id[:8]}"
        
        logger.info(f"章节导出成功: {safe_filename}.docx (包含 {len(all_chapters)} 个章节)")
        
        # 返回文件 (使用 URL 编码支持中文文件名)
        encoded_filename = quote(f"{chapter.title}.docx")
        return Response(
            content=file_stream.read(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出章节失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/documents/{doc_id}/docx")
def export_document_to_docx(
    doc_id: str,
    db: Session = Depends(get_db),
    include_chapter_titles: bool = Query(True, description="是否包含章节标题"),
    chapter_title_level: int = Query(1, ge=1, le=6, description="章节标题的级别(1-6)")
):
    """
    导出整个文档为 Word 文件(合并所有章节)
    
    Args:
        doc_id: 文档 ID
        db: 数据库会话
        include_chapter_titles: 是否在每个章节前添加章节标题
        chapter_title_level: 章节标题的级别(1-6)
        
    Returns:
        .docx 文件流
        
    Raises:
        404: 文档不存在或没有章节
        500: 导出失败
    """
    try:
        # 查询文档
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail=f"文档不存在: {doc_id}")
        
        # 查询所有章节(按顺序)
        chapters = db.query(Chapter).filter(
            Chapter.doc_id == doc_id
        ).order_by(Chapter.order_index.asc()).all()
        
        if not chapters:
            raise HTTPException(status_code=404, detail="文档没有章节")
        
        logger.info(f"开始导出文档: {doc.title} (ID: {doc_id}), 章节数: {len(chapters)}")
        
        # 合并所有章节的 Content 和 StyleSheet
        merged_content = {"blocks": []}
        merged_stylesheet = {
            "styleId": f"merged-{doc_id}",
            "appliesTo": "document",
            "rules": []
        }
        
        for idx, chapter in enumerate(chapters):
            # 添加章节标题(如果需要)
            if include_chapter_titles:
                merged_content["blocks"].append({
                    "id": f"chapter-title-{chapter.id}",
                    "type": "heading",
                    "level": chapter_title_level,
                    "text": chapter.title,
                    "marks": []
                })
            
            # 合并章节内容
            chapter_blocks = chapter.content.get("blocks", []) if isinstance(chapter.content, dict) else []
            merged_content["blocks"].extend(chapter_blocks)
            
            # 合并样式规则
            chapter_rules = chapter.stylesheet.get("rules", []) if isinstance(chapter.stylesheet, dict) else []
            merged_stylesheet["rules"].extend(chapter_rules)
            
            # 在章节之间添加分页符(除了最后一个章节)
            if idx < len(chapters) - 1:
                merged_content["blocks"].append({
                    "id": f"page-break-{idx}",
                    "type": "divider"
                })
        
        # 查询文档配置
        doc_settings = db.query(DocumentSettings).filter(
            DocumentSettings.doc_id == doc_id
        ).first()
        
        settings_dict = None
        if doc_settings:
            settings_dict = {
                'margin_top': doc_settings.margin_top,
                'margin_bottom': doc_settings.margin_bottom,
                'margin_left': doc_settings.margin_left,
                'margin_right': doc_settings.margin_right,
                'heading_styles': doc_settings.heading_styles
            }
        
        # 创建导出器（传入文档配置）
        exporter = DocxExporter(merged_content, merged_stylesheet, settings_dict)
        file_stream = exporter.export()
        
        # 生成文件名
        safe_filename = "".join(c for c in doc.title if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_filename:
            safe_filename = f"document_{doc_id[:8]}"
        
        logger.info(f"文档导出成功: {safe_filename}.docx, 总 Blocks: {len(merged_content['blocks'])}")
        
        # 返回文件 (使用 URL 编码支持中文文件名)
        encoded_filename = quote(f"{doc.title}.docx")
        return Response(
            content=file_stream.read(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出文档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/batch/docx")
def export_batch_chapters(
    request: BatchExportRequest,
    db: Session = Depends(get_db)
):
    """
    批量导出多个章节为单个 Word 文档
    
    Args:
        request: 批量导出请求(包含章节 ID 列表)
        db: 数据库会话
        
    Returns:
        .docx 文件流
        
    Raises:
        400: 章节列表为空
        404: 部分章节不存在
        500: 导出失败
    """
    try:
        if not request.chapter_ids:
            raise HTTPException(status_code=400, detail="章节列表不能为空")
        
        logger.info(f"开始批量导出 {len(request.chapter_ids)} 个章节")
        
        # 查询所有章节
        chapters = db.query(Chapter).filter(
            Chapter.id.in_(request.chapter_ids)
        ).all()
        
        # 检查是否所有章节都存在
        found_ids = {ch.id for ch in chapters}
        missing_ids = set(request.chapter_ids) - found_ids
        if missing_ids:
            raise HTTPException(
                status_code=404, 
                detail=f"以下章节不存在: {', '.join(missing_ids)}"
            )
        
        # 按请求的顺序排序章节
        chapter_map = {ch.id: ch for ch in chapters}
        ordered_chapters = [chapter_map[cid] for cid in request.chapter_ids]
        
        # 合并内容
        merged_content = {"blocks": []}
        merged_stylesheet = {
            "styleId": f"batch-export",
            "appliesTo": "document",
            "rules": []
        }
        
        for idx, chapter in enumerate(ordered_chapters):
            # 添加章节标题
            merged_content["blocks"].append({
                "id": f"chapter-title-{chapter.id}",
                "type": "heading",
                "level": 1,
                "text": chapter.title,
                "marks": []
            })
            
            # 合并章节内容
            chapter_blocks = chapter.content.get("blocks", []) if isinstance(chapter.content, dict) else []
            merged_content["blocks"].extend(chapter_blocks)
            
            # 合并样式规则
            chapter_rules = chapter.stylesheet.get("rules", []) if isinstance(chapter.stylesheet, dict) else []
            merged_stylesheet["rules"].extend(chapter_rules)
            
            # 章节之间添加分隔
            if idx < len(ordered_chapters) - 1:
                merged_content["blocks"].append({
                    "id": f"divider-{idx}",
                    "type": "divider"
                })
        
        # 查询文档配置（使用第一个章节的文档ID）
        first_chapter_doc_id = ordered_chapters[0].doc_id if ordered_chapters else None
        doc_settings = None
        if first_chapter_doc_id:
            doc_settings = db.query(DocumentSettings).filter(
                DocumentSettings.doc_id == first_chapter_doc_id
            ).first()
        
        settings_dict = None
        if doc_settings:
            settings_dict = {
                'margin_top': doc_settings.margin_top,
                'margin_bottom': doc_settings.margin_bottom,
                'margin_left': doc_settings.margin_left,
                'margin_right': doc_settings.margin_right,
                'heading_styles': doc_settings.heading_styles
            }
        
        # 创建导出器（传入文档配置）
        exporter = DocxExporter(merged_content, merged_stylesheet, settings_dict)
        file_stream = exporter.export()
        
        # 生成文件名
        safe_filename = "".join(c for c in request.document_title if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_filename:
            safe_filename = f"batch_export_{len(request.chapter_ids)}_chapters"
        
        logger.info(f"批量导出成功: {safe_filename}.docx")
        
        # 返回文件 (使用 URL 编码支持中文文件名)
        encoded_filename = quote(f"{request.document_title}.docx")
        return Response(
            content=file_stream.read(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量导出失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/health")
def export_health_check():
    """
    导出服务健康检查
    
    Returns:
        服务状态信息
    """
    return {
        "status": "healthy",
        "service": "docx_export",
        "supported_formats": ["docx"],
        "features": [
            "单章节导出",
            "整文档导出",
            "批量导出",
            "样式保留",
            "表格支持",
            "图片支持"
        ]
    }
