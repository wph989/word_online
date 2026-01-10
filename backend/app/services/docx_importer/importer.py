"""
DOCX 导入器主类

协调各模块完成 DOCX 文件的导入
"""

import os
import uuid
from typing import Optional, List
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models.database import Document, Chapter, DocumentSettings

from .config import DocxImportConfig, get_default_config
from .parser import DocxParser
from .element_converter import ElementConverter
from .image_extractor import ImageExtractor
from .chapter_builder import ChapterBuilder, ChapterData


@dataclass
class ImportedChapter:
    """导入的章节信息"""
    id: str
    title: str
    level: int
    order_index: int
    parent_id: Optional[str] = None


@dataclass
class ImportResult:
    """导入结果"""
    doc_id: str
    title: str
    chapters: List[ImportedChapter]


class DocxImporter:
    """
    DOCX 导入器主类
    
    职责:
    1. 接收上传的 DOCX 文件
    2. 调用 DocxParser 解析文档结构
    3. 调用 ElementConverter 转换为 JSON 格式
    4. 调用 ImageExtractor 提取并保存图片
    5. 调用 ChapterBuilder 根据标题拆分章节
    6. 创建 Document、Chapters、DocumentSettings 数据库记录
    """
    
    def __init__(
        self,
        file_content: bytes,
        filename: str,
        max_heading_level: Optional[int] = None,
        document_title: Optional[str] = None
    ):
        """
        初始化导入器
        
        Args:
            file_content: DOCX 文件的字节内容
            filename: 原始文件名
            max_heading_level: 最大章节标题级别（可选，覆盖配置）
            document_title: 文档标题（可选，默认使用文件名）
        """
        self.file_content = file_content
        self.filename = filename
        
        # 初始化配置
        self.config = DocxImportConfig(max_heading_level=max_heading_level)
        
        # 文档标题（移除 .docx 扩展名）
        if document_title:
            self.document_title = document_title
        else:
            self.document_title = os.path.splitext(filename)[0]
        
        # 生成文档 ID
        self.doc_id = str(uuid.uuid4())
        
        # 上传目录
        self.upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    
    def import_document(self, db: Session) -> ImportResult:
        """
        执行导入
        
        Args:
            db: 数据库会话
            
        Returns:
            ImportResult: 导入结果
            
        Raises:
            Exception: 导入失败时抛出异常
        """
        image_extractor = None
        
        try:
            # 1. 解析 DOCX 文件
            parser = DocxParser(self.file_content)
            parse_result = parser.parse()
            
            # 2. 提取并保存图片
            image_extractor = ImageExtractor(self.doc_id, self.upload_dir)
            images_path_map = image_extractor.extract_and_save(parse_result.images)
            
            # 3. 转换为 JSON 格式
            converter = ElementConverter()
            content, stylesheet = converter.convert_elements(
                parse_result.elements,
                images_path_map
            )
            
            # 调试日志：打印表格相关的样式规则
            import logging
            logger = logging.getLogger(__name__)
            cell_rules = [r for r in stylesheet.rules if r.target.blockType == "tableCell"]
            column_rules = [r for r in stylesheet.rules if r.target.blockType == "tableColumn"]
            logger.info(f"📊 导入统计: 表格单元格样式规则: {len(cell_rules)}, 列宽规则: {len(column_rules)}")
            if cell_rules:
                for rule in cell_rules[:5]:  # 只打印前5个
                    logger.info(f"  单元格样式: {rule.target.blockIds} -> {rule.style.model_dump(exclude_none=True)}")
            
            # 4. 构建章节
            chapter_builder = ChapterBuilder(
                blocks=content.blocks,
                style_rules=stylesheet.rules,
                config=self.config
            )
            chapters_data = chapter_builder.build()
            
            # 5. 创建数据库记录
            # 5.1 创建文档
            db_document = Document(
                id=self.doc_id,
                title=self.document_title
            )
            db.add(db_document)
            
            # 5.2 创建文档设置（页面边距）
            page_settings = parse_result.page_settings
            db_settings = DocumentSettings(
                doc_id=self.doc_id,
                margin_top=page_settings.margin_top or 40,
                margin_bottom=page_settings.margin_bottom or 40,
                margin_left=page_settings.margin_left or 50,
                margin_right=page_settings.margin_right or 50,
                heading_styles=self._get_default_heading_styles()
            )
            db.add(db_settings)
            
            # 5.3 创建章节
            imported_chapters = []
            for chapter_data in chapters_data:
                db_chapter = Chapter(
                    id=chapter_data.id,
                    doc_id=self.doc_id,
                    title=chapter_data.title,
                    level=chapter_data.level,
                    parent_id=chapter_data.parent_id,
                    order_index=chapter_data.order_index,
                    html_content="",  # 从 JSON 渲染
                    content=chapter_data.content.model_dump(),
                    stylesheet=chapter_data.stylesheet.model_dump()
                )
                db.add(db_chapter)
                
                imported_chapters.append(ImportedChapter(
                    id=chapter_data.id,
                    title=chapter_data.title,
                    level=chapter_data.level,
                    order_index=chapter_data.order_index,
                    parent_id=chapter_data.parent_id
                ))
            
            # 6. 提交事务
            db.commit()
            
            return ImportResult(
                doc_id=self.doc_id,
                title=self.document_title,
                chapters=imported_chapters
            )
            
        except Exception as e:
            # 回滚事务
            db.rollback()
            
            # 清理已保存的图片
            if image_extractor:
                image_extractor.cleanup()
            
            raise Exception(f"导入失败: {str(e)}")
    
    def _get_default_heading_styles(self) -> dict:
        """获取默认标题样式"""
        return {
            "h1": {
                "fontSize": 24,
                "fontFamily": "Microsoft YaHei",
                "fontWeight": "bold",
                "color": "#000000",
                "marginTop": 12.0,
                "marginBottom": 6.0
            },
            "h2": {
                "fontSize": 20,
                "fontFamily": "Microsoft YaHei",
                "fontWeight": "bold",
                "color": "#000000",
                "marginTop": 10.0,
                "marginBottom": 5.0
            },
            "h3": {
                "fontSize": 16,
                "fontFamily": "Microsoft YaHei",
                "fontWeight": "bold",
                "color": "#000000",
                "marginTop": 8.0,
                "marginBottom": 4.0
            },
            "h4": {
                "fontSize": 14,
                "fontFamily": "Microsoft YaHei",
                "fontWeight": "bold",
                "color": "#000000",
                "marginTop": 6.0,
                "marginBottom": 3.0
            },
            "h5": {
                "fontSize": 12,
                "fontFamily": "Microsoft YaHei",
                "fontWeight": "bold",
                "color": "#000000",
                "marginTop": 4.0,
                "marginBottom": 2.0
            },
            "h6": {
                "fontSize": 10,
                "fontFamily": "Microsoft YaHei",
                "fontWeight": "bold",
                "color": "#000000",
                "marginTop": 2.0,
                "marginBottom": 1.0
            }
        }
