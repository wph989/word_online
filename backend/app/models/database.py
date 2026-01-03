"""
数据库模型定义
使用 SQLAlchemy ORM 定义数据表结构
"""

from sqlalchemy import Column, String, JSON, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
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
        default=datetime.utcnow, 
        comment="创建时间"
    )
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
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
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 关联关系：章节属于一个文档
    document = relationship("Document", back_populates="chapters")


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
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
