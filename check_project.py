"""
项目结构验证脚本
检查所有必要的文件是否已创建
"""

import os
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent

# 必须存在的文件列表
REQUIRED_FILES = [
    # 根目录
    "README.md",
    "docker-compose.yml",
    "项目实现总结.md",
    
    # 后端核心文件
    "backend/requirements.txt",
    "backend/.env.example",
    "backend/Dockerfile",
    "backend/.gitignore",
    "backend/app/__init__.py",
    "backend/app/main.py",
    
    # 后端配置
    "backend/app/core/__init__.py",
    "backend/app/core/config.py",
    "backend/app/core/database.py",
    
    # 后端模型
    "backend/app/models/__init__.py",
    "backend/app/models/database.py",
    "backend/app/models/schemas.py",
    
    # 后端 API
    "backend/app/api/__init__.py",
    "backend/app/api/v1/__init__.py",
    "backend/app/api/v1/chapters.py",
    "backend/app/api/v1/documents.py",
    "backend/app/api/v1/export.py",
    
    # 后端服务
    "backend/app/services/__init__.py",
    "backend/app/services/html_parser.py",
    "backend/app/services/html_renderer.py",
    "backend/app/services/docx_exporter.py",
    
    # 后端工具
    "backend/app/utils/__init__.py",
    "backend/app/utils/table_parser.py",
    "backend/app/utils/table_renderer.py",
    
    # 前端
    "frontend/package.json",
    "frontend/.gitignore",
    "frontend/src/components/Editor.tsx",
    "frontend/src/services/api.ts",
    
    # 文档
    "docs/api.md",
    "docs/architecture.md",
    "docs/快速开始.md",
]


def check_files():
    """检查所有必要文件是否存在"""
    print("=" * 60)
    print("🔍 检查项目文件结构...")
    print("=" * 60)
    
    missing_files = []
    existing_files = []
    
    for file_path in REQUIRED_FILES:
        full_path = ROOT_DIR / file_path
        if full_path.exists():
            existing_files.append(file_path)
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path} - 缺失")
    
    print("\n" + "=" * 60)
    print(f"📊 统计结果")
    print("=" * 60)
    print(f"✅ 已创建: {len(existing_files)} 个文件")
    print(f"❌ 缺失: {len(missing_files)} 个文件")
    
    if missing_files:
        print("\n⚠️  缺失的文件:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    else:
        print("\n🎉 所有必要文件已创建！")
        return True


def check_code_quality():
    """检查代码质量（注释覆盖率）"""
    print("\n" + "=" * 60)
    print("📝 检查代码注释覆盖率...")
    print("=" * 60)
    
    core_files = [
        "backend/app/services/html_parser.py",
        "backend/app/services/html_renderer.py",
        "backend/app/utils/table_parser.py",
        "backend/app/services/docx_exporter.py",
    ]
    
    for file_path in core_files:
        full_path = ROOT_DIR / file_path
        if full_path.exists():
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                total_lines = len(lines)
                comment_lines = sum(1 for line in lines if line.strip().startswith('#') or '"""' in line or "'''" in line)
                coverage = (comment_lines / total_lines * 100) if total_lines > 0 else 0
                
                status = "✅" if coverage >= 30 else "⚠️"
                print(f"{status} {file_path}: {coverage:.1f}% ({comment_lines}/{total_lines})")


def print_next_steps():
    """打印后续步骤"""
    print("\n" + "=" * 60)
    print("🚀 后续步骤")
    print("=" * 60)
    print("""
1. 启动 MySQL 数据库:
   docker run -d --name word_editor_mysql \\
     -e MYSQL_ROOT_PASSWORD=password \\
     -e MYSQL_DATABASE=word_editor \\
     -p 3306:3306 mysql:8.0

2. 启动后端服务:
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\\Scripts\\activate
   pip install -r requirements.txt
   cp .env.example .env
   uvicorn app.main:app --reload

3. 启动前端服务:
   cd frontend
   npm install
   npm run dev

4. 访问应用:
   - 后端 API 文档: http://localhost:8000/docs
   - 前端应用: http://localhost:5173

5. 或使用 Docker Compose 一键启动:
   docker-compose up -d

📖 详细文档请查看: docs/快速开始.md
    """)


if __name__ == "__main__":
    # 检查文件
    files_ok = check_files()
    
    # 检查代码质量
    if files_ok:
        check_code_quality()
    
    # 打印后续步骤
    print_next_steps()
