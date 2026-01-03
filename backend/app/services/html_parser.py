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

from bs4 import BeautifulSoup, Tag, NavigableString
from typing import List, Tuple, Optional, Dict, Any
import uuid
import re
import json

from app.models.content_models import (
    Content, StyleSheet, Block,
    ParagraphBlock, HeadingBlock, ImageBlock, TableBlock, CodeBlock, DividerBlock,
    ParagraphAttrs, ImageMeta, TableData, TableCellData, MergeRegion,
    Mark, SimpleMark, LinkMark, ValueMark,
    StyleRule, StyleTarget, StyleDeclaration, StyleScope
)


class HtmlParser:
    """
    HTML 解析器 V2 - 增强版
    
    功能增强:
    1. 更精确的样式提取(区分用户设置 vs 默认样式)
    2. 支持表格列宽度提取
    3. 支持单元格样式提取
    4. 优化的 Mark 提取算法(避免重复和冗余)
    5. 完整的列表支持(有序、无序、嵌套)
    """
    
    def __init__(self, html_content: str):
        """
        初始化解析器
        
        Args:
            html_content: 待解析的 HTML 字符串
        """
        self.html = html_content
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.blocks: List[Block] = []
        self.style_rules: List[StyleRule] = []
        self.style_id = f"style-{uuid.uuid4().hex[:8]}"
        
        # 样式提取计数器(用于生成唯一 ID)
        self.style_counter = 0
    
    def parse(self) -> Tuple[Content, StyleSheet]:
        """
        执行解析,返回 Content 和 StyleSheet
        
        Returns:
            (Content, StyleSheet) 元组
        """
        # 解析 HTML 结构
        self._parse_body()
        
        # 构建 Content 和 StyleSheet 对象
        content = Content(blocks=self.blocks)
        stylesheet = StyleSheet(
            styleId=self.style_id,
            appliesTo=StyleScope.CHAPTER,
            rules=self.style_rules
        )
        
        return content, stylesheet
    
    def _parse_body(self):
        """解析 HTML body 中的所有顶层元素"""
        # 获取 body 标签,如果没有则使用整个文档
        body = self.soup.find('body')
        if not body:
            body = self.soup
        
        # 遍历所有子元素
        for element in body.children:
            if isinstance(element, Tag):
                block = self._parse_element(element)
                if block:
                    self.blocks.append(block)
            elif isinstance(element, NavigableString):
                # 处理纯文本节点(不在任何标签内的文本)
                text = str(element).strip()
                if text:
                    # 将纯文本包装为段落
                    block_id = f"para-{uuid.uuid4().hex[:8]}"
                    self.blocks.append(ParagraphBlock(
                        id=block_id,
                        type="paragraph",
                        text=text,
                        marks=[]
                    ))
    
    def _parse_element(self, element: Tag) -> Optional[Block]:
        """
        解析单个 HTML 元素为 Block
        
        Args:
            element: BeautifulSoup Tag 对象
            
        Returns:
            Block 对象或 None
        """
        tag_name = element.name.lower()
        
        # 段落
        if tag_name == 'p':
            return self._parse_paragraph(element)
        
        # 标题
        elif tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return self._parse_heading(element)
        
        # 表格
        elif tag_name == 'table':
            return self._parse_table(element)
        
        # 图片
        elif tag_name == 'img':
            return self._parse_image(element)
        
        # 列表(转换为带 listType 属性的段落)
        elif tag_name in ['ul', 'ol']:
            self._parse_list(element)
            return None  # 列表项已直接添加到 blocks
        
        # 代码块
        elif tag_name == 'pre':
            return self._parse_code_block(element)
        
        # 分割线
        elif tag_name == 'hr':
            return self._parse_divider(element)
        
        # 其他块级元素当作段落处理
        elif tag_name in ['div', 'section', 'article']:
            # 1. 明确的分割线包装器
            if 'w-e-textarea-divider' in element.get('class', []) or element.find('hr', recursive=False): # 浅层查找
                 return self._parse_divider(element)
            
            # 2. 检查是否包含块级子元素 (如果包含，则视为容器进行解包)
            # 定义块级标签
            block_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'ul', 'ol', 'pre', 'hr', 'blockquote', 'div', 'section', 'article']
            has_block_children = any(child.name in block_tags for child in element.children if isinstance(child, Tag))
            
            if has_block_children:
                # 递归处理子节点，并将结果直接添加到 self.blocks
                for child in element.children:
                    if isinstance(child, Tag):
                        child_block = self._parse_element(child) 
                        if child_block:
                            self.content.blocks.append(child_block)
                    elif isinstance(child, NavigableString):
                        text = str(child).strip()
                        if text:
                            block_id = f"para-{uuid.uuid4().hex[:8]}"
                            self.content.blocks.append(ParagraphBlock(
                                id=block_id,
                                type="paragraph",
                                text=text,
                                marks=[]
                            ))
                return None # 已处理，父级不需要再添加
            
            # 3. 如果没有块级子元素，但包含深层 hr (非直接子元素)
            if element.find('hr'):
                 return self._parse_divider(element)
                 
            # 4. 否则，当作普通段落处理
            return self._parse_paragraph(element)
        
        return None
    
    def _parse_paragraph(self, element: Tag) -> ParagraphBlock:
        """
        解析段落元素
        
        Args:
            element: p 标签
            
        Returns:
            ParagraphBlock 对象
        """
        block_id = f"para-{uuid.uuid4().hex[:8]}"
        
        # 提取文本内容和标记
        text, marks = self._extract_text_and_marks(element)
        
        # 提取段落级样式(只提取用户明确设置的样式)
        styles = self._extract_user_block_styles(element)
        
        # 构建 ParagraphBlock
        block = ParagraphBlock(
            id=block_id,
            type="paragraph",
            text=text,
            marks=marks
        )
        
        # 如果有样式,添加到 StyleSheet
        if styles:
            self._add_style_rule(block_id, "paragraph", styles)
        
        return block
    
    def _parse_heading(self, element: Tag) -> HeadingBlock:
        """
        解析标题元素
        
        Args:
            element: h1-h6 标签
            
        Returns:
            HeadingBlock 对象
        """
        block_id = f"heading-{uuid.uuid4().hex[:8]}"
        level = int(element.name[1])  # h1 -> 1, h2 -> 2, ...
        
        # 提取文本和标记
        text, marks = self._extract_text_and_marks(element)
        
        # 提取样式
        styles = self._extract_user_block_styles(element)
        
        # 构建 HeadingBlock
        block = HeadingBlock(
            id=block_id,
            type="heading",
            level=level,
            text=text,
            marks=marks
        )
        
        # 添加样式规则
        if styles:
            self._add_style_rule(block_id, "heading", styles, level=level)
        
        return block
    
    def _parse_table(self, element: Tag) -> TableBlock:
        """
        解析表格元素(核心功能)
        支持:
        1. 合并单元格
        2. 列宽度提取
        3. 单元格样式提取
        
        Args:
            element: table 标签
            
        Returns:
            TableBlock 对象
        """
        block_id = f"table-{uuid.uuid4().hex[:8]}"
        
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
        self._extract_column_widths(element, block_id, max_cols)
        
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
                text, marks = self._extract_text_and_marks(cell)
                
                # 提取单元格样式
                cell_id = f"cell-{row_idx}-{col_idx}"
                cell_styles = self._extract_cell_user_styles(cell)
                
                # 创建单元格数据
                cell_data = TableCellData(
                    cell=[row_idx, col_idx],
                    content={"text": text, "marks": [m.model_dump() for m in marks]}
                )
                
                # 如果有样式,添加 styleId
                if cell_styles:
                    cell_data.styleId = cell_id
                    self._add_style_rule(
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
        table_styles = self._extract_table_styles(element)
        if table_styles:
            self._add_style_rule(block_id, "table", table_styles)
        
        # 构建 TableBlock
        block = TableBlock(
            id=block_id,
            type="table",
            data=table_data
        )
        
        return block
    
    def _extract_column_widths(self, table: Tag, table_id: str, col_count: int):
        """
        提取表格列宽度
        
        Args:
            table: table 元素
            table_id: 表格 ID
            col_count: 列数
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
                        self._add_style_rule(
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
                            self._add_style_rule(
                                table_id,
                                "tableColumn",
                                {"width": width_value},
                                column_index=idx
                            )
    
    def _parse_image(self, element: Tag) -> ImageBlock:
        """
        解析图片元素
        
        Args:
            element: img 标签
            
        Returns:
            ImageBlock 对象
        """
        block_id = f"image-{uuid.uuid4().hex[:8]}"
        
        # 提取图片属性
        src = element.get('src', '')
        alt = element.get('alt', '')
        width = element.get('width')
        height = element.get('height')
        
        # 构建 ImageMeta
        meta = ImageMeta(alt=alt) if alt else None
        if width:
            if not meta:
                meta = ImageMeta()
            meta.width = int(width) if str(width).isdigit() else width
        if height:
            if not meta:
                meta = ImageMeta()
            meta.height = int(height) if str(height).isdigit() else height
        
        # 构建 ImageBlock
        block = ImageBlock(
            id=block_id,
            type="image",
            src=src,
            meta=meta
        )
        
        # 提取样式
        styles = self._extract_user_block_styles(element)
        if styles:
            self._add_style_rule(block_id, "image", styles)
        
        return block
    
    def _parse_list(self, element: Tag):
        """
        解析列表元素
        将列表项转换为带 listType 属性的段落
        
        Args:
            element: ul 或 ol 标签
        """
        list_type = "bullet" if element.name == "ul" else "ordered"
        
        # 递归解析列表项
        self._parse_list_items(element, list_type, level=0)
    
    def _parse_list_items(self, element: Tag, list_type: str, level: int):
        """
        递归解析列表项
        
        Args:
            element: ul/ol 标签
            list_type: "bullet" 或 "ordered"
            level: 嵌套层级
        """
        for li in element.find_all('li', recursive=False):
            block_id = f"para-{uuid.uuid4().hex[:8]}"
            
            # 提取文本和标记
            text, marks = self._extract_text_and_marks(li)
            
            # 构建段落属性
            attrs = ParagraphAttrs(
                listType=list_type,
                listLevel=level
            )
            
            # 如果是有序列表,添加起始序号
            if list_type == "ordered":
                start = element.get('start', 1)
                attrs.listStart = int(start)
            
            # 构建带列表属性的段落
            block = ParagraphBlock(
                id=block_id,
                type="paragraph",
                text=text,
                marks=marks,
                attrs=attrs
            )
            
            self.blocks.append(block)
            
            # 递归处理嵌套列表
            nested_list = li.find(['ul', 'ol'], recursive=False)
            if nested_list:
                nested_type = "bullet" if nested_list.name == "ul" else "ordered"
                self._parse_list_items(nested_list, nested_type, level + 1)
    
    def _parse_code_block(self, element: Tag) -> CodeBlock:
        """
        解析代码块元素
        
        Args:
            element: pre 标签
            
        Returns:
            CodeBlock 对象
        """
        block_id = f"code-{uuid.uuid4().hex[:8]}"
        
        # 提取语言
        language = None
        code_tag = element.find('code')
        if code_tag:
            # 尝试提取 class="language-xxx"
            classes = code_tag.get('class', [])
            for cls in classes:
                if cls.startswith('language-'):
                    language = cls.replace('language-', '')
                    break
            
            text = code_tag.get_text()
        else:
            text = element.get_text()
            
        return CodeBlock(
            id=block_id,
            type="code",
            text=text,
            language=language
        )

    def _parse_divider(self, element: Tag) -> DividerBlock:
        """
        解析分割线
        
        Args:
            element: hr 标签或包含 hr 的 div
            
        Returns:
            DividerBlock 对象
        """
        block_id = f"divider-{uuid.uuid4().hex[:8]}"
        return DividerBlock(id=block_id, type="divider")
        
    def _extract_text_and_marks(self, element: Tag) -> Tuple[str, List[Mark]]:
        """
        从元素中提取纯文本和格式标记(递归遍历法)
        
        优化:
        1. 避免重复标记
        2. 正确处理嵌套标记
        3. 合并相邻的相同标记
        
        Args:
            element: HTML 元素
            
        Returns:
            (text, marks) 元组
        """
        full_text = ""
        marks: List[Mark] = []
        
        def traverse(node, current_marks):
            nonlocal full_text
            
            # 文本节点
            if isinstance(node, NavigableString):
                text_content = str(node)
                if not text_content:
                    return
                
                start_idx = len(full_text)
                full_text += text_content
                end_idx = len(full_text)
                
                # 为当前文本段应用所有累积的标记
                if start_idx < end_idx:
                    for mark_info in current_marks:
                        range_tuple = (start_idx, end_idx)
                        
                        if mark_info['type'] == 'simple':
                            marks.append(SimpleMark(type=mark_info['name'], range=range_tuple))
                        elif mark_info['type'] == 'link':
                            marks.append(LinkMark(type="link", range=range_tuple, href=mark_info['href']))
                        elif mark_info['type'] == 'value':
                            marks.append(ValueMark(type=mark_info['name'], range=range_tuple, value=mark_info['value']))
                return
            
            if not isinstance(node, Tag):
                return
            
            # 处理当前节点产生的样式
            new_marks = current_marks.copy()
            
            # 1. 语义标签
            if node.name in ['strong', 'b']:
                new_marks.append({'type': 'simple', 'name': 'bold'})
            elif node.name in ['em', 'i']:
                new_marks.append({'type': 'simple', 'name': 'italic'})
            elif node.name == 'u':
                new_marks.append({'type': 'simple', 'name': 'underline'})
            elif node.name in ['s', 'strike', 'del']:
                new_marks.append({'type': 'simple', 'name': 'strike'})
            elif node.name == 'code':
                new_marks.append({'type': 'simple', 'name': 'code'})
            elif node.name == 'sup':
                new_marks.append({'type': 'simple', 'name': 'superscript'})
            elif node.name == 'sub':
                new_marks.append({'type': 'simple', 'name': 'subscript'})
            
            # 2. 链接
            elif node.name == 'a':
                href = node.get('href', '')
                new_marks.append({'type': 'link', 'href': href})
            
            # 3. 内联样式(从 style 属性提取)
            style_attr = node.get('style', '')
            if style_attr:
                # 背景色(必须先匹配,避免被 color 匹配)
                bg_match = re.search(r'background(?:-color)?:\s*([^;]+)', style_attr)
                if bg_match:
                    new_marks.append({'type': 'value', 'name': 'backgroundColor', 'value': bg_match.group(1).strip()})
                
                # 颜色(使用负向后顾断言,排除 background-color)
                color_match = re.search(r'(?<!background-)color:\s*([^;]+)', style_attr)
                if color_match:
                    new_marks.append({'type': 'value', 'name': 'color', 'value': color_match.group(1).strip()})
                
                # 字号
                size_match = re.search(r'font-size:\s*([^;]+)', style_attr)
                if size_match:
                    new_marks.append({'type': 'value', 'name': 'fontSize', 'value': size_match.group(1).strip()})
                
                # 字体
                family_match = re.search(r'font-family:\s*([^;]+)', style_attr)
                if family_match:
                    new_marks.append({'type': 'value', 'name': 'fontFamily', 'value': family_match.group(1).strip()})
            
            # 递归遍历子节点
            for child in node.children:
                traverse(child, new_marks)
        
        # 开始递归
        traverse(element, [])
        
        return full_text, marks
    
    def _extract_user_block_styles(self, element: Tag) -> Dict[str, Any]:
        """
        提取块级元素的用户明确设置的样式
        (过滤掉浏览器默认样式)
        
        Args:
            element: HTML 元素
            
        Returns:
            样式字典
        """
        styles = {}
        style_attr = element.get('style', '')
        
        if not style_attr:
            return styles
        
        # 文本对齐
        align_match = re.search(r'text-align:\s*([^;]+)', style_attr)
        if align_match:
            align = align_match.group(1).strip()
            # 只保存非默认值
            if align not in ['start', 'left']:
                styles["textAlign"] = align
        
        # 注意：字号(fontSize)和字体(fontFamily)不在段落级别提取
        # 这些样式只在字符级别（marks）中处理，避免段落样式覆盖字符样式
        
        # 颜色(使用负向后顾断言,排除 background-color)
        color_match = re.search(r'(?<!background-)color:\s*([^;]+)', style_attr)
        if color_match:
            color = color_match.group(1).strip()
            # 过滤默认黑色
            if color not in ['rgb(0, 0, 0)', '#000000', '#000', 'black']:
                styles["color"] = color
        
        # 行高
        line_height_match = re.search(r'line-height:\s*([^;]+)', style_attr)
        if line_height_match:
            lh_str = line_height_match.group(1).strip()
            try:
                styles["lineHeight"] = float(lh_str)
            except ValueError:
                pass
        
        # 缩进
        indent_match = re.search(r'text-indent:\s*([^;]+)', style_attr)
        if indent_match:
            indent_str = indent_match.group(1).strip()
            indent_num = re.search(r'(\d+)', indent_str)
            if indent_num:
                styles["textIndent"] = int(indent_num.group(1))
        
        return styles
    
    def _extract_cell_user_styles(self, cell: Tag) -> Dict[str, Any]:
        """
        提取单元格用户明确设置的样式
        
        Args:
            cell: td/th 元素
            
        Returns:
            样式字典
        """
        styles = {}
        style_attr = cell.get('style', '')
        
        # 文本对齐
        text_align = None
        if 'text-align' in style_attr:
            align_match = re.search(r'text-align:\s*([^;]+)', style_attr)
            if align_match:
                text_align = align_match.group(1).strip()
        elif cell.get('align'):
            text_align = cell.get('align')
        
        if text_align and text_align not in ['start', 'left']:
            styles["textAlign"] = text_align
        
        # 垂直对齐
        vertical_align = None
        if 'vertical-align' in style_attr:
            valign_match = re.search(r'vertical-align:\s*([^;]+)', style_attr)
            if valign_match:
                vertical_align = valign_match.group(1).strip()
        elif cell.get('valign'):
            vertical_align = cell.get('valign')
        
        if vertical_align and vertical_align != 'baseline':
            styles["verticalAlign"] = vertical_align
        
        # 字体
        family_match = re.search(r'font-family:\s*([^;]+)', style_attr)
        if family_match:
            styles["fontFamily"] = family_match.group(1).strip()
        
        # 字号
        size_match = re.search(r'font-size:\s*([^;]+)', style_attr)
        if size_match:
            size_str = size_match.group(1).strip()
            size_num = re.search(r'(\d+)', size_str)
            if size_num:
                styles["fontSize"] = int(size_num.group(1))
        
        # 字体粗细
        weight_match = re.search(r'font-weight:\s*([^;]+)', style_attr)
        if weight_match:
            weight = weight_match.group(1).strip()
            if weight not in ['normal', '400']:
                styles["fontWeight"] = weight
        
        # 文本颜色(使用负向后顾断言,排除 background-color)
        color_match = re.search(r'(?<!background-)color:\s*([^;]+)', style_attr)
        if color_match:
            color = color_match.group(1).strip()
            if color not in ['rgb(0, 0, 0)', '#000000', '#000', 'black']:
                styles["color"] = color
        
        # 背景颜色
        bg_color = None
        if 'background-color' in style_attr or 'background:' in style_attr:
            bg_match = re.search(r'background(?:-color)?:\s*([^;]+)', style_attr)
            if bg_match:
                bg_color = bg_match.group(1).strip()
        elif cell.get('bgcolor'):
            bg_color = cell.get('bgcolor')
        
        if bg_color and bg_color not in ['transparent', 'rgba(0, 0, 0, 0)']:
            styles["backgroundColor"] = bg_color
        
        return styles
    
    def _extract_table_styles(self, table: Tag) -> Dict[str, Any]:
        """
        提取表格级样式
        
        Args:
            table: table 元素
            
        Returns:
            样式字典
        """
        styles = {}
        style_attr = table.get('style', '')
        
        # 边框
        border_match = re.search(r'border:\s*([^;]+)', style_attr)
        if border_match:
            border_str = border_match.group(1).strip()
            parts = border_str.split()
            if len(parts) >= 3:
                width_match = re.search(r'\d+', parts[0])
                if width_match:
                    styles["borderWidth"] = int(width_match.group())
                styles["borderStyle"] = parts[1]
                styles["borderColor"] = parts[2]
        
        # 宽度
        width_match = re.search(r'width:\s*([^;]+)', style_attr)
        if width_match:
            width = width_match.group(1).strip()
            if width != 'auto':
                styles["width"] = width
        
        # 边框折叠
        collapse_match = re.search(r'border-collapse:\s*([^;]+)', style_attr)
        if collapse_match:
            styles["borderCollapse"] = collapse_match.group(1).strip()
        
        return styles
    
    def _add_style_rule(
        self, 
        block_id: str, 
        block_type: str, 
        styles: Dict[str, Any],
        level: Optional[int] = None,
        column_index: Optional[int] = None,
        cell_type: Optional[str] = None
    ):
        """
        添加样式规则到 StyleSheet
        
        Args:
            block_id: Block ID
            block_type: Block 类型
            styles: 样式字典
            level: 标题层级(可选)
            column_index: 列索引(可选,用于表格列)
            cell_type: 单元格类型(可选,'td' 或 'th')
        """
        # 构建 StyleTarget
        target = StyleTarget(
            blockType=block_type,
            blockIds=[block_id]
        )
        
        if level is not None:
            target.level = level
        
        if column_index is not None:
            target.columnIndex = column_index
        
        if cell_type is not None:
            target.cellType = cell_type
        
        # 构建 StyleDeclaration
        style_declaration = StyleDeclaration(**styles)
        
        # 创建 StyleRule
        rule = StyleRule(
            target=target,
            style=style_declaration
        )
        
        self.style_rules.append(rule)


# 导出便捷函数
def parse_html_to_json(html_content: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    便捷函数: 将 HTML 解析为 JSON 字典
    
    Args:
        html_content: HTML 字符串
        
    Returns:
        (content_dict, stylesheet_dict) 元组
    """
    parser = HtmlParser(html_content)
    content, stylesheet = parser.parse()
    
    return content.model_dump(), stylesheet.model_dump()
