"""
API 端点测试脚本
"""
import unittest
import json
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.app import app
from models.database import init_db

class HeimdallAPITestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        init_db()  # 确保数据库已初始化

    def test_status(self):
        """测试系统状态接口"""
        response = self.app.get('/api/status')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')
        self.assertIn('exchange', data)

    def test_config(self):
        """测试配置接口"""
        response = self.app.get('/api/config')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('symbols', data)
        self.assertIn('indicators', data)

    def test_realtime(self):
        """测试实时分析接口 (包括带斜杠的交易对)"""
        # Test generic symbol
        response = self.app.get('/api/realtime/BTC%2FUSDT')
        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertEqual(data['symbol'], 'BTC/USDT')
            self.assertIn('current_price', data)
            self.assertIn('indicators', data)
        else:
            # If network fails (no internet for CCXT), it might return 500 but still reach the endpoint.
            # If it returns 404, that's the bug we fixed.
            self.assertNotEqual(response.status_code, 404, "Endpoint not found (Routing issue)")

    def test_backtest_life_cycle(self):
        """测试回测完整生命周期: 启动 -> 列表 -> 详情"""
        # 1. Start Backtest (Short range for speed)
        payload = {
            'symbol': 'BTC/USDT',
            'days': 1,
            'use_ai': False
        }
        response = self.app.post('/api/backtest/start', 
                                 data=json.dumps(payload),
                                 content_type='application/json')
        
        # Note: Depending on implementation, start might be blocking or async.
        # In our current implementation, backtester.run_backtest is BLOCKING.
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        backtest_id = data['backtest_id']
        self.assertIsNotNone(backtest_id)
        
        # 2. Get List
        response = self.app.get('/api/backtest/list')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertTrue(any(item['id'] == backtest_id for item in data))
        
        # 3. Get Details
        response = self.app.get(f'/api/backtest/{backtest_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['id'], backtest_id)
        self.assertEqual(data['symbol'], 'BTC/USDT')
        self.assertIn('signals', data)

    def test_sentiment_endpoint(self):
        response = self.app.get('/api/market/sentiment')
        # Dependent on external API, might flake or return error if offline, but endpoint exists
        self.assertIn(response.status_code, [200, 500]) 
        
    def test_dca_simulation(self):
        payload = {
            'symbol': 'BTC/USDT',
            'days': 30,
            'amount': 100
        }
        # This will trigger 1h fetching, might take a moment
        response = self.app.post('/api/tools/dca_simulate', json=payload)
        
        if response.status_code == 200:
            data = response.get_json()
            self.assertIn('final_value', data)
            self.assertIn('roi_percent', data)
        else:
            # If no data available, it returns 400
            self.assertIn(response.status_code, [200, 400])

if __name__ == '__main__':
    unittest.main()
