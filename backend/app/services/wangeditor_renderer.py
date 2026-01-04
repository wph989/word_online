"""
WangEditor 兼容的 HTML 渲染器
生成 WangEditor 能够正确解析的 HTML 格式
"""

from typing import Dict, List
import html

from app.models.content_models import (
    Content, StyleSheet, Block,
    ParagraphBlock, HeadingBlock, ImageBlock, TableBlock, CodeBlock, DividerBlock,
    Mark, SimpleMark, LinkMark, ValueMark,
    StyleRule
)


class WangEditorRenderer:
    """
    WangEditor 兼容的 HTML 渲染器
    生成符合 WangEditor 期望的 HTML 格式
    """
    
    def __init__(self, content: Content, stylesheet: StyleSheet):
        """
        初始化渲染器
        
        Args:
            content: Content 对象
            stylesheet: StyleSheet 对象
        """
        self.content = content
        self.stylesheet = stylesheet
        self.style_map = self._build_style_map()
    
    def render(self) -> str:
        """
        执行渲染,生成 HTML
        
        Returns:
            HTML 字符串
        """
        html_parts = []
        
        i = 0
        while i < len(self.content.blocks):
            block = self.content.blocks[i]
            
            # 检查是否是列表项
            if isinstance(block, ParagraphBlock) and block.attrs and block.attrs.listType and block.attrs.listType != 'none':
                # 收集连续的同类型同层级列表项
                list_items = [block]
                list_type = block.attrs.listType
                list_level = block.attrs.listLevel or 0
                
                j = i + 1
                while j < len(self.content.blocks):
                    next_block = self.content.blocks[j]
                    if (isinstance(next_block, ParagraphBlock) and 
                        next_block.attrs and 
                        next_block.attrs.listType == list_type and
                        (next_block.attrs.listLevel or 0) == list_level):
                        list_items.append(next_block)
                        j += 1
                    else:
                        break
                
                # 渲染整个列表
                html_parts.append(self._render_list_group(list_items, list_type, list_level))
                i = j
            else:
                # 普通块
                block_html = self._render_block(block)
                if block_html:
                    html_parts.append(block_html)
                i += 1
        
        return "\n".join(html_parts)
    
    def _render_list_group(self, items: List[ParagraphBlock], list_type: str, level: int) -> str:
        """
        渲染一组列表项(合并到同一个 ul/ol 中)
        
        Args:
            items: 列表项块列表
            list_type: 列表类型 ("bullet" 或 "ordered")
            level: 缩进层级
            
        Returns:
            HTML 字符串
        """
        tag = "ul" if list_type == "bullet" else "ol"
        li_parts = []
        
        for item in items:
            formatted_text = self._apply_marks(item.text, item.marks)
            styles = self._get_block_styles(item.id)
            style_attr = self._styles_to_css(styles)
            li_parts.append(f'<li{self._attr(style_attr)}>{formatted_text}</li>')
        
        # 添加缩进样式
        indent_style = ""
        if level > 0:
            indent = level * 2  # 每级缩进 2em
            indent_style = f' style="margin-left: {indent}em"'
        
        return f'<{tag}{indent_style}>{"".join(li_parts)}</{tag}>'
    
    def _build_style_map(self) -> Dict[str, Dict[str, any]]:
        """
        构建 Block ID 到样式的映射
        
        Returns:
            {block_id: styles} 字典
        """
        style_map = {}
        
        for rule in self.stylesheet.rules:
            target = rule.target
            block_ids = target.blockIds or []
            styles = rule.style.model_dump(exclude_none=True)
            
            for block_id in block_ids:
                if block_id not in style_map:
                    style_map[block_id] = {}
                style_map[block_id].update(styles)
        
        return style_map
    
    def _render_block(self, block: Block) -> str:
        """
        渲染单个 Block(不包括列表项,列表项由 render 方法统一处理)
        
        Args:
            block: Block 对象
            
        Returns:
            HTML 字符串
        """
        if isinstance(block, ParagraphBlock):
            return self._render_paragraph(block)
        elif isinstance(block, HeadingBlock):
            return self._render_heading(block)
        elif isinstance(block, TableBlock):
            return self._render_table(block)
        elif isinstance(block, ImageBlock):
            return self._render_image(block)
        elif isinstance(block, CodeBlock):
            return self._render_code(block)
        elif isinstance(block, DividerBlock):
            return self._render_divider(block)
        
        return ""
    
    def _render_paragraph(self, block: ParagraphBlock) -> str:
        """
        渲染段落
        
        Args:
            block: ParagraphBlock 对象
            
        Returns:
            HTML 字符串
        """
        # 应用标记
        formatted_text = self._apply_marks(block.text, block.marks)
        
        # 获取样式
        styles = self._get_block_styles(block.id)
        style_attr = self._styles_to_css(styles)
        
        return f'<p{self._attr(style_attr)}>{formatted_text}</p>'
    
    def _render_heading(self, block: HeadingBlock) -> str:
        """
        渲染标题
        
        Args:
            block: HeadingBlock 对象
            
        Returns:
            HTML 字符串
        """
        # 应用标记
        formatted_text = self._apply_marks(block.text, block.marks)
        
        # 获取样式
        styles = self._get_block_styles(block.id)
        style_attr = self._styles_to_css(styles)
        
        return f'<h{block.level}{self._attr(style_attr)}>{formatted_text}</h{block.level}>'
    
    def _render_table(self, block: TableBlock) -> str:
        """
        渲染表格
        
        Args:
            block: TableBlock 对象
            
        Returns:
            HTML 字符串
        """
        from app.utils.table_renderer import TableRenderer
        
        # 获取表格样式
        styles = self._get_block_styles(block.id)
        
        # 提取列宽度(从 StyleSheet 的 tableColumn 规则中)
        column_widths = {}
        for rule in self.stylesheet.rules:
            if (rule.target.blockType == "tableColumn" and 
                block.id in (rule.target.blockIds or []) and
                rule.target.columnIndex is not None):
                col_idx = rule.target.columnIndex
                if 'width' in rule.style.model_dump(exclude_none=True):
                    column_widths[col_idx] = rule.style.width
        
        # 使用专门的表格渲染器,传递 style_map、列宽度
        renderer = TableRenderer(block.data, styles, self.style_map, column_widths)
        return renderer.render()
    
    def _render_image(self, block: ImageBlock) -> str:
        """
        渲染图片
        
        Args:
            block: ImageBlock 对象
            
        Returns:
            HTML 字符串
        """
        # 构建属性
        attrs = [f'src="{html.escape(block.src)}"']
        
        if block.meta:
            if block.meta.alt:
                attrs.append(f'alt="{html.escape(block.meta.alt)}"')
            
            if block.meta.width:
                attrs.append(f'width="{block.meta.width}"')
            
            if block.meta.height:
                attrs.append(f'height="{block.meta.height}"')
        
        # 获取样式
        styles = self._get_block_styles(block.id)
        style_attr = self._styles_to_css(styles)
        if style_attr:
            attrs.append(f'style="{style_attr}"')
        
        return f'<img {" ".join(attrs)} />'
    
    def _render_code(self, block: CodeBlock) -> str:
        """
        渲染代码块
        
        Args:
            block: CodeBlock 对象
            
        Returns:
            HTML 字符串
        """
        # 转义 HTML 特殊字符
        escaped_text = html.escape(block.text)
        
        if block.language:
            return f'<pre><code class="language-{block.language}">{escaped_text}</code></pre>'
        else:
            return f'<pre><code>{escaped_text}</code></pre>'

    def _render_divider(self, block: DividerBlock) -> str:
        """
        渲染分割线
        直接返回标准 <hr> 标签，让 WangEditor 自动转换为内部节点
        """
        return '<hr>'
    
    def _apply_marks(self, text: str, marks: List[Mark]) -> str:
        """
        应用格式标记到文本
        处理重叠标记,避免文本重复
        
        Args:
            text: 原始文本
            marks: 标记列表
            
        Returns:
            格式化后的 HTML 文本
        """
        if not marks:
            return html.escape(text)
        
        # 1. 收集所有切分点
        boundaries = {0, len(text)}
        for mark in marks:
            start, end = mark.range
            boundaries.add(max(0, start))
            boundaries.add(min(len(text), end))
            
        sorted_boundaries = sorted(list(boundaries))
        
        # 2. 构建片段
        result = []
        
        for i in range(len(sorted_boundaries) - 1):
            start = sorted_boundaries[i]
            end = sorted_boundaries[i+1]
            
            # 获取片段文本
            segment_text = html.escape(text[start:end])
            if not segment_text:
                continue
                
            # 3. 找出覆盖该片段的所有标记
            active_marks = [
                m for m in marks 
                if m.range[0] <= start and m.range[1] >= end
            ]
            
            # 4. 分组标记
            simple_marks = [m for m in active_marks if isinstance(m, SimpleMark)]
            link_marks = [m for m in active_marks if isinstance(m, LinkMark)]
            value_marks = [m for m in active_marks if isinstance(m, ValueMark)]
            
            # 5. 先应用 SimpleMark(语义标签) - 反转顺序
            # WangEditor 期望: <span><u><strong>文本</strong></u></span>
            # Mark 列表顺序: [underline, bold]
            # 反转后应用: bold -> u,保证 u 在外层
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
                elif mark.type == "code":
                    current_html = f"<code>{current_html}</code>"
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
                    # 添加末尾分号,确保 WangEditor 正确解析
                    # 移除空格以兼容某些解析器
                    style_attr = ";".join(styles) + ";"
                    # 重要: 转义属性值中的双引号等特殊字符,防止破坏 HTML 结构
                    style_attr = html.escape(style_attr)
                    current_html = f'<span style="{style_attr}">{current_html}</span>'
            
            # 7. 应用 LinkMark(最外层)
            for mark in link_marks:
                current_html = f'<a href="{html.escape(mark.href)}">{current_html}</a>'
            
            result.append(current_html)
            
        return "".join(result)
    
    def _get_block_styles(self, block_id: str) -> Dict[str, any]:
        """
        获取 Block 的样式
        
        Args:
            block_id: Block ID
            
        Returns:
            样式字典
        """
        return self.style_map.get(block_id, {})
    
    def _styles_to_css(self, styles: Dict[str, any]) -> str:
        """
        将样式字典转换为 CSS 字符串
        
        Args:
            styles: 样式字典
            
        Returns:
            CSS 字符串
        """
        if not styles:
            return ""
        
        css_parts = []
        
        # 文本对齐
        if "textAlign" in styles:
            css_parts.append(f"text-align: {styles['textAlign']}")
        
        # 字号
        if "fontSize" in styles:
            css_parts.append(f"font-size: {styles['fontSize']}px")
        
        # 颜色
        if "color" in styles:
            css_parts.append(f"color: {styles['color']}")
        
        # 行高
        if "lineHeight" in styles:
            css_parts.append(f"line-height: {styles['lineHeight']}")
        
        # 缩进
        if "textIndent" in styles:
            indent = styles["textIndent"]
            if isinstance(indent, (int, float)):
                css_parts.append(f"text-indent: {indent}px")
            else:
                css_parts.append(f"text-indent: {indent}")
        
        # 边距
        if "marginTop" in styles:
            css_parts.append(f"margin-top: {styles['marginTop']}px")
        if "marginBottom" in styles:
            css_parts.append(f"margin-bottom: {styles['marginBottom']}px")
        if "marginLeft" in styles:
            # marginLeft 可能是字符串(如 "2em")
            margin_left = styles["marginLeft"]
            if isinstance(margin_left, (int, float)):
                css_parts.append(f"margin-left: {margin_left}px")
            else:
                css_parts.append(f"margin-left: {margin_left}")
        
        # 内边距
        if "paddingTop" in styles:
            css_parts.append(f"padding-top: {styles['paddingTop']}px")
        if "paddingBottom" in styles:
            css_parts.append(f"padding-bottom: {styles['paddingBottom']}px")
        if "paddingLeft" in styles:
            css_parts.append(f"padding-left: {styles['paddingLeft']}px")
        if "paddingRight" in styles:
            css_parts.append(f"padding-right: {styles['paddingRight']}px")
        
        # 宽度
        if "width" in styles:
            width = styles["width"]
            if isinstance(width, int):
                css_parts.append(f"width: {width}px")
            else:
                css_parts.append(f"width: {width}")
        
        # 边框
        if "borderWidth" in styles:
            css_parts.append(f"border-width: {styles['borderWidth']}px")
        if "borderStyle" in styles:
            css_parts.append(f"border-style: {styles['borderStyle']}")
        if "borderColor" in styles:
            css_parts.append(f"border-color: {styles['borderColor']}")
        
        return "; ".join(css_parts)
    
    def _attr(self, style: str) -> str:
        """
        生成 style 属性字符串
        
        Args:
            style: CSS 字符串
            
        Returns:
            ' style="..."' 或空字符串
        """
        if style:
            # 确保转义
            return f' style="{html.escape(style)}"'
        return ""
