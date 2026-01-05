# HTML 生成流程详解

## 概述

HTML 生成服务负责将结构化的 JSON 数据(Content + StyleSheet)重新渲染为 HTML,用于前端编辑器回显或导出。系统提供两种渲染器:
- **HtmlRenderer**: 标准 HTML 渲染器
- **WangEditorRenderer**: WangEditor 兼容的 HTML 渲染器(推荐用于前端回显)

## 核心设计原则

1. **数据驱动**: 完全基于 Content 和 StyleSheet 生成 HTML
2. **样式合并**: 将 StyleSheet 中的样式规则应用到对应的 Block
3. **格式还原**: 正确还原 Marks 的嵌套和重叠
4. **编辑器兼容**: WangEditorRenderer 生成符合 WangEditor 期望的 HTML 格式

## 主要组件

### 1. WangEditorRenderer (推荐)

**文件位置**: `app/services/wangeditor_renderer.py`

**主要职责**:
- 将 Content 和 StyleSheet 渲染为 WangEditor 兼容的 HTML
- 正确处理列表的合并和嵌套
- 处理重叠的 Mark,避免文本重复
- 生成符合 WangEditor 解析规则的标签结构

**特点**:
- 输出标准 `<hr>` 标签(而非 WangEditor 内部包装)
- SimpleMark 反转顺序应用,确保标签嵌套正确
- ValueMark 合并到单个 `<span>`,减少冗余标签
- 样式属性添加末尾分号,确保解析正确

### 2. HtmlRenderer (标准版)

**文件位置**: `app/services/html_renderer.py`

**主要职责**:
- 生成标准的 HTML
- 适用于非 WangEditor 场景

### 3. TableRenderer (表格渲染器)

**文件位置**: `app/utils/table_renderer.py`

**主要职责**:
- 专门处理复杂表格的渲染
- 支持合并单元格(rowspan/colspan)
- 应用单元格样式
- 渲染列宽度(colgroup)

## 详细生成流程

### 第一阶段: 初始化

```python
renderer = WangEditorRenderer(content, stylesheet)
```

**执行步骤**:
1. 保存 Content 和 StyleSheet 对象
2. 调用 `_build_style_map()` 构建样式映射

**样式映射构建**:
```python
def _build_style_map() -> Dict[str, Dict[str, any]]:
    """
    构建 Block ID 到样式的映射
    
    遍历 StyleSheet.rules:
        - 提取 target.blockIds
        - 提取 style 字典
        - 合并到 style_map[block_id]
    
    返回: {block_id: {样式属性}}
    """
```

**示例**:
```python
# StyleSheet
{
  "rules": [
    {
      "target": {"blockIds": ["para-1"]},
      "style": {"textAlign": "center", "fontSize": 16}
    }
  ]
}

# style_map
{
  "para-1": {"textAlign": "center", "fontSize": 16}
}
```

### 第二阶段: 渲染主流程

**方法**: `render()`

**执行流程**:
```
1. 初始化 html_parts 列表
2. 遍历 content.blocks:
   a. 检查是否是列表项
   b. 如果是列表项:
      - 收集连续的同类型同层级列表项
      - 调用 _render_list_group() 渲染整个列表
      - 跳过已处理的列表项
   c. 如果是普通块:
      - 调用 _render_block() 渲染单个块
3. 用换行符连接所有 HTML 片段
4. 返回完整 HTML 字符串
```

**列表合并逻辑**:
```python
# 收集连续的同类型同层级列表项
list_items = [block]
list_type = block.attrs.listType  # "bullet" 或 "ordered"
list_level = block.attrs.listLevel or 0

# 向后查找连续的列表项
while next_block.attrs.listType == list_type and 
      next_block.attrs.listLevel == list_level:
    list_items.append(next_block)

# 渲染为单个 <ul> 或 <ol>
```

### 第三阶段: Block 渲染

**方法**: `_render_block(block: Block)`

**分发逻辑**:
```python
if isinstance(block, ParagraphBlock):
    return _render_paragraph(block)
elif isinstance(block, HeadingBlock):
    return _render_heading(block)
elif isinstance(block, TableBlock):
    return _render_table(block)
elif isinstance(block, ImageBlock):
    return _render_image(block)
elif isinstance(block, CodeBlock):
    return _render_code(block)
elif isinstance(block, DividerBlock):
    return _render_divider(block)
```

#### 1. 段落渲染

**方法**: `_render_paragraph(block: ParagraphBlock)`

**执行流程**:
```
1. 调用 _apply_marks() 应用格式标记
2. 调用 _get_block_styles() 获取样式
3. 调用 _styles_to_css() 转换为 CSS 字符串
4. 生成 <p> 标签,包含 style 属性
```

