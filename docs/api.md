# API 文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API 版本**: v1
- **数据格式**: JSON

## 认证

当前版本暂无认证机制，后续可添加 JWT 或 OAuth2。

---

## 文档管理 API

### 1. 创建文档

**接口**: `POST /api/v1/documents`

**请求体**:
```json
{
  "title": "我的文档"
}
```

**响应**:
```json
{
  "id": "uuid-string",
  "title": "我的文档",
  "created_at": "2026-01-02T12:00:00",
  "updated_at": "2026-01-02T12:00:00"
}
```

### 2. 获取文档详情

**接口**: `GET /api/v1/documents/{doc_id}`

**响应**:
```json
{
  "id": "uuid-string",
  "title": "我的文档",
  "created_at": "2026-01-02T12:00:00",
  "updated_at": "2026-01-02T12:00:00",
  "chapters": [
    {
      "id": "chapter-uuid",
      "doc_id": "uuid-string",
      "title": "第一章",
      "order_index": 0,
      "created_at": "2026-01-02T12:00:00",
      "updated_at": "2026-01-02T12:00:00"
    }
  ]
}
```

### 3. 获取文档列表

**接口**: `GET /api/v1/documents?page=1&page_size=10`

**响应**:
```json
{
  "total": 100,
  "page": 1,
  "page_size": 10,
  "items": [...]
}
```

### 4. 删除文档

**接口**: `DELETE /api/v1/documents/{doc_id}`

**响应**:
```json
{
  "message": "文档 '我的文档' 及其所有章节已删除",
  "success": true
}
```

---

## 章节管理 API

### 1. 创建章节（核心接口）

**接口**: `POST /api/v1/chapters`

**请求体**:
```json
{
  "doc_id": "document-uuid",
  "title": "第一章",
  "html_content": "<p>这是<strong>章节</strong>内容</p>",
  "order_index": 0
}
```

**说明**:
- `html_content`: 前端编辑器生成的 HTML
- 后端会自动解析 HTML 为 Content 和 StyleSheet JSON

**响应**:
```json
{
  "id": "chapter-uuid",
  "doc_id": "document-uuid",
  "title": "第一章",
  "order_index": 0,
  "created_at": "2026-01-02T12:00:00",
  "updated_at": "2026-01-02T12:00:00"
}
```

### 2. 获取章节（返回 HTML）

**接口**: `GET /api/v1/chapters/{chapter_id}`

**响应**:
```json
{
  "id": "chapter-uuid",
  "doc_id": "document-uuid",
  "title": "第一章",
  "order_index": 0,
  "created_at": "2026-01-02T12:00:00",
  "updated_at": "2026-01-02T12:00:00",
  "html_content": "<p>这是<strong>章节</strong>内容</p>"
}
```

**说明**:
- `html_content`: 后端从 Content 和 StyleSheet 渲染的 HTML
- 前端直接展示即可

### 3. 获取章节 JSON（调试接口）

**接口**: `GET /api/v1/chapters/{chapter_id}/json`

**响应**:
```json
{
  "id": "chapter-uuid",
  "doc_id": "document-uuid",
  "title": "第一章",
  "order_index": 0,
  "created_at": "2026-01-02T12:00:00",
  "updated_at": "2026-01-02T12:00:00",
  "content": {
    "blocks": [
      {
        "id": "para-abc123",
        "type": "paragraph",
        "text": "这是章节内容",
        "marks": [
          {
            "type": "bold",
            "range": [2, 4]
          }
        ]
      }
    ]
  },
  "stylesheet": {
    "styleId": "style-xyz",
    "appliesTo": "chapter",
    "rules": []
  }
}
```

### 4. 更新章节

**接口**: `PUT /api/v1/chapters/{chapter_id}`

**请求体**:
```json
{
  "title": "新标题",
  "html_content": "<p>更新后的内容</p>"
}
```

### 5. 删除章节

**接口**: `DELETE /api/v1/chapters/{chapter_id}`

### 6. 获取章节列表

**接口**: `GET /api/v1/chapters?doc_id={doc_id}`

---

## 导出 API

### 1. 导出章节为 Word

**接口**: `GET /api/v1/export/chapters/{chapter_id}/docx`

**响应**: 直接下载 .docx 文件

### 2. 导出整个文档为 Word

**接口**: `GET /api/v1/export/documents/{doc_id}/docx`

**响应**: 直接下载 .docx 文件（包含所有章节）

---

## 数据模型

### Content JSON 结构

```json
{
  "blocks": [
    {
      "id": "block-id",
      "type": "paragraph | heading | table | image | code",
      "text": "文本内容",
      "marks": [
        {
          "type": "bold | italic | underline | color | ...",
          "range": [start, end],
          "value": "样式值（可选）"
        }
      ],
      "attrs": {
        "listType": "bullet | ordered",
        "listLevel": 0
      }
    }
  ]
}
```

### StyleSheet JSON 结构

```json
{
  "styleId": "style-id",
  "appliesTo": "global | document | chapter",
  "rules": [
    {
      "target": {
        "blockType": "paragraph",
        "blockIds": ["block-id"]
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

---

## 错误响应

所有错误响应遵循以下格式：

```json
{
  "detail": "错误描述信息"
}
```

常见 HTTP 状态码：
- `200`: 成功
- `201`: 创建成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误
