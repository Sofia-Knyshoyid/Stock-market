import os

from fastapi.testclient import TestClient

from app.db import DB_PATH, initialize_database, reset_database
from app.main import app


client = TestClient(app)


def setup_module(module):
    if DB_PATH.exists():
        os.remove(DB_PATH)
    initialize_database()


def setup_function(function):
    reset_database()


def test_initial_state_is_empty():
    assert client.get("/stocks").status_code == 200
    assert client.get("/stocks").json() == {"stocks": []}
    assert client.get("/log").json() == {"log": []}


def test_buy_and_sell_flow():
    assert client.post("/stocks", json={"stocks": [{"name": "st1", "quantity": 2}]}).status_code == 200

    assert client.post("/wallets/w1/stocks/st1", json={"type": "buy"}).status_code == 200
    assert client.get("/wallets/w1").json() == {"id": "w1", "stocks": [{"name": "st1", "quantity": 1}]}
    assert client.get("/wallets/w1/stocks/st1").json() == 1
    assert client.get("/stocks").json() == {"stocks": [{"name": "st1", "quantity": 1}]}

    assert client.post("/wallets/w1/stocks/st1", json={"type": "sell"}).status_code == 200
    assert client.get("/wallets/w1").json() == {"id": "w1", "stocks": []}
    assert client.get("/stocks").json() == {"stocks": [{"name": "st1", "quantity": 2}]}

    assert client.get("/log").json() == {
        "log": [
            {"type": "buy", "wallet_id": "w1", "stock_name": "st1"},
            {"type": "sell", "wallet_id": "w1", "stock_name": "st1"},
        ]
    }


def test_failures_return_proper_status_codes_and_do_not_create_wallets():
    assert client.post("/stocks", json={"stocks": [{"name": "st1", "quantity": 0}]}).status_code == 200

    response = client.post("/wallets/w1/stocks/st1", json={"type": "buy"})
    assert response.status_code == 400
    assert client.get("/wallets/w1").status_code == 404

    response = client.post("/wallets/w1/stocks/missing", json={"type": "buy"})
    assert response.status_code == 404
    assert client.get("/wallets/w1").status_code == 404

    response = client.get("/wallets/unknown")
    assert response.status_code == 404


def test_zero_quantity_bank_stocks_are_returned():
    assert client.post("/stocks", json={"stocks": [{"name": "st1", "quantity": 0}]}).status_code == 200
    assert client.get("/stocks").json() == {"stocks": [{"name": "st1", "quantity": 0}]}