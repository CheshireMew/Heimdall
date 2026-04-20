
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.infra.db import build_database_runtime
from app.infra.db.schema import Base
from app.services.market.exchange_gateway import ExchangeGateway
from app.services.market.kline_store import KlineStore
from app.services.market.market_data_service import MarketDataService
from app.infra.db.schema import Kline
from config.settings import AppSettings

class CachingTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "cache.db"
        self.database_runtime = build_database_runtime(
            AppSettings(DATABASE_URL=f"sqlite:///{database_path.as_posix()}")
        )
        Base.metadata.create_all(self.database_runtime.engine)
        self.provider = MarketDataService(
            exchange_gateway=ExchangeGateway(),
            kline_store=KlineStore(database_runtime=self.database_runtime),
        )
        self.symbol = 'BTC/USDT'
        self.timeframe = '1h'
        
        # Clean up existing Klines for test symbol
        session = self.database_runtime.get_session()
        session.query(Kline).filter_by(symbol=self.symbol).delete()
        session.commit()
        session.close()

    def test_caching_flow(self):
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=10)
        
        # 1. First fetch: Should call exchange
        print("\n[Test] First fetch (empty cache)...")
        data1 = self.provider.fetch_ohlcv_range(self.symbol, self.timeframe, start_date, end_date)
        self.assertTrue(len(data1) > 0)
        
        # Verify DB has data
        session = self.database_runtime.get_session()
        count = session.query(Kline).filter_by(symbol=self.symbol).count()
        print(f"[Test] DB count after first fetch: {count}")
        self.assertTrue(count >= len(data1))
        session.close()

        exact_start = datetime.fromtimestamp(data1[0][0] / 1000)
        exact_end = datetime.fromtimestamp(data1[-1][0] / 1000)
        
        print("[Test] Second fetch (full cache hit)...")
        with patch.object(
            self.provider.exchange_gateway,
            'fetch_ohlcv',
            wraps=self.provider.exchange_gateway.fetch_ohlcv,
        ) as mock_exchange_fetch:
            data2 = self.provider.fetch_ohlcv_range(self.symbol, self.timeframe, exact_start, exact_end)

            self.assertEqual(len(data1), len(data2))
            self.assertEqual(data1[0][0], data2[0][0])
            self.assertEqual(mock_exchange_fetch.call_count, 0)
            print("[Test] Success: No exchange calls made.")
                
    def tearDown(self):
        self.database_runtime.dispose()
        self.temp_dir.cleanup()

if __name__ == '__main__':
    unittest.main()
