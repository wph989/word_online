"""
FastAPI 应用主入口
配置路由、中间件和生命周期事件
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import chapters, documents, export, upload, ai_chapters, document_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时创建数据库表
    """
    # 启动时：创建所有数据表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")
    
    yield
    
    # 关闭时：清理资源（如果需要）
    print("👋 应用关闭")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于后端中心化架构的在线 Word 编辑器",
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)


# 配置 CORS 中间件
# 允许前端跨域访问 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # 允许的源
    allow_credentials=True,  # 允许携带凭证
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有请求头
)


# 注册路由
app.include_router(documents.router)
app.include_router(chapters.router)
app.include_router(export.router)
app.include_router(upload.router)
app.include_router(ai_chapters.router)  # AI 章节处理 API
app.include_router(document_settings.router)  # 文档配置 API


# 挂载静态文件目录（用于提供上传的图片）
import os
uploads_dir = "uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/")
def root():
    """
    根路径
    返回 API 基本信息
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "欢迎使用 Web Word Editor API",
        "docs": "/docs",
        "architecture": "后端中心化 (Backend-Centric)"
    }


@app.get("/health")
def health_check():
    """
    健康检查接口
    用于监控和负载均衡
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    
    # 开发环境直接运行
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 开发模式：代码变更自动重载
    )
