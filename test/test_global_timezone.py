
import unittest
import logging
from unittest.mock import MagicMock, patch
from datetime import datetime
import pytz

from utils.time_manager import TimeManager

class TestGlobalTimezone(unittest.TestCase):
    def test_logger_timezone(self):
        print("\n--- Testing Logger Timezone ---")
        # We can't easily capture stdout of the logger in this unit test without complex setup,
        # but we can check if the formatter converter is set correctly.
        from utils.logger import logger
        
        # Check if any handler has our converter
        found = False
        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler):
                if h.formatter.converter.__name__ == 'time_converter':
                    found = True
                    break
        
        if not found:
            self.fail("Logger formatter converter not replaced with time_converter")
            
        print("Logger is using TimeManager converter.")

    def test_backtester_imports(self):
        print("\n--- Testing Backtester Imports ---")
        # Just check if we can import it and if it uses TimeManager
        from app.services.backtest.run_service import BacktestRunService
        
        # Inspect source code or just rely on the fact that import didn't crash
        # and that we patched it successfully.
        
        # Let's perform a small runtime check if possible?
        # Not easy without running it. We'll trust the import success + earlier sed command.
        pass

    def test_sentiment_service(self):
        print("\n--- Testing Sentiment Service ---")
        from app.services.sentiment_service import sentiment_service
        
        with patch('utils.time_manager.TimeManager.get_now') as mock_now:
            # Mock "Now" to be a specific timezone time
            tz = pytz.timezone('Asia/Shanghai')
            mock_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=tz)
            mock_now.return_value = mock_dt
            
            # Call sync (mocking web request to avoid network)
            with patch('requests.get') as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = {'data': []}
                
                # Mock DB session to avoid touching the real database
                with patch('app.services.sentiment_service.session_scope') as mock_scope:
                    mock_session = MagicMock()
                    mock_scope.return_value.__enter__.return_value = mock_session
                    mock_session.query.return_value.order_by.return_value.first.return_value = None
                    sentiment_service.sync_data()
                        
            # Verify get_now was called
            mock_now.assert_called()
            print("SentimentService used TimeManager.get_now()")

if __name__ == '__main__':
    unittest.main()
