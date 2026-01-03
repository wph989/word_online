"""
文档配置 API 路由
提供文档页面设置和标题样式的增删改查接口
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.database import DocumentSettings, Document
from app.models.schemas import (
    DocumentSettingsCreate,
    DocumentSettingsUpdate,
    DocumentSettingsResponse,
    MessageResponse
)

router = APIRouter(prefix="/api/v1/settings", tags=["文档配置"])


# 默认标题样式配置
DEFAULT_HEADING_STYLES = {
    "h1": {"fontSize": 22, "fontFamily": "Microsoft YaHei", "fontWeight": "bold", "color": "#333333", "marginTop": 17, "marginBottom": 16.5}, # 二号
    "h2": {"fontSize": 16, "fontFamily": "Microsoft YaHei", "fontWeight": "bold", "color": "#333333", "marginTop": 13, "marginBottom": 13}, # 三号
    "h3": {"fontSize": 14, "fontFamily": "Microsoft YaHei", "fontWeight": "bold", "color": "#333333", "marginTop": 13, "marginBottom": 13}, # 四号
    "h4": {"fontSize": 12, "fontFamily": "Microsoft YaHei", "fontWeight": "bold", "color": "#333333", "marginTop": 12, "marginBottom": 12}, # 小四
    "h5": {"fontSize": 10.5, "fontFamily": "Microsoft YaHei", "fontWeight": "bold", "color": "#333333", "marginTop": 10, "marginBottom": 10}, # 五号
    "h6": {"fontSize": 9, "fontFamily": "Microsoft YaHei", "fontWeight": "bold", "color": "#333333", "marginTop": 9, "marginBottom": 9}, # 小五
}



@router.get("/{doc_id}", response_model=DocumentSettingsResponse)
def get_document_settings(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    获取文档配置
    
    如果配置不存在，返回默认配置
    """
    settings = db.query(DocumentSettings).filter(
        DocumentSettings.doc_id == doc_id
    ).first()
    
    if not settings:
        # 返回默认配置（不写入数据库）
        from datetime import datetime
        return DocumentSettingsResponse(
            doc_id=doc_id,
            margin_top=2.54,
            margin_bottom=2.54,
            margin_left=3.17,
            margin_right=3.17,
            heading_styles=DEFAULT_HEADING_STYLES,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    return settings


@router.put("/{doc_id}", response_model=DocumentSettingsResponse)
def save_document_settings(
    doc_id: str,
    settings_in: DocumentSettingsUpdate,
    db: Session = Depends(get_db)
):
    """
    保存文档配置（创建或更新）
    
    这是唯一的保存接口：
    - 如果配置不存在，则创建新配置（使用默认值填充未提供的字段）
    - 如果配置已存在，则更新提供的字段
    """
    # 检查文档是否存在
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档 {doc_id} 不存在"
        )
    
    # 查找现有配置
    settings = db.query(DocumentSettings).filter(
        DocumentSettings.doc_id == doc_id
    ).first()
    
    # 获取更新数据的字典形式（过滤掉未设置的字段）
    update_data = settings_in.model_dump(exclude_unset=True)
    
    if not settings:
        # === 创建模式 ===
        # 补全默认值
        heading_styles = update_data.get('heading_styles')
        if heading_styles is None:
             heading_styles = DEFAULT_HEADING_STYLES
        
        settings = DocumentSettings(
            doc_id=doc_id,
            margin_top=update_data.get('margin_top', 2.54),
            margin_bottom=update_data.get('margin_bottom', 2.54),
            margin_left=update_data.get('margin_left', 3.17),
            margin_right=update_data.get('margin_right', 3.17),
            heading_styles=heading_styles
        )
        db.add(settings)
    else:
        # === 更新模式 ===
        for field, value in update_data.items():
            setattr(settings, field, value)
    
    db.commit()
    db.refresh(settings)
    
    return settings


@router.delete("/{doc_id}", response_model=MessageResponse)
def delete_document_settings(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    删除文档配置（恢复为默认配置）
    """
    settings = db.query(DocumentSettings).filter(
        DocumentSettings.doc_id == doc_id
    ).first()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档 {doc_id} 的配置不存在"
        )
    
    db.delete(settings)
    db.commit()
    
    return MessageResponse(
        message=f"文档 {doc_id} 的配置已删除，将使用默认配置",
        success=True
    )
