# 目录结构
```ini
html_parser/
├── __init__.py              # 主解析模块
├── parser.py                # HtmlParser 主类
├── element_parsers/
│   ├── __init__.py
│   ├── paragraph.py         # 段落解析
│   ├── heading.py           # 标题解析
│   ├── table.py             # 表格解析
│   ├── image.py             # 图片解析
│   ├── list.py              # 列表解析
│   ├── code.py              # 代码块解析
│   └── divider.py           # 分割线解析
├── extractors/
│   ├── __init__.py
│   ├── text_marks.py        # 文本和标记提取
│   └── styles.py            # 样式提取
└── utils/
    ├── __init__.py
    └── style_helpers.py     # 样式辅助函数
```