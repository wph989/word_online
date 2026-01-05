# HTML 解析流程详解

## 概述

HTML 解析服务负责将前端 WangEditor 生成的 HTML 内容解析为结构化的 JSON 数据,实现**内容与样式的严格分离**。解析后的数据分为两部分:
- **Content**: 存储文档的语义结构和文本内容
- **StyleSheet**: 存储样式规则,独立于内容

## 核心设计原则

1. **数据与样式严格分离**: Content 只存储语义和结构,样式信息独立存储在 StyleSheet 中
2. **保留原始 HTML**: 原始 HTML 作为备份存储,确保可以完全还原
3. **提取结构化数据**: 生成便于 AI 处理的结构化 JSON 数据
4. **样式独立存储**: 便于主题切换和样式管理

## 主要组件

### 1. HtmlParser (核心解析器)

**文件位置**: `app/services/html_parser.py`

**主要职责**:
- 解析 HTML 字符串为 BeautifulSoup 对象
- 遍历 DOM 树,提取块级元素
- 提取文本内容和格式标记(Marks)
- 提取用户设置的样式(过滤默认样式)
- 生成 Content 和 StyleSheet 对象

### 2. TableParser (表格解析器)

**文件位置**: `app/utils/table_parser.py`

**主要职责**:
- 专门处理复杂表格结构
- 支持合并单元格(rowspan/colspan)
- 提取单元格内容和格式
- 生成表格数据模型

## 详细解析流程

### 第一阶段: 初始化

```python
parser = HtmlParser(html_content)
```

**执行步骤**:
1. 使用 BeautifulSoup 解析 HTML 字符串
2. 初始化空的 blocks 列表和 style_rules 列表
3. 生成唯一的 style_id (格式: `style-{uuid}`)
4. 初始化样式计数器

### 第二阶段: 解析 Body

**方法**: `_parse_body()`

**执行流程**:
1. 查找 `<body>` 标签,如果没有则使用整个文档
2. 遍历 body 的所有直接子元素
3. 对每个子元素调用 `_parse_element()` 进行解析
4. 将解析结果添加到 blocks 列表

**特殊处理**:
- 对于纯文本节点(不在任何标签内),自动包装为段落块

### 第三阶段: 元素解析

**方法**: `_parse_element(element: Tag)`

**支持的元素类型**:

#### 1. 段落 (`<p>`)
- **处理方法**: `_parse_paragraph()`
- **提取内容**:
  - 文本内容和内联标记(Marks)
  - 块级样式(文本对齐、行高、缩进等)
- **生成**: `ParagraphBlock` 对象

#### 2. 标题 (`<h1>` - `<h6>`)
- **处理方法**: `_parse_heading()`
- **提取内容**:
  - 标题层级(1-6)
  - 文本内容和标记
  - 标题样式
- **生成**: `HeadingBlock` 对象

#### 3. 表格 (`<table>`)
- **处理方法**: `_parse_table()`
- **提取内容**:
  - 表格行数和列数
  - 单元格内容和位置
  - 合并单元格信息(rowspan/colspan)
  - 列宽度(从 colgroup 或首行提取)
  - 单元格样式
- **生成**: `TableBlock` 对象

**表格解析详细流程**:
```
1. 获取所有 <tr> 元素,计算行数
2. 遍历每行的单元格,计算最大列数
3. 创建占用矩阵(occupied),跟踪合并单元格占用情况
4. 逐行解析:
   a. 跳过被合并占用的列
   b. 提取单元格内容和标记
   c. 提取单元格样式(对齐、字体、颜色等)
   d. 标记占用区域
   e. 识别合并区域,生成 MergeRegion
5. 提取列宽度(从 colgroup 或 style 属性)
6. 提取表格级样式(边框、宽度等)
```

#### 4. 图片 (`<img>`)
- **处理方法**: `_parse_image()`
- **提取内容**:
  - src 属性(图片地址)
  - alt 属性(替代文本)
  - width/height 属性
- **生成**: `ImageBlock` 对象

#### 5. 列表 (`<ul>`, `<ol>`)
- **处理方法**: `_parse_list()` + `_parse_list_items()`
- **处理策略**: 将列表项转换为带 `listType` 属性的段落
- **支持**:
  - 有序列表(ordered)和无序列表(bullet)
  - 嵌套列表(通过 listLevel 表示层级)
  - 起始序号(listStart)

