from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.infra.db.schema_runtime import prepare_db


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    prepare_db()


if __name__ == "__main__":
    main()
