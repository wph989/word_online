"""
代码块解析器
"""

from bs4 import Tag
from app.models.content_models import CodeBlock

from ..utils import generate_block_id


def parse_code_block(element: Tag) -> CodeBlock:
    """
    解析代码块元素
    
    Args:
        element: pre 标签
        
    Returns:
        CodeBlock 对象
    """
    block_id = generate_block_id("code")
    
    # 提取语言
    language = None
    code_tag = element.find('code')
    if code_tag:
        # 尝试提取 class="language-xxx"
        classes = code_tag.get('class', [])
        for cls in classes:
            if cls.startswith('language-'):
                language = cls.replace('language-', '')
                break
        
        text = code_tag.get_text()
    else:
        text = element.get_text()
        
    return CodeBlock(
        id=block_id,
        type="code",
        text=text,
        language=language
    )
