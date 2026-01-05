"""
API 响应模型
定义统一的 API 响应格式
"""

from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """
    统一的 API 响应格式
    
    Attributes:
        success: 请求是否成功
        message: 响应消息
        data: 响应数据
        code: 业务状态码(可选)
    """
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(default="操作成功", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    code: Optional[int] = Field(default=None, description="业务状态码")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "data": {"id": "123", "title": "示例"},
                "code": 0
            }
        }


class PaginationMeta(BaseModel):
    """分页元信息"""
    page: int = Field(..., ge=1, description="当前页码")
    size: int = Field(..., ge=1, le=100, description="每页数量")
    total: int = Field(..., ge=0, description="总记录数")
    total_pages: int = Field(..., ge=0, description="总页数")
    
    @staticmethod
    def calculate_total_pages(total: int, size: int) -> int:
        """计算总页数"""
        return (total + size - 1) // size if size > 0 else 0


class PaginatedResponse(BaseModel, Generic[T]):
    """
    分页响应格式
    
    Attributes:
        items: 数据列表
        meta: 分页元信息
    """
    items: list[T] = Field(default_factory=list, description="数据列表")
    meta: PaginationMeta = Field(..., description="分页信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [{"id": "1", "title": "示例1"}],
                "meta": {
                    "page": 1,
                    "size": 10,
                    "total": 100,
                    "total_pages": 10
                }
            }
        }


class ErrorDetail(BaseModel):
    """错误详情"""
    field: Optional[str] = Field(default=None, description="错误字段")
    message: str = Field(..., description="错误消息")
    code: Optional[str] = Field(default=None, description="错误代码")


class ErrorResponse(BaseModel):
    """
    错误响应格式
    
    Attributes:
        success: 固定为 False
        message: 错误消息
        errors: 错误详情列表(可选)
    """
    success: bool = Field(default=False, description="固定为 False")
    message: str = Field(..., description="错误消息")
    errors: Optional[list[ErrorDetail]] = Field(default=None, description="错误详情")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "请求参数验证失败",
                "errors": [
                    {
                        "field": "title",
                        "message": "标题不能为空",
                        "code": "required"
                    }
                ]
            }
        }


# 便捷函数
def success_response(
    data: Any = None,
    message: str = "操作成功",
    code: Optional[int] = None
) -> dict:
    """
    创建成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
        code: 业务状态码
        
    Returns:
        响应字典
    """
    return {
        "success": True,
        "message": message,
        "data": data,
        "code": code
    }


def error_response(
    message: str,
    errors: Optional[list[dict]] = None
) -> dict:
    """
    创建错误响应
    
    Args:
        message: 错误消息
        errors: 错误详情列表
        
    Returns:
        响应字典
    """
    return {
        "success": False,
        "message": message,
        "errors": errors
    }


def paginated_response(
    items: list,
    page: int,
    size: int,
    total: int
) -> dict:
    """
    创建分页响应
    
    Args:
        items: 数据列表
        page: 当前页码
        size: 每页数量
        total: 总记录数
        
    Returns:
        分页响应字典
    """
    total_pages = PaginationMeta.calculate_total_pages(total, size)
    
    return {
        "items": items,
        "meta": {
            "page": page,
            "size": size,
            "total": total,
            "total_pages": total_pages
        }
    }
