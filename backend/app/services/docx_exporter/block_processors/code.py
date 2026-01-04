"""
代码块处理器
"""

import logging
from docx.shared import Pt, RGBColor
from typing import Dict, Any

logger = logging.getLogger(__name__)


def add_code(doc, block: Dict[str, Any]):
    """添加代码块"""
    text = block.get("text", "")
    language = block.get("language", "")
    
    # 添加语言标签(如果有)
    if language:
        lang_para = doc.add_paragraph(f"[{language}]")
        lang_para.runs[0].font.size = Pt(9)
        lang_para.runs[0].font.color.rgb = RGBColor(128, 128, 128)
    
    # 添加代码内容
    para = doc.add_paragraph(text)
    para.style = 'No Spacing'
    
    # 设置等宽字体和样式
    for run in para.runs:
        run.font.name = 'Courier New'
        run.font.size = Pt(10)
    
    # 添加背景色(通过 shading)
    from ..parsers import set_paragraph_shading
    set_paragraph_shading(para, RGBColor(245, 245, 245))
