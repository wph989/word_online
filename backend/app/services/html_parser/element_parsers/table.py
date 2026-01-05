"""
表格解析器
"""

import re
from bs4 import Tag
from app.models.content_models import TableBlock, TableData, TableCellData, MergeRegion

from ..extractors import extract_text_and_marks, extract_cell_user_styles, extract_table_styles
from ..utils import add_style_rule, generate_block_id


def parse_table(element: Tag, style_rules: list) -> TableBlock:
    """
    解析表格元素(核心功能)
    支持:
    1. 合并单元格
    2. 列宽度提取
    3. 单元格样式提取
    
    Args:
        element: table 标签
        style_rules: 样式规则列表
        
    Returns:
        TableBlock 对象
    """
    block_id = generate_block_id("table")
    
    # 初始化表格数据
    table_data = TableData(
        rows=0,
        cols=0,
        cells=[],
        mergeRegions=[]
    )
    
    # 提取表格行
    rows = element.find_all('tr', recursive=True)
    table_data.rows = len(rows)
    
    # 计算最大列数
    max_cols = 0
    for row in rows:
        cells = row.find_all(['td', 'th'], recursive=False)
        col_count = sum(int(cell.get('colspan', 1)) for cell in cells)
        max_cols = max(max_cols, col_count)
    table_data.cols = max_cols
    
    # 提取列宽度(从 colgroup 或首行单元格)
    extract_column_widths(element, block_id, max_cols, style_rules)
    
    # 解析单元格
    # 使用占用矩阵追踪合并单元格
    occupied = [[False] * max_cols for _ in range(table_data.rows)]
    
    for row_idx, row in enumerate(rows):
        cells = row.find_all(['td', 'th'], recursive=False)
        col_idx = 0
        
        for cell in cells:
            # 找到下一个未占用的列
            while col_idx < max_cols and occupied[row_idx][col_idx]:
                col_idx += 1
            
            if col_idx >= max_cols:
                break
            
            # 获取合并信息
            rowspan = int(cell.get('rowspan', 1))
            colspan = int(cell.get('colspan', 1))
            
            # 提取单元格内容
            text, marks = extract_text_and_marks(cell)
            
            # 提取单元格样式
            cell_id = f"cell-{row_idx}-{col_idx}"
            cell_styles = extract_cell_user_styles(cell)
            
            # 创建单元格数据
            cell_data = TableCellData(
                cell=[row_idx, col_idx],
                content={"text": text, "marks": [m.model_dump() for m in marks]}
            )
            
            # 如果有样式,添加 styleId
            if cell_styles:
                cell_data.styleId = cell_id
                add_style_rule(
                    style_rules, 
                    cell_id, 
                    "tableCell", 
                    cell_styles,
                    cell_type=cell.name
                )
            
            table_data.cells.append(cell_data)
            
            # 标记占用区域
            for r in range(row_idx, min(row_idx + rowspan, table_data.rows)):
                for c in range(col_idx, min(col_idx + colspan, max_cols)):
                    occupied[r][c] = True
            
            # 处理合并单元格
            if rowspan > 1 or colspan > 1:
                merge_type = 'horizontal' if rowspan == 1 else ('vertical' if colspan == 1 else 'rectangular')
                merge_region = MergeRegion(
                    id=f"merge-{row_idx}-{col_idx}",
                    start=[row_idx, col_idx],
                    end=[row_idx + rowspan - 1, col_idx + colspan - 1],
                    masterCell=[row_idx, col_idx],
                    type=merge_type
                )
                table_data.mergeRegions.append(merge_region)
            
            col_idx += 1
    
    # 提取表格级样式
    table_styles = extract_table_styles(element)
    if table_styles:
        add_style_rule(style_rules, block_id, "table", table_styles)
    
    # 构建 TableBlock
    block = TableBlock(
        id=block_id,
        type="table",
        data=table_data
    )
    
    return block


def extract_column_widths(table: Tag, table_id: str, col_count: int, style_rules: list):
    """
    提取表格列宽度
    
    Args:
        table: table 元素
        table_id: 表格 ID
        col_count: 列数
        style_rules: 样式规则列表
    """
    # 尝试从 colgroup 提取
    colgroup = table.find('colgroup')
    if colgroup:
        cols = colgroup.find_all('col')
        for idx, col in enumerate(cols):
            if idx >= col_count:
                break
            
            width = col.get('width')
            if width and width != 'auto':
                # 提取数字部分
                width_match = re.search(r'(\d+(?:\.\d+)?)', str(width))
                if width_match:
                    width_value = str(int(float(width_match.group(1))))
                    from ..utils import add_style_rule
                    add_style_rule(
                        style_rules,
                        table_id,
                        "tableColumn",
                        {"width": width_value},
                        column_index=idx
                    )
    
    # 如果 colgroup 没有宽度,尝试从首行单元格提取
    else:
        first_row = table.find('tr')
        if first_row:
            cells = first_row.find_all(['td', 'th'], recursive=False)
            for idx, cell in enumerate(cells):
                if idx >= col_count:
                    break
                
                # 尝试从 width 属性提取
                width = cell.get('width')
                if not width or width == 'auto':
                    # 尝试从 style 提取
                    style = cell.get('style', '')
                    width_match = re.search(r'width:\s*(\d+(?:\.\d+)?)', style)
                    if width_match:
                        width = width_match.group(1)
                
                if width and width != 'auto':
                    width_match = re.search(r'(\d+(?:\.\d+)?)', str(width))
                    if width_match:
                        width_value = str(int(float(width_match.group(1))))
                        from ..utils import add_style_rule
                        add_style_rule(
                            style_rules,
                            table_id,
                            "tableColumn",
                            {"width": width_value},
                            column_index=idx
                        )
