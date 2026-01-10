"""
FastAPI 应用主入口
配置路由、中间件和生命周期事件
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging
import traceback

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import chapters, documents, export, upload, ai_chapters, document_settings, ai_edit, docx_import

# 配置日志
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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


# ============ 全局异常处理器 ============

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    logger.warning(f"请求验证失败: {request.url} - {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "请求参数验证失败",
            "errors": exc.errors()
        }
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """处理数据库错误"""
    logger.error(f"数据库错误: {request.url} - {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "数据库操作失败,请稍后重试"
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """处理所有未捕获的异常"""
    logger.error(
        f"未处理的异常: {request.url} - {type(exc).__name__}: {str(exc)}\n"
        f"Traceback: {traceback.format_exc()}"
    )
    
    # 开发环境返回详细错误信息
    if settings.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": f"{type(exc).__name__}: {str(exc)}",
                "traceback": traceback.format_exc().split('\n')
            }
        )
    
    # 生产环境返回通用错误信息
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "服务器内部错误,请联系管理员"
        }
    )


# 注册路由
app.include_router(documents.router)
app.include_router(chapters.router)
app.include_router(export.router)
app.include_router(upload.router)
app.include_router(ai_chapters.router)  # AI 章节处理 API
app.include_router(document_settings.router)  # 文档配置 API
app.include_router(ai_edit.router)  # AI 编辑 API
app.include_router(docx_import.router)  # DOCX 导入 API


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
