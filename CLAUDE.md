# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# 章节级文档编辑系统 - 开发指南

## 项目概述

这是一个基于章节的在线 Word 编辑器（Web Word Editor v2），采用**后端中心化架构**，实现了内容与样式的严格分离。项目的核心目标是在网页端提供流畅编辑体验的同时，能够导出高保真的 Microsoft Word (.docx) 文档。

**技术栈**:
- **前端**: React 18 + TypeScript 5 + Vite 5, WangEditor 5.1.23
- **后端**: Python 3.11 + FastAPI 0.104, SQLAlchemy 2.0, python-docx 1.1.0
- **数据库**: MySQL 8.0
- **容器化**: Docker & Docker Compose

## 核心架构原则

### 1. 后端中心化设计

- **前端职责**：仅负责展示 WangEditor 富文本编辑器，收集用户编辑的 HTML 内容并发送到后端
- **后端职责**：负责 HTML ↔ JSON 的双向转换、数据持久化、样式计算、Word 导出等所有业务逻辑

### 2. Content × StyleSheet 分离体系

这是整个系统的核心设计理念，任何代码修改都必须遵守：

#### Content JSON 纯粹性
- **Content JSON 只存储语义、结构和文本内容**
- **严禁存储任何视觉样式属性**（如 fontSize, color, fontFamily 等）
- 所有视觉表现必须通过 StyleSheet 定义

#### StyleSheet 职责
- 所有块级样式（字体、颜色、对齐方式等）存储在 `StyleSheet.rules[]`
- 支持选择器机制：通过 blockType、blockIds、tableId、rowIndex 等精确匹配
- 支持优先级体系：blockIds > tableId + rowIndex > blockType + 伪类 > blockType

### 3. 数据流架构

```
保存章节流程:
用户编辑 WangEditor → HTML → POST /api/v1/chapters
                                    ↓
                            HtmlParser.parse()
                                    ↓
                        Content JSON + StyleSheet JSON
                                    ↓
                            保存到 MySQL

加载章节流程:
GET /api/v1/chapters/{id}
        ↓
从 MySQL 读取 Content + StyleSheet
        ↓
WangEditorRenderer.render()
        ↓
生成 HTML 返回前端
        ↓
WangEditor 展示

导出 Word 流程:
POST /api/v1/export/chapters/{id}/docx
        ↓
读取 Content + StyleSheet
        ↓
DocxExporter.export()
        ↓
生成 .docx 文件下载
```

## 常用开发命令

### 启动服务

#### 方式一：Docker Compose（推荐）

```bash
# 在项目根目录启动所有服务（MySQL + Backend + Frontend）
docker-compose up --build

# 仅启动数据库
docker-compose up db

# 查看日志
docker-compose logs -f

# 停止所有服务
docker-compose down
```

访问地址：
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

#### 方式二：本地开发

**启动后端**:
```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 DATABASE_URL

# 启动后端服务
uvicorn app.main:app --reload
```

**启动前端**:
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 测试与构建

```bash
# 前端类型检查（修改类型定义后必须执行）
cd frontend
npx tsc --noEmit

# 前端代码检查
npm run lint

# 前端构建生产版本
npm run build

# 运行后端测试
cd backend
python tests/test_hybrid_numbering.py
```

### 数据库操作

```bash
# 启动 MySQL（使用 Docker）
docker run -d \
  --name word_editor_mysql \
  -e MYSQL_ROOT_PASSWORD=password \
  -e MYSQL_DATABASE=word_editor \
  -p 3306:3306 \
  mysql:8.0

# 创建数据库（如果手动安装 MySQL）
mysql -u root -p
CREATE DATABASE word_editor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 项目结构与关键文件

### 前端核心文件 (frontend/src/)

```
src/
├── components/
│   ├── Editor/
│   │   └── EditorComponent.tsx      # ⭐ WangEditor 集成组件
│   ├── AIPanel.tsx                  # AI 辅助面板
│   ├── Sidebar.tsx                  # 章节导航侧边栏
│   ├── Toast.tsx                    # 消息提示组件
│   └── ErrorBoundary.tsx            # 错误边界
├── pages/
│   ├── DocumentEditor.tsx           # ⭐ 文档编辑主页面
│   └── DocumentList.tsx             # 文档列表页面
├── services/
│   ├── api.ts                       # ⭐ API 基础配置（axios + 拦截器）
│   └── chapterService.ts            # 章节服务封装
├── types/
│   └── api.ts                       # API 类型定义
├── config/
│   └── editorDefaults.ts            # WangEditor 默认配置
└── constants/
    └── aiActions.ts                 # AI 操作常量
