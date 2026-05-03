# Simplified Stock Market

## Overview

This service simulates a simplified stock market.

## Components

- **Wallets** – hold stocks  
- **Bank** – central liquidity provider  
- **Audit log** – tracks all successful wallet operations  

## Assumptions

- Stock price is fixed to 1  
- No wallet balance is tracked  
- All operations execute immediately  
- Bank is the only liquidity provider  
- System starts empty (no wallets, no stocks)  

---

## API

### Buy / Sell stock

POST /wallets/{wallet_id}/stocks/{stock_name}

Body:
```json
{ "type": "buy" }
```

Rules:

- 404 if stock does not exist  
- 400 if:
  - no stock in bank (buy)
  - no stock in wallet (sell)  
- 200 on success  
- wallet is created automatically if it does not exist  

---

### Get wallet

GET /wallets/{wallet_id}

---

### Get wallet stock

GET /wallets/{wallet_id}/stocks/{stock_name}

Returns number (e.g. 5)

---

### Get bank stocks

GET /stocks

---

### Set bank stocks

POST /stocks

---

### Audit log

GET /log

- ordered  
- only successful operations  

---

### Chaos endpoint

POST /chaos

Kills the instance handling the request.

---

## Running locally
```
pip install -r requirements.txt
```
```
python -m app --port 8000
```
App available at:
http://localhost:8000

---

## Running with Docker

docker compose up --build

Apps available at:
http://localhost:8000
http://localhost:8001

---

## High Availability

- Multiple instances (docker-compose)
- Each instance runs multiple workers (gunicorn)
- This way, killing one instance doesn't stop the system

---

## Testing

pytest

---

## Design decisions

- SQLite with WAL mode for concurrency
- Transactions for all operations
- Service layer for business logic
- FastAPI for REST API
- Gunicorn for production serving