**输出示例**:
```html
<p style="text-align: center; font-size: 16px">
  <strong>加粗文本</strong>
</p>
```

#### 2. 标题渲染

**方法**: `_render_heading(block: HeadingBlock)`

**执行流程**:
```
1. 应用标记
2. 获取样式
3. 生成 <h{level}> 标签
```

**输出示例**:
```html
<h1 style="text-align: center">标题文本</h1>
```

#### 3. 表格渲染

**方法**: `_render_table(block: TableBlock)`

**执行流程**:
```
1. 获取表格样式(从 style_map)
2. 提取列宽度(从 StyleSheet 的 tableColumn 规则)
3. 创建 TableRenderer 实例
4. 调用 renderer.render() 生成表格 HTML
```

**TableRenderer 详细流程**:

##### 3.1 初始化
```python
TableRenderer(table_data, table_styles, style_map, column_widths)
```
- 构建单元格位置到数据的映射 `cell_map`
- 构建被合并单元格的集合 `merged_cells`

##### 3.2 渲染表格
```
1. 构建表格样式(border-collapse, width, border)
2. 渲染 <table> 开始标签
3. 渲染 <colgroup>(列宽度)
4. 遍历每一行:
   a. 渲染 <tr> 开始标签
   b. 调用 _render_row() 渲染行内单元格
   c. 渲染 </tr> 结束标签
5. 渲染 </table> 结束标签
```

##### 3.3 渲染列宽度
```python
def _render_colgroup():
    """
    生成 <colgroup>
    
    遍历每一列:
        如果有宽度: <col width="100">
        否则: <col>
    """
```

**输出示例**:
```html
<colgroup>
  <col width="100">
  <col width="200">
</colgroup>
```

##### 3.4 渲染单元格
```python
def _render_cell(row_idx, col_idx):
    """
    1. 跳过被合并的单元格
    2. 获取单元格数据
    3. 应用标记到文本
    4. 获取 rowspan 和 colspan
    5. 构建属性:
       - rowSpan, colSpan
       - width (从 column_widths)
       - style (边框、内边距、对齐、字体、颜色)
    6. 判断标签类型(th/td)
    7. 生成 HTML
    """
```

**单元格样式合并**:
```
默认样式:
  - border: 1px solid #ddd
  - padding: 8px

如果有 styleId:
  从 style_map 获取样式:
    - textAlign, verticalAlign
    - fontFamily, fontSize, fontWeight
    - color, backgroundColor
```

**输出示例**:
```html
<td rowSpan="2" colSpan="1" width="100" 
    style="border: 1px solid #ddd; padding: 8px; text-align: center; background-color: #f0f0f0">
  <strong>单元格内容</strong>
</td>
```

#### 4. 图片渲染

**方法**: `_render_image(block: ImageBlock)`

**执行流程**:
```
1. 构建 src 属性
2. 添加 alt, width, height 属性(如果有)
3. 获取样式(如果有)
4. 生成 <img> 标签
```

**输出示例**:
```html
<img src="/uploads/image.png" alt="示例图片" width="300" height="200" />
```

#### 5. 代码块渲染

**方法**: `_render_code(block: CodeBlock)`

**执行流程**:
```
1. 转义 HTML 特殊字符
2. 如果有语言,添加 class="language-{language}"
3. 生成 <pre><code> 结构
```

**输出示例**:
```html
<pre><code class="language-python">
def hello():
    print("Hello World")
</code></pre>
```

#### 6. 分割线渲染

**方法**: `_render_divider(block: DividerBlock)`

**WangEditorRenderer 实现**:
```python
def _render_divider(block: DividerBlock) -> str:
    """直接返回标准 <hr> 标签"""
    return '<hr>'
```

**注意**: 不使用 WangEditor 内部的 div 包装,让编辑器自动转换

#### 7. 列表渲染

**方法**: `_render_list_group(items, list_type, level)`

**执行流程**:
```
1. 确定标签类型(ul/ol)
2. 遍历列表项:
   a. 应用标记
   b. 获取样式
   c. 生成 <li> 标签
3. 添加缩进样式(如果 level > 0)
4. 生成完整的 <ul> 或 <ol>
```

**缩进计算**:
```python
if level > 0:
    indent = level * 2  # 每级缩进 2em
    indent_style = f' style="margin-left: {indent}em"'
```

**输出示例**:
```html
<ul>
  <li>列表项 1</li>
  <li>列表项 2</li>
</ul>

<!-- 嵌套列表 -->
<ul style="margin-left: 2em">
  <li>嵌套项 1</li>
  <li>嵌套项 2</li>
</ul>
```

