import requests
import json
import time
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import insert
from models.database import session_scope
from models.schema import Sentiment
from utils.logger import logger
from utils.time_manager import TimeManager
from config import settings

class SentimentService:
    def __init__(self):
        self.api_url = "https://api.alternative.me/fng/"
        
    def sync_data(self):
        """
        同步最新的恐慌贪婪指数数据
        """
        try:
            # 1. 检查数据库中最新的数据日期
            latest_date = self._get_latest_date()
            
            # 如果是今天，或者昨天刚更新过，也许不需要全量更新，但 API limit=0 开销不大
            # 为了简单，如果数据为空或最新数据不是今天，就尝试更新
            today = TimeManager.get_now().date()
            
            if latest_date and latest_date.date() >= today:
                # logger.info("情绪数据已是最新")
                return

            logger.info("正在更新恐慌贪婪指数数据...")
            
            # 2. 从 API 获取此数据 (limit=0 获取全部历史)
            response = requests.get(f"{self.api_url}?limit=0")
            if response.status_code != 200:
                logger.error(f"无法获取 F&G 数据: {response.text}")
                return
                
            data = response.json()
            if 'data' not in data:
                return
                
            fng_data = data['data']
            
            # 3. 批量插入/更新
            records = []
            for item in fng_data:
                # API returns date string e.g. "2024-03-20" if date_format=cn? 
                # docs say "timestamp" is string epoch. let's verify format.
                # user provided step 189 output shows "timestamp": "1769385600"
                
                ts = int(item['timestamp'])
                dt = datetime.fromtimestamp(ts)
                
                records.append({
                    'date': dt,
                    'value': int(item['value']),
                    'classification': item['value_classification'],
                    'timestamp': ts
                })
            
            if not records:
                return

            with session_scope() as session:
                # 使用 PostgreSQL 的 ON CONFLICT DO UPDATE (Upsert)
                # 或 SqlAlchemy 的 merge (比较慢但简单)
                # 这里为了性能使用 bulk_insert_mappings 但需处理冲突？
                # 简单策略：先查询存在的，只插入不存在的？或者直接全部 merge
                
                # 优化：倒序遍历，如果数据库已有该日期且 value 一致，跳过？
                # 由于这是低频操作，使用 merge 循环即可，毕竟历史数据只有几千条
                
                # 更好的方式：找出差异
                # 这里简单实现：只插入数据库没有的日期
                
                # 获取数据库现有所有日期
                existing_dates = {
                    r[0].date() for r in session.query(Sentiment.date).all()
                }
                
                new_records = []
                for r in records:
                    if r['date'].date() not in existing_dates:
                        new_records.append(Sentiment(**r))
                        
                if new_records:
                    session.bulk_save_objects(new_records)
                    logger.info(f"已同步 {len(new_records)} 条情绪数据")
                else:
                    logger.info("情绪数据已同步")
                    
        except Exception as e:
            logger.error(f"同步情绪数据失败: {e}")

    def _get_latest_date(self):
        with session_scope() as session:
            latest = session.query(Sentiment).order_by(Sentiment.date.desc()).first()
            return latest.date if latest else None

    def get_sentiment_history(self, start_date=None, end_date=None):
        """读取历史数据"""
        # 确保数据同步
        self.sync_data()
        
        with session_scope() as session:
            query = session.query(Sentiment).order_by(Sentiment.date.asc())
            if start_date:
                query = query.filter(Sentiment.date >= start_date)
            if end_date:
                query = query.filter(Sentiment.date <= end_date)
                
            return {r.date.strftime('%Y-%m-%d'): r.value for r in query.all()}

    def get_fear_greed_index(self):
        """获取最新一期的恐慌贪婪指数"""
        # 确保数据同步
        self.sync_data()
        
        with session_scope() as session:
            latest = session.query(Sentiment).order_by(Sentiment.date.desc()).first()
            if latest:
                return {
                    "value": latest.value,
                    "value_classification": latest.classification,
                    "timestamp": latest.timestamp
                }
            return None

sentiment_service = SentimentService()
