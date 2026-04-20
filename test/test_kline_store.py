from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.market.kline_store import KlineStore


class FailingSession:
    def __init__(self) -> None:
        self.bind = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
        self.rollback_count = 0

    def execute(self, _statement) -> None:
        raise RuntimeError("value too long for type character varying(20)")

    def rollback(self) -> None:
        self.rollback_count += 1


def test_kline_cache_save_failure_is_visible_to_caller():
    session = FailingSession()

    with pytest.raises(RuntimeError, match="value too long"):
        KlineStore(database_runtime=object())._save_with_session(
            session,
            "proxy:US:NASDAQ100:QQQ",
            "1d",
            [[1775779200000, 611.84, 613.67, 609.58, 611.07, 34038526.0]],
        )

    assert session.rollback_count == 1
