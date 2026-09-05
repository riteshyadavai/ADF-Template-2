"""Asset Factory smoke: real SQL (sqlite), PII, in-memory vector sync.

Requires: ASSETS_ENABLED=true and `uv sync --extra asset-factory`.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile

from config.settings import AssetsSettings, Settings
from factories.assets.factory import make_asset_bundle


def _status(result: object) -> str:
    status = getattr(result, "status", "")
    return status.value if hasattr(status, "value") else str(status)


def _require_success(result: object, label: str) -> None:
    payload = result.to_dict() if hasattr(result, "to_dict") else result
    print(label, payload)
    if _status(result) != "success":
        raise SystemExit(f"{label} failed")


def main() -> None:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, customer TEXT)")
    conn.execute("INSERT INTO orders (customer) VALUES ('Acme')")
    conn.commit()
    conn.close()

    settings = Settings(
        assets=AssetsSettings(
            enabled=True,
            sql_db_url=f"sqlite:///{path}",
            sql_read_only=True,
            sql_max_rows=50,
        )
    )
    bundle = make_asset_bundle(settings)
    if not bundle.enabled:
        raise SystemExit("ASSETS_ENABLED=true is required")

    select = bundle.sql().safe_run(query="SELECT * FROM orders")
    _require_success(select, "sql_select")
    blocked = bundle.sql().safe_run(query="DELETE FROM orders")
    print("sql_delete_blocked", blocked.to_dict() if hasattr(blocked, "to_dict") else blocked)
    if _status(blocked) == "success":
        raise SystemExit("read_only SQL should block DELETE")

    pii = bundle.pii().safe_run(text="Contact jane@acme.com", direction="input")
    _require_success(pii, "pii")

    synced = bundle.vector_sync().safe_run(
        documents=[{"id": "doc-1", "text": "Reusable agent assets hydrate from config."}]
    )
    _require_success(synced, "vector_sync")
    os.remove(path)


if __name__ == "__main__":
    main()
