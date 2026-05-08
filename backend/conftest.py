"""
Root conftest.py — pytest configuration for the backend test suite.

Mocks asyncpg at the top-level so that modules importing SQLAlchemy's
asyncpg dialect (core/database.py) can be imported in unit tests without
requiring a live PostgreSQL connection or the asyncpg driver installed.

This file is discovered by pytest before any test module is collected,
so sys.modules patching happens before imports in test files.
"""
import sys
import types


def _mock_asyncpg() -> None:
    """Inject a minimal asyncpg stub so SQLAlchemy's asyncpg dialect loads."""
    if "asyncpg" in sys.modules:
        return  # already available (real driver or previously mocked)

    stub = types.ModuleType("asyncpg")

    # SQLAlchemy's asyncpg dialect checks for these attributes at import time.
    # We only need enough to satisfy the import; no real DB behaviour needed.
    stub.connect = None  # type: ignore[attr-defined]
    stub.Connection = object  # type: ignore[attr-defined]
    stub.Record = object  # type: ignore[attr-defined]
    stub.exceptions = types.ModuleType("asyncpg.exceptions")  # type: ignore[attr-defined]

    sys.modules["asyncpg"] = stub
    sys.modules["asyncpg.exceptions"] = stub.exceptions  # type: ignore[attr-defined]


_mock_asyncpg()
