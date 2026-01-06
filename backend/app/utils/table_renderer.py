"""
表格渲染工具（重构版）
使用 Pydantic 模型，将 TableData 结构渲染为 HTML table
支持合并单元格的正确渲染
"""

from typing import Dict, Set, Any
import html as html_lib

from app.models.content_models import TableData, Mark, SimpleMark, LinkMark, ValueMark


class TableRenderer:
    """
    表格渲染器
    将 TableData 渲染为 HTML，正确处理合并单元格
    """
    
    def __init__(self, table_data: TableData, table_styles: Dict[str, Any] = None, style_map: Dict[str, Dict[str, Any]] = None, column_widths: Dict[int, str] = None):
        """
        初始化渲染器
        
        Args:
            table_data: TableData 对象
            table_styles: 表格样式（可选）
            style_map: Block ID 到样式的映射（可选）
            column_widths: 列索引到宽度的映射（可选）
        """
        self.data = table_data
        self.styles = table_styles or {}
        self.style_map = style_map or {}  # 用于查找单元格样式
        self.column_widths = column_widths or {}  # 列宽度
        
        # 构建单元格位置到数据的映射
        self.cell_map = {
            cell.cell: cell 
            for cell in self.data.cells
        }
        
        # 构建被合并单元格的集合
        self.merged_cells = self._build_merged_cells_set()
    
    def render(self) -> str:
        """
        渲染表格为 HTML
        
        Returns:
            HTML 字符串
        """
        # 构建表格样式
        table_style = self._build_table_style()
        style_attr = f' style="{table_style}"' if table_style else ''
        
        # 开始构建 HTML
        html_parts = [f'<table{style_attr}>']
        
        # 渲染 colgroup(列宽度)
        colgroup_html = self._render_colgroup()
        if colgroup_html:
            html_parts.append(colgroup_html)
        
        # 渲染每一行
        for row_idx in range(self.data.rows):
            html_parts.append('  <tr>')
            html_parts.append(self._render_row(row_idx))
            html_parts.append('  </tr>')
        
        html_parts.append('</table>')
        
        return '\n'.join(html_parts)
    
    def _render_colgroup(self) -> str:
        """
        渲染 colgroup(列宽度)
        
        Returns:
            colgroup HTML 或空字符串
        """
        if not self.column_widths:
            return ""
        
        col_parts = []
        for col_idx in range(self.data.cols):
            if col_idx in self.column_widths:
                width = self.column_widths[col_idx]
                col_parts.append(f'<col width="{width}">')
            else:
                col_parts.append('<col>')
        
        if col_parts:
            return f'<colgroup>{"".join(col_parts)}</colgroup>'
        return ""
    
    def _build_merged_cells_set(self) -> Set[tuple]:
        """
        构建被合并单元格的位置集合
        
        Returns:
            被合并单元格的 (row, col) 集合
        """
        merged = set()
        
        for region in self.data.mergeRegions:
            start_row, start_col = region.start
            end_row, end_col = region.end
            master_row, master_col = region.masterCell
            
            # 添加所有被合并的单元格（除了主单元格）
            for r in range(start_row, end_row + 1):
                for c in range(start_col, end_col + 1):
                    if r != master_row or c != master_col:
                        merged.add((r, c))
        
        return merged
    
    def _render_row(self, row_idx: int) -> str:
        """
        渲染单行
        
        Args:
            row_idx: 行索引
            
        Returns:
            行内所有单元格的 HTML
        """
        cells_html = []
        
        for col_idx in range(self.data.cols):
            # 跳过被合并的单元格
            if (row_idx, col_idx) in self.merged_cells:
                continue
            
            # 渲染单元格
            cell_html = self._render_cell(row_idx, col_idx)
            if cell_html:
                cells_html.append(cell_html)
        
        return '\n    '.join(cells_html)
    
    def _render_cell(self, row_idx: int, col_idx: int) -> str:
        """
        渲染单个单元格
        
        Args:
            row_idx: 行索引
            col_idx: 列索引
            
        Returns:
            单元格 HTML
        """
        # 获取单元格数据
        cell_data = self.cell_map.get((row_idx, col_idx))
        
        # 如果没有数据，创建空单元格
        if not cell_data:
            return '<td></td>'
        
        # 提取内容
        text = cell_data.content.text
        marks = cell_data.content.marks
        
        # 应用标记
        formatted_text = self._apply_marks(text, marks)
        
        # 检查是否是合并单元格的主单元格
        rowspan, colspan = self._get_span(row_idx, col_idx)
        
        # 构建属性
        attrs = []
        
        # colspan 和 rowspan
        if rowspan > 1:
            attrs.append(f'rowSpan="{rowspan}"')  # WangEditor 使用 rowSpan
        if colspan > 1:
            attrs.append(f'colSpan="{colspan}"')  # WangEditor 使用 colSpan
        
        # width 属性 - 从 column_widths 中读取
        if col_idx in self.column_widths:
            width = self.column_widths[col_idx]
            attrs.append(f'width="{width}"')
        else:
            attrs.append('width="auto"')
        
        # 单元格样式 - 合并默认样式和 styleId 样式
        cell_style_parts = []
        
        # 默认边框和内边距
        cell_style_parts.append("border: 1px solid #ddd")
        cell_style_parts.append("padding: 8px")
        
        # 如果有 styleId,从 StyleSheet 中读取样式
        if hasattr(cell_data, 'styleId') and cell_data.styleId:
            cell_styles = self._get_cell_styles_from_stylesheet(cell_data.styleId)
            if cell_styles:
                # 文本对齐
                if "textAlign" in cell_styles:
                    cell_style_parts.append(f"text-align: {cell_styles['textAlign']}")
                
                # 垂直对齐
                if "verticalAlign" in cell_styles:
                    cell_style_parts.append(f"vertical-align: {cell_styles['verticalAlign']}")
                
                # 字体
                if "fontFamily" in cell_styles:
                    cell_style_parts.append(f"font-family: {cell_styles['fontFamily']}")
                
                # 字号
                if "fontSize" in cell_styles:
                    cell_style_parts.append(f"font-size: {cell_styles['fontSize']}px")
                
                # 字体粗细
                if "fontWeight" in cell_styles:
                    cell_style_parts.append(f"font-weight: {cell_styles['fontWeight']}")
                
                # 文本颜色
                if "color" in cell_styles:
                    cell_style_parts.append(f"color: {cell_styles['color']}")
                
                # 背景颜色
                if "backgroundColor" in cell_styles:
                    cell_style_parts.append(f"background-color: {cell_styles['backgroundColor']}")
        
        if cell_style_parts:
            style_str = "; ".join(cell_style_parts)
            attrs.append(f'style="{style_str}"')
        
        # 判断是表头还是数据单元格
        tag = 'th' if row_idx == 0 else 'td'
        
        attrs_str = ' ' + ' '.join(attrs) if attrs else ''
        return f'<{tag}{attrs_str}>{formatted_text}</{tag}>'
    
    def _get_cell_styles_from_stylesheet(self, style_id: str) -> Dict[str, Any]:
        """
        从 StyleSheet 中获取单元格样式
        
        Args:
            style_id: 样式 ID
            
        Returns:
            样式字典
        """
        return self.style_map.get(style_id, {})
    
    def _get_span(self, row_idx: int, col_idx: int) -> tuple[int, int]:
        """
        获取单元格的 rowspan 和 colspan
        
        Args:
            row_idx: 行索引
            col_idx: 列索引
            
        Returns:
            (rowspan, colspan) 元组
        """
        # 查找该单元格是否是某个合并区域的主单元格
        for region in self.data.mergeRegions:
            master_row, master_col = region.masterCell
            if master_row == row_idx and master_col == col_idx:
                start_row, start_col = region.start
                end_row, end_col = region.end
                rowspan = end_row - start_row + 1
                colspan = end_col - start_col + 1
                return rowspan, colspan
        
        return 1, 1
    
    def _apply_marks(self, text: str, marks: list[Mark]) -> str:
        """
        应用格式标记到文本
        
        Args:
            text: 原始文本
            marks: 标记列表
            
        Returns:
            格式化后的 HTML
        """
        if not marks:
            return html_lib.escape(text)
        
        # 1. 收集所有分段点
        positions = {0, len(text)}
        for mark in marks:
            positions.add(mark.range[0])
            positions.add(mark.range[1])
        
        sorted_positions = sorted(positions)
        
        # 2. 对每个片段应用标记
        result = []
        for i in range(len(sorted_positions) - 1):
            start = sorted_positions[i]
            end = sorted_positions[i + 1]
            
            if start >= end:
                continue
            
            segment_text = html_lib.escape(text[start:end])
            if not segment_text:
                continue
                
            # 3. 找出覆盖该片段的所有标记
            active_marks = [
                m for m in marks 
                if m.range[0] <= start and m.range[1] >= end
            ]
            
            # 4. 分组标记
            simple_marks = [m for m in active_marks if isinstance(m, SimpleMark)]
            value_marks = [m for m in active_marks if isinstance(m, ValueMark)]
            
            # 5. 先应用 SimpleMark - 反转顺序,后应用的标签在外层
            current_html = segment_text
            for mark in reversed(simple_marks):
                if mark.type == "bold":
                    current_html = f"<strong>{current_html}</strong>"
                elif mark.type == "italic":
                    current_html = f"<em>{current_html}</em>"
                elif mark.type == "underline":
                    current_html = f"<u>{current_html}</u>"
                elif mark.type == "strike":
                    current_html = f"<s>{current_html}</s>"
                elif mark.type == "superscript":
                    current_html = f"<sup>{current_html}</sup>"
                elif mark.type == "subscript":
                    current_html = f"<sub>{current_html}</sub>"
            
            # 6. 再应用 ValueMark(span 在最外层)
            if value_marks:
                styles = []
                for mark in value_marks:
                    if mark.type == "color":
                        styles.append(f"color: {mark.value}")
                    elif mark.type == "backgroundColor":
                        styles.append(f"background-color: {mark.value}")
                    elif mark.type == "fontSize":
                        styles.append(f"font-size: {mark.value}")
                    elif mark.type == "fontFamily":
                        styles.append(f"font-family: {mark.value}")
                
                if styles:
                    style_attr = "; ".join(styles) + ";"
                    current_html = f'<span style="{style_attr}">{current_html}</span>'
            
            result.append(current_html)
        
        return "".join(result)
    
    def _build_table_style(self) -> str:
        """
        构建表格级样式
        
        Returns:
            CSS 字符串
        """
        css_parts = []
        
        # 默认样式
        css_parts.append("border-collapse: collapse")
        
        # 应用自定义样式
        if "width" in self.styles:
            width = self.styles["width"]
            if isinstance(width, int):
                css_parts.append(f"width: {width}px")
            else:
                css_parts.append(f"width: {width}")
        
        if "borderWidth" in self.styles:
            css_parts.append(f"border-width: {self.styles['borderWidth']}px")
        if "borderStyle" in self.styles:
            css_parts.append(f"border-style: {self.styles['borderStyle']}")
        if "borderColor" in self.styles:
            css_parts.append(f"border-color: {self.styles['borderColor']}")
        
        # 表格布局
        if "tableLayout" in self.styles:
            css_parts.append(f"table-layout: {self.styles['tableLayout']}")
        
        return "; ".join(css_parts)
    
    def _build_cell_style(self, row_idx: int, col_idx: int) -> str:
        """
        构建单元格样式
        
        Args:
            row_idx: 行索引
            col_idx: 列索引
            
        Returns:
            CSS 字符串
        """
        css_parts = []
        
        # 默认边框
        css_parts.append("border: 1px solid #ddd")
        css_parts.append("padding: 8px")
        
        # 这里可以根据 StyleSheet 中的单元格样式规则进行扩展
        
        return "; ".join(css_parts)
