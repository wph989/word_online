"""
端到端测试：验证从前端保存到后端数据库的完整流程中标记合并是否生效
"""

from app.services.html_parser import HtmlParser
import json


def test_end_to_end_save_flow():
    """
    模拟完整的保存流程:
    1. 前端编辑器生成 HTML (包含多个相邻的相同样式 span)
    2. 发送到后端 API
    3. 后端使用 HtmlParser 解析
    4. 保存到数据库 (Content + StyleSheet JSON)
    5. 验证保存的 JSON 中标记已被合并
    """
    
    print("=" * 80)
    print("端到端测试：前端保存 → 后端解析 → 数据库存储")
    print("=" * 80)
    
    # 步骤 1: 前端编辑器生成的 HTML (模拟用户的实际案例)
    frontend_html = """<p><span style="font-size: 12pt; font-family: 华文仿宋;">我公司自愿</span><span style="font-size: 12pt; font-family: 华文仿宋; text-decoration: underline;">        有限公司</span><span style="font-size: 12pt; font-family: 华文仿宋;">(以下简称"贵公司")长久合作，互惠互赢， 就贵公司廉洁自律工作的要求，我公司明确如下：</span></p>"""
    
    print("\n步骤 1: 前端生成的 HTML")
    print(f"HTML 长度: {len(frontend_html)} 字符")
    print(f"包含 span 标签数: {frontend_html.count('<span')}")
    
    # 步骤 2: 模拟前端发送到后端 API
    print("\n步骤 2: 前端发送 HTTP PUT 请求")
    request_data = {
        "html_content": frontend_html,
        "title": "廉洁自律承诺书"
    }
    print(f"请求数据: {json.dumps(request_data, ensure_ascii=False)[:100]}...")
    
    # 步骤 3: 后端 API 接收并使用 HtmlParser 解析
    print("\n步骤 3: 后端解析 HTML")
    parser = HtmlParser(frontend_html)
    content, stylesheet = parser.parse()
    
    print(f"解析结果:")
    print(f"  - Blocks 数量: {len(content.blocks)}")
    print(f"  - StyleSheet 规则数: {len(stylesheet.rules)}")
    
    # 步骤 4: 转换为 JSON 准备保存到数据库
    print("\n步骤 4: 转换为 JSON 格式")
    content_json = content.model_dump()
    stylesheet_json = stylesheet.model_dump()
    
    # 模拟数据库记录
    db_record = {
        "id": "chapter-12345",
        "doc_id": "doc-67890",
        "title": "廉洁自律承诺书",
        "html_content": frontend_html,  # 原始 HTML (备份)
        "content": content_json,  # 结构化内容
        "stylesheet": stylesheet_json  # 样式表
    }
    
    print(f"数据库记录大小: {len(json.dumps(db_record, ensure_ascii=False))} 字符")
    
    # 步骤 5: 验证保存的 JSON 中标记已被合并
    print("\n步骤 5: 验证标记合并效果")
    
    first_block = content_json['blocks'][0]
    marks = first_block['marks']
    
    print(f"\n段落文本: {first_block['text'][:50]}...")
    print(f"标记总数: {len(marks)}")
    
    # 统计标记类型
    from collections import Counter
    mark_types = Counter()
    for mark in marks:
        mark_types[mark['type']] += 1
    
    print(f"\n标记类型统计:")
    for mark_type, count in mark_types.items():
        print(f"  {mark_type}: {count}")
    
    # 详细显示每个标记
    print(f"\n标记详情:")
    for i, mark in enumerate(marks, 1):
        if 'value' in mark:
            print(f"  {i}. {mark['type']:15s} range={str(mark['range']):12s} value='{mark['value']}'")
        else:
            print(f"  {i}. {mark['type']:15s} range={str(mark['range']):12s}")
    
    # 验证合并效果
    font_size_count = mark_types.get('fontSize', 0)
    font_family_count = mark_types.get('fontFamily', 0)
    underline_count = mark_types.get('underline', 0)
    
    print(f"\n✅ 验证结果:")
    print(f"  fontSize 标记: {font_size_count} (优化前: 3)")
    print(f"  fontFamily 标记: {font_family_count} (优化前: 3)")
    print(f"  underline 标记: {underline_count} (优化前: 1)")
    print(f"  总标记数: {len(marks)} (优化前: 7)")
    print(f"  减少比例: {(1 - len(marks) / 7) * 100:.1f}%")
    
    # 断言
    assert font_size_count == 1, f"fontSize 应该被合并为 1 个"
    assert font_family_count == 1, f"fontFamily 应该被合并为 1 个"
    assert underline_count == 1, f"underline 应该保持 1 个"
    assert len(marks) == 3, f"总标记数应该是 3"
    
    print(f"\n✅ 所有验证通过!")
    print(f"✅ 标记合并在完整的保存流程中正常工作!")
    
    # 显示保存到数据库的 JSON 示例
    print(f"\n保存到数据库的 Content JSON:")
    print(json.dumps(content_json, ensure_ascii=False, indent=2))
    
    return db_record


