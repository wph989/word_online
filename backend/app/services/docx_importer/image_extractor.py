"""
图片提取器

从 DOCX 中提取图片并保存到文件系统
"""

import os
import uuid
from typing import Dict
from pathlib import Path

from .parser import DocxImage


class ImageExtractor:
    """
    图片提取器
    
    从 DOCX 中提取嵌入图片并保存到指定目录
    """
    
    def __init__(self, doc_id: str, upload_dir: str = "./uploads"):
        """
        初始化图片提取器
        
        Args:
            doc_id: 文档 ID
            upload_dir: 上传目录根路径
        """
        self.doc_id = doc_id
        self.upload_dir = upload_dir
        self.image_dir = os.path.join(upload_dir, "images", doc_id)
    
    def extract_and_save(self, images: Dict[str, DocxImage]) -> Dict[str, str]:
        """
        提取并保存所有图片
        
        Args:
            images: {rId: DocxImage} 映射
            
        Returns:
            {rId: 图片访问路径} 映射
        """
        path_map = {}
        
        if not images:
            return path_map
        
        # 确保目录存在
        Path(self.image_dir).mkdir(parents=True, exist_ok=True)
        
        for rId, image in images.items():
            if image.image_bytes:
                # 生成唯一文件名
                filename = self._generate_filename(image)
                file_path = os.path.join(self.image_dir, filename)
                
                # 保存图片
                try:
                    with open(file_path, 'wb') as f:
                        f.write(image.image_bytes)
                    
                    # 生成访问路径
                    access_path = f"/api/v1/assets/images/{self.doc_id}/{filename}"
                    path_map[rId] = access_path
                    
                except Exception as e:
                    print(f"保存图片失败 {rId}: {e}")
        
        return path_map
    
    def _generate_filename(self, image: DocxImage) -> str:
        """生成唯一文件名"""
        # 获取扩展名
        ext = self._get_extension(image)
        
        # 使用原始文件名或生成新名称
        if image.filename:
            # 去掉原有扩展名，使用正确的扩展名
            base_name = os.path.splitext(image.filename)[0]
            # 添加唯一后缀避免重复
            unique_suffix = uuid.uuid4().hex[:6]
            return f"{base_name}_{unique_suffix}{ext}"
        else:
            return f"image_{uuid.uuid4().hex[:8]}{ext}"
    
    def _get_extension(self, image: DocxImage) -> str:
        """根据 content_type 获取文件扩展名"""
        content_type_map = {
            'image/png': '.png',
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/gif': '.gif',
            'image/bmp': '.bmp',
            'image/webp': '.webp',
            'image/tiff': '.tiff',
            'image/x-emf': '.emf',
            'image/x-wmf': '.wmf',
        }
        
        if image.content_type:
            return content_type_map.get(image.content_type.lower(), '.png')
        
        # 从原始文件名推断
        if image.filename:
            _, ext = os.path.splitext(image.filename)
            if ext:
                return ext.lower()
        
        return '.png'
    
    def cleanup(self):
        """清理文档的所有图片（用于导入失败时回滚）"""
        try:
            import shutil
            if os.path.exists(self.image_dir):
                shutil.rmtree(self.image_dir)
        except Exception as e:
            print(f"清理图片目录失败: {e}")
