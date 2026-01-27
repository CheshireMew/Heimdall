"""
创建 sentiment 表
"""
import sys
from pathlib import Path
from sqlalchemy import text

# 添加根目录到路径
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

from app.database import engine
from models.schema import Sentiment

def create_sentiment_table():
    print("🔌 连接到数据库...")
    print("🔨 正在创建 sentiment 表...")
    Sentiment.__table__.create(engine)
    print("✅ 表结构创建成功！")

if __name__ == "__main__":
    try:
        create_sentiment_table()
    except Exception as e:
        print(f"❌ 创建失败 (可能表已存在): {e}")
