"""
Word 文档导出服务
将 Content 和 StyleSheet 导出为 .docx 文件

功能特性:
1. 支持段落、标题、表格、图片、代码块、分割线
2. 支持丰富的文本标记(加粗、斜体、颜色、字号、字体等)
3. 支持表格合并单元格和单元格样式
4. 支持列表(有序、无序)
5. 支持行高、缩进、对齐等段落样式
"""

from .exporter import DocxExporter

__all__ = ['DocxExporter']
