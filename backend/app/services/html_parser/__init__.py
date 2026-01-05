"""
HTML 解析服务 V2 - 优化版
将前端 HTML 解析为数据结构与样式分离的 JSON 格式
确保数据与样式完全分离,且能完全还原为原始 HTML

核心设计原则:
1. 数据与样式严格分离
2. 保留原始 HTML 用于完全还原
3. 提取结构化数据用于 AI 赋能
4. 样式信息独立存储,便于主题切换
"""

from .parser import HtmlParser, parse_html_to_json

__all__ = [
    'HtmlParser',
    'parse_html_to_json'
]
