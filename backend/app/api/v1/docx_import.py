"""
DOCX 导入 API

提供 DOCX 文件导入功能
"""

import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.schemas import ImportResponse, ImportChapterInfo
from app.services.docx_importer import DocxImporter


router = APIRouter(prefix="/api/v1/documents", tags=["import"])


@router.post("/import", response_model=ImportResponse, status_code=201)
async def import_docx(
    file: UploadFile = File(..., description="DOCX 文件"),
    max_heading_level: Optional[int] = Form(None, ge=1, le=6, description="最大章节标题级别 (1-6)"),
    document_title: Optional[str] = Form(None, description="文档标题（默认使用文件名）"),
    db: Session = Depends(get_db)
):
    """
    导入 DOCX 文件
    
    上传 DOCX 文件，根据标题级别自动创建文档和章节。
    
    - **file**: DOCX 文件（必填）
    - **max_heading_level**: 最大章节标题级别，H1~H{level} 将创建为独立章节（可选，默认为 2）
    - **document_title**: 文档标题（可选，默认使用文件名）
    
    返回创建的文档 ID 和章节列表。
    """
    # 验证文件类型
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(
            status_code=400, 
            detail="仅支持 .docx 格式文件"
        )
    
    # 读取文件内容
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取文件失败: {str(e)}")
    
    # 验证文件大小
    max_size = int(os.getenv("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))  # 默认 10MB
    if len(content) > max_size:
        raise HTTPException(
            status_code=413, 
            detail=f"文件大小超过限制（{max_size // 1024 // 1024}MB）"
        )
    
    # 验证文件内容（检查 DOCX 魔数）
    if len(content) < 4 or content[:4] != b'PK\x03\x04':
        raise HTTPException(
            status_code=400,
            detail="文件已损坏或不是有效的 DOCX 文件"
        )
    
    try:
        # 执行导入
        importer = DocxImporter(
            file_content=content,
            filename=file.filename,
            max_heading_level=max_heading_level,
            document_title=document_title
        )
        result = importer.import_document(db)
        
        # 构建响应
        chapters = [
            ImportChapterInfo(
                id=ch.id,
                title=ch.title,
                level=ch.level,
                order_index=ch.order_index,
                parent_id=ch.parent_id
            )
            for ch in result.chapters
        ]
        
        return ImportResponse(
            doc_id=result.doc_id,
            title=result.title,
            chapters=chapters,
            message=f"导入成功，共创建 {len(chapters)} 个章节"
        )
        
    except Exception as e:
        # 记录错误日志
        print(f"❌ DOCX 导入失败: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500, 
            detail=f"文档解析失败: {str(e)}"
        )
