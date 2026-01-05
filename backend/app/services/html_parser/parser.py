"""
HTML 解析器主类
"""

from bs4 import BeautifulSoup, Tag, NavigableString
from typing import List, Tuple, Dict, Any
import uuid

from app.models.content_models import (
    Content, StyleSheet, Block, ParagraphBlock, StyleScope
)

from .element_parsers import (
    parse_paragraph,
    parse_heading,
    parse_table,
    parse_image,
    parse_list,
    parse_code_block,
    parse_divider
)
from .utils import generate_block_id


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
        self.style_rules: List = []
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
                    block_id = generate_block_id("para")
                    self.blocks.append(ParagraphBlock(
                        id=block_id,
                        type="paragraph",
                        text=text,
                        marks=[]
                    ))
    
    def _parse_element(self, element: Tag) -> Block:
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
            return parse_paragraph(element, self.style_rules)
        
        # 标题
        elif tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return parse_heading(element, self.style_rules)
        
        # 表格
        elif tag_name == 'table':
            return parse_table(element, self.style_rules)
        
        # 图片
        elif tag_name == 'img':
            return parse_image(element, self.style_rules)
        
        # 列表(转换为带 listType 属性的段落)
        elif tag_name in ['ul', 'ol']:
            parse_list(element, self.blocks)
            return None  # 列表项已直接添加到 blocks
        
        # 代码块
        elif tag_name == 'pre':
            return parse_code_block(element)
        
        # 分割线
        elif tag_name == 'hr':
            return parse_divider(element)
        
        # 其他块级元素当作段落处理
        elif tag_name in ['div', 'section', 'article']:
            # 1. 明确的分割线包装器
            if 'w-e-textarea-divider' in element.get('class', []) or element.find('hr', recursive=False): # 浅层查找
                 return parse_divider(element)
            
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
                            self.blocks.append(child_block)
                    elif isinstance(child, NavigableString):
                        text = str(child).strip()
                        if text:
                            block_id = generate_block_id("para")
                            self.blocks.append(ParagraphBlock(
                                id=block_id,
                                type="paragraph",
                                text=text,
                                marks=[]
                            ))
                return None # 已处理，父级不需要再添加
            
            # 3. 如果没有块级子元素，但包含深层 hr (非直接子元素)
            if element.find('hr'):
                 return parse_divider(element)
                 
            # 4. 否则，当作普通段落处理
            return parse_paragraph(element, self.style_rules)
        
        return None


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
