"""
标题解析器
"""

from bs4 import Tag
from app.models.content_models import HeadingBlock

from ..extractors import extract_text_and_marks, extract_user_block_styles
from ..utils import add_style_rule, generate_block_id


def parse_heading(element: Tag, style_rules: list) -> HeadingBlock:
    """
    解析标题元素
    
    Args:
        element: h1-h6 标签
        style_rules: 样式规则列表
        
    Returns:
        HeadingBlock 对象
    """
    block_id = generate_block_id("heading")
    level = int(element.name[1])  # h1 -> 1, h2 -> 2, ...
    
    # 提取文本和标记
    text, marks = extract_text_and_marks(element)
    
    # 提取样式
    styles = extract_user_block_styles(element)
    
    # 构建 HeadingBlock
    block = HeadingBlock(
        id=block_id,
        type="heading",
        level=level,
        text=text,
        marks=marks
    )
    
    # 添加样式规则
    if styles:
        add_style_rule(style_rules, block_id, "heading", styles, level=level)
    
    return block
