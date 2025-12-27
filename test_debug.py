print("DEBUG: Script started")
import sys
import logging

try:
    print("DEBUG: Importing logger")
    from utils.logger import logger
    logger.info("Logger initialized")
except Exception as e:
    print(f"DEBUG: Logger import failed: {e}")

try:
    print("DEBUG: Importing ccxt")
    import ccxt
    print(f"DEBUG: CCXT version: {ccxt.__version__}")
    exchange = ccxt.binance()
    print("DEBUG: Exchange instantiated")
except Exception as e:
    print(f"DEBUG: CCXT failed: {e}")

print("DEBUG: Script finished")
