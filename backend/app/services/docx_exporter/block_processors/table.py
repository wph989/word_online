"""
表格处理器
"""

import logging
from typing import Dict, Any

from ..style_utils import apply_cell_style, apply_header_style

logger = logging.getLogger(__name__)


def add_table(doc, block: Dict[str, Any], cell_style_map: Dict[str, Dict[str, Any]]):
    """添加表格(支持合并单元格和单元格样式)"""
    table_data = block.get("data", {})
    rows = table_data.get("rows", 0)
    cols = table_data.get("cols", 0)
    cells = table_data.get("cells", [])
    merge_regions = table_data.get("mergeRegions", [])
    
    if rows == 0 or cols == 0:
        logger.warning("表格行数或列数为 0,跳过")
        return
    
    # 创建表格
    table = doc.add_table(rows=rows, cols=cols)
    table.style = 'Table Grid'
    
    # 构建单元格映射
    cell_map = {tuple(cell["cell"]): cell for cell in cells}
    
    # 填充单元格内容和样式
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
                from .paragraph import add_text_with_marks
                add_text_with_marks(para, text, marks)
                
                # 应用单元格样式 - 使用 cell-X-Y 格式的 ID
                cell_id = f"cell-{row_idx}-{col_idx}"
                apply_cell_style(cell, para, cell_id, cell_style_map)
                
                # 为表头行（第一行）应用默认样式
                if row_idx == 0:
                    apply_header_style(cell, para)
    
    # 处理合并单元格
    for region in merge_regions:
        try:
            start_row, start_col = region["start"]
            end_row, end_col = region["end"]
            
            # 合并单元格
            start_cell = table.cell(start_row, start_col)
            end_cell = table.cell(end_row, end_col)
            start_cell.merge(end_cell)
        except Exception as e:
            logger.error(f"合并单元格失败: {e}")
