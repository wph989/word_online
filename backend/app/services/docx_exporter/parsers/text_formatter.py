"""
文本格式化工具
"""

import logging
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from typing import Dict, Any, List, Optional

from ..parsers.color_parser import parse_color
from ..parsers.length_parser import parse_font_size
from app.config.editor_defaults import (
    get_default_font_family,
    get_default_font_size_pt
)

logger = logging.getLogger(__name__)


def apply_default_style_to_run(run, default_style: Optional[Dict[str, Any]], inherit_paragraph_style: bool = False):
    """应用默认样式到 run
    
    Args:
        run: Word run 对象
        default_style: 默认样式字典
        inherit_paragraph_style: 是否继承段落样式(True 时不设置字体和字号)
    """
    # 如果继承段落样式(如标题),则不设置默认字体和字号
    # 让 run 继承段落样式模板的设置
    if not inherit_paragraph_style:
        # 基础默认值(仅用于普通段落)
        run.font.name = get_default_font_family()
        run.font.size = Pt(get_default_font_size_pt())
    
    if not default_style:
        return
        
    # 应用传入的覆盖样式
    if default_style.get("fontSize"):
        pt_size = default_style["fontSize"]
        run.font.size = Pt(pt_size)
    
    if default_style.get("color"):
        rgb = parse_color(default_style["color"])
        if rgb:
            run.font.color.rgb = RGBColor(*rgb)
    
    if default_style.get("fontFamily"):
        font_family = default_style["fontFamily"]
        run.font.name = font_family
        # 设置中文字体
        run._element.rPr.rFonts.set(qn('w:eastAsia'), font_family)

    if default_style.get("fontWeight") == "bold":
        run.bold = True


def apply_marks_to_run(run, marks: List[Dict[str, Any]]):
    """应用标记到 run"""
    for mark in marks:
        # 支持字符串或列表类型的 mark type
        raw_type = mark["type"]
        mark_types = raw_type if isinstance(raw_type, list) else [raw_type]
        
        for mark_type in mark_types:
        
            if mark_type == "bold":
                run.bold = True
            elif mark_type == "italic":
                run.italic = True
            elif mark_type == "underline":
                run.underline = True
            elif mark_type == "strike":
                run.font.strike = True
            elif mark_type == "superscript":
                run.font.superscript = True
            elif mark_type == "subscript":
                run.font.subscript = True
            elif mark_type == "color":
                color_str = mark.get("value", "")
                rgb = parse_color(color_str)
                if rgb:
                    run.font.color.rgb = RGBColor(*rgb)
            elif mark_type == "backgroundColor":
                color_str = mark.get("value", "")
                rgb = parse_color(color_str)
                if rgb:
                    set_run_background(run, RGBColor(*rgb))
            elif mark_type == "fontSize":
                size_str = mark.get("value", "")
                size = parse_font_size(size_str)
                if size:
                    run.font.size = Pt(size)
            elif mark_type == "fontFamily":
                family = mark.get("value", "")
                if family:
                    # 清理字体名称：移除引号和多余空格
                    family = family.strip().strip('"').strip("'")
                    # 如果有多个字体（用逗号分隔），只取第一个
                    if ',' in family:
                        family = family.split(',')[0].strip().strip('"').strip("'")
                    
                    logger.debug(f"应用字体: {family}")
                    run.font.name = family
                    # 同时设置东亚字体（对中文很重要）
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), family)


def set_run_background(run, color: RGBColor):
    """设置 run 背景色"""
    try:
        from docx.oxml import OxmlElement
        rPr = run._element.get_or_add_rPr()
        shading = OxmlElement('w:shd')
        # RGBColor 对象需要转换为十六进制字符串
        color_hex = f"{color[0]:02X}{color[1]:02X}{color[2]:02X}" if isinstance(color, tuple) else f"{color.r:02X}{color.g:02X}{color.b:02X}"
        shading.set(qn('w:fill'), color_hex)
        rPr.append(shading)
    except Exception as e:
        logger.error(f"设置 run 背景色失败: {e}")


def set_paragraph_shading(para, color: RGBColor):
    """设置段落背景色"""
    try:
        from docx.oxml import OxmlElement
        pPr = para._element.get_or_add_pPr()
        shading = OxmlElement('w:shd')
        # RGBColor 对象需要转换为十六进制字符串
        color_hex = f"{color[0]:02X}{color[1]:02X}{color[2]:02X}" if isinstance(color, tuple) else f"{color.r:02X}{color.g:02X}{color.b:02X}"
        shading.set(qn('w:fill'), color_hex)
        pPr.append(shading)
    except Exception as e:
        logger.error(f"设置段落背景色失败: {e}")


def set_cell_background(cell, color: RGBColor):
    """设置单元格背景色"""
    try:
        from docx.oxml import OxmlElement
        shading_elm = OxmlElement('w:shd')
        # RGBColor 对象需要转换为十六进制字符串
        color_hex = f"{color[0]:02X}{color[1]:02X}{color[2]:02X}" if isinstance(color, tuple) else f"{color.r:02X}{color.g:02X}{color.b:02X}"
        shading_elm.set(qn('w:fill'), color_hex)
        cell._element.get_or_add_tcPr().append(shading_elm)
    except Exception as e:
        logger.error(f"设置单元格背景色失败: {e}")