**列表解析流程**:
```
1. 识别列表类型(ul -> bullet, ol -> ordered)
2. 递归遍历 <li> 元素:
   a. 提取文本和标记
   b. 创建 ParagraphBlock,设置 attrs.listType
   c. 设置 attrs.listLevel(嵌套层级)
   d. 如果是有序列表,设置 attrs.listStart
3. 递归处理嵌套列表(level + 1)
```

#### 6. 代码块 (`<pre>`)
- **处理方法**: `_parse_code_block()`
- **提取内容**:
  - 代码文本
  - 编程语言(从 `class="language-xxx"` 提取)
- **生成**: `CodeBlock` 对象

#### 7. 分割线 (`<hr>`)
- **处理方法**: `_parse_divider()`
- **生成**: `DividerBlock` 对象

#### 8. 容器元素 (`<div>`, `<section>`, `<article>`)
**特殊处理逻辑**:
1. 如果是分割线包装器 -> 解析为 DividerBlock
2. 如果包含块级子元素 -> 递归解包,处理子元素
3. 如果包含深层 `<hr>` -> 解析为 DividerBlock
4. 否则 -> 当作普通段落处理

### 第四阶段: 文本和标记提取

**方法**: `_extract_text_and_marks(element: Tag)`

**核心算法**: 递归遍历法

**执行流程**:
```
1. 定义递归函数 traverse(node, current_marks)
2. 对于文本节点:
   a. 记录文本起始位置
   b. 添加文本到 full_text
   c. 为文本段应用所有累积的标记
3. 对于元素节点:
   a. 识别语义标签(strong, em, u, s, code, sup, sub)
   b. 识别链接标签(<a>)
   c. 从 style 属性提取内联样式(color, fontSize, fontFamily, backgroundColor)
   d. 将新标记添加到 current_marks
   e. 递归处理子节点
```

**标记类型**:

1. **SimpleMark** (语义标签):
   - `bold` (<strong>, <b>)
   - `italic` (<em>, <i>)
   - `underline` (<u>)
   - `strike` (<s>, <strike>, <del>)
   - `code` (<code>)
   - `superscript` (<sup>)
   - `subscript` (<sub>)

2. **LinkMark** (链接):
   - `link` (<a href="...">)

3. **ValueMark** (样式值):
   - `color` (文本颜色)
   - `backgroundColor` (背景色)
   - `fontSize` (字号)
   - `fontFamily` (字体)

**标记范围**: 每个 Mark 包含 `range: [start, end]`,表示在文本中的起止位置

### 第五阶段: 样式提取

#### 1. 块级样式提取

**方法**: `_extract_user_block_styles(element: Tag)`

**提取策略**: 只提取用户明确设置的样式,过滤默认样式

**提取的样式**:
- `textAlign`: 文本对齐(过滤 start/left)
- `color`: 文本颜色(过滤黑色)
- `lineHeight`: 行高
- `textIndent`: 首行缩进

**不提取的样式**:
- `fontSize` 和 `fontFamily`: 这些样式在字符级别(Marks)处理,避免段落样式覆盖字符样式

#### 2. 单元格样式提取

**方法**: `_extract_cell_user_styles(cell: Tag)`

**提取的样式**:
- `textAlign`: 文本对齐
- `verticalAlign`: 垂直对齐
- `fontFamily`: 字体
- `fontSize`: 字号
- `fontWeight`: 字体粗细
- `color`: 文本颜色
- `backgroundColor`: 背景色

**样式来源**:
- style 属性
- HTML 属性(align, valign, bgcolor)

#### 3. 表格样式提取

**方法**: `_extract_table_styles(table: Tag)`

**提取的样式**:
- `borderWidth`, `borderStyle`, `borderColor`: 边框
- `width`: 表格宽度
- `borderCollapse`: 边框折叠

#### 4. 列宽度提取

**方法**: `_extract_column_widths(table, table_id, col_count)`

**提取策略**:
1. 优先从 `<colgroup>` 的 `<col>` 元素提取
2. 如果没有 colgroup,从首行单元格的 width 属性或 style 提取
3. 过滤 "auto" 值
4. 提取数字部分,转换为整数

**存储方式**: 为每列生成一个 StyleRule,target 指定 `columnIndex`

### 第六阶段: 样式规则生成

**方法**: `_add_style_rule(block_id, block_type, styles, ...)`

