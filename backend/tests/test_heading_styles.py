"""
测试标题样式导出功能
验证标题格式是否正确写入 Word 的标题样式模板
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))

from app.services.docx_exporter import DocxExporter
from docx import Document
import logging

logging.basicConfig(level=logging.INFO)

# 测试数据
content = {
    "blocks": [
        {
            "id": "h1-1",
            "type": "heading",
            "level": 1,
            "text": "这是一级标题",
            "marks": []
        },
        {
            "id": "h1-2",
            "type": "heading",
            "level": 1,
            "text": "这是带局部红色的标题",
            "marks": [
                {"type": "color", "value": "#ff0000", "range": [3, 7]}
            ]
        },
        {
            "id": "h2-1",
            "type": "heading",
            "level": 2,
            "text": "这是二级标题",
            "marks": []
        },
        {
            "id": "h2-2",
            "type": "heading",
            "level": 2,
            "text": "这是带局部加粗的二级标题",
            "marks": [
                {"type": "bold", "range": [3, 7]}
            ]
        }
    ]
}

stylesheet = {
    "styleId": "test-style",
    "appliesTo": "chapter",
    "rules": []
}

# 文档配置 - 定义标题样式
document_settings = {
    "margin_top": 2.54,
    "margin_bottom": 2.54,
    "margin_left": 3.17,
    "margin_right": 3.17,
    "heading_styles": {
        "h1": {
            "fontSize": 22,
            "fontFamily": "微软雅黑",
            "color": "#000000",
            "fontWeight": "bold",
            "marginTop": 12,
            "marginBottom": 12
        },
        "h2": {
            "fontSize": 18,
            "fontFamily": "微软雅黑",
            "color": "#333333",
            "fontWeight": "bold",
            "marginTop": 10,
            "marginBottom": 10
        }
    }
}

print("=" * 60)
print("测试标题样式导出")
print("=" * 60)

# 创建导出器
exporter = DocxExporter(content, stylesheet, document_settings)

# 导出文档
file_stream = exporter.export()

# 保存到文件
output_path = "test_heading_styles.docx"
with open(output_path, "wb") as f:
    f.write(file_stream.read())

print(f"\n✅ 文档已导出: {output_path}")

# 验证文档
print("\n" + "=" * 60)
print("验证导出的文档")
print("=" * 60)

doc = Document(output_path)

# 检查标题样式模板
print("\n【标题样式模板配置】")
for level in [1, 2]:
    style_name = f'Heading {level}'
    if style_name in doc.styles:
        style = doc.styles[style_name]
        print(f"\n{style_name}:")
        print(f"  - 字体: {style.font.name}")
        print(f"  - 字号: {style.font.size.pt if style.font.size else 'None'} pt")
        print(f"  - 颜色: {style.font.color.rgb if style.font.color.rgb else 'None'}")
        print(f"  - 加粗: {style.font.bold}")
        print(f"  - 段前间距: {style.paragraph_format.space_before.pt if style.paragraph_format.space_before else 'None'} pt")
        print(f"  - 段后间距: {style.paragraph_format.space_after.pt if style.paragraph_format.space_after else 'None'} pt")

# 检查段落内容
print("\n【段落内容】")
for i, para in enumerate(doc.paragraphs):
    if para.text:
        print(f"\n段落 {i+1}: {para.text}")
        print(f"  - 样式: {para.style.name}")
        
        # 检查 runs
        if para.runs:
            print(f"  - Runs 数量: {len(para.runs)}")
            for j, run in enumerate(para.runs):
                print(f"    Run {j+1}: '{run.text}'")
                print(f"      字体: {run.font.name}")
                print(f"      字号: {run.font.size.pt if run.font.size else 'None'} pt")
                print(f"      颜色: {run.font.color.rgb if run.font.color.rgb else 'None'}")
                print(f"      加粗: {run.bold}")

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)
print("\n请打开 test_heading_styles.docx 文件验证:")
print("1. 标题样式是否正确应用到 Word 的样式模板")
print("2. 局部 mark 格式是否正确叠加")
print("3. 修改样式模板后,所有使用该样式的标题是否同步更新")
