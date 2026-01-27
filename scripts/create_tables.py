"""
创建数据库表结构
"""
import sys
from pathlib import Path

# 添加根目录到路径
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

from app.database import engine, Base
from app.models import schema  # 导入模型以注册到Base

def create_tables():
    print("🔌 连接到数据库...")
    print("🔨 正在创建表结构...")
    Base.metadata.create_all(bind=engine)
    print("✅ 表结构创建成功！")

if __name__ == "__main__":
    create_tables()
