"""
编辑器默认样式配置

这些值会应用于：
1. DOCX 导出时的默认样式
2. 应与前端配置 (frontend/src/config/editorDefaults.ts) 保持一致

修改这里的值可以统一调整导出文档的默认样式
"""

# 默认字体
DEFAULT_FONT_FAMILY = "Microsoft YaHei"  # 微软雅黑

# 默认字号（磅，Word 中常用单位）
# 16px ≈ 12pt (1px ≈ 0.75pt)
DEFAULT_FONT_SIZE_PT = 12  # 磅

# 默认行高（倍数）
DEFAULT_LINE_HEIGHT = 1.5

# 默认文字颜色 (RGB)
DEFAULT_TEXT_COLOR = (51, 51, 51)  # #333333

# 默认段落间距（磅）
DEFAULT_PARAGRAPH_SPACING_PT = 7.5  # 约 10px


def get_default_font_family() -> str:
    """获取默认字体"""
    return DEFAULT_FONT_FAMILY


def get_default_font_size_pt() -> float:
    """获取默认字号（磅）"""
    return DEFAULT_FONT_SIZE_PT


def get_default_line_height() -> float:
    """获取默认行高"""
    return DEFAULT_LINE_HEIGHT
