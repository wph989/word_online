"""
标题处理器
"""

import logging
from typing import Dict, Any

from ..style_utils import apply_paragraph_style
from .paragraph import add_text_with_marks

logger = logging.getLogger(__name__)


def add_heading(doc, block: Dict[str, Any], style_map: Dict[str, Dict[str, Any]], 
                heading_number_generator=None):
    """添加标题
    
    标题格式处理规则:
    1. 标题样式模板在 configure_heading_styles() 中已配置到 Word 文档
    2. 创建的标题段落会自动继承对应的样式模板(Heading 1-6)
    3. 如果启用了编号生成器，会在标题文本前添加编号前缀
    4. 如果文本有 mark 格式,在样式模板基础上叠加这些格式
    5. mark 格式只影响当前标题文本,不修改样式模板本身
    
    Args:
        doc: Word 文档对象
        block: Block 字典
        style_map: 样式映射
        heading_number_generator: 标题编号生成器（可选）
    """
    level = block.get("level", 1)
    text = block.get("text", "")
    marks = block.get("marks", [])
    block_id = block.get("id")
    
    # 获取编号前缀（如果启用）
    number_prefix = ""
    if heading_number_generator:
        number_prefix = heading_number_generator.get_number(level)
    
    # 创建标题段落 (会自动应用对应的 Heading 样式模板)
    para = doc.add_heading(level=level)
    para.text = ""  # 清空默认文本
    # 显式清除所有 runs,防止保留一个空 run
    for run in list(para.runs):
        run._element.getparent().remove(run._element)
    
    # 添加编号前缀（如果有）
    if number_prefix:
        # 编号部分使用标题样式，但不应用 marks
        prefix_run = para.add_run(number_prefix)
        # 编号继承段落样式
    
    # 添加文本和标记
    # inherit_paragraph_style=True 表示 run 继承段落样式模板,不应用默认字体和字号
    # marks 会在样式模板的基础上叠加(如局部加粗、变色等)
    add_text_with_marks(para, text, marks, inherit_paragraph_style=True)
    
    # 应用 StyleSheet 中的段落级样式(如对齐、行高等)
    apply_paragraph_style(para, block_id, style_map)