**执行步骤**:
1. 构建 `StyleTarget` 对象:
   - `blockType`: Block 类型(paragraph, heading, table, tableCell, tableColumn)
   - `blockIds`: 目标 Block ID 列表
   - `level`: 标题层级(可选)
   - `columnIndex`: 列索引(可选,用于表格列)
   - `cellType`: 单元格类型(可选,th/td)

2. 构建 `StyleDeclaration` 对象:
   - 将样式字典转换为 Pydantic 模型

3. 创建 `StyleRule` 对象:
   - 包含 target 和 style

4. 添加到 `style_rules` 列表

### 第七阶段: 生成最终结果

**方法**: `parse()`

**返回值**: `(Content, StyleSheet)` 元组

**Content 结构**:
```json
{
  "blocks": [
    {
      "id": "para-xxx",
      "type": "paragraph",
      "text": "文本内容",
      "marks": [
        {"type": "bold", "range": [0, 2]},
        {"type": "color", "range": [3, 5], "value": "red"}
      ],
      "attrs": {
        "listType": "none"
      }
    }
  ]
}
```

**StyleSheet 结构**:
```json
{
  "styleId": "style-abc123",
  "appliesTo": "chapter",
  "rules": [
    {
      "target": {
        "blockType": "paragraph",
        "blockIds": ["para-xxx"]
      },
      "style": {
        "textAlign": "center",
        "fontSize": 16
      }
    }
  ]
}
```

## 关键优化

### 1. 样式过滤
- 只保存用户明确设置的样式
- 过滤浏览器默认样式(如黑色文本、左对齐)
- 减少冗余数据

### 2. Mark 去重
- 避免重复标记
- 正确处理嵌套标记
- 合并相邻的相同标记

### 3. 表格优化
- 使用占用矩阵高效处理合并单元格
- 一次遍历完成所有提取
- 支持复杂的合并场景(横向、纵向、矩形)

### 4. 列表处理
- 将列表项转换为段落,通过属性标识
- 支持任意层级嵌套
- 保留列表语义

## 使用示例

```python
from app.services.html_parser import HtmlParser

# 1. 创建解析器
html_content = "<p>Hello <strong>World</strong></p>"
parser = HtmlParser(html_content)

# 2. 执行解析
content, stylesheet = parser.parse()

# 3. 转换为字典(用于 JSON 序列化)
content_dict = content.model_dump()
stylesheet_dict = stylesheet.model_dump()

# 4. 便捷函数
from app.services.html_parser import parse_html_to_json
content_dict, stylesheet_dict = parse_html_to_json(html_content)
```

## 错误处理

- **无效 HTML**: BeautifulSoup 会尽力解析,容错性强
- **缺失属性**: 使用 `.get()` 方法,提供默认值
- **样式解析失败**: 使用正则表达式匹配,失败时跳过
- **类型转换失败**: 使用 try-except 捕获,使用默认值

## 性能考虑

- **单次遍历**: 尽量在一次遍历中完成所有提取
- **延迟计算**: 只在需要时计算复杂属性
- **缓存**: 对于重复查询的元素,使用局部变量缓存
- **正则编译**: 频繁使用的正则表达式可以预编译

## 扩展性

### 添加新的 Block 类型
1. 在 `content_models.py` 中定义新的 Block 类
2. 在 `_parse_element()` 中添加新的分支
3. 实现对应的 `_parse_xxx()` 方法

### 添加新的样式属性
1. 在 `StyleDeclaration` 相关类中添加新字段
2. 在 `_extract_user_block_styles()` 或 `_extract_cell_user_styles()` 中添加提取逻辑

### 添加新的 Mark 类型
1. 在 `content_models.py` 中定义新的 Mark 类
2. 在 `_extract_text_and_marks()` 的 traverse 函数中添加识别逻辑

## 注意事项

1. **ID 唯一性**: 每个 Block 的 ID 必须唯一,使用 UUID 生成
2. **Range 准确性**: Mark 的 range 必须准确对应文本位置
3. **样式一致性**: 确保提取的样式值格式统一(如颜色格式)
4. **嵌套处理**: 正确处理嵌套的标签和样式
5. **空值处理**: 对于可选字段,使用 None 而不是空字符串

## 测试建议

1. **基础元素测试**: 测试每种 Block 类型的解析
2. **复杂嵌套测试**: 测试嵌套的列表、表格
3. **样式提取测试**: 验证样式正确提取和过滤
4. **边界情况测试**: 空内容、特殊字符、超长文本
5. **往返测试**: 解析后重新生成 HTML,验证一致性
