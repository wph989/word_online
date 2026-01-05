"""
提取器模块
"""

from .text_marks import extract_text_and_marks
from .styles import extract_user_block_styles, extract_cell_user_styles, extract_table_styles

__all__ = [
    'extract_text_and_marks',
    'extract_user_block_styles',
    'extract_cell_user_styles',
    'extract_table_styles'
]
