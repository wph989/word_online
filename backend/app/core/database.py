"""
数据库连接管理模块
配置 SQLAlchemy 引擎和会话
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 创建数据库引擎
# echo=True 会打印所有 SQL 语句，生产环境应设为 False
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # 连接池预检查，防止连接失效
    pool_recycle=3600,   # 连接回收时间（秒）
)

# 创建会话工厂
# autocommit=False: 需要显式调用 commit()
# autoflush=False: 需要显式调用 flush()
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 创建 ORM 基类
Base = declarative_base()


def get_db():
    """
    获取数据库会话的依赖注入函数
    使用 yield 确保会话在请求结束后正确关闭
    
    用法:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
