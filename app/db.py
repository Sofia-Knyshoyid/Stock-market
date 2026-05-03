from __future__ import annotations

import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from threading import Lock

_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "stock_market.sqlite3"
DB_PATH = Path(os.getenv("STOCK_MARKET_DB", _DEFAULT_DB_PATH))

_INIT_LOCK = Lock()


def _connect(retries: int = 10, delay: float = 0.5) -> sqlite3.Connection:
    last_err = None

    for _ in range(retries):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA busy_timeout = 5000;")
            return conn
        except Exception as e:
            last_err = e
            time.sleep(delay)

    raise RuntimeError(f"DB connection failed after retries: {last_err}")


@contextmanager
def connection() -> sqlite3.Connection:
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def initialize_database() -> None:
    with _INIT_LOCK:
        with connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS wallets (
                    id TEXT PRIMARY KEY
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS wallet_stocks (
                    wallet_id TEXT NOT NULL,
                    stock_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL CHECK(quantity >= 0),
                    PRIMARY KEY (wallet_id, stock_name),
                    FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE CASCADE
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bank_stocks (
                    stock_name TEXT PRIMARY KEY,
                    quantity INTEGER NOT NULL CHECK(quantity >= 0)
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT NOT NULL,
                    wallet_id TEXT NOT NULL,
                    stock_name TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )


def reset_database() -> None:
    with connection() as conn:
        conn.execute("DELETE FROM audit_log;")
        conn.execute("DELETE FROM wallet_stocks;")
        conn.execute("DELETE FROM wallets;")
        conn.execute("DELETE FROM bank_stocks;")