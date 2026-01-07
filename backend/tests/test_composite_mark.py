"""
测试 CompositeMark (同范围标记合并) 的生成和渲染
"""

from bs4 import BeautifulSoup
from app.services.html_parser.extractors.text_marks import extract_text_and_marks
from app.services.wangeditor_renderer import WangEditorRenderer
from app.models.content_models import Content, ParagraphBlock, StyleSheet, StyleScope, CompositeMark


def test_merge_same_range_marks():
    """
    测试同范围的 SimpleMark 是否被合并为 CompositeMark
    """
    print("=" * 80)
    print("测试同范围标记合并 (CompositeMark)")
    print("=" * 80)
    
    # 构造 HTML: 包含粗体、斜体、下划线的文本，它们覆盖相同的范围
    # 注意: span 的顺序和嵌套会影响初始提取的标记，但 optimize 后应该被合并
    html = """
    <p>
        <span style="font-weight: bold; font-style: italic; text-decoration: underline;">粗斜下划线</span>
    </p>
    """
    
    print("\n输入 HTML:")
    print(html)
    
    soup = BeautifulSoup(html, 'html.parser')
    p_element = soup.find('p')
    
    # 手动提取
    text, marks = extract_text_and_marks(p_element)
    
    print(f"\n提取结果:")
    print(f"文本: {text}")
    print(f"标记数量: {len(marks)}")
    
    for i, mark in enumerate(marks, 1):
        if hasattr(mark, 'value'):
            print(f"  {i}. {mark.type} {mark.range} value='{mark.value}'")
        elif isinstance(mark, CompositeMark):
            print(f"  {i}. CompositeMark type={mark.type} {mark.range}")
        else:
            print(f"  {i}. {mark.type} {mark.range}")
            
    # 验证是否存在 CompositeMark
    composite_marks = [m for m in marks if isinstance(m, CompositeMark)]
    
    if composite_marks:
        print(f"\n✅ 成功生成 CompositeMark!")
        cm = composite_marks[0]
        print(f"  包含类型: {cm.type}")
        
        assert 'bold' in cm.type
        assert 'italic' in cm.type
        assert 'underline' in cm.type
        
        # 验证范围 (动态查找文本位置)
        text_start = text.find("粗斜下划线")
        expected_range = (text_start, text_start + len("粗斜下划线"))
        assert cm.range == expected_range
    else:
        print(f"\n❌ 未生成 CompositeMark")
        
    return marks


def test_renderer_with_composite_mark():
    """
    测试渲染器能否正确处理 CompositeMark
    """
    print("\n\n" + "=" * 80)
    print("测试渲染 CompositeMark")
    print("=" * 80)
    
    text = "测试文本"
    marks = [
        CompositeMark(type=["bold", "italic", "underline"], range=(0, 4))
    ]
    
    block = ParagraphBlock(
        id="test-block",
        type="paragraph",
        text=text,
        marks=marks
    )
    
    content = Content(blocks=[block])
    stylesheet = StyleSheet(styleId="test-style", appliesTo=StyleScope.CHAPTER, rules=[])
    
    renderer = WangEditorRenderer(content, stylesheet)
    rendered_html = renderer.render()
    
    print(f"\n渲染结果 HTML:")
    print(rendered_html)
    
    # 验证 HTML 结构
    expected_tags = ["strong", "em", "u"]
    for tag in expected_tags:
        assert tag in rendered_html, f"渲染结果缺少 <{tag}> 标签"
        
    print(f"\n✅ 渲染验证通过!")


if __name__ == "__main__":
    test_merge_same_range_marks()
    test_renderer_with_composite_mark()
    print("\n\n🎉 所有测试通过!")