### 第四阶段: Mark 应用

**方法**: `_apply_marks(text: str, marks: List[Mark])`

**核心算法**: 文本分段 + 标记应用

**执行流程**:

#### 1. 收集切分点
```python
boundaries = {0, len(text)}
for mark in marks:
    boundaries.add(mark.range[0])
    boundaries.add(mark.range[1])
sorted_boundaries = sorted(boundaries)
```

**示例**:
```
文本: "Hello World"
Marks:
  - bold: [0, 5]
  - color(red): [6, 11]

切分点: {0, 5, 6, 11}
片段:
  - [0, 5]: "Hello"
  - [5, 6]: " "
  - [6, 11]: "World"
```

#### 2. 遍历片段
```python
for i in range(len(sorted_boundaries) - 1):
    start = sorted_boundaries[i]
    end = sorted_boundaries[i+1]
    segment_text = html.escape(text[start:end])
```

#### 3. 查找覆盖该片段的标记
```python
active_marks = [
    m for m in marks 
    if m.range[0] <= start and m.range[1] >= end
]
```

#### 4. 分组标记
```python
simple_marks = [m for m in active_marks if isinstance(m, SimpleMark)]
link_marks = [m for m in active_marks if isinstance(m, LinkMark)]
value_marks = [m for m in active_marks if isinstance(m, ValueMark)]
```

#### 5. 应用 SimpleMark (反转顺序)

**WangEditorRenderer 实现**:
```python
current_html = segment_text
for mark in reversed(simple_marks):
    if mark.type == "bold":
        current_html = f"<strong>{current_html}</strong>"
    elif mark.type == "italic":
        current_html = f"<em>{current_html}</em>"
    elif mark.type == "underline":
        current_html = f"<u>{current_html}</u>"
    # ... 其他类型
```

**为什么反转?**
```
Marks 列表: [underline, bold]
期望输出: <u><strong>文本</strong></u>

反转后应用:
  1. bold -> <strong>文本</strong>
  2. underline -> <u><strong>文本</strong></u>
```

#### 6. 应用 ValueMark (合并到单个 span)

```python
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
        style_attr = ";".join(styles) + ";"  # 末尾分号
        style_attr = html.escape(style_attr)  # 转义
        current_html = f'<span style="{style_attr}">{current_html}</span>'
```

**优化**: 多个 ValueMark 合并到一个 `<span>`,减少标签嵌套

#### 7. 应用 LinkMark (最外层)

```python
for mark in link_marks:
    current_html = f'<a href="{html.escape(mark.href)}">{current_html}</a>'
```

**标签嵌套顺序**:
```
文本 -> SimpleMark -> ValueMark -> LinkMark

示例:
<a href="...">
  <span style="color: red;">
    <strong>文本</strong>
  </span>
</a>
```

#### 8. 拼接结果
```python
result.append(current_html)
return "".join(result)
```

**完整示例**:
```
输入:
  text: "Hello World"
  marks:
    - bold: [0, 5]
    - color(red): [0, 5]
    - italic: [6, 11]

输出:
<span style="color: red;"><strong>Hello</strong></span> <em>World</em>
```

### 第五阶段: 样式转换

**方法**: `_styles_to_css(styles: Dict[str, any])`

**执行流程**:
```
1. 初始化 css_parts 列表
2. 遍历样式字典,转换为 CSS 属性:
   - textAlign -> text-align
   - fontSize -> font-size (添加 px)
   - color -> color
   - lineHeight -> line-height
   - textIndent -> text-indent (添加 px)
   - margin/padding -> 添加 px
   - width -> 处理数字和字符串
   - border -> 拆分为 width/style/color
3. 用 "; " 连接所有 CSS 属性
4. 返回 CSS 字符串
```

**转换规则**:
```python
# 文本对齐
"textAlign": "center" -> "text-align: center"

# 字号(添加单位)
"fontSize": 16 -> "font-size: 16px"

# 宽度(智能处理)
"width": 100 -> "width: 100px"
"width": "50%" -> "width: 50%"

# 边框(组合属性)
"borderWidth": 1, "borderStyle": "solid", "borderColor": "#000"
-> "border-width: 1px; border-style: solid; border-color: #000"
```

**输出示例**:
```css
text-align: center; font-size: 16px; color: #333; line-height: 1.5
```

### 第六阶段: 属性生成

**方法**: `_attr(style: str)`

**执行逻辑**:
```python
def _attr(style: str) -> str:
    if style:
        return f' style="{html.escape(style)}"'
    return ""
```

**用途**: 生成 HTML 元素的 style 属性

**示例**:
```python
_attr("color: red") -> ' style="color: red"'
_attr("") -> ""
```

