# server.py
# Mock Trading Platform Server
# - FastAPI
# - In-memory users / markets
# - Random market movement
# - Multiple concurrent clients supported

import threading
import time
import random
import uuid
from typing import Dict

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

# -----------------------
# App setup
# -----------------------
app = FastAPI(title="Mock Trading Server")

# -----------------------
# Data storage (in-memory)
# -----------------------
USERS: Dict[str, dict] = {}        # username -> {password, cash, positions}
TOKENS: Dict[str, str] = {}        # token -> username
MARKETS: Dict[str, dict] = {}      # symbol -> {name, price}

STARTING_CASH = 10_000.0


# -----------------------
# Models
# -----------------------
class AuthRequest(BaseModel):
    username: str
    password: str


class OrderRequest(BaseModel):
    symbol: str
    side: str
    qty: float


# -----------------------
# Auth helpers
# -----------------------
def require_user(auth: str | None) -> str:
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing auth token")

    token = auth.split()[1]
    user = TOKENS.get(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


# -----------------------
# Endpoints
# -----------------------
@app.post("/register")
def register(req: AuthRequest):
    if req.username in USERS:
        raise HTTPException(status_code=400, detail="User already exists")

    USERS[req.username] = {
        "password": req.password,
        "cash": STARTING_CASH,
        "positions": {},
    }
    return {"ok": True}


@app.post("/login")
def login(req: AuthRequest):
    user = USERS.get(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = str(uuid.uuid4())
    TOKENS[token] = req.username
    return {"token": token}


@app.get("/markets")
def markets(authorization: str | None = Header(default=None)):
    require_user(authorization)
    return {
        "markets": [
            {"symbol": s, "name": m["name"], "price": m["price"]}
            for s, m in MARKETS.items()
        ]
    }


@app.get("/account")
def account(authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    u = USERS[user]
    return {
        "cash": u["cash"],
        "positions": u["positions"],
    }


@app.post("/order")
def order(req: OrderRequest, authorization: str | None = Header(default=None)):
    user = require_user(authorization)

    if req.symbol not in MARKETS:
        raise HTTPException(status_code=400, detail="Unknown symbol")

    if req.qty <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be > 0")

    side = req.side.upper()
    if side not in ("BUY", "SELL"):
        raise HTTPException(status_code=400, detail="Side must be BUY or SELL")

    price = MARKETS[req.symbol]["price"]
    u = USERS[user]
    pos = u["positions"].get(req.symbol, 0.0)

    if side == "BUY":
        cost = price * req.qty
        if u["cash"] < cost:
            return {"ok": False, "message": "Insufficient cash"}
        u["cash"] -= cost
        u["positions"][req.symbol] = pos + req.qty

    else:  # SELL
        if pos < req.qty:
            return {"ok": False, "message": "Insufficient position"}
        u["cash"] += price * req.qty
        u["positions"][req.symbol] = pos - req.qty

    return {"ok": True, "message": f"{side} {req.qty} {req.symbol} @ {price:.4f}"}


# -----------------------
# Market simulation
# -----------------------
def market_simulator():
    while True:
        time.sleep(1)
        for m in MARKETS.values():
            drift = random.uniform(-0.5, 0.5)
            m["price"] = max(0.01, m["price"] + drift)


# -----------------------
# Bootstrap markets
# -----------------------
def init_markets():
    symbols = {
        "BTC-USD": "Bitcoin",
        "ETH-USD": "Ethereum",
        "OIL": "Crude Oil",
        "GOLD": "Gold",
        "SP500": "S&P 500 Index",
    }
    for s, name in symbols.items():
        MARKETS[s] = {
            "name": name,
            "price": random.uniform(50, 200),
        }


# -----------------------
# Startup
# -----------------------
init_markets()
threading.Thread(target=market_simulator, daemon=True).start()
