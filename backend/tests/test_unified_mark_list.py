"""
测试统一标记为列表格式的功能验证
"""

from bs4 import BeautifulSoup
from app.services.html_parser.extractors.text_marks import extract_text_and_marks, merge_same_range_marks
from app.models.content_models import SimpleMark, CompositeMark
from app.services.docx_exporter.parsers.text_formatter import apply_marks_to_run
from unittest.mock import MagicMock

def test_unified_list_format():
    """
    测试单个 SimpleMark 是否被统一转换为列表格式的 CompositeMark
    """
    print("=" * 80)
    print("测试统一标记为列表格式")
    print("=" * 80)
    
    # CASE 1: 单个粗体标记
    html = "<p><strong>粗体文本</strong></p>"
    print(f"\n输入 HTML: {html}")
    
    soup = BeautifulSoup(html, 'html.parser')
    p_element = soup.find('p')
    text, marks = extract_text_and_marks(p_element)
    
    print(f"提取结果标记: {marks}")
    
    # 验证生成的标记类型
    assert len(marks) == 1
    mark = marks[0]
    
    print(f"标记类: {mark.__class__.__name__}")
    print(f"标记类型字段: {mark.type}")
    
    # 期望: CompositeMark, type=['bold']
    # 注意: extract_text_and_marks 内部现在会调用 merge_same_range_marks
    # 而 merge_same_range_marks 被我们修改为总是生成 CompositeMark
    
    assert isinstance(mark, CompositeMark), "应该转换为 CompositeMark"
    assert isinstance(mark.type, list), "type 字段应该是列表"
    assert mark.type == ['bold'], f"type 应该是 ['bold'], 实际为 {mark.type}"
    
    print("✅ 单个标记成功转换为列表格式")
    
    # CASE 2: 多个标记 (粗体+斜体)
    html_multi = "<p><strong><em>粗斜文本</em></strong></p>"
    print(f"\n输入 HTML: {html_multi}")
    
    soup = BeautifulSoup(html_multi, 'html.parser')
    p_element = soup.find('p')
    text, marks = extract_text_and_marks(p_element)
    
    print(f"提取结果标记: {marks}")
    assert len(marks) == 1
    mark = marks[0]
    
    print(f"标记类型字段: {mark.type}")
    assert isinstance(mark, CompositeMark)
    assert 'bold' in mark.type
    assert 'italic' in mark.type
    
    print("✅ 多个标记成功合并为列表格式")


def test_docx_formatter_with_list():
    """
    测试 DOCX 导出逻辑是否支持列表格式的 type
    """
    print("\n\n" + "=" * 80)
    print("测试 DOCX 导出格式化器支持列表 type")
    print("=" * 80)
    
    # 模拟 Word Run 对象
    mock_run = MagicMock()
    mock_run.font = MagicMock()
    
    # 构造带有列表 type 的 mark
    marks = [
        {"type": ["bold", "italic", "underline"], "range": [0, 5], "value": None}
    ]
    
    print(f"输入 Marks: {marks}")
    
    # 调用被修改的函数
    apply_marks_to_run(mock_run, marks)
    
    # 验证是否设置了属性
    print(f"校验 bold: {mock_run.bold}")
    print(f"校验 italic: {mock_run.italic}")
    print(f"校验 underline: {mock_run.underline}")
    
    assert mock_run.bold is True, "Bold 属性未设置"
    assert mock_run.italic is True, "Italic 属性未设置"
    assert mock_run.underline is True, "Underline 属性未设置"
    
    print("✅ apply_marks_to_run 成功处理列表格式 type")

if __name__ == "__main__":
    test_unified_list_format()
    test_docx_formatter_with_list()
    print("\n🎉 所有验证通过!")
