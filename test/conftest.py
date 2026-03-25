"""
Shared pytest fixtures for Heimdall tests.
"""
from pathlib import Path
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.infra.db.schema import Base


@pytest.fixture(scope="session")
def db_engine():
    """Create an in-memory SQLite engine for testing (shared across all tests)."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Provide a transactional database session that rolls back after each test."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def mock_kline_data():
    """Sample OHLCV data for testing: [timestamp_ms, open, high, low, close, volume]."""
    base_ts = 1700000000000  # Nov 2023
    return [
        [base_ts + i * 3600000, 40000 + i * 10, 40050 + i * 10, 39950 + i * 10, 40000 + i * 15, 100 + i]
        for i in range(300)
    ]