## 关键优化

### 1. 列表合并
- 将连续的同类型同层级列表项合并到一个 `<ul>` 或 `<ol>`
- 避免生成多个独立的列表标签
- 提高 HTML 语义性和可读性

### 2. Mark 去重
- 通过文本分段算法,避免重复应用标记
- 正确处理重叠的标记
- 确保每个文本片段只被处理一次

### 3. 样式合并
- 将多个 ValueMark 合并到单个 `<span>`
- 减少标签嵌套层级
- 提高 HTML 简洁性

### 4. 表格优化
- 使用 `colgroup` 统一管理列宽度
- 单元格样式集中处理
- 正确处理合并单元格的 rowspan/colspan

### 5. 转义处理
- 文本内容使用 `html.escape()` 转义
- 属性值使用 `html.escape()` 转义
- 防止 XSS 攻击

## 使用示例

### 基础使用
```python
from app.services.wangeditor_renderer import WangEditorRenderer
from app.models.content_models import Content, StyleSheet

# 1. 准备数据
content = Content(blocks=[...])
stylesheet = StyleSheet(styleId="...", appliesTo="chapter", rules=[...])

# 2. 创建渲染器
renderer = WangEditorRenderer(content, stylesheet)

# 3. 生成 HTML
html_output = renderer.render()
```

### 从 JSON 创建
```python
import json
from app.models.content_models import Content, StyleSheet

# 1. 从 JSON 字符串解析
content_json = json.loads(content_str)
stylesheet_json = json.loads(stylesheet_str)

# 2. 创建 Pydantic 模型
content = Content(**content_json)
stylesheet = StyleSheet(**stylesheet_json)

# 3. 渲染
renderer = WangEditorRenderer(content, stylesheet)
html = renderer.render()
```

### 从数据库读取
```python
from app.services.wangeditor_renderer import WangEditorRenderer
from app.models.content_models import Content, StyleSheet

# 1. 从数据库读取 JSON
chapter = db.query(Chapter).filter_by(id=chapter_id).first()

# 2. 解析为 Pydantic 模型
content = Content(**chapter.content)
stylesheet = StyleSheet(**chapter.stylesheet)

# 3. 渲染
renderer = WangEditorRenderer(content, stylesheet)
html = renderer.render()
```

## 错误处理

### 1. 缺失数据
```python
# 单元格数据缺失
if not cell_data:
    return '<td></td>'  # 返回空单元格
```

### 2. 样式缺失
```python
# Block 没有样式
styles = self._get_block_styles(block.id)  # 返回 {}
style_attr = self._styles_to_css(styles)  # 返回 ""
```

### 3. 类型错误
```python
# 宽度可能是数字或字符串
if isinstance(width, int):
    css_parts.append(f"width: {width}px")
else:
    css_parts.append(f"width: {width}")
```

## 性能考虑

### 1. 样式映射预构建
- 在初始化时构建 `style_map`
- 避免在渲染每个 Block 时重复查找

### 2. 字符串拼接优化
- 使用列表收集 HTML 片段
- 最后用 `join()` 一次性拼接
- 避免多次字符串连接

### 3. 条件渲染
- 只在有样式时生成 style 属性
- 只在有属性时生成属性字符串

### 4. 缓存计算结果
- 单元格的 rowspan/colspan 计算后缓存
- 避免重复遍历 mergeRegions

## 扩展性

### 添加新的 Block 渲染
1. 在 `_render_block()` 中添加新的分支
2. 实现对应的 `_render_xxx()` 方法

### 添加新的样式属性
1. 在 `_styles_to_css()` 中添加新的转换规则
2. 确保单位和格式正确

### 自定义渲染逻辑
1. 继承 `WangEditorRenderer`
2. 重写需要自定义的方法
3. 保持接口一致性

## 注意事项

1. **HTML 转义**: 所有文本内容和属性值必须转义
2. **标签嵌套**: 确保标签正确嵌套和闭合
3. **样式格式**: CSS 属性值格式要正确(如单位、颜色格式)
4. **编辑器兼容**: WangEditorRenderer 的输出必须符合 WangEditor 的解析规则
5. **空值处理**: 对于空文本、空样式,生成合法的 HTML

## 测试建议

1. **基础渲染测试**: 测试每种 Block 类型的渲染
2. **样式应用测试**: 验证样式正确应用
3. **Mark 重叠测试**: 测试复杂的 Mark 组合
4. **表格渲染测试**: 测试合并单元格、列宽度
5. **往返测试**: HTML -> 解析 -> 渲染 -> HTML,验证一致性
6. **编辑器兼容测试**: 在 WangEditor 中加载渲染结果,验证正确性
