"""
测试完整的 HTML 解析流程中的标记合并
"""

from app.services.html_parser import HtmlParser


def test_html_parser_with_mark_merging():
    """
    测试从 HTML 解析到 JSON 的完整流程中，标记是否被正确合并
    """
    # 模拟前端发送的 HTML (多个相邻 span 有相同样式)
    html = """
    <p>
        <span style="font-size: 12pt; font-family: 华文仿宋;">我公司自愿</span><span style="font-size: 12pt; font-family: 华文仿宋; text-decoration: underline;">        有限公司</span><span style="font-size: 12pt; font-family: 华文仿宋;">(以下简称"贵公司")长久合作，互惠互赢， 就贵公司廉洁自律工作的要求，我公司明确如下：</span>
    </p>
    """
    
    print("=" * 80)
    print("测试 HTML 解析器的标记合并功能")
    print("=" * 80)
    
    print("\n输入 HTML:")
    print(html)
    
    # 解析 HTML
    parser = HtmlParser(html)
    content, stylesheet = parser.parse()
    
    print(f"\n解析结果:")
    print(f"Blocks 数量: {len(content.blocks)}")
    
    # 获取第一个段落
    if content.blocks:
        block = content.blocks[0]
        print(f"\n第一个 Block:")
        print(f"  类型: {block.type}")
        print(f"  文本: {block.text}")
        print(f"  文本长度: {len(block.text)}")
        print(f"  标记数量: {len(block.marks)}")
        
        print(f"\n标记详情:")
        for i, mark in enumerate(block.marks, 1):
            if hasattr(mark, 'value'):
                print(f"  {i}. {mark.type:15s} range={str(mark.range):12s} value='{mark.value}'")
            else:
                print(f"  {i}. {mark.type:15s} range={str(mark.range):12s}")
        
        # 统计标记类型
        from collections import Counter
        mark_types = Counter(m.type for m in block.marks)
        
        print(f"\n标记类型统计:")
        for mark_type, count in mark_types.items():
            print(f"  {mark_type}: {count}")
        
        # 验证合并效果
        font_size_marks = [m for m in block.marks if m.type == 'fontSize']
        font_family_marks = [m for m in block.marks if m.type == 'fontFamily']
        underline_marks = [m for m in block.marks if m.type == 'underline']
        
        print(f"\n验证结果:")
        print(f"  fontSize 标记数: {len(font_size_marks)} (期望: 1)")
        print(f"  fontFamily 标记数: {len(font_family_marks)} (期望: 1)")
        print(f"  underline 标记数: {len(underline_marks)} (期望: 1)")
        
        # 断言
        assert len(font_size_marks) == 1, f"fontSize 应该被合并为 1 个标记，实际为 {len(font_size_marks)}"
        assert len(font_family_marks) == 1, f"fontFamily 应该被合并为 1 个标记，实际为 {len(font_family_marks)}"
        assert len(underline_marks) == 1, f"underline 应该只有 1 个标记，实际为 {len(underline_marks)}"
        
        # 验证范围 (考虑文本可能有前后空白)
        text_start = 0
        text_end = len(block.text)
        
        # 跳过开头的空白
        while text_start < text_end and block.text[text_start].isspace():
            text_start += 1
        
        # 跳过结尾的空白
        while text_end > text_start and block.text[text_end - 1].isspace():
            text_end -= 1
        
        # fontSize 和 fontFamily 应该覆盖所有非空白文本
        assert font_size_marks[0].range[0] <= text_start, "fontSize 应该从文本开始"
        assert font_size_marks[0].range[1] >= text_end, "fontSize 应该到文本结束"
        assert font_family_marks[0].range[0] <= text_start, "fontFamily 应该从文本开始"
        assert font_family_marks[0].range[1] >= text_end, "fontFamily 应该到文本结束"
        
        print(f"\n✅ 所有验证通过!")
        print(f"✅ 标记成功从 {3 + 3 + 1} 个合并为 {len(block.marks)} 个")
    
    # 输出 JSON 格式
    print(f"\n生成的 JSON (Content):")
    import json
    content_dict = content.model_dump()
    print(json.dumps(content_dict, ensure_ascii=False, indent=2))
    
    return content, stylesheet


def test_multiple_paragraphs_with_merging():
    """
    测试多个段落的标记合并
    """
    html = """
    <p><span style="font-size: 14pt; color: red;">红色</span><span style="font-size: 14pt; color: red;">文本</span></p>
    <p><span style="font-size: 16pt; font-family: 宋体;">这是</span><span style="font-size: 16pt; font-family: 宋体; text-decoration: underline;">重要</span><span style="font-size: 16pt; font-family: 宋体;">内容</span></p>
    """
    
    print("\n\n" + "=" * 80)
    print("测试多个段落的标记合并")
    print("=" * 80)
    
    parser = HtmlParser(html)
    content, stylesheet = parser.parse()
    
    print(f"\n解析结果:")
    print(f"Blocks 数量: {len(content.blocks)}")
    
    for i, block in enumerate(content.blocks, 1):
        print(f"\n段落 {i}:")
        print(f"  文本: {block.text}")
        print(f"  标记数量: {len(block.marks)}")
        
        # 统计标记类型
        from collections import Counter
        mark_types = Counter(m.type for m in block.marks)
        print(f"  标记类型: {dict(mark_types)}")
    
    # 验证第一个段落
    block1 = content.blocks[0]
    color_marks = [m for m in block1.marks if m.type == 'color']
    font_size_marks = [m for m in block1.marks if m.type == 'fontSize']
    
    assert len(color_marks) == 1, f"段落1 的 color 应该被合并为 1 个标记"
    assert len(font_size_marks) == 1, f"段落1 的 fontSize 应该被合并为 1 个标记"
    
    # 验证第二个段落
    block2 = content.blocks[1]
    font_size_marks2 = [m for m in block2.marks if m.type == 'fontSize']
    font_family_marks2 = [m for m in block2.marks if m.type == 'fontFamily']
    underline_marks2 = [m for m in block2.marks if m.type == 'underline']
    
    assert len(font_size_marks2) == 1, f"段落2 的 fontSize 应该被合并为 1 个标记"
    assert len(font_family_marks2) == 1, f"段落2 的 fontFamily 应该被合并为 1 个标记"
    assert len(underline_marks2) == 1, f"段落2 的 underline 应该只有 1 个标记"
    
    print(f"\n✅ 所有段落的标记都成功合并!")


if __name__ == "__main__":
    test_html_parser_with_mark_merging()
    test_multiple_paragraphs_with_merging()
    print("\n\n🎉 所有测试通过! 标记合并在完整的 HTML 解析流程中正常工作!")
