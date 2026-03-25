"""
创建数据库表结构
"""

from app.infra.db.database import engine
from app.infra.db.schema import Base

def create_tables():
    print("[CONN] 连接到数据库...")
    print("[BUILD] 正在创建表结构...")
    Base.metadata.create_all(bind=engine)
    print("[OK] 表结构创建成功！")

if __name__ == "__main__":
    create_tables()
