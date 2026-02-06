# team: jaden Fang, Jason Lyu
# server.py — stdlib-only mock trading server (multi-client + slower tick)
import json
import threading
import time
import random
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

HOST = "127.0.0.1"
PORT = 8000

START_CASH = 10_000.0

# Slower market movement so humans can react
MARKET_TICK_SEC = 3.0
# Typical per-tick % move range (e.g., 0.7% up/down)
MAX_PCT_MOVE = 0.007

# In-memory storage
STATE_LOCK = threading.Lock()
USERS = {}   # username -> {password, cash, positions}
TOKENS = {}  # token -> username
MARKETS = {
    "BTC":  {"name": "Bitcoin",   "price": 30000.0},
    "ETH":  {"name": "Ethereum",  "price": 2000.0},
    "GOLD": {"name": "Gold",      "price": 1900.0},
    "OIL":  {"name": "Crude Oil", "price": 75.0},
    "SPX":  {"name": "S&P 500",   "price": 4800.0},
}

def market_simulator():
    while True:
        time.sleep(MARKET_TICK_SEC)
        with STATE_LOCK:
            for m in MARKETS.values():
                pct = random.uniform(-MAX_PCT_MOVE, MAX_PCT_MOVE)
                new_price = m["price"] * (1.0 + pct)
                m["price"] = max(0.01, float(new_price))

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class Handler(BaseHTTPRequestHandler):
    server_version = "MockTradingServer/1.0"

    def _json(self, code, data):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_body_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def _auth_user(self):
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        token = auth.split(" ", 1)[1].strip()
        with STATE_LOCK:
            return TOKENS.get(token)

    def do_POST(self):
        data = self._read_body_json()

        if self.path == "/register":
            u = (data.get("username") or "").strip()
            p = (data.get("password") or "").strip()
            if not u or not p:
                return self._json(400, {"error": "Missing username/password"})
            with STATE_LOCK:
                if u in USERS:
                    return self._json(400, {"error": "User exists"})
                USERS[u] = {"password": p, "cash": float(START_CASH), "positions": {}}
            return self._json(200, {"ok": True})

        if self.path == "/login":
            u = (data.get("username") or "").strip()
            p = (data.get("password") or "").strip()
            with STATE_LOCK:
                user = USERS.get(u)
                if not user or user["password"] != p:
                    return self._json(401, {"error": "Invalid login"})
                token = secrets.token_hex(16)
                TOKENS[token] = u
            return self._json(200, {"token": token})

        if self.path == "/order":
            user = self._auth_user()
            if not user:
                return self._json(401, {"error": "Unauthorized"})

            sym = (data.get("symbol") or "").strip().upper()
            side = (data.get("side") or "").strip().upper()
            try:
                qty = float(data.get("qty"))
            except Exception:
                return self._json(400, {"error": "Invalid qty"})

            if sym not in MARKETS:
                return self._json(400, {"error": "Unknown symbol"})
            if side not in ("BUY", "SELL"):
                return self._json(400, {"error": "Side must be BUY/SELL"})
            if qty <= 0:
                return self._json(400, {"error": "Qty must be > 0"})

            with STATE_LOCK:
                price = float(MARKETS[sym]["price"])
                acct = USERS[user]
                pos = float(acct["positions"].get(sym, 0.0))

                if side == "BUY":
                    cost = price * qty
                    if acct["cash"] < cost:
                        return self._json(200, {"ok": False, "message": "Insufficient cash"})
                    acct["cash"] -= cost
                    acct["positions"][sym] = pos + qty
                else:
                    if pos < qty:
                        return self._json(200, {"ok": False, "message": "Insufficient position"})
                    acct["cash"] += price * qty
                    new_pos = pos - qty
                    if new_pos <= 1e-12:
                        acct["positions"].pop(sym, None)
                    else:
                        acct["positions"][sym] = new_pos

            return self._json(200, {"ok": True, "message": f"{side} {qty:g} {sym} @ {price:.2f}"})

        return self._json(404, {"error": "Not found"})

    def do_GET(self):
        user = self._auth_user()
        if not user:
            return self._json(401, {"error": "Unauthorized"})

        if self.path == "/markets":
            with STATE_LOCK:
                markets = [
                    {"symbol": s, "name": m["name"], "price": float(m["price"])}
                    for s, m in MARKETS.items()
                ]
            return self._json(200, {"markets": markets})

        if self.path == "/account":
            with STATE_LOCK:
                acct = USERS[user]
                out = {"cash": float(acct["cash"]), "positions": dict(acct["positions"])}
            return self._json(200, out)

        return self._json(404, {"error": "Not found"})

if __name__ == "__main__":
    print(f"Server running on http://{HOST}:{PORT}")
    threading.Thread(target=market_simulator, daemon=True).start()
    ThreadedHTTPServer((HOST, PORT), Handler).serve_forever()
