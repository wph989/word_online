"""
块处理器模块
"""

from .paragraph import add_paragraph, add_text_with_marks
from .heading import add_heading
from .table import add_table
from .image import add_image
from .code import add_code
from .divider import add_divider

__all__ = [
    'add_paragraph',
    'add_text_with_marks',
    'add_heading',
    'add_table',
    'add_image',
    'add_code',
    'add_divider'
]
