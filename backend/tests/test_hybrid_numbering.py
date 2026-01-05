"""
测试混合编号方案
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.docx_exporter import DocxExporter


def test_hybrid_numbering():
    """测试混合编号方案"""
    print("\n=== 测试混合编号方案 ===\n")
    
    # 模拟内容
    content = {
        "blocks": [
            {"id": "1", "type": "heading", "level": 1, "text": "第一章 引言", "marks": []},
            {"id": "2", "type": "heading", "level": 2, "text": "研究背景", "marks": []},
            {"id": "3", "type": "heading", "level": 2, "text": "研究目的", "marks": []},
            {"id": "4", "type": "heading", "level": 3, "text": "主要目标", "marks": []},
            {"id": "5", "type": "heading", "level": 3, "text": "次要目标", "marks": []},
            {"id": "6", "type": "heading", "level": 1, "text": "第二章 方法", "marks": []},
            {"id": "7", "type": "heading", "level": 2, "text": "研究设计", "marks": []},
            {"id": "8", "type": "heading", "level": 2, "text": "数据收集", "marks": []},
        ]
    }
    
    stylesheet = {"rules": []}
    
    # 测试场景
    test_cases = [
        {
            "name": "文本前缀编号 - Style2",
            "config": {
                'heading_numbering_style': {
                    'enabled': True,
                    'style': 'style2',
                    'useAutoNumbering': False
                }
            },
            "filename": "test_hybrid_text_prefix.docx"
        },
        {
            "name": "Word自动编号 - Style2",
            "config": {
                'heading_numbering_style': {
                    'enabled': True,
                    'style': 'style2',
                    'useAutoNumbering': True
                }
            },
            "filename": "test_hybrid_auto_numbering.docx"
        },
        {
            "name": "禁用编号",
            "config": {
                'heading_numbering_style': {
                    'enabled': False
                }
            },
            "filename": "test_hybrid_no_numbering.docx"
        },
        {
            "name": "文本前缀编号 - Style1 (中文)",
            "config": {
                'heading_numbering_style': {
                    'enabled': True,
                    'style': 'style1',
                    'useAutoNumbering': False
                }
            },
            "filename": "test_hybrid_text_style1.docx"
        },
        {
            "name": "Word自动编号 - Style1 (中文)",
            "config": {
                'heading_numbering_style': {
                    'enabled': True,
                    'style': 'style1',
                    'useAutoNumbering': True
                }
            },
            "filename": "test_hybrid_auto_style1.docx"
        },
    ]
    
    for test_case in test_cases:
        print(f"测试: {test_case['name']}")
        
        try:
            exporter = DocxExporter(content, stylesheet, test_case['config'])
            
            # 检查初始化状态
            if test_case['config']['heading_numbering_style'].get('useAutoNumbering'):
                if exporter.auto_numbering_id:
                    print(f"  ✓ 自动编号ID: {exporter.auto_numbering_id}")
                else:
                    print(f"  ✗ 自动编号未创建")
            else:
                if exporter.heading_number_generator:
                    print(f"  ✓ 文本编号生成器已创建")
                else:
                    print(f"  ✓ 编号已禁用")
            
            # 导出文件
            file_stream = exporter.export()
            file_size = file_stream.getbuffer().nbytes
            print(f"  ✓ 导出成功，文件大小: {file_size} 字节")
            
            # 保存测试文件
            with open(test_case['filename'], 'wb') as f:
                f.write(file_stream.getvalue())
            print(f"  ✓ 已保存到: {test_case['filename']}")
            
        except Exception as e:
            print(f"  ✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("=== 测试完成 ===")
    print("\n请打开生成的 test_hybrid_*.docx 文件查看效果！")
    print("\n对比说明:")
    print("- text_prefix: 编号是文本，不能在Word中调整")
    print("- auto_numbering: 编号是Word多级列表，可以在Word中右键调整")
    print()


if __name__ == "__main__":
    test_hybrid_numbering()
