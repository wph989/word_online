# 架构设计文档

## 一、设计理念

### 1.1 后端中心化 (Backend-Centric)

传统的富文本编辑器通常将数据处理逻辑放在前端，这导致：
- 前端代码复杂，难以维护
- 数据格式不统一
- 难以实现高保真的文档导出

本项目采用**后端中心化**架构，核心思想是：

```
前端职责：展示 + 收集用户输入
后端职责：解析 + 存储 + 渲染 + 导出
```

### 1.2 内容与样式分离

严格遵循 **Content × StyleSheet** 解耦体系：

- **Content JSON**: 存储文档的语义、结构和文本
- **StyleSheet JSON**: 存储所有视觉样式规则

这种设计的优势：
1. **可维护性**: 修改样式不影响内容
2. **可扩展性**: 轻松支持主题切换
3. **导出友好**: 样式规则可直接映射到 Word/PDF

---

## 二、系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                        前端层                            │
│  ┌──────────────┐      ┌──────────────┐                │
│  │ WangEditor   │ ───▶ │  API Client  │                │
│  │ (富文本编辑器)│      │  (axios)     │                │
│  └──────────────┘      └──────────────┘                │
└────────────────────────────┬────────────────────────────┘
                             │ HTTP/JSON
                             ▼
┌─────────────────────────────────────────────────────────┐
│                        后端层                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │              FastAPI Application                  │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐ │  │
│  │  │ Documents  │  │  Chapters  │  │   Export   │ │  │
│  │  │    API     │  │    API     │  │    API     │ │  │
│  │  └────────────┘  └────────────┘  └────────────┘ │  │
│  └──────────────────────────────────────────────────┘  │
│                             │                           │
│  ┌──────────────────────────┼────────────────────────┐ │
│  │          服务层 (Services)                        │ │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────┐│ │
│  │  │ HtmlParser  │  │ HtmlRenderer │  │  Docx    ││ │
│  │  │  (HTML→JSON)│  │  (JSON→HTML) │  │ Exporter ││ │
│  │  └─────────────┘  └──────────────┘  └──────────┘│ │
│  └───────────────────────────────────────────────────┘ │
│                             │                           │
│  ┌──────────────────────────┼────────────────────────┐ │
│  │          工具层 (Utils)                           │ │
│  │  ┌─────────────┐  ┌──────────────┐               │ │
│  │  │TableParser  │  │TableRenderer │               │ │
│  │  │(表格解析)    │  │(表格渲染)     │               │ │
│  │  └─────────────┘  └──────────────┘               │ │
│  └───────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────┘
                             │ SQLAlchemy ORM
                             ▼
┌─────────────────────────────────────────────────────────┐
│                      数据库层                            │
│                    MySQL 8.0                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  documents   │  │   chapters   │  │    assets    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 2.2 数据流向

#### 保存章节流程

```
1. 用户在 WangEditor 中编辑
   ↓
2. 前端获取 HTML: editor.getHtml()
   ↓
3. POST /api/v1/chapters { html_content: "..." }
   ↓
4. 后端 HtmlParser 解析 HTML
   ├─ 提取文本和标记 → Content JSON
   └─ 提取样式规则 → StyleSheet JSON
   ↓
5. 保存到数据库
   ├─ chapters.html_content (原始 HTML)
   ├─ chapters.content (Content JSON)
   └─ chapters.stylesheet (StyleSheet JSON)
```

#### 加载章节流程

```
1. 前端请求: GET /api/v1/chapters/{id}
   ↓
2. 后端从数据库读取
   ├─ content (Content JSON)
   └─ stylesheet (StyleSheet JSON)
   ↓
3. 后端 HtmlRenderer 渲染
   ├─ 遍历 blocks
   ├─ 应用样式规则
   └─ 生成 HTML
   ↓
4. 返回 { html_content: "..." }
   ↓
5. 前端 WangEditor 展示
```

---

## 三、核心模块设计

### 3.1 HtmlParser（HTML 解析器）

**职责**: 将富文本编辑器生成的 HTML 转换为结构化的 Content 和 StyleSheet

**核心算法**:

```python
class HtmlParser:
    def parse(html: str) -> (Content, StyleSheet):
        # 1. 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # 2. 遍历所有顶层元素
        for element in soup.children:
            if element.name == 'p':
                block = parse_paragraph(element)
            elif element.name in ['h1', 'h2', ...]:
                block = parse_heading(element)
            elif element.name == 'table':
                block = parse_table(element)
            
            # 3. 提取样式
            styles = extract_styles(element)
            if styles:
                add_style_rule(block.id, styles)
        
        return content, stylesheet
```

**关键点**:
- 支持段落、标题、表格、图片、列表、代码块
- 自动识别合并单元格（rowspan/colspan）
- 提取行内标记（粗体、斜体、颜色等）
- 提取块级样式（对齐、字号、行高等）

### 3.2 HtmlRenderer（HTML 渲染器）

**职责**: 将 Content 和 StyleSheet 渲染为 HTML

**核心算法**:

```python
class HtmlRenderer:
    def render(content: Content, stylesheet: StyleSheet) -> str:
        # 1. 构建样式映射
        style_map = build_style_map(stylesheet)
        
        # 2. 渲染每个 Block
        html_parts = []
        for block in content.blocks:
            # 获取 Block 样式
            styles = style_map.get(block.id)
            
            # 渲染 Block
            if block.type == 'paragraph':
                html = render_paragraph(block, styles)
            elif block.type == 'table':
                html = render_table(block, styles)
            
            html_parts.append(html)
        
        return '\n'.join(html_parts)
```

### 3.3 TableParser（表格解析器）

**职责**: 专门处理 HTML 表格，支持合并单元格

