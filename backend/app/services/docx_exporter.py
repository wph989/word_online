"""
Word 文档导出服务
将 Content 和 StyleSheet 导出为 .docx 文件
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from typing import Dict, Any, List
import io
import re


class DocxExporter:
    """
    Word 文档导出器
    将结构化的 Content 和 StyleSheet 转换为 Word 文档
    """
    
    def __init__(self, content: Dict[str, Any], stylesheet: Dict[str, Any]):
        """
        初始化导出器
        
        Args:
            content: Content JSON
            stylesheet: StyleSheet JSON
        """
        self.content = content
        self.stylesheet = stylesheet
        self.doc = Document()
        self.style_map = self._build_style_map()
    
    def export(self) -> io.BytesIO:
        """
        执行导出，生成 Word 文档
        
        Returns:
            包含 .docx 文件的 BytesIO 对象
        """
        # 处理所有 Block
        for block in self.content.get("blocks", []):
            self._process_block(block)
        
        # 保存到内存
        file_stream = io.BytesIO()
        self.doc.save(file_stream)
        file_stream.seek(0)
        
        return file_stream
    
    def _build_style_map(self) -> Dict[str, Dict[str, Any]]:
        """构建 Block ID 到样式的映射"""
        style_map = {}
        
        for rule in self.stylesheet.get("rules", []):
            target = rule.get("target", {})
            block_ids = target.get("blockIds", [])
            styles = rule.get("style", {})
            
            for block_id in block_ids:
                if block_id not in style_map:
                    style_map[block_id] = {}
                style_map[block_id].update(styles)
        
        return style_map
    
    def _process_block(self, block: Dict[str, Any]):
        """
        处理单个 Block
        
        Args:
            block: Block 字典
        """
        block_type = block.get("type")
        
        if block_type == "paragraph":
            self._add_paragraph(block)
        elif block_type == "heading":
            self._add_heading(block)
        elif block_type == "table":
            self._add_table(block)
        elif block_type == "image":
            self._add_image(block)
        elif block_type == "code":
            self._add_code(block)
    
    def _add_paragraph(self, block: Dict[str, Any]):
        """添加段落"""
        text = block.get("text", "")
        marks = block.get("marks", [])
        block_id = block.get("id")
        attrs = block.get("attrs", {})
        
        # 创建段落
        para = self.doc.add_paragraph()
        
        # 应用列表样式
        list_type = attrs.get("listType")
        if list_type == "bullet":
            para.style = 'List Bullet'
        elif list_type == "ordered":
            para.style = 'List Number'
        
        # 添加文本和标记
        self._add_text_with_marks(para, text, marks)
        
        # 应用段落样式
        self._apply_paragraph_style(para, block_id)
    
    def _add_heading(self, block: Dict[str, Any]):
        """添加标题"""
        level = block.get("level", 1)
        text = block.get("text", "")
        marks = block.get("marks", [])
        block_id = block.get("id")
        
        # 创建标题段落
        para = self.doc.add_heading(level=level)
        para.text = ""  # 清空默认文本
        
        # 添加文本和标记
        self._add_text_with_marks(para, text, marks)
        
        # 应用样式
        self._apply_paragraph_style(para, block_id)
    
    def _add_table(self, block: Dict[str, Any]):
        """添加表格（支持合并单元格）"""
        table_data = block.get("data", {})
        rows = table_data.get("rows", 0)
        cols = table_data.get("cols", 0)
        cells = table_data.get("cells", [])
        merge_regions = table_data.get("mergeRegions", [])
        
        # 创建表格
        table = self.doc.add_table(rows=rows, cols=cols)
        table.style = 'Table Grid'
        
        # 构建单元格映射
        cell_map = {tuple(cell["cell"]): cell for cell in cells}
        
        # 填充单元格内容
        for row_idx in range(rows):
            for col_idx in range(cols):
                cell_data = cell_map.get((row_idx, col_idx))
                if cell_data:
                    cell = table.cell(row_idx, col_idx)
                    content = cell_data.get("content", {})
                    text = content.get("text", "")
                    marks = content.get("marks", [])
                    
                    # 清空默认段落
                    cell.text = ""
                    para = cell.paragraphs[0]
                    
                    # 添加文本和标记
                    self._add_text_with_marks(para, text, marks)
        
        # 处理合并单元格
        for region in merge_regions:
            start_row, start_col = region["start"]
            end_row, end_col = region["end"]
            
            # 合并单元格
            start_cell = table.cell(start_row, start_col)
            end_cell = table.cell(end_row, end_col)
            start_cell.merge(end_cell)
    
    def _add_image(self, block: Dict[str, Any]):
        """添加图片"""
        src = block.get("src", "")
        meta = block.get("meta", {})
        
        # 这里需要根据 src 加载图片
        # 简化处理：如果是本地路径或 URL，尝试添加
        try:
            width = meta.get("width")
            if width:
                width_inches = Inches(width / 96)  # 假设 96 DPI
                self.doc.add_picture(src, width=width_inches)
            else:
                self.doc.add_picture(src)
        except Exception as e:
            # 如果图片加载失败，添加占位文本
            para = self.doc.add_paragraph(f"[图片: {src}]")
            para.italic = True
    
    def _add_code(self, block: Dict[str, Any]):
        """添加代码块"""
        text = block.get("text", "")
        
        para = self.doc.add_paragraph(text)
        para.style = 'No Spacing'
        
        # 设置等宽字体
        for run in para.runs:
            run.font.name = 'Courier New'
            run.font.size = Pt(10)
    
    def _add_text_with_marks(self, para, text: str, marks: List[Dict[str, Any]]):
        """
        添加带标记的文本到段落
        
        Args:
            para: Word 段落对象
            text: 文本内容
            marks: 标记列表
        """
        if not marks:
            para.add_run(text)
            return
        
        # 按范围排序标记
        sorted_marks = sorted(marks, key=lambda m: m["range"][0])
        
        last_pos = 0
        for mark in sorted_marks:
            mark_type = mark["type"]
            start, end = mark["range"]
            
            # 添加标记前的文本
            if start > last_pos:
                para.add_run(text[last_pos:start])
            
            # 添加标记文本
            run = para.add_run(text[start:end])
            
            # 应用标记格式
            if mark_type == "bold":
                run.bold = True
            elif mark_type == "italic":
                run.italic = True
            elif mark_type == "underline":
                run.underline = True
            elif mark_type == "strike":
                run.font.strike = True
            elif mark_type == "color":
                color_str = mark.get("value", "")
                rgb = self._parse_color(color_str)
                if rgb:
                    run.font.color.rgb = RGBColor(*rgb)
            elif mark_type == "fontSize":
                size_str = mark.get("value", "")
                size = self._parse_font_size(size_str)
                if size:
                    run.font.size = Pt(size)
            elif mark_type == "fontFamily":
                family = mark.get("value", "")
                run.font.name = family
            
            last_pos = end
        
        # 添加剩余文本
        if last_pos < len(text):
            para.add_run(text[last_pos:])
    
    def _apply_paragraph_style(self, para, block_id: str):
        """
        应用段落样式
        
        Args:
            para: Word 段落对象
            block_id: Block ID
        """
        styles = self.style_map.get(block_id, {})
        
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
        
        # 字号（应用到所有 run）
        font_size = styles.get("fontSize")
        if font_size:
            for run in para.runs:
                run.font.size = Pt(font_size)
        
        # 颜色
        color = styles.get("color")
        if color:
            rgb = self._parse_color(color)
            if rgb:
                for run in para.runs:
                    run.font.color.rgb = RGBColor(*rgb)
    
    def _parse_color(self, color_str: str) -> tuple:
        """
        解析颜色字符串为 RGB 元组
        
        Args:
            color_str: 颜色字符串（如 "#ff0000" 或 "rgb(255, 0, 0)"）
            
        Returns:
            (r, g, b) 元组或 None
        """
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
        
        return None
    
    def _parse_font_size(self, size_str: str) -> int:
        """
        解析字号字符串为数字
        
        Args:
            size_str: 字号字符串（如 "16px" 或 "16"）
            
        Returns:
            字号数字或 None
        """
        match = re.search(r'(\d+)', size_str)
        if match:
            return int(match.group(1))
        return None
