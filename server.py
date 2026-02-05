# server.py
# Standard-library-only mock trading server

import json
import threading
import time
import random
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

HOST = "127.0.0.1"
PORT = 8000

USERS = {}      # username -> {password, cash, positions}
TOKENS = {}     # token -> username
MARKETS = {
    "BTC": {"name": "Bitcoin", "price": 30000.0},
    "ETH": {"name": "Ethereum", "price": 2000.0},
    "GOLD": {"name": "Gold", "price": 1900.0},
}

START_CASH = 10000.0


def market_simulator():
    while True:
        time.sleep(1)
        for m in MARKETS.values():
            m["price"] = max(1.0, m["price"] + random.uniform(-5, 5))


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or "{}")

    def _auth_user(self):
        auth = self.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "")
        return TOKENS.get(token)

    def do_POST(self):
        data = self._body()

        if self.path == "/register":
            u, p = data.get("username"), data.get("password")
            if u in USERS:
                return self._json(400, {"error": "User exists"})
            USERS[u] = {"password": p, "cash": START_CASH, "positions": {}}
            return self._json(200, {"ok": True})

        if self.path == "/login":
            u, p = data.get("username"), data.get("password")
            if u not in USERS or USERS[u]["password"] != p:
                return self._json(401, {"error": "Invalid login"})
            token = str(random.random())
            TOKENS[token] = u
            return self._json(200, {"token": token})

        if self.path == "/order":
            user = self._auth_user()
            if not user:
                return self._json(401, {"error": "Unauthorized"})

            sym = data["symbol"]
            side = data["side"]
            qty = float(data["qty"])
            price = MARKETS[sym]["price"]
            acct = USERS[user]
            pos = acct["positions"].get(sym, 0)

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
                acct["positions"][sym] = pos - qty

            return self._json(200, {"ok": True})

        self._json(404, {})

    def do_GET(self):
        user = self._auth_user()
        if not user:
            return self._json(401, {"error": "Unauthorized"})

        if self.path == "/markets":
            return self._json(200, {
                "markets": [
                    {"symbol": s, "name": m["name"], "price": m["price"]}
                    for s, m in MARKETS.items()
                ]
            })

        if self.path == "/account":
            acct = USERS[user]
            return self._json(200, {
                "cash": acct["cash"],
                "positions": acct["positions"]
            })

        self._json(404, {})


if __name__ == "__main__":
    print(f"Server running on http://{HOST}:{PORT}")
    threading.Thread(target=market_simulator, daemon=True).start()
    ThreadedHTTPServer((HOST, PORT), Handler).serve_forever()
