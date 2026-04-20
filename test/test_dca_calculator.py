import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.schemas.market import MarketIndexHistoryResponse, build_ohlcv_points

from app.services.tools.dca_service import DCAService as DCACalculator


class TestValueAveraging(unittest.TestCase):
    def setUp(self):
        self.calculator = DCACalculator(
            market_data_service=MagicMock(),
            sentiment_service=MagicMock(),
            index_data_service=MagicMock(),
        )
        self.calculator.index_data_service.get_instrument.return_value = None

    def test_value_averaging_zero_invested(self):
        print("\n--- Testing Value Averaging Zero Invested Scenario ---")

        d1 = datetime(2024, 1, 1, 23, 0, tzinfo=timezone.utc)
        d2 = datetime(2024, 1, 2, 23, 0, tzinfo=timezone.utc)
        d3 = datetime(2024, 1, 3, 23, 0, tzinfo=timezone.utc)

        def make_kline(dt, price):
            ts = int(dt.timestamp() * 1000)
            return [ts, price, price, price, price, 1000]

        mock_data = [
            make_kline(d1, 100.0),
            make_kline(d2, 300.0),
            make_kline(d3, 1000.0),
        ]

        self.calculator.market_data_service.fetch_ohlcv_range.return_value = mock_data
        self.calculator.market_data_service.get_kline_data.return_value = [[
            int(d3.timestamp() * 1000), 1000.0, 1000.0, 1000.0, 1000.0, 1000
        ]]

        result = self.calculator.calculate_dca(
            symbol='BTC/USDT',
            start_date_str='2024-01-01',
            end_date_str='2024-01-03',
            daily_investment=100.0,
            target_time_str='23:00',
            timezone='UTC',
            strategy='value_averaging',
            strategy_params={'fee_rate': 0},
        )

        if 'error' in result:
            print(f"Error returned: {result['error']}")
            self.fail("Calculator returned error")

        print("Result Summary:")
        print(f"Total Invested: {result['total_invested']}")
        print(f"Final Value: {result['final_value']}")
        print(f"ROI: {result['roi']}%")
        print(f"Profit/Loss: {result['profit_loss']}")

        for item in result['history']:
            print(
                f"Date: {item['date']}, Price: {item['price']}, Invested: {item['invested']}, "
                f"Value: {item['value']}, ROI: {item['roi']}%"
            )

        h1 = result['history'][1]
        self.assertEqual(h1['invested'], 0.0)
        self.assertEqual(h1['roi'], 0.0)

        h2 = result['history'][2]
        self.assertTrue(h2['invested'] < 0)
        self.assertEqual(h2['roi'], 0.0)

    def test_index_standard_dca_uses_daily_history(self):
        index_service = MagicMock()
        index_service.get_instrument.return_value = object()
        index_service.get_pricing_history.return_value = MarketIndexHistoryResponse(
            symbol="HK_HSI",
            name="Hang Seng Index",
            market="HK",
            currency="HKD",
            native_currency="HKD",
            timeframe="1d",
            source="test",
            price_basis="proxy_etf",
            pricing_symbol="02800",
            pricing_name="Tracker Fund of Hong Kong",
            pricing_currency="USD",
            is_close_only=False,
            count=3,
            data=build_ohlcv_points([
                [1704067200000, 100.0, 100.0, 100.0, 100.0, 0],
                [1704153600000, 110.0, 110.0, 110.0, 110.0, 0],
                [1704240000000, 120.0, 120.0, 120.0, 120.0, 0],
            ]),
        )
        calculator = DCACalculator(
            market_data_service=MagicMock(),
            sentiment_service=MagicMock(),
            index_data_service=index_service,
        )

        result = calculator.calculate_dca(
            symbol='HK_HSI',
            start_date_str='2024-01-01',
            end_date_str='2024-01-03',
            daily_investment=100.0,
            target_time_str='23:00',
            timezone='Asia/Shanghai',
            strategy='standard',
            strategy_params={'fee_rate': 0},
        )

        self.assertNotIn('error', result)
        self.assertEqual(result['asset_class'], 'index')
        self.assertEqual(result['total_days'], 3)
        self.assertEqual(result['current_price'], 120.0)
        self.assertEqual(result['price_basis'], 'proxy_etf')
        self.assertEqual(result['pricing_symbol'], '02800')
        self.assertEqual(result['pricing_currency'], 'USD')


if __name__ == '__main__':
    unittest.main()
