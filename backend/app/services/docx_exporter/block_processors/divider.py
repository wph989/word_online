"""
分割线处理器
"""

import logging
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from typing import Dict, Any

logger = logging.getLogger(__name__)


def add_divider(doc, block: Dict[str, Any]):
    """添加分割线"""
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(6)
    para.paragraph_format.space_after = Pt(6)
    
    # 添加底部边框作为分割线
    pPr = para._element.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')  # 线宽
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '000000')  # 黑色
    
    pBdr.append(bottom)
    pPr.append(pBdr)
