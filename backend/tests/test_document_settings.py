"""
文档配置功能测试脚本
测试文档配置的创建、查询、更新和导出应用
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def check_response(response, expected_status=200):
    """检查响应状态码，如果失败则打印错误信息"""
    if response.status_code != expected_status and response.status_code != 201:
        print(f"\n❌ 请求失败: {response.status_code}")
        print(f"   响应内容: {response.text}")
        response.raise_for_status()
    return response.json()

def test_document_settings():
    """测试文档配置功能"""
    
    print("=" * 60)
    print("文档配置功能测试")
    print("=" * 60)
    
    # 1. 创建测试文档
    print("\n1. 创建测试文档...")
    doc_response = requests.post(
        f"{BASE_URL}/api/v1/documents",
        json={"title": "测试文档 - 配置功能"}
    )
    doc_id = check_response(doc_response)["id"]
    print(f"✅ 文档创建成功: {doc_id}")
    
    # 2. 创建文档配置 (使用 PUT Upsert)
    print("\n2. 创建文档配置 (PUT)...")
    settings_data = {
        # 注意: doc_id 在 URL 中传递
        "margin_top": 60,
        "margin_bottom": 60,
        "margin_left": 80,
        "margin_right": 80,
        "heading_styles": {
            "h1": {
                "fontSize": 28,
                "fontWeight": "bold",
                "color": "#1890ff",
                "marginTop": 30,
                "marginBottom": 15
            },
            "h2": {
                "fontSize": 24,
                "fontWeight": "bold",
                "color": "#333333",
                "marginTop": 24,
                "marginBottom": 12
            },
            "h3": {
                "fontSize": 20,
                "fontWeight": "bold",
                "color": "#666666",
                "marginTop": 18,
                "marginBottom": 9
            },
            "h4": {
                "fontSize": 18,
                "fontWeight": "bold",
                "color": "#666666",
                "marginTop": 16,
                "marginBottom": 8
            },
            "h5": {
                "fontSize": 16,
                "fontWeight": "bold",
                "color": "#666666",
                "marginTop": 14,
                "marginBottom": 7
            },
            "h6": {
                "fontSize": 14,
                "fontWeight": "bold",
                "color": "#999999",
                "marginTop": 12,
                "marginBottom": 6
            }
        }
    }
    
    # 第一次 PUT: 创建
    settings_response = requests.put(
        f"{BASE_URL}/api/v1/settings/{doc_id}",
        json=settings_data
    )
    # PUT 通常返回 200 OK
    settings_json = check_response(settings_response, 200)
    print(f"✅ 配置创建成功")
    print(f"   页边距: 上={settings_json['margin_top']}px")
    print(f"   H1字号: {settings_json['heading_styles']['h1']['fontSize']}px")
    
    # 3. 查询文档配置
    print("\n3. 查询文档配置...")
    get_response = requests.get(f"{BASE_URL}/api/v1/settings/{doc_id}")
    settings = check_response(get_response)
    print(f"✅ 配置查询成功")
    print(f"   上边距: {settings['margin_top']}px")
    print(f"   H1颜色: {settings['heading_styles']['h1']['color']}")
    
    # 4. 更新文档配置
    print("\n4. 更新文档配置...")
    update_data = {
        "margin_top": 100,
        "heading_styles": {
            **settings_data["heading_styles"],
            "h1": {
                "fontSize": 32,
                "fontWeight": "bold",
                "color": "#ff0000",
                "marginTop": 40,
                "marginBottom": 20
            }
        }
    }
    
    update_response = requests.put(
        f"{BASE_URL}/api/v1/settings/{doc_id}",
        json=update_data
    )
    update_json = check_response(update_response)
    print(f"✅ 配置更新成功")
    print(f"   新上边距: {update_json['margin_top']}px")
    print(f"   新H1字号: {update_json['heading_styles']['h1']['fontSize']}px")
    
    # 5. 创建测试章节
    print("\n5. 创建测试章节...")
    chapter_html = """
    <h1>这是一级标题</h1>
    <p>这是正文段落。</p>
    <h2>这是二级标题</h2>
    <p>更多内容。</p>
    """
    
    chapter_response = requests.post(
        f"{BASE_URL}/api/v1/chapters",
        json={
            "doc_id": doc_id,
            "title": "测试章节",
            "html_content": chapter_html,
            "order_index": 0
        }
    )
    chapter_id = check_response(chapter_response)["id"]
    print(f"✅ 章节创建成功: {chapter_id}")
    
    # 6. 测试导出（验证配置是否应用）
    print("\n6. 测试导出与验证...")
    export_url = f"{BASE_URL}/api/v1/export/chapters/{chapter_id}/docx"
    print(f"   下载URL: {export_url}")
    
    # 下载文件
    try:
        from docx import Document
        from io import BytesIO
        
        response = requests.get(export_url)
        if response.status_code != 200:
             print(f"   ❌ 下载失败: {response.status_code}")
             print(f"   {response.text}")
             return

        
        doc_stream = BytesIO(response.content)
        doc = Document(doc_stream)
        
        # 验证 H1 样式
        # 第一个是标题 "测试章节" (如果我们开启了 include_title=True，默认是 True)
        # 或者 HTML 内容中的 H1 "这是一级标题"
        
        # 查找内容中的 H1
        h1_para = None
        for para in doc.paragraphs:
            if para.text == "这是一级标题":
                h1_para = para
                break
        
        if h1_para:
            print("   ✅ 找到 H1 段落: '这是一级标题'")
            runs = h1_para.runs
            if runs:
                # 检查字号 (H1 配置为 32px -> 24pt, 1px ~ 0.75pt)
                # Word 中 font.size 是 EMU 或 PT? python-docx 中 font.size 返回 Pt 对象
                # 我们在 exporter 中设置的是 Pt(32), 实际上我们传入的是 32，在 Exporter 内部被转为 Pt(32)。 
                # 等等，前端传的是 px。Export 内部:
                # run.font.size = Pt(default_style["fontSize"])
                # 所以如果是 32，就是 32pt。
                
                font_size = runs[0].font.size
                if font_size and font_size.pt == 32.0:
                    print(f"   ✅ H1 字号验证通过: {font_size.pt}pt (配置值: 32)")
                else:
                    print(f"   ❌ H1 字号验证失败: {font_size.pt if font_size else 'None'}pt (预期: 32pt)")

                # 检查颜色
                # H1 配置为 #ff0000 (红色) -> RGB(255, 0, 0)
                color = runs[0].font.color.rgb
                if color and color == (255, 0, 0): # python-docx RGBColor 比较
                     print(f"   ✅ H1 颜色验证通过: #{color}")
                else:
                     print(f"   ❌ H1 颜色验证失败: {color} (预期: FF0000)")
            else:
                print("   ❌ H1 段落没有 runs")
        else:
            print("   ❌ 未能在文档中找到 '这是一级标题'")

    except ImportError:
        print("   ⚠️ 未安装 python-docx，跳过 Word 文档内容验证")
    except Exception as e:
        print(f"   ❌ 验证过程出错: {e}")
    
    # 7. 清理（可选）
    print("\n7. 测试完成")
    print(f"   文档ID: {doc_id}")
    print(f"   章节ID: {chapter_id}")
    print(f"   可以访问 http://localhost:8000/docs 查看API文档")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_document_settings()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
