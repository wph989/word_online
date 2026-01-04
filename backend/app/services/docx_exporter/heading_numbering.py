"""
标题编号生成器
支持为每个级别的标题独立配置编号格式
"""

from typing import Dict, List, Optional


class HeadingNumberGenerator:
    """标题编号生成器 - 支持每个级别独立配置"""
    
    # 中文数字映射
    CHINESE_NUMBERS = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    
    # 带圈数字（用于某些样式）
    CIRCLED_NUMBERS = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"]
    
    # 可用的编号格式类型
    AVAILABLE_FORMATS = {
        "chinese": "中文数字（一、二、三）",
        "number": "阿拉伯数字（1、2、3）",
        "number_dot": "数字+点（1.、2.、3.）",
        "hierarchical": "层级编号（1.1、1.2）",
        "parenthesis": "括号数字（(1)、(2)）",
        "circled": "带圈数字（①、②、③）",
        "chapter": "章节格式（第一章、第二章）",
        "none": "无编号"
    }
    
    def __init__(self, level_formats: Optional[Dict[int, str]] = None, enabled: bool = True):
        """
        初始化编号生成器
        
        Args:
            level_formats: 每个级别的编号格式配置
                格式: {1: "chinese", 2: "hierarchical", 3: "parenthesis", ...}
                如果某个级别未配置，默认使用 "hierarchical"
            enabled: 是否启用编号
        """
        self.enabled = enabled
        self.level_formats = level_formats or {}
        # 存储每个层级的计数器列表
        self.counters: Dict[int, List[int]] = {}
    
    def reset(self):
        """重置所有计数器"""
        self.counters = {}
    
    def get_number(self, level: int) -> str:
        """
        获取指定层级的编号
        
        Args:
            level: 标题层级 (1-6)
            
        Returns:
            编号字符串，如 "一、", "1.1 ", "(1) " 等
        """
        if not self.enabled:
            return ""
        
        # 确保层级在有效范围内
        level = max(1, min(6, level))
        
        # 更新计数器
        self._update_counter(level)
        
        # 获取该层级的格式配置
        format_type = self.level_formats.get(level, "hierarchical")
        
        # 根据格式生成编号
        return self._generate_number(level, format_type)
    
    def _update_counter(self, level: int):
        """更新指定层级的计数器"""
        if level == 1:
            # 一级标题
            if 1 not in self.counters:
                self.counters[1] = [1]
            else:
                self.counters[1][0] += 1
            # 清除所有更深层级
            for l in list(self.counters.keys()):
                if l > 1:
                    del self.counters[l]
        else:
            # 多级标题
            parent_level = level - 1
            
            # 确保父级存在
            if parent_level not in self.counters:
                # 如果父级不存在，初始化所有父级
                self.counters[parent_level] = [1] * parent_level
            
            # 初始化或更新当前级别
            if level not in self.counters:
                # 继承父级计数器并添加新层级
                self.counters[level] = self.counters[parent_level].copy() + [1]
            else:
                # 检查是否需要重置（父级计数器改变了）
                parent_counters = self.counters[parent_level]
                current_counters = self.counters[level]
                
                # 如果当前计数器的父级部分与实际父级不匹配，需要重置
                if len(current_counters) < level or current_counters[:parent_level] != parent_counters:
                    self.counters[level] = parent_counters.copy() + [1]
                else:
                    # 增加当前层级的计数
                    self.counters[level][-1] += 1
            
            # 清除所有更深层级
            for l in list(self.counters.keys()):
                if l > level:
                    del self.counters[l]
    
    def _generate_number(self, level: int, format_type: str) -> str:
        """
        根据格式类型生成编号
        
        Args:
            level: 标题层级
            format_type: 格式类型
            
        Returns:
            编号字符串
        """
        counters = self.counters.get(level, [1])
        current_num = counters[-1] if counters else 1
        
        if format_type == "chinese":
            # 中文数字：一、二、三
            return self._to_chinese_number(current_num) + "、"
        
        elif format_type == "number":
            # 阿拉伯数字：1、2、3
            return f"{current_num}、"
        
        elif format_type == "number_dot":
            # 数字+点：1. 、2. 、3.
            return f"{current_num}. "
        
        elif format_type == "hierarchical":
            # 层级编号：1.1、1.2、1.1.1
            number_str = ".".join(str(c) for c in counters)
            return f"{number_str} "
        
        elif format_type == "parenthesis":
            # 括号数字：(1)、(2)、(3)
            return f"({current_num}) "
        
        elif format_type == "circled":
            # 带圈数字：①、②、③
            if current_num <= 10:
                return self.CIRCLED_NUMBERS[current_num - 1] + " "
            else:
                # 超过10个使用括号数字
                return f"({current_num}) "
        
        elif format_type == "chapter":
            # 章节格式：第一章、第二章
            if current_num <= 10:
                return f"第{self._to_chinese_number(current_num)}章 "
            else:
                return f"第{current_num}章 "
        
        elif format_type == "none":
            # 无编号
            return ""
        
        else:
            # 默认使用层级编号
            number_str = ".".join(str(c) for c in counters)
            return f"{number_str} "
    
    def _to_chinese_number(self, num: int) -> str:
        """
        将阿拉伯数字转换为中文数字
        
        Args:
            num: 阿拉伯数字 (1-99)
            
        Returns:
            中文数字字符串
        """
        if num <= 0:
            return "零"
        elif num <= 10:
            return self.CHINESE_NUMBERS[num]
        elif num < 20:
            return "十" + self.CHINESE_NUMBERS[num - 10]
        else:
            tens = num // 10
            ones = num % 10
            result = self.CHINESE_NUMBERS[tens] + "十"
            if ones > 0:
                result += self.CHINESE_NUMBERS[ones]
            return result