```

**关键说明**：
- `EditorComponent.tsx`：WangEditor 的核心集成，负责初始化编辑器、收集 HTML、监听变化
- `DocumentEditor.tsx`：主编辑页面，包含章节列表、编辑器、保存/导出按钮
- `api.ts`：配置了 axios 拦截器、错误处理、重试逻辑

### 后端核心文件 (backend/app/)

```
app/
├── api/v1/
│   ├── chapters.py                  # ⭐ 章节 CRUD API
│   ├── documents.py                 # 文档 CRUD API
│   ├── export.py                    # ⭐ Word 导出 API
│   ├── ai_chapters.py               # AI 辅助章节编辑
│   └── upload.py                    # 文件上传
├── services/
│   ├── html_parser/                 # ⭐ HTML → JSON 解析器（模块化）
│   │   ├── parser.py                # 解析器入口
│   │   ├── element_parsers/         # 各类元素解析器
│   │   └── extractors/              # 样式提取器
│   ├── wangeditor_renderer.py       # ⭐ JSON → HTML 渲染器
│   ├── docx_exporter/               # ⭐ JSON → DOCX 导出器
│   │   ├── exporter.py              # 导出器主类
│   │   ├── auto_numbering.py        # 自动编号实现
│   │   ├── heading_numbering.py     # 标题编号处理
│   │   ├── style_utils.py           # 样式工具
│   │   └── block_processors/        # 块级元素处理器
│   └── ai_service.py                # AI 服务集成
├── models/
│   ├── database.py                  # ⭐ SQLAlchemy ORM 模型
│   ├── content_models.py            # ⭐ Pydantic Content/StyleSheet 模型
│   └── schemas.py                   # API 请求/响应模型
├── core/
│   ├── config.py                    # 配置管理
│   └── database.py                  # 数据库连接
└── main.py                          # ⭐ FastAPI 应用入口
```

**关键说明**：
- `html_parser/`：模块化的 HTML 解析器，支持段落、标题、表格、图片、列表等
- `wangeditor_renderer.py`：将 Content + StyleSheet 渲染为 WangEditor 兼容的 HTML
- `docx_exporter/`：强大的 Word 导出引擎，支持自动编号、样式映射、表格合并等
- `content_models.py`：定义了 Block、Mark、StyleSheet、StyleRule 等核心数据结构

### 数据模型文件

- `backend/app/models/content_models.py`：完整的 Content 和 StyleSheet 数据模型定义
- `backend/app/models/database.py`：数据库表结构（Document、Chapter、DocumentSettings）

## 核心实现细节

### 1. 块类型与属性规则

**允许的结构属性**（可存储在 Content.attrs 中）：
```python
ParagraphAttrs {
  listType?: 'bullet' | 'ordered' | 'none'  # 列表类型（结构性）
  listLevel?: number                         # 缩进层级（结构性）
  listStart?: number                         # 有序列表起始序号（结构性）
  headingLevel?: 1 | 2 | 3 | 4 | 5 | 6     # 标题级别（结构性）
}

TableAttrs {
  rows: number           # 表格行数（结构性）
  cols: number           # 表格列数（结构性）
  colWidths?: number[]   # 列宽权重（结构性）
}

