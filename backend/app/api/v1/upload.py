"""
图片上传接口
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1/upload", tags=["upload"])

# 配置上传目录
UPLOAD_DIR = Path("uploads/images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 允许的图片格式
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}

# 最大文件大小 (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024


def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return Path(filename).suffix.lower()


def is_allowed_file(filename: str) -> bool:
    """检查文件类型是否允许"""
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


def generate_unique_filename(original_filename: str) -> str:
    """生成唯一的文件名"""
    ext = get_file_extension(original_filename)
    # 使用日期和UUID生成唯一文件名
    date_str = datetime.now().strftime("%Y%m%d")
    unique_id = uuid.uuid4().hex[:8]
    return f"{date_str}_{unique_id}{ext}"


@router.post("/image")
async def upload_image(file: UploadFile = File(..., alias="wangeditor-uploaded-image")) -> Dict:
    """
    上传图片
    
    Args:
        file: 上传的图片文件（WangEditor 使用 'wangeditor-uploaded-image' 作为字段名）
        
    Returns:
        包含图片URL的响应
    """
    try:
        # 检查文件是否存在
        if not file:
            raise HTTPException(status_code=400, detail="没有上传文件")
        
        # 检查文件类型
        if not is_allowed_file(file.filename or ""):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型。允许的类型: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # 读取文件内容
        contents = await file.read()
        
        # 检查文件大小
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件太大。最大允许 {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # 生成唯一文件名
        filename = generate_unique_filename(file.filename or "image.jpg")
        file_path = UPLOAD_DIR / filename
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # 返回图片URL
        # 注意：这里返回相对路径，前端需要配置静态文件服务
        image_url = f"/uploads/images/{filename}"
        
        return {
            "errno": 0,  # WangEditor 要求的错误码，0 表示成功
            "data": {
                "url": image_url,
                "alt": file.filename,
                "href": image_url
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")
