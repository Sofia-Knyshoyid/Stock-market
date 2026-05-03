from __future__ import annotations

import argparse
import os
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Response, Request
from fastapi.responses import RedirectResponse

from .db import connection, initialize_database
from .schemas import BankUpdateRequest, TradeRequest
from .services import trade



@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        initialize_database()
    except Exception as e:
        print(f"[WARN] DB not ready yet: {e}")
    yield

app = FastAPI(title="Simplified Stock Market", lifespan=lifespan)


def wallet_exists(conn, wallet_id: str) -> bool:
    row = conn.execute("SELECT 1 FROM wallets WHERE id = ?", (wallet_id,)).fetchone()
    return row is not None


@app.get("/")
def root():
    return RedirectResponse(url="/docs")

@app.get("/whoami")
def whoami(request: Request):
    return {
        "container": os.getenv("HOSTNAME"),
    }


@app.get("/wallets/{wallet_id}")
def get_wallet(wallet_id: str) -> dict[str, Any]:
    with connection() as conn:
        if not wallet_exists(conn, wallet_id):
            raise HTTPException(status_code=404, detail="Wallet not found")

        rows = conn.execute(
            """
            SELECT stock_name, quantity
            FROM wallet_stocks
            WHERE wallet_id = ? AND quantity > 0
            ORDER BY stock_name
            """,
            (wallet_id,),
        ).fetchall()

        return {
            "id": wallet_id,
            "stocks": [
                {"name": row["stock_name"], "quantity": row["quantity"]}
                for row in rows
            ],
        }


@app.get("/wallets/{wallet_id}/stocks/{stock_name}")
def get_wallet_stock(wallet_id: str, stock_name: str) -> int:
    with connection() as conn:
        if not wallet_exists(conn, wallet_id):
            raise HTTPException(status_code=404, detail="Wallet not found")

        row = conn.execute(
            """
            SELECT quantity FROM wallet_stocks
            WHERE wallet_id = ? AND stock_name = ?
            """,
            (wallet_id, stock_name),
        ).fetchone()

        return 0 if row is None else int(row["quantity"])


@app.get("/stocks")
def get_bank_stocks() -> dict[str, Any]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT stock_name, quantity FROM bank_stocks ORDER BY stock_name"
        ).fetchall()

        return {
            "stocks": [
                {"name": row["stock_name"], "quantity": row["quantity"]}
                for row in rows
            ]
        }


@app.post("/stocks")
def set_bank_stocks(payload: BankUpdateRequest) -> Response:
    seen = set()
    for s in payload.stocks:
        if s.name in seen:
            raise HTTPException(status_code=400, detail="Duplicate stock name")
        seen.add(s.name)

    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE;")
        try:
            conn.execute("DELETE FROM bank_stocks;")
            for s in payload.stocks:
                conn.execute(
                    "INSERT INTO bank_stocks (stock_name, quantity) VALUES (?, ?)",
                    (s.name, s.quantity),
                )
            conn.commit()
        except:
            conn.rollback()
            raise

    return Response(status_code=200)


@app.post("/wallets/{wallet_id}/stocks/{stock_name}")
def trade_stock(wallet_id: str, stock_name: str, payload: TradeRequest):
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE;")
        try:
            trade(conn, wallet_id, stock_name, payload.type)
            conn.commit()
        except HTTPException:
            conn.rollback()
            raise
        except:
            conn.rollback()
            raise

    return Response(status_code=200)


@app.get("/log")
def get_log():
    with connection() as conn:
        rows = conn.execute(
            "SELECT operation_type, wallet_id, stock_name FROM audit_log ORDER BY id ASC"
        ).fetchall()

        return {
            "log": [
                {
                    "type": r["operation_type"],
                    "wallet_id": r["wallet_id"],
                    "stock_name": r["stock_name"],
                }
                for r in rows
            ]
        }



@app.post("/chaos")
def chaos():
    os._exit(1)
    return {"status": "terminating"}


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, required=True)
    return parser


def main():
    args = build_parser().parse_args()

    import uvicorn

    uvicorn.run("app.main:app", host=args.host, port=args.port, workers=1)