# 预定义的样式模板
PRESET_STYLES = {
    "style1": {
        "name": "中文混合样式",
        "description": "一、二、三 / 1.1、1.2 / (1)、(2)",
        "formats": {
            1: "chinese",      # 一、二、三
            2: "hierarchical", # 1.1、1.2
            3: "parenthesis",  # (1)、(2)
            4: "hierarchical", # 1.1.1.1
            5: "parenthesis",  # (1)、(2)
            6: "circled"       # ①、②、③
        }
    },
    "style2": {
        "name": "纯数字样式",
        "description": "1、2、3 / 1.1、1.2 / 1.1.1、1.1.2",
        "formats": {
            1: "number",       # 1、2、3
            2: "hierarchical", # 1.1、1.2
            3: "hierarchical", # 1.1.1、1.1.2
            4: "hierarchical", # 1.1.1.1
            5: "hierarchical", # 1.1.1.1.1
            6: "hierarchical"  # 1.1.1.1.1.1
        }
    },
    "style3": {
        "name": "数字点号样式",
        "description": "1.、2.、3. / 1.1、1.2 / 1.1.1、1.1.2",
        "formats": {
            1: "number_dot",   # 1. 、2. 、3.
            2: "hierarchical", # 1.1、1.2
            3: "hierarchical", # 1.1.1、1.1.2
            4: "hierarchical", # 1.1.1.1
            5: "hierarchical", # 1.1.1.1.1
            6: "hierarchical"  # 1.1.1.1.1.1
        }
    },
    "style4": {
        "name": "章节样式",
        "description": "第一章、第二章 / 1.1、1.2 / 1.1.1、1.1.2",
        "formats": {
            1: "chapter",      # 第一章、第二章
            2: "hierarchical", # 1.1、1.2
            3: "hierarchical", # 1.1.1、1.1.2
            4: "hierarchical", # 1.1.1.1
            5: "hierarchical", # 1.1.1.1.1
            6: "hierarchical"  # 1.1.1.1.1.1
        }
    }
}


def create_heading_number_generator(numbering_config: Optional[Dict]) -> Optional[HeadingNumberGenerator]:
    """
    根据配置创建编号生成器
    
    Args:
        numbering_config: 编号配置字典
            格式1（使用预设样式）: {"style": "style1", "enabled": true}
            格式2（自定义每级）: {"enabled": true, "formats": {1: "chinese", 2: "hierarchical", ...}}
        
    Returns:
        HeadingNumberGenerator 实例，如果未启用则返回 None
    """
    if not numbering_config:
        return None
    
    enabled = numbering_config.get("enabled", False)
    if not enabled:
        return None
    
    # 检查是否使用预设样式
    if "style" in numbering_config:
        style_name = numbering_config["style"]
        if style_name in PRESET_STYLES:
            level_formats = PRESET_STYLES[style_name]["formats"]
            return HeadingNumberGenerator(level_formats=level_formats, enabled=True)
    
    # 检查是否有自定义格式配置
    if "formats" in numbering_config:
        level_formats = numbering_config["formats"]
        # 转换键为整数
        level_formats = {int(k): v for k, v in level_formats.items()}
        return HeadingNumberGenerator(level_formats=level_formats, enabled=True)
    
    # 默认使用 style2（纯数字样式）
    return HeadingNumberGenerator(level_formats=PRESET_STYLES["style2"]["formats"], enabled=True)
