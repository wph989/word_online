"""
列表解析器
"""

from bs4 import Tag
from app.models.content_models import ParagraphBlock, ParagraphAttrs

from ..extractors import extract_text_and_marks
from ..utils import generate_block_id


def parse_list(element: Tag, blocks: list):
    """
    解析列表元素
    将列表项转换为带 listType 属性的段落
    
    Args:
        element: ul 或 ol 标签
        blocks: 块列表
    """
    list_type = "bullet" if element.name == "ul" else "ordered"
    
    # 递归解析列表项
    parse_list_items(element, list_type, level=0, blocks=blocks)


def parse_list_items(element: Tag, list_type: str, level: int, blocks: list):
    """
    递归解析列表项
    
    Args:
        element: ul/ol 标签
        list_type: "bullet" 或 "ordered"
        level: 嵌套层级
        blocks: 块列表
    """
    for li in element.find_all('li', recursive=False):
        block_id = generate_block_id("para")
        
        # 提取文本和标记
        text, marks = extract_text_and_marks(li)
        
        # 构建段落属性
        attrs = ParagraphAttrs(
            listType=list_type,
            listLevel=level
        )
        
        # 如果是有序列表,添加起始序号
        if list_type == "ordered":
            start = element.get('start', 1)
            attrs.listStart = int(start)
        
        # 构建带列表属性的段落
        block = ParagraphBlock(
            id=block_id,
            type="paragraph",
            text=text,
            marks=marks,
            attrs=attrs
        )
        
        blocks.append(block)
        
        # 递归处理嵌套列表
        nested_list = li.find(['ul', 'ol'], recursive=False)
        if nested_list:
            nested_type = "bullet" if nested_list.name == "ul" else "ordered"
            parse_list_items(nested_list, nested_type, level + 1, blocks)
