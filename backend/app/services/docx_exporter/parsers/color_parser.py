"""
颜色解析工具
"""

import re
from typing import Optional, Tuple


def parse_color(color_str: str) -> Optional[Tuple[int, int, int]]:
    """
    解析颜色字符串为 RGB 元组
    
    Args:
        color_str: 颜色字符串(如 "#ff0000" 或 "rgb(255, 0, 0)")
        
    Returns:
        (r, g, b) 元组或 None
    """
    if not color_str:
        return None
    
    # 处理十六进制颜色
    hex_match = re.match(r'#([0-9a-fA-F]{6})', color_str)
    if hex_match:
        hex_color = hex_match.group(1)
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)
    
    # 处理 rgb() 格式
    rgb_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color_str)
    if rgb_match:
        r = int(rgb_match.group(1))
        g = int(rgb_match.group(2))
        b = int(rgb_match.group(3))
        return (r, g, b)
    
    # 处理 rgba() 格式(忽略 alpha)
    rgba_match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*[\d.]+\)', color_str)
    if rgba_match:
        r = int(rgba_match.group(1))
        g = int(rgba_match.group(2))
        b = int(rgba_match.group(3))
        return (r, g, b)
    
    return None
