"""
DOCX 导入服务模块

提供 DOCX 文件导入功能，将文档解析为 Content/StyleSheet JSON 格式
"""

from .config import DocxImportConfig, get_default_config
from .parser import DocxParser, DocxParseResult
from .element_converter import ElementConverter
from .image_extractor import ImageExtractor
from .chapter_builder import ChapterBuilder, ChapterData
from .importer import DocxImporter, ImportResult, ImportedChapter

__all__ = [
    "DocxImportConfig",
    "get_default_config",
    "DocxParser",
    "DocxParseResult",
    "ElementConverter",
    "ImageExtractor",
    "ChapterBuilder",
    "ChapterData",
    "DocxImporter",
    "ImportResult",
    "ImportedChapter",
]

