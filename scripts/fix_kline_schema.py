"""
修复 klines 表 timestamp 字段类型
"""
from sqlalchemy import text

from app.infra.db.database import engine

def fix_schema():
    print("[CONN] 连接到数据库...")
    with engine.connect() as conn:
        print("[BUILD] 正在修改 klines 表结构...")
        # PostgreSQL specific syntax to alter column type
        try:
            conn.execute(text("ALTER TABLE klines ALTER COLUMN timestamp TYPE BIGINT"))
            conn.commit()
            print("[OK] 成功将 timestamp 字段修改为 BIGINT！")
        except Exception as e:
            print(f"[ERROR] 修改失败: {e}")

if __name__ == "__main__":
    fix_schema()
