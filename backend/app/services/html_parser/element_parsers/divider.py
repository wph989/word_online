"""
分割线解析器
"""

from bs4 import Tag
from app.models.content_models import DividerBlock

from ..utils import generate_block_id


def parse_divider(element: Tag) -> DividerBlock:
    """
    解析分割线
    
    Args:
        element: hr 标签或包含 hr 的 div
        
    Returns:
        DividerBlock 对象
    """
    block_id = generate_block_id("divider")
    return DividerBlock(id=block_id, type="divider")
