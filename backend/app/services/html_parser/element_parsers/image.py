"""
图片解析器
"""

from bs4 import Tag
from app.models.content_models import ImageBlock, ImageMeta

from ..extractors import extract_user_block_styles
from ..utils import add_style_rule, generate_block_id


def parse_image(element: Tag, style_rules: list) -> ImageBlock:
    """
    解析图片元素
    
    Args:
        element: img 标签
        style_rules: 样式规则列表
        
    Returns:
        ImageBlock 对象
    """
    block_id = generate_block_id("image")
    
    # 提取图片属性
    src = element.get('src', '')
    alt = element.get('alt', '')
    width = element.get('width')
    height = element.get('height')
    
    # 构建 ImageMeta
    meta = ImageMeta(alt=alt) if alt else None
    if width:
        if not meta:
            meta = ImageMeta()
        meta.width = int(width) if str(width).isdigit() else width
    if height:
        if not meta:
            meta = ImageMeta()
        meta.height = int(height) if str(height).isdigit() else height
    
    # 构建 ImageBlock
    block = ImageBlock(
        id=block_id,
        type="image",
        src=src,
        meta=meta
    )
    
    # 提取样式
    styles = extract_user_block_styles(element)
    if styles:
        add_style_rule(style_rules, block_id, "image", styles)
    
    return block
