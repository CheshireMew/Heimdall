"""
修复 klines 表 timestamp 字段类型
"""
import sys
from pathlib import Path
from sqlalchemy import text

# 添加根目录到路径
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

from app.database import engine

def fix_schema():
    print("🔌 连接到数据库...")
    with engine.connect() as conn:
        print("🔨 正在修改 klines 表结构...")
        # PostgreSQL specific syntax to alter column type
        try:
            conn.execute(text("ALTER TABLE klines ALTER COLUMN timestamp TYPE BIGINT"))
            conn.commit()
            print("✅ 成功将 timestamp 字段修改为 BIGINT！")
        except Exception as e:
            print(f"❌ 修改失败: {e}")

if __name__ == "__main__":
    fix_schema()