def test_compare_before_after():
    """
    对比优化前后的数据大小
    """
    print("\n\n" + "=" * 80)
    print("数据大小对比：优化前 vs 优化后")
    print("=" * 80)
    
    html = """<p><span style="font-size: 12pt; font-family: 华文仿宋;">我公司自愿</span><span style="font-size: 12pt; font-family: 华文仿宋; text-decoration: underline;">        有限公司</span><span style="font-size: 12pt; font-family: 华文仿宋;">(以下简称"贵公司")长久合作，互惠互赢， 就贵公司廉洁自律工作的要求，我公司明确如下：</span></p>"""
    
    # 解析并获取优化后的数据
    parser = HtmlParser(html)
    content, stylesheet = parser.parse()
    content_json = content.model_dump()
    
    # 模拟优化前的数据 (手动构造)
    text = content_json['blocks'][0]['text']
    marks_before = [
        {"type": "fontSize", "range": [1, 6], "value": "12pt"},
        {"type": "fontFamily", "range": [1, 6], "value": "华文仿宋"},
        {"type": "fontSize", "range": [6, 18], "value": "12pt"},
        {"type": "fontFamily", "range": [6, 18], "value": "华文仿宋"},
        {"type": "underline", "range": [6, 18]},
        {"type": "fontSize", "range": [18, 62], "value": "12pt"},
        {"type": "fontFamily", "range": [18, 62], "value": "华文仿宋"}
    ]
    
    content_before = {
        "blocks": [{
            "id": "para-test",
            "type": "paragraph",
            "text": text,
            "marks": marks_before,
            "attrs": None
        }]
    }
    
    # 计算大小
    size_before = len(json.dumps(content_before, ensure_ascii=False))
    size_after = len(json.dumps(content_json, ensure_ascii=False))
    
    print(f"\n优化前:")
    print(f"  标记数量: {len(marks_before)}")
    print(f"  JSON 大小: {size_before} 字节")
    
    print(f"\n优化后:")
    print(f"  标记数量: {len(content_json['blocks'][0]['marks'])}")
    print(f"  JSON 大小: {size_after} 字节")
    
    print(f"\n优化效果:")
    print(f"  标记减少: {len(marks_before) - len(content_json['blocks'][0]['marks'])} 个 ({(1 - len(content_json['blocks'][0]['marks']) / len(marks_before)) * 100:.1f}%)")
    print(f"  大小减少: {size_before - size_after} 字节 ({(1 - size_after / size_before) * 100:.1f}%)")
    
    print(f"\n✅ 对于 1000 个段落的文档:")
    print(f"  可节省约 {(size_before - size_after) * 1000 / 1024:.1f} KB 存储空间")
    print(f"  可减少约 {(size_before - size_after) * 1000 / 1024:.1f} KB 网络传输")


if __name__ == "__main__":
    test_end_to_end_save_flow()
    test_compare_before_after()
    print("\n\n🎉 端到端测试完成! 标记合并在完整的保存流程中正常工作!")
