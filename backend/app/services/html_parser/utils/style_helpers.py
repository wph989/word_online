"""
样式辅助函数
"""

import uuid
from typing import Dict, Any, Optional

from app.models.content_models import (
    StyleRule, StyleTarget, StyleDeclaration
)


def add_style_rule(
    style_rules: list,
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
        style_rules: 样式规则列表
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
    
    style_rules.append(rule)


def generate_block_id(prefix: str) -> str:
    """生成唯一的块 ID"""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"
