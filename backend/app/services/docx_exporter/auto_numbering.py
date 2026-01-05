"""
Word 自动编号配置工具
使用 Word 内置的多级列表编号功能
"""

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


def create_multilevel_numbering(doc: Document, numbering_config: Optional[Dict]) -> Optional[int]:
    """
    创建多级列表编号定义
    
    Args:
        doc: Word 文档对象
        numbering_config: 编号配置 {"enabled": true, "style": "style1", "useAutoNumbering": true}
    
    Returns:
        numbering ID，如果未启用或不使用自动编号则返回 None
    """
    if not numbering_config or not numbering_config.get('enabled'):
        return None
    
    # 检查是否使用自动编号
    if not numbering_config.get('useAutoNumbering', False):
        return None
    
    try:
        style = numbering_config.get('style', 'style2')
        
        # 获取numbering part
        numbering_part = doc.part.numbering_part
        if numbering_part is None:
            # 创建numbering part
            from docx.opc.part import Part
            from docx.opc.constants import CONTENT_TYPE as CT
            numbering_part = Part(
                CT.WML_NUMBERING,
                doc.part.package
            )
            doc.part.numbering_part = numbering_part
            
            # 创建基础numbering元素
            numbering_part._element = OxmlElement('w:numbering')
            numbering_part._element.set(qn('xmlns:w'), 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')
        
        # 创建抽象编号定义
        abstract_num_id = len(numbering_part.element.findall(qn('w:abstractNum')))
        abstract_num = create_abstract_num_element(abstract_num_id, style)
        numbering_part.element.append(abstract_num)
        
        # 创建编号实例
        num_id = len(numbering_part.element.findall(qn('w:num'))) + 1
        num = OxmlElement('w:num')
        num.set(qn('w:numId'), str(num_id))
        
        abstract_num_id_ref = OxmlElement('w:abstractNumId')
        abstract_num_id_ref.set(qn('w:val'), str(abstract_num_id))
        num.append(abstract_num_id_ref)
        
        numbering_part.element.append(num)
        
        logger.info(f"创建自动编号定义成功: numId={num_id}, style={style}")
        return num_id
        
    except Exception as e:
        logger.error(f"创建自动编号失败: {e}", exc_info=True)
        return None


def create_abstract_num_element(abstract_num_id: int, style: str) -> OxmlElement:
    """
    创建抽象编号定义元素
    
    Args:
        abstract_num_id: 抽象编号ID
        style: 样式名称
    
    Returns:
        抽象编号XML元素
    """
    abstract_num = OxmlElement('w:abstractNum')
    abstract_num.set(qn('w:abstractNumId'), str(abstract_num_id))
    
    # 多级列表类型
    multi_level_type = OxmlElement('w:multiLevelType')
    multi_level_type.set(qn('w:val'), 'multilevel')
    abstract_num.append(multi_level_type)
    
    # 获取样式配置
    level_configs = get_numbering_level_configs(style)
    
    # 为每个级别创建配置
    for ilvl in range(6):
        lvl_element = create_level_element(ilvl, level_configs[ilvl])
        abstract_num.append(lvl_element)
    
    return abstract_num


def create_level_element(ilvl: int, config: Dict) -> OxmlElement:
    """
    创建单个级别的编号元素
    
    Args:
        ilvl: 级别索引 (0-5)
        config: 级别配置
    
    Returns:
        级别XML元素
    """
    lvl = OxmlElement('w:lvl')
    lvl.set(qn('w:ilvl'), str(ilvl))
    
    # 起始值
    start = OxmlElement('w:start')
    start.set(qn('w:val'), '1')
    lvl.append(start)
    
    # 编号格式
    num_fmt = OxmlElement('w:numFmt')
    num_fmt.set(qn('w:val'), config['numFmt'])
    lvl.append(num_fmt)
    
    # 级别文本
    lvl_text = OxmlElement('w:lvlText')
    lvl_text.set(qn('w:val'), config['lvlText'])
    lvl.append(lvl_text)
    
    # 正规形式编号 (强制引用为阿拉伯数字)
    if config.get('isLgl'):
        is_lgl = OxmlElement('w:isLgl')
        lvl.append(is_lgl)
    
    # 对齐
    lvl_jc = OxmlElement('w:lvlJc')
    lvl_jc.set(qn('w:val'), 'left')
    lvl.append(lvl_jc)
    
    # 段落属性
    pPr = OxmlElement('w:pPr')
    ind = OxmlElement('w:ind')
    ind.set(qn('w:left'), str(config.get('left', 0)))
    ind.set(qn('w:hanging'), str(config.get('hanging', 0)))
    pPr.append(ind)
    lvl.append(pPr)
    
    return lvl


def get_numbering_level_configs(style: str) -> list:
    """
    获取编号级别配置
    
    Args:
        style: 样式名称
    
    Returns:
        6个级别的配置列表
    """
    configs = {
        'style1': [
            # H1: 一、二、三（中文数字显示）
            {'numFmt': 'chineseCounting', 'lvlText': '%1、', 'left': 0, 'hanging': 0},
            # H2: 1.1、1.2（使用isLgl强制将%1转换为阿拉伯数字）
            {'numFmt': 'decimal', 'lvlText': '%1.%2 ', 'isLgl': True, 'left': 420, 'hanging': 0},
            # H3: 1.1.1（使用isLgl）
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3 ', 'isLgl': True, 'left': 840, 'hanging': 0},
            # H4: 1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4 ', 'isLgl': True, 'left': 1260, 'hanging': 0},
            # H5: 1.1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4.%5 ', 'isLgl': True, 'left': 1680, 'hanging': 0},
            # H6: 1.1.1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4.%5.%6 ', 'isLgl': True, 'left': 2100, 'hanging': 0},
        ],
        'style2': [
            # H1: 1、2、3
            {'numFmt': 'decimal', 'lvlText': '%1、', 'left': 0, 'hanging': 0},
            # H2: 1.1、1.2
            {'numFmt': 'decimal', 'lvlText': '%1.%2 ', 'left': 420, 'hanging': 0},
            # H3: 1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3 ', 'left': 840, 'hanging': 0},
            # H4: 1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4 ', 'left': 1260, 'hanging': 0},
            # H5: 1.1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4.%5 ', 'left': 1680, 'hanging': 0},
            # H6: 1.1.1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4.%5.%6 ', 'left': 2100, 'hanging': 0},
        ],
        'style3': [
            # H1: 1. 2. 3.
            {'numFmt': 'decimal', 'lvlText': '%1. ', 'left': 0, 'hanging': 0},
            # H2: 1.1、1.2
            {'numFmt': 'decimal', 'lvlText': '%1.%2 ', 'left': 420, 'hanging': 0},
            # H3: 1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3 ', 'left': 840, 'hanging': 0},
            # H4: 1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4 ', 'left': 1260, 'hanging': 0},
            # H5: 1.1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4.%5 ', 'left': 1680, 'hanging': 0},
            # H6: 1.1.1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4.%5.%6 ', 'left': 2100, 'hanging': 0},
        ],
        'style4': [
            # H1: 第一章、第二章（中文章节显示）
            {'numFmt': 'chineseCounting', 'lvlText': '第%1章 ', 'left': 0, 'hanging': 0},
            # H2: 1.1、1.2（使用isLgl强制将%1转换为阿拉伯数字）
            {'numFmt': 'decimal', 'lvlText': '%1.%2 ', 'isLgl': True, 'left': 420, 'hanging': 0},
            # H3: 1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3 ', 'isLgl': True, 'left': 840, 'hanging': 0},
            # H4: 1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4 ', 'isLgl': True, 'left': 1260, 'hanging': 0},
            # H5: 1.1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4.%5 ', 'isLgl': True, 'left': 1680, 'hanging': 0},
            # H6: 1.1.1.1.1.1
            {'numFmt': 'decimal', 'lvlText': '%1.%2.%3.%4.%5.%6 ', 'isLgl': True, 'left': 2100, 'hanging': 0},
        ]
    }
    
    return configs.get(style, configs['style2'])


def apply_numbering_to_heading(para, num_id: int, level: int):
    """
    为标题段落应用自动编号
    
    Args:
        para: 段落对象
        num_id: 编号ID
        level: 标题级别 (1-6)
    """
    try:
        pPr = para._element.get_or_add_pPr()
        
        # 移除已有的编号
        for numPr in pPr.findall(qn('w:numPr')):
            pPr.remove(numPr)
        
        # 添加新的编号
        numPr = OxmlElement('w:numPr')
        
        # 级别索引 (0-based)
        ilvl = OxmlElement('w:ilvl')
        ilvl.set(qn('w:val'), str(level - 1))
        numPr.append(ilvl)
        
        # 编号ID
        numId = OxmlElement('w:numId')
        numId.set(qn('w:val'), str(num_id))
        numPr.append(numId)
        
        pPr.append(numPr)
        
    except Exception as e:
        logger.error(f"应用编号失败: {e}", exc_info=True)
