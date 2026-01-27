
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone

# Add root to sys.path
sys.path.append(os.getcwd())

from core.dca_calculator import DCACalculator

class TestValueAveraging(unittest.TestCase):
    def setUp(self):
        self.calculator = DCACalculator()
        self.calculator.market_provider = MagicMock()
        
    def test_value_averaging_zero_invested(self):
        print("\n--- Testing Value Averaging Zero Invested Scenario ---")
        
        # Scenario: 
        # Day 1: Price 100. Target 100. Invest 100.
        # Day 2: Price 300. Target 200. Value 300. Sell 100. Invested 0.
        # Day 3: Price 1000. Target 300. Value 666. Sell 366. Invested -3666.
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 3)
        
        # Mock fetch_ohlcv_range return value
        # Format: [timestamp, open, high, low, close, volume]
        # timestamps need to be ms
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 3)
        
        # Mock fetch_ohlcv_range return value
        # Format: [timestamp, open, high, low, close, volume]
        # timestamps need to be ms
        
        # Use UTC for consistency with CCXT/Pandas default
        d1 = datetime(2024, 1, 1, 23, 0, tzinfo=timezone.utc)
        d2 = datetime(2024, 1, 2, 23, 0, tzinfo=timezone.utc)
        d3 = datetime(2024, 1, 3, 23, 0, tzinfo=timezone.utc)

        def make_kline(dt, price):
            ts = int(dt.timestamp() * 1000)
            return [ts, price, price, price, price, 1000]
            
        mock_data = [
            make_kline(d1, 100.0),
            make_kline(d2, 300.0),
            make_kline(d3, 1000.0)
        ]

        
        self.calculator.market_provider.fetch_ohlcv_range.return_value = mock_data
        
        # Mock get_kline_data for current price check at end
        self.calculator.market_provider.get_kline_data.return_value = [[
             int(d3.timestamp() * 1000), 1000.0, 1000.0, 1000.0, 1000.0, 1000
        ]]

        result = self.calculator.calculate_dca(
            symbol='BTC/USDT',
            start_date_str='2024-01-01',
            end_date_str='2024-01-03',
            daily_investment=100.0,
            target_time_str='23:00',
            strategy='value_averaging'
        )
        
        if 'error' in result:
             print(f"Error returned: {result['error']}")
             self.fail("Calculator returned error")
             
        print("Result Summary:")
        print(f"Total Invested: {result['total_invested']}")
        print(f"Final Value: {result['final_value']}")
        print(f"ROI: {result['roi']}%")
        print(f"Profit/Loss: {result['profit_loss']}")
        
        for h in result['history']:
             print(f"Date: {h['date']}, Price: {h['price']}, Invested: {h['invested']}, Value: {h['value']}, ROI: {h['roi']}%")
             
        # Assertions
        # Day 2 (Index 1): Invested should be 0. ROI should be 0 (as per our fix) or handled.
        h1 = result['history'][1]
        self.assertEqual(h1['invested'], 0.0)
        self.assertEqual(h1['roi'], 0.0) # Check if our fix works
        
        # Day 3 (Index 2): Invested negative.
        h2 = result['history'][2]
        self.assertTrue(h2['invested'] < 0)
        self.assertEqual(h2['roi'], 0.0) # Check if our fix works for negative
        
if __name__ == '__main__':
    unittest.main()
