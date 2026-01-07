"""
Content 和 StyleSheet 数据模型
使用 Pydantic 2.0 定义，与前端 TypeScript 类型完全对应
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal, Tuple
from enum import Enum


# ============ Mark 类型定义 ============

class MarkType(str, Enum):
    """Mark 类型枚举"""
    BOLD = "bold"
    ITALIC = "italic"
    UNDERLINE = "underline"
    STRIKE = "strike"
    CODE = "code"
    SUBSCRIPT = "subscript"
    SUPERSCRIPT = "superscript"
    LINK = "link"
    COLOR = "color"
    FONT_SIZE = "fontSize"
    FONT_FAMILY = "fontFamily"
    BACKGROUND_COLOR = "backgroundColor"


class BaseMark(BaseModel):
    """Mark 基类"""
    type: str
    range: Tuple[int, int] = Field(..., description="标记范围 [start, end]")


class SimpleMark(BaseMark):
    """简单 Mark（无额外属性）"""
    type: Union[Literal["bold", "italic", "underline", "strike", "code", "subscript", "superscript"], List[str]]


class LinkMark(BaseMark):
    """链接 Mark"""
    type: Literal["link"]
    href: str = Field(..., description="链接地址")


class ValueMark(BaseMark):
    """带值的 Mark（颜色、字号等）"""
    type: Literal["color", "fontSize", "fontFamily", "backgroundColor"]
    value: str = Field(..., description="样式值")


class CompositeMark(BaseMark):
    """组合 Mark（多个简单标记的集合）"""
    type: List[str]


# Mark 联合类型
Mark = Union[SimpleMark, LinkMark, ValueMark, CompositeMark]


# ============ Block 属性定义 ============

class ParagraphAttrs(BaseModel):
    """段落属性（包含列表信息）"""
    listType: Optional[Literal["bullet", "ordered", "none"]] = Field(None, description="列表类型")
    listLevel: Optional[int] = Field(None, ge=0, description="列表层级（0-based）")
    listStart: Optional[int] = Field(None, description="有序列表起始序号")


# ============ Block 定义 ============

class BlockType(str, Enum):
    """Block 类型枚举"""
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    IMAGE = "image"
    TABLE = "table"
    CODE = "code"
    DIVIDER = "divider"


class ParagraphBlock(BaseModel):
    """段落 Block"""
    id: str = Field(..., description="Block 唯一标识")
    type: Literal["paragraph"]
    text: str = Field(..., description="文本内容")
    marks: List[Mark] = Field(default_factory=list, description="格式标记列表")
    attrs: Optional[ParagraphAttrs] = Field(None, description="段落属性")


class HeadingBlock(BaseModel):
    """标题 Block"""
    id: str = Field(..., description="Block 唯一标识")
    type: Literal["heading"]
    text: str = Field(..., description="文本内容")
    level: Literal[1, 2, 3, 4, 5, 6] = Field(..., description="标题层级")
    marks: List[Mark] = Field(default_factory=list, description="格式标记列表")
    attrs: Optional[ParagraphAttrs] = Field(None, description="段落属性（支持列表）")


class ImageMeta(BaseModel):
    """图片元信息"""
    width: Optional[Union[int, str]] = Field(None, description="宽度")
    height: Optional[Union[int, str]] = Field(None, description="高度")
    alt: Optional[str] = Field(None, description="替代文本")


class ImageBlock(BaseModel):
    """图片 Block"""
    id: str = Field(..., description="Block 唯一标识")
    type: Literal["image"]
    src: str = Field(..., description="图片源地址")
    meta: Optional[ImageMeta] = Field(None, description="图片元信息")


class CodeBlock(BaseModel):
    """代码块 Block"""
    id: str = Field(..., description="Block 唯一标识")
    type: Literal["code"]
    text: str = Field(..., description="代码内容")
    language: Optional[str] = Field(None, description="编程语言")


class DividerBlock(BaseModel):
    """分割线 Block"""
    id: str = Field(..., description="Block 唯一标识")
    type: Literal["divider"]


# ============ 表格相关定义 ============

class TableCellContent(BaseModel):
    """单元格内容"""
    text: str = Field(..., description="文本内容")
    marks: List[Mark] = Field(default_factory=list, description="格式标记列表")


class TableCellData(BaseModel):
    """表格单元格数据"""
    cell: Tuple[int, int] = Field(..., description="单元格位置 [row, col]")
    content: TableCellContent = Field(..., description="单元格内容")
    styleId: Optional[str] = Field(None, description="样式 ID 引用")


class MergeRegion(BaseModel):
    """合并单元格区域"""
    id: str = Field(..., description="合并区域唯一标识")
    start: Tuple[int, int] = Field(..., description="起始位置 [row, col]")
    end: Tuple[int, int] = Field(..., description="结束位置 [row, col]")
    masterCell: Tuple[int, int] = Field(..., description="主单元格位置 [row, col]")
    type: Literal["horizontal", "vertical", "rectangular"] = Field(..., description="合并类型")


class TableData(BaseModel):
    """表格数据"""
    rows: int = Field(..., ge=0, description="行数")
    cols: int = Field(..., ge=0, description="列数")
    cells: List[TableCellData] = Field(default_factory=list, description="单元格数据列表")
    mergeRegions: List[MergeRegion] = Field(default_factory=list, description="合并区域列表")


class TableBlock(BaseModel):
    """表格 Block"""
    id: str = Field(..., description="Block 唯一标识")
    type: Literal["table"]
    data: TableData = Field(..., description="表格数据")
    styleId: Optional[str] = Field(None, description="表格样式 ID")


# Block 联合类型
Block = Union[ParagraphBlock, HeadingBlock, ImageBlock, TableBlock, CodeBlock, DividerBlock]


# ============ Content 定义 ============

class Content(BaseModel):
    """Content 模型（文档内容）"""
    blocks: List[Block] = Field(default_factory=list, description="Block 列表")


# ============ StyleSheet 定义 ============

class StyleScope(str, Enum):
    """样式作用域"""
    GLOBAL = "global"
    DOCUMENT = "document"
    CHAPTER = "chapter"


class StyleTarget(BaseModel):
    """样式目标选择器"""
    blockType: Optional[Literal["paragraph", "heading", "image", "table", "tableRow", "tableCell", "tableColumn", "tableMerge"]] = None
    listType: Optional[Literal["bullet", "ordered"]] = None
    level: Optional[int] = Field(None, description="标题层级")
    markType: Optional[Literal["bold", "italic", "underline", "code", "link"]] = None
    scope: Optional[Literal["block", "container", "inline"]] = None
    blockIds: Optional[List[str]] = Field(None, description="精确命中的 Block ID 列表")
    
    # 表格特定目标
    cellType: Optional[Literal["th", "td"]] = None
    cellPosition: Optional[str] = Field(None, description="单元格位置 'row-col'")
    rowType: Optional[Literal["header", "body", "footer"]] = None
    rowIndex: Optional[Union[Literal["odd", "even"], int]] = None
    columnIndex: Optional[int] = None
    mergeId: Optional[str] = None


class LayoutStyle(BaseModel):
    """布局样式"""
    width: Optional[Union[int, str]] = None
    height: Optional[Union[int, str]] = None
    align: Optional[Literal["left", "center", "right"]] = None
    display: Optional[Literal["block", "inline-block"]] = None


class TextStyle(BaseModel):
    """文本样式"""
    fontSize: Optional[int] = Field(None, description="字号（pt 或 px）")
    fontFamily: Optional[str] = None
    fontWeight: Optional[Union[int, str]] = None
    lineHeight: Optional[float] = None
    color: Optional[str] = None
    textAlign: Optional[Literal["left", "center", "right", "justify"]] = None
    textIndent: Optional[Union[int, str]] = None
    letterSpacing: Optional[float] = None
    backgroundColor: Optional[str] = None


class BorderStyle(BaseModel):
    """边框样式"""
    borderWidth: Optional[int] = None
    borderStyle: Optional[Literal["solid", "dashed", "dotted", "double"]] = None
    borderColor: Optional[str] = None
    borderRadius: Optional[int] = None
    
    # 四边独立控制
    borderTopWidth: Optional[int] = None
    borderTopStyle: Optional[str] = None
    borderTopColor: Optional[str] = None
    borderBottomWidth: Optional[int] = None
    borderBottomStyle: Optional[str] = None
    borderBottomColor: Optional[str] = None
    borderLeftWidth: Optional[int] = None
    borderLeftStyle: Optional[str] = None
    borderLeftColor: Optional[str] = None
    borderRightWidth: Optional[int] = None
    borderRightStyle: Optional[str] = None
    borderRightColor: Optional[str] = None


class SpacingStyle(BaseModel):
    """间距样式"""
    marginTop: Optional[int] = None
    marginBottom: Optional[int] = None
    paddingTop: Optional[int] = None
    paddingBottom: Optional[int] = None
    paddingLeft: Optional[int] = None
    paddingRight: Optional[int] = None
    padding: Optional[Union[str, int]] = None
    
    # 扩展
    minWidth: Optional[Union[str, int]] = None
    maxWidth: Optional[Union[str, int]] = None
    minHeight: Optional[Union[str, int]] = None


class ListStyle(BaseModel):
    """列表样式"""
    listStyleType: Optional[Literal["disc", "circle", "square", "decimal", "lower-alpha"]] = None
    markerColor: Optional[str] = None


class TableStyle(BaseModel):
    """表格样式"""
    borderCollapse: Optional[Literal["collapse", "separate"]] = None
    tableLayout: Optional[Literal["auto", "fixed"]] = None
    cellSpacing: Optional[str] = None
    cellPadding: Optional[str] = None


class CellStyle(BaseModel):
    """单元格样式"""
    verticalAlign: Optional[Literal["top", "middle", "bottom"]] = None


class StyleDeclaration(LayoutStyle, TextStyle, BorderStyle, SpacingStyle, ListStyle, TableStyle, CellStyle):
    """
    样式声明（组合所有样式类型）
    继承所有样式基类，形成完整的样式定义
    """
    pass


class StyleRule(BaseModel):
    """样式规则"""
    target: StyleTarget = Field(..., description="样式目标选择器")
    style: StyleDeclaration = Field(..., description="样式声明")


class StyleSheet(BaseModel):
    """样式表"""
    styleId: str = Field(..., description="样式表唯一标识")
    appliesTo: StyleScope = Field(..., description="样式作用域")
    rules: List[StyleRule] = Field(default_factory=list, description="样式规则列表")
