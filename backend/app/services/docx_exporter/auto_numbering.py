"""
Word 自动编号配置工具
使用 Word 内置的多级列表编号功能
"""

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from typing import Optional, Dict


def create_numbering_definition(doc: Document, numbering_config: Optional[Dict]) -> Optional[int]:
    """
    创建 Word 自动编号定义
    
    Args:
        doc: Word 文档对象
        numbering_config: 编号配置 {"enabled": true, "style": "style1"}
    
    Returns:
        numbering ID，如果未启用则返回 None
    """
    if not numbering_config or not numbering_config.get('enabled'):
        return None
    
    style = numbering_config.get('style', 'style2')
    
    # 获取或创建 numbering part
    if not hasattr(doc, '_part') or not hasattr(doc._part, 'numbering_part'):
        return None
    
    numbering_part = doc._part.numbering_part
    if numbering_part is None:
        # 创建 numbering part
        from docx.opc.constants import RELATIONSHIP_TYPE as RT
        numbering_part = doc._part.add_part(
            doc._part.package.part_related_by(doc._part, RT.NUMBERING)
        )
    
    # 创建抽象编号定义
    abstract_num_id = len(numbering_part.element.findall(qn('w:abstractNum')))
    
    # 根据样式创建不同的编号格式
    abstract_num = create_abstract_num(abstract_num_id, style)
    numbering_part.element.append(abstract_num)
    
    # 创建编号实例
    num_id = len(numbering_part.element.findall(qn('w:num'))) + 1
    num = OxmlElement('w:num')
    num.set(qn('w:numId'), str(num_id))
    
    abstract_num_id_ref = OxmlElement('w:abstractNumId')
    abstract_num_id_ref.set(qn('w:val'), str(abstract_num_id))
    num.append(abstract_num_id_ref)
    
    numbering_part.element.append(num)
    
    return num_id


def create_abstract_num(abstract_num_id: int, style: str) -> OxmlElement:
    """
    创建抽象编号定义
    
    Args:
        abstract_num_id: 抽象编号ID
        style: 样式名称 (style1, style2, style3, style4)
    
    Returns:
        抽象编号元素
    """
    abstract_num = OxmlElement('w:abstractNum')
    abstract_num.set(qn('w:abstractNumId'), str(abstract_num_id))
    
    # 多级列表ID
    multi_level_type = OxmlElement('w:multiLevelType')
    multi_level_type.set(qn('w:val'), 'multilevel')
    abstract_num.append(multi_level_type)
    
    # 根据样式配置创建6个级别
    style_configs = get_style_config(style)
    
    for level in range(6):
        lvl = create_level(level, style_configs[level])
        abstract_num.append(lvl)
    
    return abstract_num


def create_level(level: int, config: Dict) -> OxmlElement:
    """
    创建单个级别的编号定义
    
    Args:
        level: 级别 (0-5 对应 H1-H6)
        config: 级别配置
    
    Returns:
        级别元素
    """
    lvl = OxmlElement('w:lvl')
    lvl.set(qn('w:ilvl'), str(level))
    
    # 起始值
    start = OxmlElement('w:start')
    start.set(qn('w:val'), '1')
    lvl.append(start)
    
    # 编号格式
    num_fmt = OxmlElement('w:numFmt')
    num_fmt.set(qn('w:val'), config['numFmt'])
    lvl.append(num_fmt)
    
    # 编号文本
    lvl_text = OxmlElement('w:lvlText')
    lvl_text.set(qn('w:val'), config['lvlText'])
    lvl.append(lvl_text)
    
    # 对齐方式
    lvl_jc = OxmlElement('w:lvlJc')
    lvl_jc.set(qn('w:val'), 'left')
    lvl.append(lvl_jc)
    
    # 段落属性
    pPr = OxmlElement('w:pPr')
    
    # 缩进
    ind = OxmlElement('w:ind')
    ind.set(qn('w:left'), str(config['indent']))
    ind.set(qn('w:hanging'), str(config['hanging']))
    pPr.append(ind)
    
    lvl.append(pPr)
    
    # 字符属性（可选）
    if config.get('suffix'):
        suff = OxmlElement('w:suff')
        suff.set(qn('w:val'), config['suffix'])
        lvl.append(suff)
    
    return lvl


