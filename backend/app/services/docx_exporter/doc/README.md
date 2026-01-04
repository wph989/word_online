# 目录结构
```ini
docx_exporter/
├── __init__.py              # 主导出模块
├── exporter.py              # DocxExporter 主类
├── style_utils.py           # 样式处理工具
├── parsers/
│   ├── __init__.py
│   ├── color_parser.py      # 颜色解析
│   ├── length_parser.py     # 长度解析
│   └── text_formatter.py    # 文本格式化
└── block_processors/
    ├── __init__.py
    ├── paragraph.py         # 段落处理器
    ├── heading.py           # 标题处理器
    ├── table.py             # 表格处理器
    ├── image.py             # 图片处理器
    ├── code.py              # 代码块处理器
    └── divider.py           # 分割线处理器
```