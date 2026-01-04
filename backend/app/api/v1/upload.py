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


# 文件头魔数验证 (防止伪造扩展名)
FILE_SIGNATURES = {
    b'\xFF\xD8\xFF': '.jpg',  # JPEG
    b'\x89PNG\r\n\x1a\n': '.png',  # PNG
    b'GIF87a': '.gif',  # GIF87a
    b'GIF89a': '.gif',  # GIF89a
    b'BM': '.bmp',  # BMP
    b'RIFF': '.webp',  # WebP (需要进一步检查)
    b'\u003c?xml': '.svg',  # SVG
    b'\u003csvg': '.svg',  # SVG
}


def verify_file_signature(content: bytes, filename: str) -> bool:
    """
    验证文件头魔数,确保文件类型真实
    
    Args:
        content: 文件内容
        filename: 文件名
        
    Returns:
        是否通过验证
    """
    if len(content) < 12:
        return False
    
    ext = get_file_extension(filename)
    
    # 检查文件头
    for signature, expected_ext in FILE_SIGNATURES.items():
        if content.startswith(signature):
            # 对于 WebP,需要额外检查
            if signature == b'RIFF' and expected_ext == '.webp':
                if len(content) >= 12 and content[8:12] == b'WEBP':
                    return ext == '.webp'
                return False
            return ext == expected_ext or expected_ext in ALLOWED_EXTENSIONS
    
    return False


def sanitize_filename(filename: str) -> str:
    """
    清理文件名,防止路径遍历攻击
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
    """
    # 移除路径分隔符
    filename = os.path.basename(filename)
    # 移除特殊字符
    filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))
    return filename


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
        
        # 清理文件名,防止路径遍历
        safe_filename = sanitize_filename(file.filename or "image.jpg")
        
        # 检查文件类型
        if not is_allowed_file(safe_filename):
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
        
        # 验证文件头魔数
        if not verify_file_signature(contents, safe_filename):
            raise HTTPException(
                status_code=400,
                detail="文件类型验证失败。文件可能已损坏或类型不匹配"
            )
        
        # 生成唯一文件名
        filename = generate_unique_filename(safe_filename)
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
