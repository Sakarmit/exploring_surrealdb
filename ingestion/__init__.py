"""Ingestion package."""
from .surreal_client import SurrealClient
from .ingest import run as ingest_all

__all__ = ["SurrealClient", "ingest_all"]
