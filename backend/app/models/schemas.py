"""
Pydantic 数据模型（Schemas）
用于 API 请求验证和响应序列化
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# ============ 文档相关模型 ============

class DocumentCreate(BaseModel):
    """创建文档的请求模型"""
    title: str = Field(..., min_length=1, max_length=255, description="文档标题")


class DocumentUpdate(BaseModel):
    """更新文档的请求模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="文档标题")


class DocumentBase(BaseModel):
    """文档基础信息"""
    id: str = Field(..., description="文档ID")
    title: str = Field(..., description="文档标题")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True  # Pydantic V2 语法，替代 orm_mode


# ============ 章节相关模型 ============

class ChapterCreate(BaseModel):
    """
    创建章节的请求模型
    前端只需要传递 HTML 内容，后端负责解析
    """
    doc_id: str = Field(..., description="所属文档ID")
    title: str = Field(..., min_length=1, max_length=255, description="章节标题")
    html_content: str = Field(..., description="HTML内容（从编辑器获取）")
    order_index: int = Field(default=0, description="排序索引")


class ChapterUpdate(BaseModel):
    """
    更新章节的请求模型
    允许部分更新
    """
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="章节标题")
    html_content: Optional[str] = Field(None, description="HTML内容")
    order_index: Optional[int] = Field(None, description="排序索引")


class ChapterBase(BaseModel):
    """章节基础信息（不包含完整内容）"""
    id: str = Field(..., description="章节ID")
    doc_id: str = Field(..., description="所属文档ID")
    title: str = Field(..., description="章节标题")
    order_index: int = Field(..., description="排序索引")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class ChapterDetail(ChapterBase):
    """
    章节详细信息
    包含解析后的 Content 和 StyleSheet
    """
    content: Dict[str, Any] = Field(..., description="Content JSON")
    stylesheet: Dict[str, Any] = Field(..., description="StyleSheet JSON")


class ChapterHtmlResponse(ChapterBase):
    """
    章节 HTML 响应
    用于前端展示，返回渲染后的 HTML
    """
    html_content: str = Field(..., description="渲染后的HTML内容")


# ============ 列表响应模型 ============

class DocumentWithChapters(DocumentBase):
    """带章节列表的文档信息"""
    chapters: List[ChapterBase] = Field(default=[], description="章节列表")


class PaginatedResponse(BaseModel):
    """分页响应基类"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[Any] = Field(..., description="数据列表")


class DocumentListResponse(PaginatedResponse):
    """文档列表响应"""
    items: List[DocumentWithChapters] = Field(..., description="文档列表")


# ============ 导出相关模型 ============

class ExportRequest(BaseModel):
    """导出请求模型"""
    format: str = Field(default="docx", description="导出格式（docx/pdf）")
    include_styles: bool = Field(default=True, description="是否包含样式")


# ============ 通用响应模型 ============

class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str = Field(..., description="响应消息")
    success: bool = Field(default=True, description="是否成功")


# ============ 文档配置相关模型 ============

class HeadingStyle(BaseModel):
    """单个标题级别的样式配置"""
    fontSize: float = Field(..., ge=1, le=100, description="字号 (pt)")
    fontFamily: str = Field(default="Microsoft YaHei", description="字体名称")
    fontWeight: str = Field(..., description="字体粗细 (normal/bold)")
    color: str = Field(..., description="颜色 (HEX格式)")
    marginTop: float = Field(..., ge=0, description="段前距 (pt)")
    marginBottom: float = Field(..., ge=0, description="段后距 (pt)")


class DocumentSettingsCreate(BaseModel):
    """创建文档配置的请求模型"""
    doc_id: str = Field(..., description="所属文档ID")
    margin_top: float = Field(default=2.54, ge=0, description="上边距 (cm)")
    margin_bottom: float = Field(default=2.54, ge=0, description="下边距 (cm)")
    margin_left: float = Field(default=3.17, ge=0, description="左边距 (cm)")
    margin_right: float = Field(default=3.17, ge=0, description="右边距 (cm)")
    heading_styles: Dict[str, HeadingStyle] = Field(
        ..., 
        description="标题样式配置 (h1-h6)"
    )


class DocumentSettingsUpdate(BaseModel):
    """更新文档配置的请求模型"""
    margin_top: Optional[float] = Field(None, ge=0, description="上边距 (cm)")
    margin_bottom: Optional[float] = Field(None, ge=0, description="下边距 (cm)")
    margin_left: Optional[float] = Field(None, ge=0, description="左边距 (cm)")
    margin_right: Optional[float] = Field(None, ge=0, description="右边距 (cm)")
    heading_styles: Optional[Dict[str, HeadingStyle]] = Field(
        None, 
        description="标题样式配置 (h1-h6)"
    )


class DocumentSettingsResponse(BaseModel):
    """文档配置响应模型"""
    doc_id: str = Field(..., description="所属文档ID")
    margin_top: float = Field(..., description="上边距 (cm)")
    margin_bottom: float = Field(..., description="下边距 (cm)")
    margin_left: float = Field(..., description="左边距 (cm)")
    margin_right: float = Field(..., description="右边距 (cm)")
    heading_styles: Dict[str, Any] = Field(..., description="标题样式配置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True

