"""
测试标记合并优化功能
"""

from bs4 import BeautifulSoup
from app.services.html_parser.extractors.text_marks import extract_text_and_marks


def test_merge_adjacent_marks():
    """
    测试相邻相同标记的合并
    
    模拟场景:
    HTML 中有多个相邻的 span 标签,每个都有相同的 font-size 和 font-family
    应该合并为一个标记
    """
    html = """<p><span style="font-size: 12pt; font-family: 华文仿宋;">我公司自愿</span><span style="font-size: 12pt; font-family: 华文仿宋; text-decoration: underline;">        有限公司</span><span style="font-size: 12pt; font-family: 华文仿宋;">(以下简称"贵公司")长久合作，互惠互赢， 就贵公司廉洁自律工作的要求，我公司明确如下：</span></p>"""
    
    soup = BeautifulSoup(html, 'html.parser')
    p_element = soup.find('p')
    
    text, marks = extract_text_and_marks(p_element)
    
    print("提取的文本:")
    print(repr(text))
    print(f"\n文本长度: {len(text)}")
    
    print("\n提取的标记 (优化后):")
    for i, mark in enumerate(marks):
        print(f"{i+1}. {mark}")
    
    # 验证标记数量
    print(f"\n总标记数: {len(marks)}")
    
    # 统计每种类型的标记
    from collections import Counter
    mark_types = Counter()
    for mark in marks:
        mark_types[mark.type] += 1
    
    print("\n标记类型统计:")
    for mark_type, count in mark_types.items():
        print(f"  {mark_type}: {count}")
    
    # 验证 fontSize 和 fontFamily 是否被合并
    font_size_marks = [m for m in marks if m.type == 'fontSize']
    font_family_marks = [m for m in marks if m.type == 'fontFamily']
    
    print(f"\nfontSize 标记数: {len(font_size_marks)}")
    for mark in font_size_marks:
        print(f"  range: {mark.range}, value: {mark.value}")
    
    print(f"\nfontFamily 标记数: {len(font_family_marks)}")
    for mark in font_family_marks:
        print(f"  range: {mark.range}, value: {mark.value}")
    
    # 验证 underline 标记
    underline_marks = [m for m in marks if m.type == 'underline']
    print(f"\nunderline 标记数: {len(underline_marks)}")
    for mark in underline_marks:
        print(f"  range: {mark.range}")
        print(f"  对应文本: {repr(text[mark.range[0]:mark.range[1]])}")
    
    # 断言验证
    assert len(font_size_marks) == 1, f"fontSize 应该被合并为 1 个标记,实际为 {len(font_size_marks)}"
    assert font_size_marks[0].range == (0, len(text)), f"fontSize 应该覆盖整个文本"
    assert font_size_marks[0].value == '12pt', f"fontSize 值应该为 '12pt'"
    
    assert len(font_family_marks) == 1, f"fontFamily 应该被合并为 1 个标记,实际为 {len(font_family_marks)}"
    assert font_family_marks[0].range == (0, len(text)), f"fontFamily 应该覆盖整个文本"
    assert font_family_marks[0].value == '华文仿宋', f"fontFamily 值应该为 '华文仿宋'"
    
    assert len(underline_marks) == 1, f"underline 应该只有 1 个标记,实际为 {len(underline_marks)}"
    # underline 只应用于第二个 span
    expected_underline_text = "        有限公司"
    actual_underline_text = text[underline_marks[0].range[0]:underline_marks[0].range[1]]
    assert actual_underline_text == expected_underline_text, \
        f"underline 文本不匹配: 期望 {repr(expected_underline_text)}, 实际 {repr(actual_underline_text)}"
    
    print("\n✅ 所有断言通过!")


def test_merge_multiple_types():
    """
    测试多种类型标记的合并
    """
    html = """<p><span style="font-size: 14pt; color: red;">红色</span><span style="font-size: 14pt; color: red;">文本</span><span style="font-size: 14pt; color: blue;">蓝色</span><span style="font-size: 14pt; color: blue;">文本</span></p>"""
    
    soup = BeautifulSoup(html, 'html.parser')
    p_element = soup.find('p')
    
    text, marks = extract_text_and_marks(p_element)
    
    print("\n\n=== 测试多种类型标记的合并 ===")
    print("提取的文本:")
    print(repr(text))
    
    print("\n提取的标记:")
    for i, mark in enumerate(marks):
        print(f"{i+1}. {mark}")
    
    # 验证
    font_size_marks = [m for m in marks if m.type == 'fontSize']
    color_marks = [m for m in marks if m.type == 'color']
    
    print(f"\nfontSize 标记数: {len(font_size_marks)}")
    print(f"color 标记数: {len(color_marks)}")
    
    # fontSize 应该被合并为 1 个(覆盖整个文本)
    assert len(font_size_marks) == 1, f"fontSize 应该被合并为 1 个标记"
    assert font_size_marks[0].range == (0, len(text))
    
    # color 应该是 2 个(红色和蓝色各一个)
    assert len(color_marks) == 2, f"color 应该有 2 个标记(红色和蓝色)"
    
    red_marks = [m for m in color_marks if m.value == 'red']
    blue_marks = [m for m in color_marks if m.value == 'blue']
    
    assert len(red_marks) == 1, "应该有 1 个红色标记"
    assert len(blue_marks) == 1, "应该有 1 个蓝色标记"
    
    # 验证红色标记覆盖 "红色文本"
    red_text = text[red_marks[0].range[0]:red_marks[0].range[1]]
    assert red_text == "红色文本", f"红色标记应该覆盖 '红色文本', 实际为 {repr(red_text)}"
    
    # 验证蓝色标记覆盖 "蓝色文本"
    blue_text = text[blue_marks[0].range[0]:blue_marks[0].range[1]]
    assert blue_text == "蓝色文本", f"蓝色标记应该覆盖 '蓝色文本', 实际为 {repr(blue_text)}"
    
    print("\n✅ 所有断言通过!")


def test_merge_with_gaps():
    """
    测试有间隙的标记不会被合并
    """
    html = """<p><span style="font-size: 12pt;">第一段</span><span>无样式</span><span style="font-size: 12pt;">第二段</span></p>"""
    
    soup = BeautifulSoup(html, 'html.parser')
    p_element = soup.find('p')
    
    text, marks = extract_text_and_marks(p_element)
    
    print("\n\n=== 测试有间隙的标记不会被合并 ===")
    print("提取的文本:")
    print(repr(text))
    
    print("\n提取的标记:")
    for i, mark in enumerate(marks):
        print(f"{i+1}. {mark}")
    
    font_size_marks = [m for m in marks if m.type == 'fontSize']
    
    print(f"\nfontSize 标记数: {len(font_size_marks)}")
    for mark in font_size_marks:
        print(f"  range: {mark.range}, 文本: {repr(text[mark.range[0]:mark.range[1]])}")
    
    # 应该有 2 个 fontSize 标记(因为中间有无样式的文本)
    assert len(font_size_marks) == 2, f"应该有 2 个 fontSize 标记,实际为 {len(font_size_marks)}"
    
    print("\n✅ 所有断言通过!")


if __name__ == "__main__":
    test_merge_adjacent_marks()
    test_merge_multiple_types()
    test_merge_with_gaps()
    print("\n\n🎉 所有测试通过!")
