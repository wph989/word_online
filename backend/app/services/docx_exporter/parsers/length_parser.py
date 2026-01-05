"""
长度解析工具
"""

import re
from typing import Union, Optional


def parse_font_size(size_str: Union[str, int, float]) -> Optional[float]:
    """
    解析字号字符串为 Pt 数值 (float)
    
    Args:
        size_str: 字号字符串(如 "16px", "10.5pt", "16")
        
    Returns:
        字号(Pt) 或 None
    """
    if not size_str:
        return None
    
    # 如果已经是数字，默认为 pt (因为现在的系统主要推崇 pt)
    if isinstance(size_str, (int, float)):
        return float(size_str)
    
    s = str(size_str).lower().strip()
    
    # 提取数值
    match = re.search(r'(\d+(\.\d+)?)', s)
    if not match:
        return None
        
    val = float(match.group(1))
    
    # 单位判断
    if 'px' in s:
        # px 转 pt (Web常用 1px = 0.75pt)
        return val * 0.75
    
    # 默认或明确为 pt -> 直接返回
    return val


def parse_length(length_val: Union[str, int, float]) -> Optional[float]:
    """
    解析长度值为 Pt 数值 (float)
    支持的单位: px, pt, cm, mm, in, em, rem
    """
    if length_val is None:
        return None
        
    # 如果是数字，默认为 pt (因为 docx 库主要使用 Pt)
    if isinstance(length_val, (int, float)):
        return float(length_val)
        
    s = str(length_val).lower().strip()
    if not s or s == "auto":
        return None
        
    # 提取数值
    match = re.search(r'(-?\d+(\.\d+)?)', s)
    if not match:
        return None
        
    val = float(match.group(1))
    
    # 单位转换
    if 'px' in s:
        return val * 0.75
    elif 'cm' in s:
        return val * 28.3465
    elif 'mm' in s:
        return val * 2.83465
    elif 'in' in s:
        return val * 72.0
    elif 'em' in s or 'rem' in s:
        # 1em 约等于 1个字号，默认按 12pt (小四/五号之间) 计算
        # 对于中文首行缩进 2em，通常期望是 2个汉字宽度
        # Word 中通常用 Character Units，但 python-docx 只支持 Pt/Emu
        return val * 12.0  # 粗略估算
    elif '%' in s:
        # 百分比无法直接转换为固定长度，忽略或返回 None
        return None
        
    # 默认视为 pt
    return val
