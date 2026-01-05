"""
文本和标记提取器
"""

import re
from bs4 import BeautifulSoup, Tag, NavigableString
from typing import List, Tuple

from app.models.content_models import (
    Mark, SimpleMark, LinkMark, ValueMark
)


def extract_text_and_marks(element: Tag) -> Tuple[str, List[Mark]]:
    """
    从元素中提取纯文本和格式标记(递归遍历法)
    
    优化:
    1. 避免重复标记
    2. 正确处理嵌套标记
    3. 合并相邻的相同标记
    
    Args:
        element: HTML 元素
        
    Returns:
        (text, marks) 元组
    """
    full_text = ""
    marks: List[Mark] = []
    
    def traverse(node, current_marks):
        nonlocal full_text
        
        # 文本节点
        if isinstance(node, NavigableString):
            text_content = str(node)
            if not text_content:
                return
            
            start_idx = len(full_text)
            full_text += text_content
            end_idx = len(full_text)
            
            # 为当前文本段应用所有累积的标记
            if start_idx < end_idx:
                for mark_info in current_marks:
                    range_tuple = (start_idx, end_idx)
                    
                    if mark_info['type'] == 'simple':
                        marks.append(SimpleMark(type=mark_info['name'], range=range_tuple))
                    elif mark_info['type'] == 'link':
                        marks.append(LinkMark(type="link", range=range_tuple, href=mark_info['href']))
                    elif mark_info['type'] == 'value':
                        marks.append(ValueMark(type=mark_info['name'], range=range_tuple, value=mark_info['value']))
            return
        
        if not isinstance(node, Tag):
            return
        
        # 处理当前节点产生的样式
        new_marks = current_marks.copy()
        
        # 1. 语义标签
        if node.name in ['strong', 'b']:
            new_marks.append({'type': 'simple', 'name': 'bold'})
        elif node.name in ['em', 'i']:
            new_marks.append({'type': 'simple', 'name': 'italic'})
        elif node.name == 'u':
            new_marks.append({'type': 'simple', 'name': 'underline'})
        elif node.name in ['s', 'strike', 'del']:
            new_marks.append({'type': 'simple', 'name': 'strike'})
        elif node.name == 'code':
            new_marks.append({'type': 'simple', 'name': 'code'})
        elif node.name == 'sup':
            new_marks.append({'type': 'simple', 'name': 'superscript'})
        elif node.name == 'sub':
            new_marks.append({'type': 'simple', 'name': 'subscript'})
        
        # 2. 链接
        elif node.name == 'a':
            href = node.get('href', '')
            new_marks.append({'type': 'link', 'href': href})
        
        # 3. 内联样式(从 style 属性提取)
        style_attr = node.get('style', '')
        if style_attr:
            # 背景色(必须先匹配,避免被 color 匹配)
            bg_match = re.search(r'background(?:-color)?:\s*([^;]+)', style_attr)
            if bg_match:
                new_marks.append({'type': 'value', 'name': 'backgroundColor', 'value': bg_match.group(1).strip()})
            
            # 颜色(使用负向后顾断言,排除 background-color)
            color_match = re.search(r'(?<!background-)color:\s*([^;]+)', style_attr)
            if color_match:
                new_marks.append({'type': 'value', 'name': 'color', 'value': color_match.group(1).strip()})
            
            # 字号
            size_match = re.search(r'font-size:\s*([^;]+)', style_attr)
            if size_match:
                new_marks.append({'type': 'value', 'name': 'fontSize', 'value': size_match.group(1).strip()})
            
            # 字体
            family_match = re.search(r'font-family:\s*([^;]+)', style_attr)
            if family_match:
                new_marks.append({'type': 'value', 'name': 'fontFamily', 'value': family_match.group(1).strip()})
        
        # 递归遍历子节点
        for child in node.children:
            traverse(child, new_marks)
    
    # 开始递归
    traverse(element, [])
    
    return full_text, marks
