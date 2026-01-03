"""
表格解析工具（重构版）
使用 Pydantic 模型，专门处理 HTML 表格的解析
完整支持合并单元格（rowspan 和 colspan）
"""

from bs4 import Tag
from typing import List
import uuid

from app.models.content_models import (
    TableData, TableCellData, TableCellContent, MergeRegion,
    Mark, SimpleMark, LinkMark, ValueMark
)
import re


class TableParser:
    """
    表格解析器
    将 HTML table 元素转换为 TableData 结构
    完整支持 rowspan 和 colspan
    
    算法：
    1. 创建占用矩阵，跟踪哪些单元格被合并占用
    2. 遍历所有单元格，提取内容和标记
    3. 识别合并区域，生成 MergeRegion 对象
    """
    
    def __init__(self, table_element: Tag):
        """
        初始化表格解析器
        
        Args:
            table_element: BeautifulSoup 的 table Tag 对象
        """
        self.table = table_element
        self.cells: List[TableCellData] = []
        self.merge_regions: List[MergeRegion] = []
        self.rows = 0
        self.cols = 0
    
    def parse(self) -> TableData:
        """
        执行解析
        
        Returns:
            TableData 对象
        """
        # 获取所有行
        tr_elements = self.table.find_all('tr')
        self.rows = len(tr_elements)
        
        # 计算最大列数
        self._calculate_dimensions(tr_elements)
        
        # 创建占用矩阵，用于跟踪哪些单元格被合并占用
        occupancy = [[False] * self.cols for _ in range(self.rows)]
        
        # 解析每一行
        for row_idx, tr in enumerate(tr_elements):
            self._parse_row(tr, row_idx, occupancy)
        
        # 构建 TableData 对象
        return TableData(
            rows=self.rows,
            cols=self.cols,
            cells=self.cells,
            mergeRegions=self.merge_regions
        )
    
    def _calculate_dimensions(self, tr_elements: List[Tag]):
        """
        计算表格的实际列数（考虑 colspan）
        
        Args:
            tr_elements: 所有 tr 元素列表
        """
        max_cols = 0
        
        for tr in tr_elements:
            cells = tr.find_all(['td', 'th'])
            col_count = 0
            
            for cell in cells:
                colspan = int(cell.get('colspan', 1))
                col_count += colspan
            
            max_cols = max(max_cols, col_count)
        
        self.cols = max_cols
    
    def _parse_row(self, tr: Tag, row_idx: int, occupancy: List[List[bool]]):
        """
        解析单行
        
        Args:
            tr: tr 元素
            row_idx: 行索引
            occupancy: 占用矩阵
        """
        cells = tr.find_all(['td', 'th'])
        col_idx = 0
        
        for cell in cells:
            # 跳过已被合并占用的列
            while col_idx < self.cols and occupancy[row_idx][col_idx]:
                col_idx += 1
            
            if col_idx >= self.cols:
                break
            
            # 获取 rowspan 和 colspan
            rowspan = int(cell.get('rowspan', 1))
            colspan = int(cell.get('colspan', 1))
            
            # 提取单元格内容和标记
            text, marks = self._extract_cell_content(cell)
            
            # 创建 TableCellContent
            content = TableCellContent(
                text=text,
                marks=marks
            )
            
            # 创建 TableCellData
            cell_data = TableCellData(
                cell=(row_idx, col_idx),
                content=content
            )
            
            self.cells.append(cell_data)
            
            # 标记占用的单元格
            for r in range(row_idx, min(row_idx + rowspan, self.rows)):
                for c in range(col_idx, min(col_idx + colspan, self.cols)):
                    occupancy[r][c] = True
            
            # 如果有合并，创建合并区域
            if rowspan > 1 or colspan > 1:
                merge_type = self._get_merge_type(rowspan, colspan)
                merge_region = MergeRegion(
                    id=f"merge-{row_idx}-{col_idx}",
                    start=(row_idx, col_idx),
                    end=(row_idx + rowspan - 1, col_idx + colspan - 1),
                    masterCell=(row_idx, col_idx),
                    type=merge_type
                )
                self.merge_regions.append(merge_region)
            
            col_idx += 1
    
    def _extract_cell_content(self, cell: Tag) -> tuple[str, List[Mark]]:
        """
        提取单元格的文本和格式标记
        
        Args:
            cell: td 或 th 元素
            
        Returns:
            (text, marks) 元组
        """
        text = cell.get_text()
        marks: List[Mark] = []
        
        # 粗体
        for bold in cell.find_all(['strong', 'b']):
            mark_range = self._get_text_range(cell, bold)
            if mark_range:
                marks.append(SimpleMark(type="bold", range=mark_range))
        
        # 斜体
        for italic in cell.find_all(['em', 'i']):
            mark_range = self._get_text_range(cell, italic)
            if mark_range:
                marks.append(SimpleMark(type="italic", range=mark_range))
        
        # 下划线
        for underline in cell.find_all('u'):
            mark_range = self._get_text_range(cell, underline)
            if mark_range:
                marks.append(SimpleMark(type="underline", range=mark_range))
        
        # 删除线
        for strike in cell.find_all(['s', 'strike', 'del']):
            mark_range = self._get_text_range(cell, strike)
            if mark_range:
                marks.append(SimpleMark(type="strike", range=mark_range))
        
        # 从 span 提取颜色、字号等
        for span in cell.find_all('span'):
            style = span.get('style', '')
            mark_range = self._get_text_range(cell, span)
            
            if not mark_range:
                continue
            
            # 颜色
            color_match = re.search(r'color:\s*([^;]+)', style)
            if color_match:
                marks.append(ValueMark(
                    type="color",
                    range=mark_range,
                    value=color_match.group(1).strip()
                ))
            
            # 背景色
            bg_match = re.search(r'background(?:-color)?:\s*([^;]+)', style)
            if bg_match:
                marks.append(ValueMark(
                    type="backgroundColor",
                    range=mark_range,
                    value=bg_match.group(1).strip()
                ))
            
            # 字号
            size_match = re.search(r'font-size:\s*([^;]+)', style)
            if size_match:
                marks.append(ValueMark(
                    type="fontSize",
                    range=mark_range,
                    value=size_match.group(1).strip()
                ))
            
            # 字体
            family_match = re.search(r'font-family:\s*([^;]+)', style)
            if family_match:
                marks.append(ValueMark(
                    type="fontFamily",
                    range=mark_range,
                    value=family_match.group(1).strip()
                ))
        
        return text, marks
    
    def _get_text_range(self, parent: Tag, child: Tag) -> tuple[int, int] | None:
        """
        获取子元素在父元素文本中的范围
        
        Args:
            parent: 父元素
            child: 子元素
            
        Returns:
            (start, end) 或 None
        """
        parent_text = parent.get_text()
        child_text = child.get_text()
        
        if not child_text:
            return None
        
        start = parent_text.find(child_text)
        if start == -1:
            return None
        
        return (start, start + len(child_text))
    
    def _get_merge_type(self, rowspan: int, colspan: int) -> str:
        """
        判断合并类型
        
        Args:
            rowspan: 行跨度
            colspan: 列跨度
            
        Returns:
            "horizontal" | "vertical" | "rectangular"
        """
        if rowspan == 1 and colspan > 1:
            return "horizontal"
        elif rowspan > 1 and colspan == 1:
            return "vertical"
        else:
            return "rectangular"
