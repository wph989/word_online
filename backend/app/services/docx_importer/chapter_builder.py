"""
章节构建器

根据标题级别将文档内容拆分为章节
"""

import uuid
from typing import List, Optional, Tuple
from dataclasses import dataclass, field

from app.models.content_models import (
    Content, StyleSheet, StyleScope, StyleRule,
    Block, HeadingBlock, ParagraphBlock
)

from .config import DocxImportConfig


@dataclass
class ChapterData:
    """章节数据"""
    id: str
    title: str
    level: int
    parent_id: Optional[str]
    order_index: int
    content: Content
    stylesheet: StyleSheet
    
    # 用于构建父子关系
    heading_level: int = 1  # 原始标题级别


class ChapterBuilder:
    """
    章节构建器
    
    根据配置的 max_heading_level 将文档元素拆分为章节：
    - H1 ~ H{max_level} 作为章节标题
    - H{max_level+1} ~ H6 作为章节内容中的 HeadingBlock
    - 首内容非标题时创建默认章节
    """
    
    def __init__(
        self, 
        blocks: List[Block], 
        style_rules: List[StyleRule],
        config: DocxImportConfig
    ):
        """
        初始化章节构建器
        
        Args:
            blocks: 所有 Block 列表
            style_rules: 所有样式规则
            config: 导入配置
        """
        self.blocks = blocks
        self.style_rules = style_rules
        self.config = config
        self.max_level = config.max_heading_level
        self.default_title = config.default_chapter_title
    
    def build(self) -> List[ChapterData]:
        """
        构建章节列表
        
        Returns:
            ChapterData 列表，包含层级关系
        """
        chapters = []
        current_blocks: List[Block] = []
        current_chapter_info: Optional[Tuple[str, int]] = None  # (title, heading_level)
        
        # 用于追踪父章节栈
        parent_stack: List[ChapterData] = []  # 按级别排列的父章节
        
        for block in self.blocks:
            if self._is_chapter_heading(block):
                # 保存当前章节（如果有内容）
                if current_chapter_info or current_blocks:
                    chapter = self._create_chapter(
                        title=current_chapter_info[0] if current_chapter_info else self.default_title,
                        heading_level=current_chapter_info[1] if current_chapter_info else 1,
                        blocks=current_blocks,
                        parent_stack=parent_stack,
                        order_index=len(chapters)
                    )
                    chapters.append(chapter)
                    self._update_parent_stack(parent_stack, chapter)
                
                # 开始新章节（标题本身不加入内容）
                current_chapter_info = (block.text, block.level)
                current_blocks = []
            else:
                # 加入当前章节内容
                current_blocks.append(block)
        
        # 处理最后一个章节
        if current_chapter_info or current_blocks:
            chapter = self._create_chapter(
                title=current_chapter_info[0] if current_chapter_info else self.default_title,
                heading_level=current_chapter_info[1] if current_chapter_info else 1,
                blocks=current_blocks,
                parent_stack=parent_stack,
                order_index=len(chapters)
            )
            chapters.append(chapter)
        
        # 如果没有创建任何章节，创建一个默认章节
        if not chapters:
            chapters.append(self._create_default_chapter())
        
        # 重新计算 order_index（同一父节点下从 0 开始）
        self._recalculate_order_indices(chapters)
        
        return chapters
    
    def _is_chapter_heading(self, block: Block) -> bool:
        """判断是否为章节标题"""
        if not isinstance(block, HeadingBlock):
            return False
        return self.config.is_chapter_heading(block.level)
    
    def _create_chapter(
        self,
        title: str,
        heading_level: int,
        blocks: List[Block],
        parent_stack: List[ChapterData],
        order_index: int
    ) -> ChapterData:
        """创建章节"""
        chapter_id = str(uuid.uuid4())
        
        # 确定父章节
        parent_id = self._find_parent_id(heading_level, parent_stack)
        
        # 确定章节层级
        level = heading_level  # 章节层级等于标题层级
        
        # 收集相关样式规则
        block_ids = [b.id for b in blocks]
        related_rules = [r for r in self.style_rules if self._rule_matches_blocks(r, block_ids)]
        
        # 创建 Content 和 StyleSheet
        content = Content(blocks=blocks)
        stylesheet = StyleSheet(
            styleId=f"style-{chapter_id[:8]}",
            appliesTo=StyleScope.CHAPTER,
            rules=related_rules
        )
        
        return ChapterData(
            id=chapter_id,
            title=title,
            level=level,
            parent_id=parent_id,
            order_index=order_index,
            content=content,
            stylesheet=stylesheet,
            heading_level=heading_level
        )
    
    def _find_parent_id(self, heading_level: int, parent_stack: List[ChapterData]) -> Optional[str]:
        """找到父章节 ID"""
        # 从后向前查找第一个级别更低的章节
        for chapter in reversed(parent_stack):
            if chapter.heading_level < heading_level:
                return chapter.id
        return None
    
    def _update_parent_stack(self, parent_stack: List[ChapterData], chapter: ChapterData):
        """更新父章节栈"""
        # 移除所有级别 >= 当前章节的项
        while parent_stack and parent_stack[-1].heading_level >= chapter.heading_level:
            parent_stack.pop()
        # 添加当前章节
        parent_stack.append(chapter)
    
    def _create_default_chapter(self) -> ChapterData:
        """创建默认章节"""
        chapter_id = str(uuid.uuid4())
        
        return ChapterData(
            id=chapter_id,
            title=self.default_title,
            level=1,
            parent_id=None,
            order_index=0,
            content=Content(blocks=[]),
            stylesheet=StyleSheet(
                styleId=f"style-{chapter_id[:8]}",
                appliesTo=StyleScope.CHAPTER,
                rules=[]
            ),
            heading_level=1
        )
    
    def _rule_matches_blocks(self, rule: StyleRule, block_ids: List[str]) -> bool:
        """检查样式规则是否匹配指定的 Block
        
        特殊处理：
        - tableCell 和 tableColumn 规则的 blockIds 是 cell-X-Y 或 table-ID 格式
        - 需要特殊处理使其与章节中的表格块关联
        """
        block_type = rule.target.blockType
        
        # 对于表格单元格和列宽样式，检查表格块是否在当前章节中
        if block_type in ("tableCell", "tableColumn"):
            # tableColumn 规则的 blockIds 是表格 ID
            if block_type == "tableColumn":
                if rule.target.blockIds:
                    return any(bid in block_ids for bid in rule.target.blockIds)
            # tableCell 规则总是应该被包含（因为它们的 ID 是 cell-X-Y）
            # 我们需要检查是否有表格块在当前章节中
            # 简化处理：如果章节中有任何表格块，就包含表格相关的样式
            for bid in block_ids:
                if bid.startswith("table-"):
                    return True
            return False
        
        # 普通 block 样式
        if rule.target.blockIds:
            return any(bid in block_ids for bid in rule.target.blockIds)
        return False
    
    def _recalculate_order_indices(self, chapters: List[ChapterData]):
        """重新计算 order_index（同一父节点下从 0 开始）"""
        # 按父节点分组
        parent_groups = {}
        for chapter in chapters:
            parent_id = chapter.parent_id
            if parent_id not in parent_groups:
                parent_groups[parent_id] = []
            parent_groups[parent_id].append(chapter)
        
        # 为每组分配 order_index
        for chapters_in_group in parent_groups.values():
            for idx, chapter in enumerate(chapters_in_group):
                chapter.order_index = idx
