"""
元素转换器

将 DOCX 解析结果转换为 Content/StyleSheet JSON 格式
"""

import uuid
import re
from typing import List, Tuple, Optional
from dataclasses import dataclass

from app.models.content_models import (
    Content, StyleSheet, StyleScope, StyleRule, StyleTarget, StyleDeclaration,
    ParagraphBlock, HeadingBlock, TableBlock, ImageBlock, DividerBlock,
    TableData, TableCellData, TableCellContent, MergeRegion,
    SimpleMark, ValueMark, LinkMark, Mark, ParagraphAttrs, ImageMeta
)

from .parser import (
    DocxElement, DocxParagraph, DocxTable, DocxImage,
    RunData, RunFormat, CellData
)


def generate_block_id(prefix: str) -> str:
    """生成 Block ID"""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def parse_size_value(value: str) -> Optional[int]:
    """
    解析尺寸值，将带单位的字符串转换为整数
    
    Examples:
        "12pt" -> 12
        "24.5pt" -> 25
        "0.1pt" -> 0
    """
    if not value:
        return None
    
    # 提取数字部分
    match = re.match(r'([\d.]+)', str(value))
    if match:
        try:
            return round(float(match.group(1)))
        except ValueError:
            return None
    return None


class ElementConverter:
    """
    元素转换器
    
    将 DocxParser 的解析结果转换为 Content Block 和 StyleSheet Rule
    """
    
    def __init__(self):
        self.style_rules: List[StyleRule] = []
        self.style_id = f"style-{uuid.uuid4().hex[:8]}"
    
    def convert_elements(self, elements: List[DocxElement], images_path_map: dict = None) -> Tuple[Content, StyleSheet]:
        """
        转换所有元素
        
        Args:
            elements: DocxElement 列表
            images_path_map: 图片 rId 到访问路径的映射
            
        Returns:
            (Content, StyleSheet) 元组
        """
        blocks = []
        
        for element in elements:
            if element.element_type == "paragraph":
                block = self.convert_paragraph(element.data)
                if block:
                    blocks.append(block)
            elif element.element_type == "table":
                block = self.convert_table(element.data)
                if block:
                    blocks.append(block)
            elif element.element_type == "image":
                block = self.convert_image(element.data, images_path_map)
                if block:
                    blocks.append(block)
        
        content = Content(blocks=blocks)
        stylesheet = StyleSheet(
            styleId=self.style_id,
            appliesTo=StyleScope.CHAPTER,
            rules=self.style_rules
        )
        
        return content, stylesheet
    
    def convert_paragraph(self, para: DocxParagraph) -> Optional[ParagraphBlock | HeadingBlock]:
        """转换段落/标题"""
        if para.heading_level:
            return self._convert_heading(para)
        else:
            return self._convert_para(para)
    
    def _convert_para(self, para: DocxParagraph) -> ParagraphBlock:
        """转换普通段落"""
        block_id = generate_block_id("para")
        
        # 转换 Marks
        marks = self._convert_marks(para.runs)
        
        # 转换段落属性
        attrs = None
        if para.list_info:
            attrs = ParagraphAttrs(
                listType=para.list_info.list_type,
                listLevel=para.list_info.level,
                listStart=para.list_info.start
            )
        
        # 添加段落样式规则
        style_decl = self._convert_paragraph_style(para)
        if style_decl:
            self.style_rules.append(StyleRule(
                target=StyleTarget(blockType="paragraph", blockIds=[block_id]),
                style=style_decl
            ))
        
        return ParagraphBlock(
            id=block_id,
            type="paragraph",
            text=para.text,
            marks=marks,
            attrs=attrs
        )
    
    def _convert_heading(self, para: DocxParagraph) -> HeadingBlock:
        """转换标题"""
        block_id = generate_block_id("heading")
        
        # 转换 Marks
        marks = self._convert_marks(para.runs)
        
        # 添加标题样式规则
        style_decl = self._convert_paragraph_style(para)
        if style_decl:
            self.style_rules.append(StyleRule(
                target=StyleTarget(blockType="heading", blockIds=[block_id], level=para.heading_level),
                style=style_decl
            ))
        
        return HeadingBlock(
            id=block_id,
            type="heading",
            text=para.text,
            level=para.heading_level,
            marks=marks
        )
    
    def _convert_marks(self, runs: List[RunData]) -> List[Mark]:
        """将 Runs 转换为 Marks"""
        marks = []
        
        for run in runs:
            fmt = run.format
            start = run.start
            end = run.end
            
            if start == end:
                continue
            
            # 简单格式
            if fmt.bold:
                marks.append(SimpleMark(type="bold", range=(start, end)))
            if fmt.italic:
                marks.append(SimpleMark(type="italic", range=(start, end)))
            if fmt.underline:
                marks.append(SimpleMark(type="underline", range=(start, end)))
            if fmt.strike:
                marks.append(SimpleMark(type="strike", range=(start, end)))
            if fmt.superscript:
                marks.append(SimpleMark(type="superscript", range=(start, end)))
            if fmt.subscript:
                marks.append(SimpleMark(type="subscript", range=(start, end)))
            
            # 带值格式
            if fmt.color:
                marks.append(ValueMark(type="color", range=(start, end), value=fmt.color))
            if fmt.font_size:
                marks.append(ValueMark(type="fontSize", range=(start, end), value=fmt.font_size))
            if fmt.font_family:
                marks.append(ValueMark(type="fontFamily", range=(start, end), value=fmt.font_family))
            elif fmt.font_family_east_asia:
                marks.append(ValueMark(type="fontFamily", range=(start, end), value=fmt.font_family_east_asia))
            if fmt.background_color:
                marks.append(ValueMark(type="backgroundColor", range=(start, end), value=fmt.background_color))
        
        return marks
    
    def _convert_paragraph_style(self, para: DocxParagraph) -> Optional[StyleDeclaration]:
        """转换段落样式为 StyleDeclaration"""
        fmt = para.format
        
        style_dict = {}
        
        if fmt.alignment:
            style_dict['textAlign'] = fmt.alignment
        if fmt.first_line_indent:
            # textIndent 支持字符串或整数
            style_dict['textIndent'] = fmt.first_line_indent
        if fmt.left_indent:
            # 转换为整数
            style_dict['paddingLeft'] = parse_size_value(fmt.left_indent)
        if fmt.right_indent:
            # 转换为整数
            style_dict['paddingRight'] = parse_size_value(fmt.right_indent)
        if fmt.space_before:
            # 转换为整数
            style_dict['marginTop'] = parse_size_value(fmt.space_before)
        if fmt.space_after:
            # 转换为整数
            style_dict['marginBottom'] = parse_size_value(fmt.space_after)
        if fmt.line_spacing:
            # lineHeight 可以是数字（倍数）或带单位的字符串
            try:
                # 尝试解析为纯数字（倍数）
                style_dict['lineHeight'] = float(fmt.line_spacing)
            except ValueError:
                # 如果是带单位的字符串，提取数值部分
                parsed = parse_size_value(fmt.line_spacing)
                if parsed is not None:
                    style_dict['lineHeight'] = float(parsed)
        
        # 过滤掉 None 值
        style_dict = {k: v for k, v in style_dict.items() if v is not None}
        
        if style_dict:
            return StyleDeclaration(**style_dict)
        return None
    
    def convert_table(self, table: DocxTable) -> TableBlock:
        """转换表格"""
        block_id = generate_block_id("table")
        
        # 转换单元格
        cells = []
        merge_regions = []
        processed_merges = set()
        
        for cell_data in table.cells:
            # 转换单元格内容
            cell_content = TableCellContent(
                text=cell_data.text,
                marks=self._convert_cell_marks(cell_data.runs)
            )
            
            # 生成单元格 styleId
            cell_style_id = f"cell-{cell_data.row}-{cell_data.col}"
            
            cells.append(TableCellData(
                cell=(cell_data.row, cell_data.col),
                content=cell_content,
                styleId=cell_style_id
            ))
            
            # 处理合并单元格
            if cell_data.rowspan > 1 or cell_data.colspan > 1:
                merge_key = (cell_data.row, cell_data.col)
                if merge_key not in processed_merges:
                    merge_type = "rectangular"
                    if cell_data.rowspan == 1:
                        merge_type = "horizontal"
                    elif cell_data.colspan == 1:
                        merge_type = "vertical"
                    
                    merge_regions.append(MergeRegion(
                        id=f"merge-{cell_data.row}-{cell_data.col}",
                        start=(cell_data.row, cell_data.col),
                        end=(cell_data.row + cell_data.rowspan - 1, cell_data.col + cell_data.colspan - 1),
                        masterCell=(cell_data.row, cell_data.col),
                        type=merge_type
                    ))
                    processed_merges.add(merge_key)
            
            # 添加单元格样式规则
            cell_style = self._convert_cell_style(cell_data)
            if cell_style:
                self.style_rules.append(StyleRule(
                    target=StyleTarget(blockType="tableCell", blockIds=[cell_style_id]),
                    style=cell_style
                ))
        
        # 添加列宽样式规则
        for col_idx, width in enumerate(table.column_widths):
            self.style_rules.append(StyleRule(
                target=StyleTarget(blockType="tableColumn", blockIds=[block_id], columnIndex=col_idx),
                style=StyleDeclaration(width=width)
            ))
        
        # 构建 TableData
        table_data = TableData(
            rows=table.rows,
            cols=table.cols,
            cells=cells,
            mergeRegions=merge_regions
        )
        
        return TableBlock(
            id=block_id,
            type="table",
            data=table_data,
            styleId=block_id
        )
    
    def _convert_cell_marks(self, runs: List[RunData]) -> List[Mark]:
        """转换单元格内的 Marks"""
        return self._convert_marks(runs)
    
    def _convert_cell_style(self, cell: CellData) -> Optional[StyleDeclaration]:
        """转换单元格样式"""
        style_dict = {}
        
        if cell.background_color:
            style_dict['backgroundColor'] = cell.background_color
        if cell.vertical_align:
            style_dict['verticalAlign'] = cell.vertical_align
        if cell.text_align:
            style_dict['textAlign'] = cell.text_align
        if cell.width:
            style_dict['width'] = cell.width
        
        # 边框样式 - 转换宽度为整数
        if cell.border_top:
            width = parse_size_value(cell.border_top.get('width'))
            if width is not None:
                style_dict['borderTopWidth'] = width
            style_dict['borderTopStyle'] = cell.border_top.get('style', 'solid')
            style_dict['borderTopColor'] = cell.border_top.get('color')
        if cell.border_bottom:
            width = parse_size_value(cell.border_bottom.get('width'))
            if width is not None:
                style_dict['borderBottomWidth'] = width
            style_dict['borderBottomStyle'] = cell.border_bottom.get('style', 'solid')
            style_dict['borderBottomColor'] = cell.border_bottom.get('color')
        if cell.border_left:
            width = parse_size_value(cell.border_left.get('width'))
            if width is not None:
                style_dict['borderLeftWidth'] = width
            style_dict['borderLeftStyle'] = cell.border_left.get('style', 'solid')
            style_dict['borderLeftColor'] = cell.border_left.get('color')
        if cell.border_right:
            width = parse_size_value(cell.border_right.get('width'))
            if width is not None:
                style_dict['borderRightWidth'] = width
            style_dict['borderRightStyle'] = cell.border_right.get('style', 'solid')
            style_dict['borderRightColor'] = cell.border_right.get('color')
        
        # 过滤掉 None 值
        style_dict = {k: v for k, v in style_dict.items() if v is not None}
        
        if style_dict:
            return StyleDeclaration(**style_dict)
        return None
    
    def convert_image(self, image: DocxImage, path_map: dict = None) -> Optional[ImageBlock]:
        """转换图片"""
        if path_map is None:
            path_map = {}
        
        block_id = generate_block_id("image")
        
        # 获取图片路径
        src = path_map.get(image.rId, f"/api/v1/assets/images/{image.rId}")
        
        # 图片元信息
        meta = None
        if image.width or image.height or image.alt:
            meta = ImageMeta(
                width=image.width,
                height=image.height,
                alt=image.alt
            )
        
        return ImageBlock(
            id=block_id,
            type="image",
            src=src,
            meta=meta
        )
