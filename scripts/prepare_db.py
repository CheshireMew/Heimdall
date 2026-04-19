from __future__ import annotations

import logging

from app.infra.db.database import prepare_db


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    prepare_db()


if __name__ == "__main__":
    main()
