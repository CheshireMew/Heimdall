# Global Timezone Refactoring Plan

## Goal Description

Expand timezone support from just the DCA module to the entire project. This ensures that logs, backtests, and data synchronization (Sentiment) all respect the user's configured timezone (default: Asia/Shanghai), even if the underlying server/OS is in UTC.

## User Review Required

> [!NOTE]
> **Logging Time**: Application logs will now explicitly match the configured timezone.
> **Backtest Defaults**: Default start/end times for backtests will use current **Local Time** instead of System Time.

## Proposed Changes

### 1. Logger

#### [MODIFY] [logger.py](file:///e:/Work/Code/Heimdall/utils/logger.py)

- Import `TimeManager`.
- Override `logging.Formatter.converter` to use `TimeManager`'s timezone logic.
- This ensures all logs (INFO, ERROR) print the correct local time.

### 2. Core Modules

#### [MODIFY] [backtester.py](file:///e:/Work/Code/Heimdall/core/backtester.py)

- Replace `datetime.now()` with `TimeManager.get_now()`.
- When converting timestamps `datetime.fromtimestamp()`, ensure timezone awareness is used if applicable, or convert to UTC then Local.

#### [MODIFY] [market_provider.py](file:///e:/Work/Code/Heimdall/core/market_provider.py)

- (Optional) Ensure logging metrics use consistent time. (Handled by Logger update).
- Any internal logic relying on `time.time()` (duration calculation) is fine.
- Any logic relying on "Start of Day" should use `TimeManager`.

### 3. Services

#### [MODIFY] [sentiment_service.py](file:///e:/Work/Code/Heimdall/services/sentiment_service.py)

- Replace `datetime.now().date()` with `TimeManager.get_now().date()`.
- Ensure parsed API timestamps are treated correctly (UTC vs Local).

## Verification Plan

### Automated Tests

- **Run `test_timezone.py`**: Ensure basic Utils still work.
- **Run `dca_calculator.py`**: Ensure regerssion testing.
- **New Test**: Check Logger output time (Manual or simple script).

### Manual Verification

1. **Check Logs**: Run `python main.py` or any script, observe the timestamp in the console. It should match the user's wall clock (Beijing Time).
2. **Sentiment Sync**: Run sentiment sync, ensure it judges "Today" correctly.