TableCellAttrs {
  rowSpan?: number       # 跨行数（结构性）
  colSpan?: number       # 跨列数（结构性）
  cellType?: 'th' | 'td' # 单元格类型（结构性）
}
```

**禁止的样式属性**（必须存储在 StyleSheet 中）：
```python
# ❌ 禁止在 Content.attrs 中存储
textAlign, fontSize, color, fontFamily, backgroundColor,
lineHeight, marginTop, padding, border 等所有视觉样式
```

### 2. 列表系统实现

列表通过段落属性实现，而非独立的 List 容器：

```python
# 连续的段落可能属于同一个列表
ParagraphBlock {
  id: "p1",
  text: "第一项",
  attrs: { listType: "bullet", listLevel: 0 }
}
ParagraphBlock {
  id: "p2",
  text: "第二项",
  attrs: { listType: "bullet", listLevel: 0 }
}
```

**重要注意事项**：
- 前端渲染时需要识别连续列表项，包裹在同一个 `<ul>` 或 `<ol>` 中
- 后端导出 Word 时，同一列表的项必须共享 `numId`，否则编号会重复从 1 开始

### 3. 表格单元格递归结构

每个 `TableCell` 包含完整的 `Content` 递归结构：

```python
TableCell {
  id: string,
  attrs?: {
    rowSpan?: number,  # 合并单元格
    colSpan?: number,
    isRef?: boolean,   # 是否为占位单元格
    refCellId?: string # 引用的主单元格 ID
  },
  content: Content  # 可以包含段落、列表、甚至嵌套表格
}
```

**合并单元格处理**：
- 使用稠密网格模型（禁止稀疏模型）
- 左上角 master 单元格保存 rowSpan/colSpan 信息
- 被覆盖的格子用 ref 占位（isRef=true, refCellId 指向 master）

### 4. 标题编号系统

系统支持两种编号模式：

**模式一：文本前缀编号**（numbering_mode: "text"）
- 编号直接写入文本内容：`"1.1 标题文本"`
- 优点：简单、跨平台兼容性好
- 缺点：用户手动修改编号时不会自动调整

**模式二：Word 自动编号**（numbering_mode: "auto"）
- 使用 Word 的多级列表功能
- 编号写入 Heading 1-6 样式定义中（样式级编号）
- 优点：用户在 Word 中修改时自动更新
- 缺点：依赖 Word 特性

**支持的编号样式**：
- `style1`：中文混合（一、二、三 + 阿拉伯数字子级）
- `style2`：纯数字顿号（1、1.1、1.1.1）
- `style3`：数字点号（1. 1.1 1.1.1）
- `style4`：章节格式（第一章、第二章 + 阿拉伯数字子级）

**关键实现**：
- 文件：`backend/app/services/docx_exporter/auto_numbering.py`
- 文件：`backend/app/services/docx_exporter/heading_numbering.py`
- 当 H1 使用中文或章节格式时，H2-H6 的编号会跳过 H1 计数器

### 5. 图片资源管理

```python
ImageBlock {
  id: string,
  type: "image",
  src: string,  # 资源 URL 或路径
  attrs?: {
    alt?: string  # 替代文本（无障碍访问）
  }
}
```

**导出处理**：
- 根据 `src` 下载或读取图片文件
- 使用 `doc.add_picture(stream, width=Inches(x))` 插入
- 单位转换：`Inches = px / 96`（Web DPI 为 96）

## 开发规范与最佳实践

### 代码注释要求

- **注释覆盖率**：不低于 30%
- **注释语言**：中文
- **文档语言**：中文

### 代码风格

- **Python**：遵循 PEP 8，函数和变量使用 snake_case
- **TypeScript**：遵循 ESLint 规则，函数和变量使用 camelCase
- **组件命名**：React 组件使用 PascalCase

### 修改数据模型时的流程

1. 先修改 `backend/app/models/content_models.py` 中的 Pydantic 模型
2. 更新 `backend/app/services/html_parser/` 中的解析逻辑
3. 更新 `backend/app/services/wangeditor_renderer.py` 中的渲染逻辑
4. 更新 `backend/app/services/docx_exporter/` 中的导出逻辑
5. 运行类型检查：`npx tsc --noEmit`（前端）
6. 手动测试：编辑 → 保存 → 刷新 → 导出 Word

### 禁止行为

1. **禁止在 Content.attrs 中存储样式属性**
   ```python
   # ❌ 错误
   ParagraphBlock {
     attrs: { textAlign: "center" }  # 样式属性，禁止
   }

   # ✅ 正确：存储在 StyleSheet
   StyleSheet.rules: [
     { target: { blockIds: ["p1"] }, style: { textAlign: "center" } }
   ]
   ```

2. **禁止直接存储 HTML**
   ```python
   # ❌ 错误
   ParagraphBlock { html: "<p>Text</p>" }

   # ✅ 正确：通过 HtmlParser 转换
   content, stylesheet = HtmlParser.parse(html)
   ```

3. **禁止跳过类型检查**
   - 修改类型定义后必须运行 `npx tsc --noEmit`
   - 避免使用 `@ts-ignore` 除非有充分理由并添加注释

4. **禁止丢失数据**
   - Block ID 必须保留
   - 结构属性必须保留（listLevel, rowSpan 等）
   - HTML → Content → HTML 转换必须无损（round-trip）

### 推荐实践

1. **调试编辑器问题**
   ```typescript
   // 在 EditorComponent.tsx 中打印状态
   console.log('Content:', content)
   console.log('StyleSheet:', stylesheet)
   ```

2. **验证样式分离**
   - 检查保存的 JSON：Content 中不应有样式属性
   - 所有样式应在 StyleSheet.rules 中
   - 使用浏览器 DevTools 查看 Network 请求

3. **测试 Word 导出**
   - 导出后在 Word 中打开验证格式
   - 检查标题编号、表格边框、列表缩进等
   - 测试合并单元格是否正确

## API 端点

### 文档管理
- `GET /api/v1/documents` - 获取文档列表
- `POST /api/v1/documents` - 创建文档
- `GET /api/v1/documents/{id}` - 获取文档详情
- `PUT /api/v1/documents/{id}` - 更新文档
- `DELETE /api/v1/documents/{id}` - 删除文档

### 章节管理
- `GET /api/v1/chapters` - 获取章节列表（按 doc_id 过滤）
- `POST /api/v1/chapters` - 创建章节（发送 HTML）
- `GET /api/v1/chapters/{id}` - 获取章节（返回渲染的 HTML）
- `PUT /api/v1/chapters/{id}` - 更新章节（发送 HTML）
- `DELETE /api/v1/chapters/{id}` - 删除章节

### 导出功能
- `POST /api/v1/export/chapters/{id}/docx` - 导出单个章节为 Word
- `POST /api/v1/export/documents/{id}/docx` - 导出整个文档为 Word

### 文档设置
- `GET /api/v1/documents/{id}/settings` - 获取文档设置
- `PUT /api/v1/documents/{id}/settings` - 更新文档设置（编号样式、页边距等）

### AI 功能
- `POST /api/v1/chapters/ai/edit` - AI 辅助编辑章节
- `POST /api/v1/ai/generate` - AI 生成内容

## 测试清单

每次提交前至少覆盖以下测试：

1. **章节编辑**：
   - [ ] 输入文本、格式化（粗体、斜体、颜色）
   - [ ] 撤销/重做功能
   - [ ] 保存后刷新页面，内容一致

2. **Round-trip 测试**：
   - [ ] Content + StyleSheet → HTML → Content + StyleSheet 不丢失 ID/结构

3. **列表功能**：
   - [ ] 有序列表/无序列表
   - [ ] 多级列表（缩进）
   - [ ] 自定义起始编号

4. **表格功能**：
   - [ ] 创建表格
   - [ ] 合并/拆分单元格（rowSpan/colSpan）
   - [ ] 插入/删除行列
   - [ ] 单元格内嵌段落/列表
   - [ ] 从外部粘贴 HTML 表格

5. **Word 导出**：
   - [ ] 表格边框/底纹/列宽/对齐正确
   - [ ] 合并单元格正确
   - [ ] 标题编号格式正确（测试所有 4 种样式）
   - [ ] 段落/列表样式匹配

6. **标题编号**：
   - [ ] 文本编号模式正常
   - [ ] Word 自动编号模式正常
   - [ ] 中文混合样式（一、二、三 + 1、2）正确
   - [ ] 章节格式（第一章 + 1、2）正确

## 环境变量配置

### 前端 (frontend/.env)
```env
VITE_API_BASE_URL=http://localhost:8000
```

### 后端 (backend/.env)
```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/word_editor
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# AI 服务（可选）
OPENAI_API_KEY=your-api-key
OPENAI_API_BASE=https://api.openai.com/v1
```

## 常见问题

### 数据库连接失败
检查 `.env` 文件中的 `DATABASE_URL` 是否正确，确保 MySQL 服务已启动。

### 前端无法访问后端
检查 CORS 配置，确保 `app/core/config.py` 中的 `CORS_ORIGINS` 包含前端地址。

### 表格合并单元格显示异常
确保 HTML 中的 `rowspan` 和 `colspan` 属性正确，后端会自动解析并生成 ref 占位单元格。

### 标题编号格式不正确
- 检查 `document_settings` 中的 `numbering_style` 配置
- 查看 `backend/docs/标题编号格式优化说明.md` 了解最新修复
- 确保使用的是样式级编号（而非段落级）

### Word 导出后编号重置
确保同一列表的连续段落被识别并分配相同的 `numId`。参考 `auto_numbering.py` 中的列表连续性判断逻辑。

## 参考文档

- 架构设计：`docs/architecture.md`
- API 文档：`docs/api.md` 或 http://localhost:8000/docs
- 快速开始：`docs/快速开始.md`
- 最近改进：
  - `backend/docs/标题编号格式优化说明.md`
  - `backend/docs/编号写入样式改进说明.md`

## Git 工作流

- 当前分支：`develop`
- 提交前务必：
  1. 运行 `npm run lint`（前端）
  2. 运行 `npx tsc --noEmit`（类型检查）
  3. 手动测试关键功能（编辑、保存、导出）
  4. 检查是否有新的未跟踪文件需要添加

---

**最后更新**: 2026-01-05
**项目维护**: 确保代码注释和文档都使用中文
