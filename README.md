# Web Word Editor - 后端中心化架构 (Backend-Centric Architecture)

## 项目概述

这是一个基于 FastAPI 的在线 Word 编辑器后端服务，采用**后端中心化**的设计理念。

### 核心设计理念

1. **前端职责最小化**：前端仅负责：
   - 展示富文本编辑器（WangEditor）
   - 收集用户编辑的 HTML 内容
   - 将 HTML 发送到后端保存
   - 接收后端返回的 HTML 并展示

2. **后端职责最大化**：后端负责：
   - HTML → JSON (Content + StyleSheet) 的解析转换
   - JSON → HTML 的渲染生成
   - 数据持久化（MySQL）
   - Word 文档导入/导出
   - 样式计算与应用

### 技术栈

- **后端框架**: FastAPI 0.104+
- **数据库**: MySQL 8.0
- **ORM**: SQLAlchemy 2.0
- **Word 处理**: python-docx
- **HTML 解析**: BeautifulSoup4
- **数据验证**: Pydantic V2

### 项目结构

```
new_pro/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # API 路由
│   │   │   ├── v1/
│   │   │   │   ├── chapters.py      # 章节管理
│   │   │   │   ├── documents.py     # 文档管理
│   │   │   │   └── export.py        # 导出功能
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py            # 配置管理
│   │   │   └── database.py          # 数据库连接
│   │   ├── models/            # 数据模型
│   │   │   ├── database.py          # SQLAlchemy 模型
│   │   │   └── schemas.py           # Pydantic 模型
│   │   ├── services/          # 业务逻辑层
│   │   │   ├── html_parser.py       # HTML 解析服务
│   │   │   ├── html_renderer.py     # HTML 渲染服务
│   │   │   ├── style_extractor.py   # 样式提取服务
│   │   │   ├── docx_exporter.py     # Word 导出服务
│   │   │   └── docx_importer.py     # Word 导入服务
│   │   ├── utils/             # 工具函数
│   │   │   ├── table_parser.py      # 表格解析工具
│   │   │   ├── merge_handler.py     # 合并单元格处理
│   │   │   └── style_resolver.py    # 样式解析工具
│   │   └── main.py            # 应用入口
│   ├── tests/                 # 测试文件
│   ├── requirements.txt       # Python 依赖
│   └── .env.example          # 环境变量示例
├── frontend/                  # 前端（简化版）
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   └── Editor.tsx          # 编辑器组件
│   │   ├── services/
│   │   │   └── api.ts              # API 调用
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── docs/                      # 文档
│   ├── api.md                       # API 文档
│   ├── architecture.md              # 架构设计
│   └── deployment.md                # 部署指南
└── docker-compose.yml         # Docker 编排

```

## 核心工作流程

### 1. 保存章节（前端 → 后端）

```
用户编辑 → WangEditor HTML → POST /api/v1/chapters
                                    ↓
                            HTML Parser Service
                                    ↓
                        Content JSON + StyleSheet JSON
                                    ↓
                            保存到 MySQL
```

### 2. 加载章节（后端 → 前端）

```
GET /api/v1/chapters/{id}
        ↓
从 MySQL 读取 Content + StyleSheet
        ↓
HTML Renderer Service
        ↓
生成 HTML 返回前端
        ↓
WangEditor 展示
```

### 3. 导出 Word

```
POST /api/v1/chapters/{id}/export
        ↓
读取 Content + StyleSheet
        ↓
Docx Exporter Service
        ↓
生成 .docx 文件
```

## 数据模型

### Content JSON 结构

```json
{
  "blocks": [
    {
      "id": "block-1",
      "type": "paragraph",
      "text": "这是一段文本",
      "marks": [
        { "type": "bold", "range": [0, 2] }
      ]
    },
    {
      "id": "block-2",
      "type": "table",
      "data": {
        "rows": 3,
        "cols": 3,
        "cells": [
          {
            "cell": [0, 0],
            "content": { "text": "单元格内容" }
          }
        ],
        "mergeRegions": []
      }
    }
  ]
}
```

### StyleSheet JSON 结构

```json
{
  "styleId": "style-1",
  "appliesTo": "chapter",
  "rules": [
    {
      "target": {
        "blockType": "paragraph",
        "blockIds": ["block-1"]
      },
      "style": {
        "fontSize": 16,
        "color": "#333333",
        "textAlign": "left"
      }
    }
  ]
}
```

## 快速开始

### 1. 启动数据库

```bash
docker-compose up -d mysql
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 4. 访问应用

- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 开发规范

### 代码注释要求

- **注释覆盖率**: 不低于 30%
- **注释语言**: 中文
- **文档语言**: 中文

### 代码风格

- **Python**: 遵循 PEP 8，使用 Black 格式化
- **TypeScript**: 遵循 ESLint 规则
- **命名规范**: 
  - Python: snake_case
  - TypeScript: camelCase

## 许可证

MIT License
