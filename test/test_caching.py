
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from app.services.market.exchange_gateway import ExchangeGateway
from app.services.market.kline_store import KlineStore
from app.services.market.market_data_service import MarketDataService
from app.infra.db.database import get_session
from app.infra.db.schema_runtime import init_db
from app.infra.db.schema import Kline

class CachingTestCase(unittest.TestCase):
    def setUp(self):
        # Use a test DB or just ensure we clean up
        init_db()
        self.provider = MarketDataService(
            exchange_gateway=ExchangeGateway(),
            kline_store=KlineStore(),
        )
        self.symbol = 'BTC/USDT'
        self.timeframe = '1h'
        
        # Clean up existing Klines for test symbol
        session = get_session()
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
        session = get_session()
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
        # Optional: Clean up
        pass

if __name__ == '__main__':
    unittest.main()
