"""Initialize the PostgreSQL/PGVector tables used by the knowledge service."""

from __future__ import annotations

import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from storage.database.db import get_engine, get_session
from storage.database.document_manager import DocumentManager
from storage.database.shared.model import Base


def main() -> None:
    """Create application tables and the default knowledge collection."""
    if not os.getenv("PGDATABASE_URL"):
        raise RuntimeError("PGDATABASE_URL must be set before initialization")

    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    db = get_session()
    try:
        manager = DocumentManager()
        if manager.collection_exists(db, "knowledge_base"):
            print("knowledge_base already exists")
        else:
            manager.create_collection(db, collection_name="knowledge_base")
            print("knowledge_base created")
    finally:
        db.close()


if __name__ == "__main__":
    main()
