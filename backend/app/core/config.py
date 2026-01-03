"""
配置管理模块
使用 Pydantic Settings 管理应用配置
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    """
    应用配置类
    从环境变量或 .env 文件读取配置
    """
    
    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/word_editor"
    
    # 应用基本信息
    APP_NAME: str = "Web Word Editor"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    
    # CORS 配置
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://localhost:3000"
    ]
    
    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "./uploads"
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    class Config:
        """Pydantic 配置"""
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()
