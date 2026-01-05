"""
HTML 解析服务 V2 - 兼容性包装器
将前端 HTML 解析为数据结构与样式分离的 JSON 格式
确保数据与样式完全分离,且能完全还原为原始 HTML

此文件保持向后兼容性，实际实现已拆分到 html_parser/ 文件夹中
"""

# 导入拆分后的模块
from .html_parser import HtmlParser, parse_html_to_json

# 保持向后兼容性
__all__ = [
    'HtmlParser',
    'parse_html_to_json'
]
