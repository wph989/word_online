"""
API 请求参数验证模型
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class PaginationParams(BaseModel):
    """
    分页参数验证
    
    Attributes:
        page: 页码(从 1 开始)
        size: 每页数量(1-100)
    """
    page: int = Field(default=1, ge=1, le=10000, description="页码")
    size: int = Field(default=10, ge=1, le=100, description="每页数量")
    
    @field_validator('page')
    @classmethod
    def validate_page(cls, v):
        """验证页码"""
        if v < 1:
            raise ValueError('页码必须大于 0')
        if v > 10000:
            raise ValueError('页码不能超过 10000')
        return v
    
    @field_validator('size')
    @classmethod
    def validate_size(cls, v):
        """验证每页数量"""
        if v < 1:
            raise ValueError('每页数量必须大于 0')
        if v > 100:
            raise ValueError('每页数量不能超过 100')
        return v
    
    def get_offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.size
    
    def get_limit(self) -> int:
        """获取限制数量"""
        return self.size


class SortParams(BaseModel):
    """
    排序参数验证
    
    Attributes:
        sort_by: 排序字段
        order: 排序方向(asc/desc)
    """
    sort_by: Optional[str] = Field(default=None, description="排序字段")
    order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$", description="排序方向")
    
    @field_validator('order')
    @classmethod
    def validate_order(cls, v):
        """验证排序方向"""
        if v and v.lower() not in ['asc', 'desc']:
            raise ValueError('排序方向必须是 asc 或 desc')
        return v.lower() if v else 'desc'


class SearchParams(BaseModel):
    """
    搜索参数验证
    
    Attributes:
        keyword: 搜索关键词
        fields: 搜索字段列表
    """
    keyword: Optional[str] = Field(default=None, max_length=200, description="搜索关键词")
    fields: Optional[list[str]] = Field(default=None, description="搜索字段")
    
    @field_validator('keyword')
    @classmethod
    def validate_keyword(cls, v):
        """验证搜索关键词"""
        if v:
            # 去除首尾空格
            v = v.strip()
            # 如果为空字符串,返回 None
            if not v:
                return None
        return v


class DateRangeParams(BaseModel):
    """
    日期范围参数验证
    
    Attributes:
        start_date: 开始日期
        end_date: 结束日期
    """
    start_date: Optional[str] = Field(default=None, description="开始日期(YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="结束日期(YYYY-MM-DD)")
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v):
        """验证日期格式"""
        if v:
            from datetime import datetime
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('日期格式必须是 YYYY-MM-DD')
        return v
