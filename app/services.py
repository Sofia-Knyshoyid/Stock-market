from __future__ import annotations

import sqlite3
from fastapi import HTTPException


def ensure_wallet(conn: sqlite3.Connection, wallet_id: str) -> None:
    row = conn.execute("SELECT 1 FROM wallets WHERE id = ?", (wallet_id,)).fetchone()
    if row is None:
        conn.execute("INSERT INTO wallets (id) VALUES (?)", (wallet_id,))


def get_bank_stock(conn: sqlite3.Connection, stock_name: str):
    return conn.execute(
        "SELECT quantity FROM bank_stocks WHERE stock_name = ?",
        (stock_name,),
    ).fetchone()


def get_wallet_stock(conn: sqlite3.Connection, wallet_id: str, stock_name: str):
    return conn.execute(
        """
        SELECT quantity FROM wallet_stocks
        WHERE wallet_id = ? AND stock_name = ?
        """,
        (wallet_id, stock_name),
    ).fetchone()


def trade(conn: sqlite3.Connection, wallet_id: str, stock_name: str, op_type: str) -> None:
    ensure_wallet(conn, wallet_id)

    bank_row = get_bank_stock(conn, stock_name)
    if bank_row is None:
        raise HTTPException(status_code=404, detail="Stock not found")

    wallet_row = get_wallet_stock(conn, wallet_id, stock_name)

    if op_type == "buy":
        if int(bank_row["quantity"]) < 1:
            raise HTTPException(status_code=400, detail="No stock available in the bank")

        conn.execute(
            "UPDATE bank_stocks SET quantity = quantity - 1 WHERE stock_name = ?",
            (stock_name,),
        )

        if wallet_row is None:
            conn.execute(
                "INSERT INTO wallet_stocks (wallet_id, stock_name, quantity) VALUES (?, ?, 1)",
                (wallet_id, stock_name),
            )
        else:
            conn.execute(
                "UPDATE wallet_stocks SET quantity = quantity + 1 WHERE wallet_id = ? AND stock_name = ?",
                (wallet_id, stock_name),
            )

    else:
        if wallet_row is None or int(wallet_row["quantity"]) < 1:
            raise HTTPException(status_code=400, detail="No stock available in the wallet")

        if int(wallet_row["quantity"]) == 1:
            conn.execute(
                "DELETE FROM wallet_stocks WHERE wallet_id = ? AND stock_name = ?",
                (wallet_id, stock_name),
            )
        else:
            conn.execute(
                "UPDATE wallet_stocks SET quantity = quantity - 1 WHERE wallet_id = ? AND stock_name = ?",
                (wallet_id, stock_name),
            )

        conn.execute(
            "UPDATE bank_stocks SET quantity = quantity + 1 WHERE stock_name = ?",
            (stock_name,),
        )

    conn.execute(
        """
        INSERT INTO audit_log (operation_type, wallet_id, stock_name)
        VALUES (?, ?, ?)
        """,
        (op_type, wallet_id, stock_name),
    )