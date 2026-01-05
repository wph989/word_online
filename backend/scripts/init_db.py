"""
数据库初始化脚本
删除所有表并重新创建
"""

import sys
sys.path.insert(0, 'g:/aicode/web_word_edit/new_pro/backend')

from app.core.database import engine, Base
from app.models.database import Document, Chapter, Asset

def init_db():
    """初始化数据库：删除所有表并重新创建"""
    print("正在删除所有表...")
    Base.metadata.drop_all(bind=engine)
    print("✓ 所有表已删除")
    
    print("\n正在创建新表...")
    Base.metadata.create_all(bind=engine)
    print("✓ 所有表已创建")
    
    print("\n数据库初始化完成！")
    print("\n创建的表：")
    print("  - documents (文档表)")
    print("  - chapters (章节表)")
    print("  - assets (资源表)")

if __name__ == "__main__":
    init_db()
