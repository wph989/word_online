"""
样式处理工具
"""

import logging
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from typing import Dict, Any

from .parsers import parse_color, parse_length, set_paragraph_shading, set_cell_background
from app.config.editor_defaults import get_default_line_height

logger = logging.getLogger(__name__)


def apply_paragraph_style(para, block_id: str, style_map: Dict[str, Dict[str, Any]]):
    """
    应用段落样式
    
    Args:
        para: Word 段落对象
        block_id: Block ID
        style_map: 样式映射字典
    """
    styles = style_map.get(block_id, {})
    
    # 文本对齐
    align = styles.get("textAlign")
    if align == "left":
        para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    elif align == "center":
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "right":
        para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    elif align == "justify":
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    # 行高
    line_height = styles.get("lineHeight")
    if line_height:
        # 尝试解析为倍数
        try:
            # 如果是纯数字字符串或数字，视为倍数行距
            if isinstance(line_height, (int, float)) or (isinstance(line_height, str) and line_height.replace('.', '', 1).isdigit()):
               lh_val = float(line_height)
               para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
               para.paragraph_format.line_spacing = lh_val
            else:
               # 尝试解析为长度（如 20px） -> 固定值
               lh_pt = parse_length(line_height)
               if lh_pt is not None:
                   para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
                   para.paragraph_format.line_spacing = Pt(lh_pt)
        except Exception as e:
            logger.warning(f"应用行高失败: {line_height}, error: {e}")
    else:
        # 如果段落样式中没有设置行高，应用默认行高
        try:
            para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
            para.paragraph_format.line_spacing = get_default_line_height()
        except:
            pass
    
    # 缩进
    text_indent = styles.get("textIndent")
    if text_indent:
        indent_pt = parse_length(text_indent)
        if indent_pt is not None:
            para.paragraph_format.first_line_indent = Pt(indent_pt)
    
    # 段落间距
    margin_top = styles.get("marginTop")
    if margin_top:
        top_pt = parse_length(margin_top)
        if top_pt is not None:
            para.paragraph_format.space_before = Pt(top_pt)
    
    margin_bottom = styles.get("marginBottom")
    if margin_bottom:
        bottom_pt = parse_length(margin_bottom)
        if bottom_pt is not None:
            para.paragraph_format.space_after = Pt(bottom_pt)
    
    # 注意：字号和字体不在段落级别处理，只在字符级别（marks）处理
    # 这样可以避免段落样式覆盖字符级样式
    
    # 颜色
    color = styles.get("color")
    if color:
        rgb = parse_color(color)
        if rgb:
            for run in para.runs:
                run.font.color.rgb = RGBColor(*rgb)
    
    # 背景色
    background_color = styles.get("backgroundColor")
    if background_color:
        rgb = parse_color(background_color)
        if rgb:
            set_paragraph_shading(para, RGBColor(*rgb))


def apply_cell_style(cell, para, cell_id: str, cell_style_map: Dict[str, Dict[str, Any]]):
    """应用单元格样式"""
    styles = cell_style_map.get(cell_id, {})
    
    # 背景色
    background_color = styles.get("backgroundColor")
    if background_color:
        rgb = parse_color(background_color)
        if rgb:
            set_cell_background(cell, RGBColor(*rgb))
    
    # 文本对齐
    text_align = styles.get("textAlign")
    if text_align == "left":
        para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    elif text_align == "center":
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif text_align == "right":
        para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    # 垂直对齐
    vertical_align = styles.get("verticalAlign")
    if vertical_align:
        cell.vertical_alignment = {
            "top": 0,
            "middle": 1,
            "bottom": 2
        }.get(vertical_align, 1)


def apply_header_style(cell, para):
    """为表头单元格应用默认样式"""
    # 设置灰色背景 (#F2F2F2)
    set_cell_background(cell, RGBColor(242, 242, 242))
    
    # 设置文本居中（如果没有其他对齐方式）
    if not para.alignment:
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 设置文本加粗
    for run in para.runs:
        run.bold = True


def apply_page_margins(doc, document_settings: Dict[str, Any]):
    """应用页边距配置到文档"""
    if not document_settings:
        return
    
    from docx.shared import Cm
    
    # 获取页边距配置 (单位: cm)
    margin_top = document_settings.get('margin_top', 2.54)
    margin_bottom = document_settings.get('margin_bottom', 2.54)
    margin_left = document_settings.get('margin_left', 3.17)
    margin_right = document_settings.get('margin_right', 3.17)
    
    # 应用到所有节（Section）
    for section in doc.sections:
        section.top_margin = Cm(margin_top)
        section.bottom_margin = Cm(margin_bottom)
        section.left_margin = Cm(margin_left)
        section.right_margin = Cm(margin_right)
    
    logger.info(f"✅ 应用页边距: 上={margin_top}cm, 下={margin_bottom}cm, 左={margin_left}cm, 右={margin_right}cm")


def configure_heading_styles(doc, document_settings: Dict[str, Any]):
    """配置 Word 的标题样式模板"""
    if not document_settings or 'heading_styles' not in document_settings:
        return
    
    heading_styles_config = document_settings['heading_styles']
    
    for level in range(1, 7):  # Word 支持 Heading 1-6
        h_key = f"h{level}"
        if h_key not in heading_styles_config:
            continue
        
        config = heading_styles_config[h_key]
        style_name = f'Heading {level}'
        
        try:
            # 获取或创建标题样式
            if style_name in doc.styles:
                style = doc.styles[style_name]
            else:
                logger.warning(f"样式 {style_name} 不存在,跳过配置")
                continue
            
            # 配置字体
            if config.get('fontFamily'):
                style.font.name = config['fontFamily']
                # 设置中文字体
                style.element.rPr.rFonts.set(qn('w:eastAsia'), config['fontFamily'])
            
            # 配置字号 (pt)
            if config.get('fontSize'):
                style.font.size = Pt(config['fontSize'])
            
            # 配置颜色
            if config.get('color'):
                rgb = parse_color(config['color'])
                if rgb:
                    style.font.color.rgb = RGBColor(*rgb)
            
            # 配置加粗
            if config.get('fontWeight') == 'bold':
                style.font.bold = True
            
            # 配置段落间距
            if config.get('marginTop'):
                style.paragraph_format.space_before = Pt(config['marginTop'])
            if config.get('marginBottom'):
                style.paragraph_format.space_after = Pt(config['marginBottom'])
            
            logger.info(f"✅ 配置标题样式: {style_name} - 字体={config.get('fontFamily')}, 字号={config.get('fontSize')}pt")
            
        except Exception as e:
            logger.error(f"配置标题样式 {style_name} 失败: {e}", exc_info=True)
