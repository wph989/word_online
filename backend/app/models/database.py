"""
数据库模型定义
使用 SQLAlchemy ORM 定义数据表结构
"""

from sqlalchemy import Column, String, JSON, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class Document(Base):
    """
    文档表
    一个文档包含多个章节
    """
    __tablename__ = "documents"
    
    # 主键：使用 UUID 字符串
    id = Column(String(36), primary_key=True, comment="文档唯一标识")
    
    # 基本信息
    title = Column(String(255), nullable=False, comment="文档标题")
    
    # 时间戳
    created_at = Column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        comment="创建时间"
    )
    updated_at = Column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间"
    )
    
    # 关联关系：一个文档有多个章节
    # cascade="all, delete-orphan" 表示删除文档时级联删除所有章节
    chapters = relationship(
        "Chapter", 
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="Chapter.order_index"
    )
    
    # 关联关系：文档配置 (一对一)
    # cascade="all, delete-orphan" 确保删除文档时同时删除配置
    settings = relationship(
        "DocumentSettings",
        back_populates="document",
        uselist=False,
        cascade="all, delete-orphan"
    )


class Chapter(Base):
    """
    章节表
    存储章节的 HTML、Content JSON 和 StyleSheet JSON
    """
    __tablename__ = "chapters"
    
    # 主键
    id = Column(String(36), primary_key=True, comment="章节唯一标识")
    
    # 外键：关联到文档
    doc_id = Column(
        String(36), 
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属文档ID"
    )
    
    # 基本信息
    title = Column(String(255), nullable=False, comment="章节标题")
    order_index = Column(Integer, default=0, comment="章节排序索引")
    
    # 核心数据：存储原始 HTML（从前端接收）
    html_content = Column(Text, nullable=True, comment="原始HTML内容")
    
    # 解析后的结构化数据
    content = Column(JSON, nullable=False, comment="Content JSON（结构数据）")
    stylesheet = Column(JSON, nullable=False, comment="StyleSheet JSON（样式数据）")
    
    # 时间戳
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间"
    )
    
    # 关联关系：章节属于一个文档
    document = relationship("Document", back_populates="chapters")


class DocumentSettings(Base):
    """
    文档配置表
    存储文档的页面设置和标题样式配置
    """
    __tablename__ = "document_settings"
    
    # 主键：与文档 ID 一致（一对一关系）
    doc_id = Column(
        String(36), 
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
        comment="所属文档ID"
    )
    
    # 页边距配置 (单位: px)
    margin_top = Column(Integer, default=40, comment="上边距")
    margin_bottom = Column(Integer, default=40, comment="下边距")
    margin_left = Column(Integer, default=50, comment="左边距")
    margin_right = Column(Integer, default=50, comment="右边距")
    
    # 标题样式配置 (JSON 格式存储 H1-H6 的样式)
    # 格式: {"h1": {"fontSize": 24, "fontWeight": "bold", "color": "#333", ...}, ...}
    heading_styles = Column(
        JSON, 
        nullable=False,
        comment="标题样式配置 (H1-H6)"
    )
    
    # 时间戳
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间"
    )
    
    # 关联关系：配置属于一个文档
    # 关联关系：配置属于一个文档
    document = relationship("Document", back_populates="settings")


class Asset(Base):
    """
    资源表
    存储图片等静态资源的元信息
    """
    __tablename__ = "assets"
    
    # 主键
    id = Column(String(36), primary_key=True, comment="资源唯一标识")
    
    # 文件信息
    file_path = Column(String(512), nullable=False, comment="文件存储路径")
    file_type = Column(String(50), comment="文件类型（image/png等）")
    file_size = Column(Integer, comment="文件大小（字节）")
    
    # 关联信息
    chapter_id = Column(
        String(36),
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="关联的章节ID"
    )
    
    # 时间戳
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
