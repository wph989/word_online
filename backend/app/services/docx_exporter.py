"""
Word 文档导出服务 - 兼容性包装器
将 Content 和 StyleSheet 导出为 .docx 文件

此文件保持向后兼容性，实际实现已拆分到 docx_exporter/ 文件夹中
"""

# 导入拆分后的模块
from .docx_exporter import DocxExporter

# 保持向后兼容性
__all__ = ['DocxExporter']
