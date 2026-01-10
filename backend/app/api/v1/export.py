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
    
    使用延迟加载策略：先获取章节树结构，再逐个加载内容
    
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
        # 只查询章节基本信息（不加载 content 和 stylesheet）
        chapter = db.query(Chapter.id, Chapter.title, Chapter.level, Chapter.doc_id).filter(
            Chapter.id == chapter_id
        ).first()
        
        if not chapter:
            raise HTTPException(status_code=404, detail=f"章节不存在: {chapter_id}")
        
        logger.info(f"开始导出章节: {chapter.title} (ID: {chapter_id})")
        
        # 递归收集章节 ID 树（只获取 ID、title、level，不加载内容）
        def collect_chapter_ids(parent_id):
            """递归收集章节 ID 及基本信息"""
            chapter_infos = []
            
            # 只查询必要字段
            children = db.query(
                Chapter.id, Chapter.title, Chapter.level, Chapter.parent_id
            ).filter(
                Chapter.parent_id == parent_id
            ).order_by(Chapter.order_index.asc()).all()
            
            for child in children:
                chapter_infos.append({
                    'id': child.id,
                    'title': child.title,
                    'level': child.level
                })
                # 递归收集子章节
                chapter_infos.extend(collect_chapter_ids(child.id))
            
            return chapter_infos
        
        # 收集所有章节 ID（父章节 + 所有子孙章节）
        all_chapter_infos = [{
            'id': chapter.id,
            'title': chapter.title,
            'level': chapter.level
        }]
        all_chapter_infos.extend(collect_chapter_ids(chapter.id))
        
        logger.info(f"收集到 {len(all_chapter_infos)} 个章节（包含子章节）")
        
        # 合并所有章节的内容
        merged_content = {"blocks": []}
        merged_stylesheet = {
            "styleId": f"chapter-export-{chapter_id}",
            "appliesTo": "document",
            "rules": []
        }
        
        # 逐个加载章节内容
        for idx, ch_info in enumerate(all_chapter_infos):
            # 添加章节标题
            if include_title or idx > 0:
                title_level = min(ch_info['level'], 6)
                merged_content["blocks"].append({
                    "id": f"chapter-title-{ch_info['id']}",
                    "type": "heading",
                    "level": title_level,
                    "text": ch_info['title'],
                    "marks": []
                })
            
            # 按需加载章节内容（只加载当前章节）
            ch_data = db.query(Chapter.content, Chapter.stylesheet).filter(
                Chapter.id == ch_info['id']
            ).first()
            
            if ch_data:
                # 合并章节内容
                chapter_blocks = ch_data.content.get("blocks", []) if isinstance(ch_data.content, dict) else []
                merged_content["blocks"].extend(chapter_blocks)
                
                # 合并样式规则
                chapter_rules = ch_data.stylesheet.get("rules", []) if isinstance(ch_data.stylesheet, dict) else []
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
                'heading_styles': doc_settings.heading_styles,
                'heading_numbering_style': doc_settings.heading_numbering_style
            }
        
        # 创建导出器（传入文档配置）
        exporter = DocxExporter(merged_content, merged_stylesheet, settings_dict)
        file_stream = exporter.export()
        
        # 生成文件名(移除非法字符)
        safe_filename = "".join(c for c in chapter.title if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_filename:
            safe_filename = f"chapter_{chapter_id[:8]}"
        
        logger.info(f"章节导出成功: {safe_filename}.docx (包含 {len(all_chapter_infos)} 个章节)")
        
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
    chapter_title_level: int = Query(1, ge=1, le=6, description="已弃用，现使用章节实际层级")
):
    """
    导出整个文档为 Word 文件(按层级顺序合并所有章节及其子章节)
    
    使用延迟加载策略：先获取章节树结构，再逐个加载内容
    
    Args:
        doc_id: 文档 ID
        db: 数据库会话
        include_chapter_titles: 是否在每个章节前添加章节标题
        chapter_title_level: 已弃用，现使用章节的实际 level 字段
        
    Returns:
        .docx 文件流
        
    说明:
        - 按照章节层级顺序导出：先导出顶级章节及其所有子章节，再导出下一个顶级章节
        - 每个章节使用其实际的 level 值作为标题级别
        - 在顶级章节之间自动添加分页符
        
    Raises:
        404: 文档不存在或没有章节
        500: 导出失败
    """
    try:
        # 查询文档
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail=f"文档不存在: {doc_id}")
        
        # 递归收集章节 ID 树（只获取基本信息）
        def collect_chapter_ids(parent_id):
            """递归收集章节 ID 及基本信息"""
            chapter_infos = []
            
            # 只查询必要字段
            children = db.query(
                Chapter.id, Chapter.title, Chapter.level, Chapter.parent_id
            ).filter(
                Chapter.parent_id == parent_id
            ).order_by(Chapter.order_index.asc()).all()
            
            for child in children:
                chapter_infos.append({
                    'id': child.id,
                    'title': child.title,
                    'level': child.level,
                    'parent_id': child.parent_id
                })
                # 递归收集子章节
                chapter_infos.extend(collect_chapter_ids(child.id))
            
            return chapter_infos
        
        # 只查询顶级章节的基本信息
        top_level_chapters = db.query(
            Chapter.id, Chapter.title, Chapter.level, Chapter.parent_id
        ).filter(
            Chapter.doc_id == doc_id,
            Chapter.parent_id.is_(None)
        ).order_by(Chapter.order_index.asc()).all()
        
        if not top_level_chapters:
            raise HTTPException(status_code=404, detail="文档没有章节")
        
        # 收集所有章节信息（包括子章节），保持层级顺序
        all_chapter_infos = []
        for top_chapter in top_level_chapters:
            all_chapter_infos.append({
                'id': top_chapter.id,
                'title': top_chapter.title,
                'level': top_chapter.level,
                'parent_id': top_chapter.parent_id
            })
            all_chapter_infos.extend(collect_chapter_ids(top_chapter.id))
        
        logger.info(f"开始导出文档: {doc.title} (ID: {doc_id}), 顶级章节数: {len(top_level_chapters)}, 总章节数: {len(all_chapter_infos)}")
        
        # 合并所有章节的 Content 和 StyleSheet
        merged_content = {"blocks": []}
        merged_stylesheet = {
            "styleId": f"merged-{doc_id}",
            "appliesTo": "document",
            "rules": []
        }
        
        # 逐个加载章节内容
        for idx, ch_info in enumerate(all_chapter_infos):
            # 添加章节标题(如果需要)
            if include_chapter_titles:
                # 使用章节的实际层级
                title_level = min(ch_info['level'], 6)
                merged_content["blocks"].append({
                    "id": f"chapter-title-{ch_info['id']}",
                    "type": "heading",
                    "level": title_level,
                    "text": ch_info['title'],
                    "marks": []
                })
            
            # 按需加载章节内容（只加载当前章节）
            ch_data = db.query(Chapter.content, Chapter.stylesheet).filter(
                Chapter.id == ch_info['id']
            ).first()
            
            if ch_data:
                # 合并章节内容
                chapter_blocks = ch_data.content.get("blocks", []) if isinstance(ch_data.content, dict) else []
                merged_content["blocks"].extend(chapter_blocks)
                
                # 合并样式规则
                chapter_rules = ch_data.stylesheet.get("rules", []) if isinstance(ch_data.stylesheet, dict) else []
                merged_stylesheet["rules"].extend(chapter_rules)
            
            # 在顶级章节之间添加分页符(除了最后一个顶级章节)
            if idx < len(all_chapter_infos) - 1:
                next_chapter = all_chapter_infos[idx + 1]
                # 如果下一个章节是顶级章节，添加分页符
                if next_chapter['parent_id'] is None:
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
                'heading_styles': doc_settings.heading_styles,
                'heading_numbering_style': doc_settings.heading_numbering_style
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
    批量导出多个章节为单个 Word 文档（自动包含所有子章节）
    
    Args:
        request: 批量导出请求(包含章节 ID 列表)
        db: 数据库会话
        
    Returns:
        .docx 文件流
        
    说明:
        - 对于每个请求的章节，会自动递归包含其所有子章节
        - 按请求的章节顺序导出，每个章节及其子章节作为一个完整单元
        - 每个章节使用其实际的 level 值作为标题级别
        - 在请求的顶级章节之间自动添加分隔符
        
    Raises:
        400: 章节列表为空
        404: 部分章节不存在
        500: 导出失败
    """
    try:
        if not request.chapter_ids:
            raise HTTPException(status_code=400, detail="章节列表不能为空")
        
        logger.info(f"开始批量导出 {len(request.chapter_ids)} 个章节")
        
        # 递归收集章节树的函数
        def collect_chapter_tree(parent_chapter):
            """递归收集章节及其子章节"""
            chapters = [parent_chapter]
            
            # 查询子章节（按 order_index 排序）
            children = db.query(Chapter).filter(
                Chapter.parent_id == parent_chapter.id
            ).order_by(Chapter.order_index.asc()).limit(1000).all()
            
            # 递归收集每个子章节
            for child in children:
                chapters.extend(collect_chapter_tree(child))
            
            return chapters
        
        # 查询所有请求的章节
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
        
        # 按请求的顺序排序章节，并收集每个章节的子章节
        chapter_map = {ch.id: ch for ch in chapters}
        all_chapters = []
        for cid in request.chapter_ids:
            # 递归收集该章节及其所有子章节
            all_chapters.extend(collect_chapter_tree(chapter_map[cid]))
        
        logger.info(f"收集到 {len(all_chapters)} 个章节（包含子章节）")
        
        # 合并内容
        merged_content = {"blocks": []}
        merged_stylesheet = {
            "styleId": f"batch-export",
            "appliesTo": "document",
            "rules": []
        }
        
        for idx, chapter in enumerate(all_chapters):
            # 添加章节标题，使用章节的实际层级
            title_level = min(chapter.level, 6)
            merged_content["blocks"].append({
                "id": f"chapter-title-{chapter.id}",
                "type": "heading",
                "level": title_level,
                "text": chapter.title,
                "marks": []
            })
            
            # 合并章节内容
            chapter_blocks = chapter.content.get("blocks", []) if isinstance(chapter.content, dict) else []
            merged_content["blocks"].extend(chapter_blocks)
            
            # 合并样式规则
            chapter_rules = chapter.stylesheet.get("rules", []) if isinstance(chapter.stylesheet, dict) else []
            merged_stylesheet["rules"].extend(chapter_rules)
            
            # 在请求的顶级章节之间添加分隔符
            # 检查下一个章节是否是新的请求章节（而非当前章节的子章节）
            if idx < len(all_chapters) - 1:
                next_chapter = all_chapters[idx + 1]
                # 如果下一个章节的 ID 在请求列表中，说明是新的顶级章节
                if next_chapter.id in request.chapter_ids:
                    merged_content["blocks"].append({
                        "id": f"divider-{idx}",
                        "type": "divider"
                    })
        
        # 查询文档配置（使用第一个章节的文档ID）
        first_chapter_doc_id = all_chapters[0].doc_id if all_chapters else None
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
                'heading_styles': doc_settings.heading_styles,
                'heading_numbering_style': doc_settings.heading_numbering_style
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
