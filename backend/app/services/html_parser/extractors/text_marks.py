"""
文本和标记提取器
"""

import re
from bs4 import BeautifulSoup, Tag, NavigableString
from typing import List, Tuple

from app.models.content_models import (
    Mark, SimpleMark, LinkMark, ValueMark
)


def merge_adjacent_marks(marks: List[Mark]) -> List[Mark]:
    """
    合并相邻的相同类型标记
    
    优化策略:
    1. 对于 SimpleMark: 合并相邻且类型相同的标记
    2. 对于 ValueMark: 合并相邻且类型和值都相同的标记
    3. 对于 LinkMark: 合并相邻且 href 相同的标记
    
    Args:
        marks: 原始标记列表
        
    Returns:
        优化后的标记列表
    """
    if not marks:
        return marks
    
    # 按类型分组标记
    from collections import defaultdict
    mark_groups = defaultdict(list)
    
    for mark in marks:
        if isinstance(mark, SimpleMark):
            key = ('simple', mark.type)
        elif isinstance(mark, ValueMark):
            key = ('value', mark.type, mark.value)
        elif isinstance(mark, LinkMark):
            key = ('link', mark.href)
        else:
            # 未知类型,保持原样
            key = ('unknown', id(mark))
        
        mark_groups[key].append(mark)
    
    # 合并每组中的相邻标记
    merged_marks = []
    
    for key, group in mark_groups.items():
        # 按起始位置排序
        group.sort(key=lambda m: m.range[0])
        
        # 合并相邻标记
        i = 0
        while i < len(group):
            current_mark = group[i]
            start, end = current_mark.range
            
            # 查找所有相邻的标记
            j = i + 1
            while j < len(group):
                next_mark = group[j]
                # 如果下一个标记紧接着当前标记(或有重叠)
                # 相邻: next_mark.range[0] == end
                # 重叠: next_mark.range[0] < end
                if next_mark.range[0] <= end:
                    # 扩展范围
                    end = max(end, next_mark.range[1])
                    j += 1
                else:
                    break
            
            # 创建合并后的标记
            if isinstance(current_mark, SimpleMark):
                merged_marks.append(SimpleMark(type=current_mark.type, range=(start, end)))
            elif isinstance(current_mark, ValueMark):
                merged_marks.append(ValueMark(type=current_mark.type, range=(start, end), value=current_mark.value))
            elif isinstance(current_mark, LinkMark):
                merged_marks.append(LinkMark(type=current_mark.type, range=(start, end), href=current_mark.href))
            else:
                # 未知类型,保持原样
                merged_marks.append(current_mark)
            
            i = j
    
    # 按起始位置排序最终结果
    merged_marks.sort(key=lambda m: m.range[0])
    
    return merged_marks


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
            
            # 文本装饰 (text-decoration)
            decoration_match = re.search(r'text-decoration:\s*([^;]+)', style_attr)
            if decoration_match:
                decoration_value = decoration_match.group(1).strip().lower()
                if 'underline' in decoration_value:
                    new_marks.append({'type': 'simple', 'name': 'underline'})
                if 'line-through' in decoration_value:
                    new_marks.append({'type': 'simple', 'name': 'strike'})
        
        # 递归遍历子节点
        for child in node.children:
            traverse(child, new_marks)
    
    # 开始递归
    traverse(element, [])
    
    # 合并相邻的相同标记
    marks = merge_adjacent_marks(marks)
    
    return full_text, marks
