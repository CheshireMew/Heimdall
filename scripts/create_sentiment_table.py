"""
创建 sentiment 表
"""

from app.infra.db import get_database_runtime
from app.infra.db.schema import Sentiment

def create_sentiment_table():
    print("[CONN] 连接到数据库...")
    print("[BUILD] 正在创建 sentiment 表...")
    Sentiment.__table__.create(get_database_runtime().engine)
    print("[OK] 表结构创建成功！")

if __name__ == "__main__":
    try:
        create_sentiment_table()
    except Exception as e:
        print(f"[ERROR] 创建失败 (可能表已存在): {e}")