**核心算法**:

```python
class TableParser:
    def parse(table_element) -> TableData:
        # 1. 计算表格维度
        rows = len(table.find_all('tr'))
        cols = calculate_max_cols(table)
        
        # 2. 创建占用矩阵
        occupancy = [[False] * cols for _ in range(rows)]
        
        # 3. 遍历单元格
        for row_idx, tr in enumerate(table.find_all('tr')):
            for cell in tr.find_all(['td', 'th']):
                # 跳过被占用的列
                col_idx = find_next_free_col(occupancy, row_idx)
                
                # 提取 rowspan/colspan
                rowspan = int(cell.get('rowspan', 1))
                colspan = int(cell.get('colspan', 1))
                
                # 标记占用
                mark_occupied(occupancy, row_idx, col_idx, rowspan, colspan)
                
                # 创建合并区域
                if rowspan > 1 or colspan > 1:
                    create_merge_region(row_idx, col_idx, rowspan, colspan)
        
        return table_data
```

### 3.4 DocxExporter（Word 导出器）

**职责**: 将 Content 和 StyleSheet 导出为 .docx 文件

**核心算法**:

```python
class DocxExporter:
    def export(content: Content, stylesheet: StyleSheet) -> BytesIO:
        doc = Document()
        
        for block in content.blocks:
            if block.type == 'paragraph':
                para = doc.add_paragraph(block.text)
                apply_paragraph_styles(para, block.id, stylesheet)
                apply_marks(para, block.marks)
            
            elif block.type == 'table':
                table = doc.add_table(rows, cols)
                fill_table_cells(table, block.data)
                merge_cells(table, block.data.mergeRegions)
        
        return save_to_stream(doc)
```

---

## 四、数据模型设计

### 4.1 数据库表结构

#### documents 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) | 主键，UUID |
| title | VARCHAR(255) | 文档标题 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### chapters 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) | 主键，UUID |
| doc_id | VARCHAR(36) | 外键，关联 documents |
| title | VARCHAR(255) | 章节标题 |
| html_content | TEXT | 原始 HTML（备份） |
| content | JSON | Content JSON |
| stylesheet | JSON | StyleSheet JSON |
| order_index | INT | 排序索引 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 4.2 JSON 数据结构

详见 [word在线编辑_v2.md](../../docs/word在线编辑_v2.md)

---

## 五、技术选型

### 5.1 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.104+ | Web 框架 |
| SQLAlchemy | 2.0+ | ORM |
| Pydantic | 2.5+ | 数据验证 |
| BeautifulSoup4 | 4.12+ | HTML 解析 |
| python-docx | 1.1+ | Word 文档生成 |
| MySQL | 8.0+ | 数据库 |

### 5.2 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18+ | UI 框架 |
| TypeScript | 5+ | 类型安全 |
| WangEditor | 5+ | 富文本编辑器 |
| Axios | 1.6+ | HTTP 客户端 |
| Vite | 5+ | 构建工具 |

---

## 六、扩展性设计

### 6.1 支持更多导出格式

当前支持 Word (.docx)，未来可扩展：

```python
# 添加 PDF 导出器
class PdfExporter:
    def export(content, stylesheet) -> BytesIO:
        # 使用 ReportLab 或 WeasyPrint
        pass

# 添加 Markdown 导出器
class MarkdownExporter:
    def export(content, stylesheet) -> str:
        # 转换为 Markdown 格式
        pass
```

### 6.2 支持协同编辑

可集成 WebSocket 实现实时协同：

```python
from fastapi import WebSocket

@app.websocket("/ws/chapters/{chapter_id}")
async def websocket_endpoint(websocket: WebSocket, chapter_id: str):
    # 实现 OT (Operational Transformation) 或 CRDT
    pass
```

### 6.3 支持版本控制

在 chapters 表中添加版本字段：

```sql
ALTER TABLE chapters ADD COLUMN version INT DEFAULT 1;
CREATE TABLE chapter_history (
    id VARCHAR(36) PRIMARY KEY,
    chapter_id VARCHAR(36),
    version INT,
    content JSON,
    stylesheet JSON,
    created_at DATETIME
);
```

---

## 七、性能优化

### 7.1 数据库优化

- 为 `doc_id` 和 `order_index` 添加索引
- 使用连接池（SQLAlchemy 默认支持）
- 大文档分章节存储，避免单次查询过大

### 7.2 缓存策略

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def render_chapter(chapter_id: str) -> str:
    # 缓存渲染结果
    pass
```

### 7.3 异步处理

对于大文档导出，使用后台任务：

```python
from fastapi import BackgroundTasks

@app.post("/api/v1/export/documents/{doc_id}/async")
async def export_async(doc_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(export_large_document, doc_id)
    return {"message": "导出任务已提交"}
```

---

## 八、安全性考虑

### 8.1 输入验证

- 使用 Pydantic 验证所有输入
- 限制 HTML 内容大小（防止 DoS）
- 过滤危险的 HTML 标签（XSS 防护）

### 8.2 SQL 注入防护

- 使用 SQLAlchemy ORM（自动参数化查询）
- 禁止拼接 SQL 字符串

### 8.3 文件上传安全

- 限制文件大小和类型
- 使用 UUID 重命名文件
- 存储在非 Web 目录

---

## 九、总结

本项目通过**后端中心化**架构，将复杂的数据处理逻辑从前端转移到后端，实现了：

1. **前端简化**: 只需关注展示和用户交互
2. **数据一致性**: 统一的 JSON 格式存储
3. **高保真导出**: 样式规则直接映射到 Word
4. **易于维护**: 清晰的分层架构

这种设计特别适合需要高质量文档导出的场景，如企业文档管理、在线协作平台等。