def get_style_config(style: str) -> list:
    """
    获取样式配置
    
    Args:
        style: 样式名称
    
    Returns:
        6个级别的配置列表
    """
    configs = {
        'style1': [
            # H1: 一、二、三
            {'numFmt': 'chineseCounting', 'lvlText': '%1、', 'indent': 0, 'hanging': 0, 'suffix': 'space'},
            # H2: 1.1、1.2
            {'numFmt': 'decimal', 'lvlText': '%1.%2 ', 'indent': 420, 'hanging': 0, 'suffix': 'space'},
            # H3: (1)、(2)
            {'numFmt': 'decimal', 'lvlText': '(%3) ', 'indent': 840, 'hanging': 0, 'suffix': 'space'},
            # H4: 1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4 ', 'indent': 1260, 'hanging': 0, 'suffix': 'space'},
            # H5: (1)
            {'numFmt': 'decimal', 'lvlText': '(%5) ', 'indent': 1680, 'hanging': 0, 'suffix': 'space'},
            # H6: ①②③
            {'numFmt': 'decimalEnclosedCircle', 'lvlText': '%6 ', 'indent': 2100, 'hanging': 0, 'suffix': 'space'},
        ],
        'style2': [
            # H1: 1、2、3
            {'numFmt': 'decimal', 'lvlText': '%1、', 'indent': 0, 'hanging': 0, 'suffix': 'space'},
            # H2: 1.1、1.2
            {'numFmt': 'decimal', 'lvlText': '%1.%2 ', 'indent': 420, 'hanging': 0, 'suffix': 'space'},
            # H3: 1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3 ', 'indent': 840, 'hanging': 0, 'suffix': 'space'},
            # H4: 1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4 ', 'indent': 1260, 'hanging': 0, 'suffix': 'space'},
            # H5: 1.1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4.%5 ', 'indent': 1680, 'hanging': 0, 'suffix': 'space'},
            # H6: 1.1.1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4.%5.%6 ', 'indent': 2100, 'hanging': 0, 'suffix': 'space'},
        ],
        'style3': [
            # H1: 1. 2. 3.
            {'numFmt': 'decimal', 'lvlText': '%1. ', 'indent': 0, 'hanging': 0, 'suffix': 'space'},
            # H2: 1.1 1.2
            {'numFmt': 'decimal', 'lvlText': '%1.%2 ', 'indent': 420, 'hanging': 0, 'suffix': 'space'},
            # H3: 1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3 ', 'indent': 840, 'hanging': 0, 'suffix': 'space'},
            # H4: 1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4 ', 'indent': 1260, 'hanging': 0, 'suffix': 'space'},
            # H5: 1.1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4.%5 ', 'indent': 1680, 'hanging': 0, 'suffix': 'space'},
            # H6: 1.1.1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4.%5.%6 ', 'indent': 2100, 'hanging': 0, 'suffix': 'space'},
        ],
        'style4': [
            # H1: 第一章、第二章（使用中文计数）
            {'numFmt': 'chineseCounting', 'lvlText': '第%1章 ', 'indent': 0, 'hanging': 0, 'suffix': 'space'},
            # H2: 1.1 1.2
            {'numFmt': 'decimal', 'lvlText': '%1.%2 ', 'indent': 420, 'hanging': 0, 'suffix': 'space'},
            # H3: 1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3 ', 'indent': 840, 'hanging': 0, 'suffix': 'space'},
            # H4: 1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4 ', 'indent': 1260, 'hanging': 0, 'suffix': 'space'},
            # H5: 1.1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4.%5 ', 'indent': 1680, 'hanging': 0, 'suffix': 'space'},
            # H6: 1.1.1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4.%5.%6 ', 'indent': 2100, 'hanging': 0, 'suffix': 'space'},
        ]
    }
    
    return configs.get(style, configs['style2'])


def apply_numbering_to_paragraph(para, num_id: int, level: int):
    """
    为段落应用编号
    
    Args:
        para: 段落对象
        num_id: 编号ID
        level: 级别 (0-5)
    """
    pPr = para._element.get_or_add_pPr()
    
    # 移除已有的编号
    for numPr in pPr.findall(qn('w:numPr')):
        pPr.remove(numPr)
    
    # 添加新的编号
    numPr = OxmlElement('w:numPr')
    
    ilvl = OxmlElement('w:ilvl')
    ilvl.set(qn('w:val'), str(level))
    numPr.append(ilvl)
    
    numId = OxmlElement('w:numId')
    numId.set(qn('w:val'), str(num_id))
    numPr.append(numId)
    
    pPr.append(numPr)
