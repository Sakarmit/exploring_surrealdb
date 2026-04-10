"""
ingestion/surreal_client.py
Thin wrapper around the SurrealDB Python SDK (surrealdb>=0.3).
Falls back to the REST HTTP API if the SDK is unavailable.
"""

from __future__ import annotations
import json
import os
from typing import Any


# ── Try the official SDK first ────────────────────────────────────────────────
try:
    from surrealdb import Surreal as _Surreal          # type: ignore
    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False


class SurrealClient:
    """
    Async-friendly SurrealDB client.

    Usage (sync helper via asyncio.run):
        from ingestion.surreal_client import SurrealClient
        client = SurrealClient()
        client.connect_sync()
        client.create_sync("lecture", {...})
        client.close_sync()
    """

    def __init__(
        self,
        url: str = "http://localhost:8000",
        user: str = "root",
        password: str = "root",
        namespace: str = "education",
        database: str = "learning_management_db",
    ):
        self.url = url
        self.user = user
        self.password = password
        self.namespace = namespace
        self.database = database
        self._db = None          # SDK handle
        self._session = None     # requests.Session for HTTP fallback

    # ── SDK path ──────────────────────────────────────────────────────────────

    async def connect(self):
        if not _SDK_AVAILABLE:
            raise RuntimeError("surrealdb SDK not installed. Run: pip install surrealdb")
        self._db = _Surreal(self.url)
        await self._db.connect()
        await self._db.signin({"user": self.user, "pass": self.password})
        await self._db.use(self.namespace, self.database)

    async def create(self, table: str, data: dict) -> Any:
        return await self._db.create(table, data)

    async def query(self, sql: str, vars: dict | None = None) -> Any:
        return await self._db.query(sql, vars or {})

    async def close(self):
        if self._db:
            await self._db.close()

    # ── Sync convenience wrappers (uses asyncio.run) ──────────────────────────

    def connect_sync(self):
        import asyncio
        asyncio.run(self._connect_and_store())

    async def _connect_and_store(self):
        await self.connect()

    def create_sync(self, table: str, data: dict) -> Any:
        import asyncio
        return asyncio.run(self.create(table, data))

    def query_sync(self, sql: str, vars: dict | None = None) -> Any:
        import asyncio
        return asyncio.run(self.query(sql, vars))

    def close_sync(self):
        import asyncio
        asyncio.run(self.close())

    # ── HTTP fallback (no SDK required) ──────────────────────────────────────

    def _http_headers(self) -> dict:
        import base64
        token = base64.b64encode(f"{self.user}:{self.password}".encode()).decode()
        return {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            # "NS": self.namespace,
            # "DB": self.database,
            "surreal-ns": self.namespace,
            "surreal-db": self.database,
        }

    def http_create(self, table: str, data: dict) -> Any:
        """Create a record via HTTP REST API (no SDK needed)."""
        import requests  # type: ignore
        record_id = data.get("id", "")
        # Strip table prefix if present (e.g. "lecture:notes1" -> "notes1")
        if ":" in record_id:
            record_id = record_id.split(":", 1)[1]
        url = f"{self.url}/key/{table}/{record_id}"
        payload = {k: v for k, v in data.items() if k != "id"}
        resp = requests.post(url, headers=self._http_headers(), json=payload)
        resp.raise_for_status()
        return resp.json()

    def http_query(self, sql: str) -> Any:
        """Run a SurrealQL query via HTTP REST API."""
        import requests  # type: ignore
        resp = requests.post(
            f"{self.url}/sql",
            headers=self._http_headers(),
            data=sql,
        )
        resp.raise_for_status()
        return resp.json()

    def execute_schema_file(self, schema_path: str):
        """Execute a .surql schema file via HTTP."""
        with open(schema_path, "r") as f:
            sql = f.read()
        return self.http_query(sql)
