"""
段落解析器
"""

from bs4 import Tag
from app.models.content_models import ParagraphBlock

from ..extractors import extract_text_and_marks, extract_user_block_styles
from ..utils import add_style_rule, generate_block_id


def parse_paragraph(element: Tag, style_rules: list) -> ParagraphBlock:
    """
    解析段落元素
    
    Args:
        element: p 标签
        style_rules: 样式规则列表
        
    Returns:
        ParagraphBlock 对象
    """
    block_id = generate_block_id("para")
    
    # 提取文本内容和标记
    text, marks = extract_text_and_marks(element)
    
    # 提取段落级样式(只提取用户明确设置的样式)
    styles = extract_user_block_styles(element)
    
    # 构建 ParagraphBlock
    block = ParagraphBlock(
        id=block_id,
        type="paragraph",
        text=text,
        marks=marks
    )
    
    # 如果有样式,添加到 StyleSheet
    if styles:
        add_style_rule(style_rules, block_id, "paragraph", styles)
    
    return block
