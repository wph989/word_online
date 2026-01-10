"""
DOCX 导入配置
"""

import os
from typing import Optional


class DocxImportConfig:
    """DOCX 导入配置类"""
    
    # 默认值
    DEFAULT_MAX_HEADING_LEVEL = 2
    DEFAULT_CHAPTER_TITLE = "默认章节"
    
    def __init__(
        self,
        max_heading_level: Optional[int] = None,
        default_chapter_title: Optional[str] = None
    ):
        """
        初始化配置
        
        Args:
            max_heading_level: 最大章节标题级别(1-6)
            default_chapter_title: 无标题时的默认章节名
        """
        # 从环境变量读取默认值
        env_max_level = os.getenv("DOCX_IMPORT_MAX_HEADING_LEVEL")
        env_default_title = os.getenv("DOCX_IMPORT_DEFAULT_CHAPTER_TITLE")
        
        # 优先使用传入参数，否则使用环境变量，最后使用默认值
        self._max_heading_level = max_heading_level or (
            int(env_max_level) if env_max_level else self.DEFAULT_MAX_HEADING_LEVEL
        )
        self._default_chapter_title = default_chapter_title or (
            env_default_title or self.DEFAULT_CHAPTER_TITLE
        )
        
        # 验证参数范围
        if not 1 <= self._max_heading_level <= 6:
            raise ValueError(f"max_heading_level must be between 1 and 6, got {self._max_heading_level}")
    
    @property
    def max_heading_level(self) -> int:
        """最大章节标题级别"""
        return self._max_heading_level
    
    @property
    def default_chapter_title(self) -> str:
        """默认章节标题"""
        return self._default_chapter_title
    
    def is_chapter_heading(self, level: int) -> bool:
        """
        判断标题级别是否应创建为独立章节
        
        Args:
            level: 标题级别 (1-6)
            
        Returns:
            True 如果该级别应创建为章节
        """
        return 1 <= level <= self._max_heading_level


# 便捷函数：获取默认配置
def get_default_config() -> DocxImportConfig:
    """获取默认配置实例"""
    return DocxImportConfig()
