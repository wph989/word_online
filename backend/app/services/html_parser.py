"""
HTML 解析服务（重构版）
使用 Pydantic 模型，确保数据结构与前端完全一致
负责将前端传来的 HTML 转换为 Content 和 StyleSheet
"""

from bs4 import BeautifulSoup, Tag
from typing import List, Tuple, Optional, Dict, Any
import uuid
import re

from app.models.content_models import (
    Content, StyleSheet, Block,
    ParagraphBlock, HeadingBlock, ImageBlock, TableBlock, CodeBlock,
    ParagraphAttrs, ImageMeta,
    Mark, SimpleMark, LinkMark, ValueMark,
    StyleRule, StyleTarget, StyleDeclaration, StyleScope
)


class HtmlParser:
    """
    HTML 解析器
    将富文本编辑器生成的 HTML 转换为结构化的 Content 和 StyleSheet
    
    功能：
    1. 解析段落、标题、表格、图片、列表、代码块
    2. 提取行内标记（粗体、斜体、颜色等）
    3. 提取块级样式并生成 StyleSheet
    4. 支持表格合并单元格
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
    
    def parse(self) -> Tuple[Content, StyleSheet]:
        """
        执行解析，返回 Content 和 StyleSheet
        
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
        # 获取 body 标签，如果没有则使用整个文档
        body = self.soup.find('body')
        if not body:
            body = self.soup
        
        # 遍历所有子元素
        for element in body.children:
            if isinstance(element, Tag):
                block = self._parse_element(element)
                if block:
                    self.blocks.append(block)
    
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
        
        # 列表（转换为带 listType 属性的段落）
        elif tag_name in ['ul', 'ol']:
            self._parse_list(element)
            return None  # 列表项已直接添加到 blocks
        
        # 代码块
        elif tag_name == 'pre':
            return self._parse_code_block(element)
        
        # 其他块级元素当作段落处理
        elif tag_name in ['div', 'section', 'article']:
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
        
        # 提取段落级样式
        styles = self._extract_block_styles(element)
        
        # 构建 ParagraphBlock
        block = ParagraphBlock(
            id=block_id,
            type="paragraph",
            text=text,
            marks=marks
        )
        
        # 如果有样式，添加到 StyleSheet
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
        styles = self._extract_block_styles(element)
        
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
        解析表格元素（核心功能）
        支持合并单元格
        
        Args:
            element: table 标签
            
        Returns:
            TableBlock 对象
        """
        from app.utils.table_parser import TableParser
        
        # 使用专门的表格解析器
        parser = TableParser(element)
        table_data = parser.parse()
        
        block_id = f"table-{uuid.uuid4().hex[:8]}"
        
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
        meta = ImageMeta(alt=alt)
        if width:
            meta.width = int(width) if str(width).isdigit() else width
        if height:
            meta.height = int(height) if str(height).isdigit() else height
        
        # 构建 ImageBlock
        block = ImageBlock(
            id=block_id,
            type="image",
            src=src,
            meta=meta if (alt or width or height) else None
        )
        
        # 提取样式
        styles = self._extract_block_styles(element)
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
            
            # 如果是有序列表，添加起始序号
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
        解析代码块
        
        Args:
            element: pre 标签
            
        Returns:
            CodeBlock 对象
        """
        block_id = f"code-{uuid.uuid4().hex[:8]}"
        
        # 提取代码内容
        code_element = element.find('code')
        text = code_element.get_text() if code_element else element.get_text()
        
        # 尝试提取语言信息
        language = None
        if code_element:
            class_attr = code_element.get('class', [])
            for cls in class_attr:
                if cls.startswith('language-'):
                    language = cls.replace('language-', '')
                    break
        
        # 构建 CodeBlock
        block = CodeBlock(
            id=block_id,
            type="code",
            text=text,
            language=language
        )
        
        return block
    
    def _extract_text_and_marks(self, element: Tag) -> Tuple[str, List[Mark]]:
        """
        从元素中提取纯文本和格式标记 (递归遍历法)
        
        Args:
            element: HTML 元素
            
        Returns:
            (text, marks) 元组
        """
        full_text = ""
        marks: List[Mark] = []
        
        def traverse(node, current_marks):
            nonlocal full_text
            
            if isinstance(node, str):
                # 文本节点
                text_content = str(node)
                if not text_content:
                    return
                
                start_idx = len(full_text)
                full_text += text_content
                end_idx = len(full_text)
                
                # 为当前文本段应用所有累积的标记
                # 注意：这里我们为每个样式创建一个新的 Mark 对象，覆盖当前文本范围
                if start_idx < end_idx:
                    for mark_info in current_marks:
                        # 复制标记信息，但在新的范围内
                        range_tuple = (start_idx, end_idx)
                        
                        if mark_info['type'] == 'simple':
                            marks.append(SimpleMark(type=mark_info['name'], range=range_tuple))
                        elif mark_info['type'] == 'link':
                            marks.append(LinkMark(type="link", range=range_tuple, href=mark_info['href']))
                        elif mark_info['type'] == 'value':
                            marks.append(ValueMark(type=mark_info['name'], range=range_tuple, value=mark_info['value']))
                return

            if not hasattr(node, 'children'):
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
            
            # 2. 链接
            elif node.name == 'a':
                href = node.get('href', '')
                new_marks.append({'type': 'link', 'href': href})
            
            # 3. Span 样式 (Style 属性)
            # 注意：其他标签也可能带有 style，所以统一检查 style 属性
            # 但通常主要处理 span
            style_attr = node.get('style', '')
            if style_attr:
                # 颜色
                color_match = re.search(r'color:\s*([^;]+)', style_attr)
                if color_match:
                    new_marks.append({'type': 'value', 'name': 'color', 'value': color_match.group(1).strip()})
                
                # 背景色
                bg_match = re.search(r'background(?:-color)?:\s*([^;]+)', style_attr)
                if bg_match:
                    new_marks.append({'type': 'value', 'name': 'backgroundColor', 'value': bg_match.group(1).strip()})
                
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
        
        # 合并相邻且相同的 Mark (优化步骤，减少冗余 Mark)
        # 这一步是可选的，但推荐加上，可以让数据更干净
        final_marks = self._merge_marks(marks)
        
        return full_text, final_marks

    def _merge_marks(self, marks: List[Mark]) -> List[Mark]:
        """合并相同属性且相邻的标记"""
        if not marks:
            return []
            
        # 按类型和起始位置排序
        # 这里的排序策略需要保证同类型的标记在一起比较
        
        # 简单策略：直接返回原标记，渲染器已经能处理重叠和碎片化
        # 如果需要优化存储大小，可以在这里实现合并逻辑
        # 目前为了稳定性，先不合并，因为 html_renderer 已经能完美处理碎片化标记
        return marks

    # 废弃的方法，保留占位以防调用出错 (实际上应该被移除)
    def _get_text_range(self, parent: Tag, child: Tag) -> Optional[Tuple[int, int]]:
        return None
    
    def _extract_block_styles(self, element: Tag) -> Dict[str, Any]:
        """
        提取块级元素的样式
        
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
            styles["textAlign"] = align_match.group(1).strip()
        
        # 字号
        size_match = re.search(r'font-size:\s*([^;]+)', style_attr)
        if size_match:
            size_str = size_match.group(1).strip()
            # 尝试转换为数字（去除单位）
            size_num = re.search(r'(\d+)', size_str)
            if size_num:
                styles["fontSize"] = int(size_num.group(1))
        
        # 颜色
        color_match = re.search(r'color:\s*([^;]+)', style_attr)
        if color_match:
            styles["color"] = color_match.group(1).strip()
        
        # 行高
        line_height_match = re.search(r'line-height:\s*([^;]+)', style_attr)
        if line_height_match:
            lh_str = line_height_match.group(1).strip()
            # 尝试转换为数字
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
    
    def _extract_table_styles(self, element: Tag) -> Dict[str, Any]:
        """
        提取表格级样式
        
        Args:
            element: table 元素
            
        Returns:
            样式字典
        """
        styles = {}
        style_attr = element.get('style', '')
        
        # 边框
        border_match = re.search(r'border:\s*([^;]+)', style_attr)
        if border_match:
            border_str = border_match.group(1).strip()
            # 解析 "1px solid #ccc" 格式
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
            styles["width"] = width_match.group(1).strip()
        
        return styles
    
    def _add_style_rule(
        self, 
        block_id: str, 
        block_type: str, 
        styles: Dict[str, Any],
        level: Optional[int] = None
    ):
        """
        添加样式规则到 StyleSheet
        
        Args:
            block_id: Block ID
            block_type: Block 类型
            styles: 样式字典
            level: 标题层级（可选）
        """
        # 构建 StyleTarget
        target = StyleTarget(
            blockType=block_type,
            blockIds=[block_id]
        )
        
        if level is not None:
            target.level = level
        
        # 构建 StyleDeclaration
        style_declaration = StyleDeclaration(**styles)
        
        # 创建 StyleRule
        rule = StyleRule(
            target=target,
            style=style_declaration
        )
        
        self.style_rules.append(rule)
