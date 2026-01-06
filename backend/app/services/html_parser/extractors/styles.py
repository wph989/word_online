"""
样式提取器
"""

import re
from bs4 import Tag
from typing import Dict, Any


def extract_user_block_styles(element: Tag) -> Dict[str, Any]:
    """
    提取块级元素的用户明确设置的样式
    (过滤掉浏览器默认样式)
    
    Args:
        element: HTML 元素
        
    Returns:
        样式字典
    """
    styles = {}
    style_attr = element.get('style', '')
    
    if not style_attr:
        return styles
    
    # 文本对齐
    align_match = re.search(r'text-align:\s*([^;]+)', style_attr)
    if align_match:
        align = align_match.group(1).strip()
        # 只保存非默认值
        if align not in ['start', 'left']:
            styles["textAlign"] = align
    
    # 注意：字号(fontSize)和字体(fontFamily)不在段落级别提取
    # 这些样式只在字符级别（marks）中处理，避免段落样式覆盖字符样式
    
    # 颜色(使用负向后顾断言,排除 background-color)
    color_match = re.search(r'(?<!background-)color:\s*([^;]+)', style_attr)
    if color_match:
        color = color_match.group(1).strip()
        # 过滤默认黑色
        if color not in ['rgb(0, 0, 0)', '#000000', '#000', 'black']:
            styles["color"] = color
    
    # 行高
    line_height_match = re.search(r'line-height:\s*([^;]+)', style_attr)
    if line_height_match:
        lh_str = line_height_match.group(1).strip()
        try:
            styles["lineHeight"] = float(lh_str)
        except ValueError:
            pass
    
    # 缩进
    indent_match = re.search(r'text-indent:\s*([^;]+)', style_attr)
    if indent_match:
        styles["textIndent"] = indent_match.group(1).strip()
    
    return styles


def extract_cell_user_styles(cell: Tag) -> Dict[str, Any]:
    """
    提取单元格用户明确设置的样式
    
    Args:
        cell: td/th 元素
        
    Returns:
        样式字典
    """
    styles = {}
    style_attr = cell.get('style', '')
    
    # 文本对齐
    text_align = None
    if 'text-align' in style_attr:
        align_match = re.search(r'text-align:\s*([^;]+)', style_attr)
        if align_match:
            text_align = align_match.group(1).strip()
    elif cell.get('align'):
        text_align = cell.get('align')
    
    if text_align and text_align not in ['start', 'left']:
        styles["textAlign"] = text_align
    
    # 垂直对齐
    vertical_align = None
    if 'vertical-align' in style_attr:
        valign_match = re.search(r'vertical-align:\s*([^;]+)', style_attr)
        if valign_match:
            vertical_align = valign_match.group(1).strip()
    elif cell.get('valign'):
        vertical_align = cell.get('valign')
    
    if vertical_align and vertical_align != 'baseline':
        styles["verticalAlign"] = vertical_align
    
    # 字体
    family_match = re.search(r'font-family:\s*([^;]+)', style_attr)
    if family_match:
        styles["fontFamily"] = family_match.group(1).strip()
    
    # 字号
    size_match = re.search(r'font-size:\s*([^;]+)', style_attr)
    if size_match:
        size_str = size_match.group(1).strip()
        size_num = re.search(r'(\d+)', size_str)
        if size_num:
            styles["fontSize"] = int(size_num.group(1))
    
    # 字体粗细
    weight_match = re.search(r'font-weight:\s*([^;]+)', style_attr)
    if weight_match:
        weight = weight_match.group(1).strip()
        if weight not in ['normal', '400']:
            styles["fontWeight"] = weight
    
    # 文本颜色(使用负向后顾断言,排除 background-color)
    color_match = re.search(r'(?<!background-)color:\s*([^;]+)', style_attr)
    if color_match:
        color = color_match.group(1).strip()
        if color not in ['rgb(0, 0, 0)', '#000000', '#000', 'black']:
            styles["color"] = color
    
    # 背景颜色
    bg_color = None
    if 'background-color' in style_attr or 'background:' in style_attr:
        bg_match = re.search(r'background(?:-color)?:\s*([^;]+)', style_attr)
        if bg_match:
            bg_color = bg_match.group(1).strip()
    elif cell.get('bgcolor'):
        bg_color = cell.get('bgcolor')
    
    if bg_color and bg_color not in ['transparent', 'rgba(0, 0, 0, 0)']:
        styles["backgroundColor"] = bg_color
    
    return styles


def extract_table_styles(table: Tag) -> Dict[str, Any]:
    """
    提取表格级样式
    
    Args:
        table: table 元素
        
    Returns:
        样式字典
    """
    styles = {}
    style_attr = table.get('style', '')
    
    # 边框
    border_match = re.search(r'border:\s*([^;]+)', style_attr)
    if border_match:
        border_str = border_match.group(1).strip()
        parts = border_str.split()
        if len(parts) >= 3:
            width_match = re.search(r'\d+', parts[0])
            if width_match:
                styles["borderWidth"] = int(width_match.group())
            styles["borderStyle"] = parts[1]
            styles["borderColor"] = parts[2]
    
    # 宽度
    width_match = re.search(r'width:\s*([^;]+)', style_attr)
    if width_match:
        width = width_match.group(1).strip()
        if width != 'auto':
            styles["width"] = width
    
    # 边框折叠
    collapse_match = re.search(r'border-collapse:\s*([^;]+)', style_attr)
    if collapse_match:
        styles["borderCollapse"] = collapse_match.group(1).strip()

    # 表格布局 (critical for fixed width columns)
    layout_match = re.search(r'table-layout:\s*([^;]+)', style_attr)
    if layout_match:
        styles["tableLayout"] = layout_match.group(1).strip()
    
    return styles
