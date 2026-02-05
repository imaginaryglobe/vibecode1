# client.py — stdlib-only dashboard GUI trading client
import json
import time
import threading
import urllib.request
import urllib.error
import tkinter as tk
from tkinter import ttk, messagebox

SERVER = "http://127.0.0.1:8000"

# Slower refresh so users can react
POLL_SEC = 2.5
START_CASH = 10_000.0  # used for P/L display only (server also starts at 10k)

TOKEN = None

def api(path, data=None):
    req = urllib.request.Request(SERVER + path)
    if data is not None:
        req.data = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    try:
        with urllib.request.urlopen(req, timeout=4) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
            j = json.loads(body)
            raise RuntimeError(j.get("error") or body)
        except Exception:
            raise RuntimeError(f"HTTP {e.code}")
    except Exception as e:
        raise RuntimeError(str(e))

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mock Trading Dashboard (Client)")
        self.geometry("1100x650")
        self.minsize(980, 600)

        self.selected_symbol = None
        self.last_prices = {}   # symbol -> last price
        self.history = {}       # symbol -> [prices]
        self.stop_evt = threading.Event()

        self._theme()
        self._build_login()

    # ---------- Theme ----------
    def _theme(self):
        self.bg = "#0b1220"
        self.card = "#111a2e"
        self.text = "#e5e7eb"
        self.muted = "#9ca3af"
        self.grid = "#1f2a44"
        self.green = "#22c55e"
        self.red = "#ef4444"
        self.accent = "#60a5fa"

        self.configure(bg=self.bg)
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(".", font=("Segoe UI", 10))
        style.configure("TFrame", background=self.bg)
        style.configure("Card.TFrame", background=self.card)
        style.configure("TLabel", background=self.card, foreground=self.text)
        style.configure("Muted.TLabel", background=self.card, foreground=self.muted)
        style.configure("Header.TLabel", background=self.bg, foreground=self.text, font=("Segoe UI", 16, "bold"))
        style.configure("SubHeader.TLabel", background=self.bg, foreground=self.muted, font=("Segoe UI", 10))
        style.configure("TButton", padding=8)
        style.configure("Accent.TButton", background=self.accent)
        style.map("TButton", background=[("active", "#1b2a4b")])

        style.configure(
            "Treeview",
            background=self.card,
            fieldbackground=self.card,
            foreground=self.text,
            rowheight=28,
            bordercolor=self.grid,
            lightcolor=self.grid,
            darkcolor=self.grid,
        )
        style.configure("Treeview.Heading", background=self.bg, foreground=self.muted, font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#1e3a8a")])

    # ---------- Utilities ----------
    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _card(self, parent, padx=14, pady=12):
        f = ttk.Frame(parent, style="Card.TFrame", padding=(padx, pady))
        return f

    # ---------- Login ----------
    def _build_login(self):
        self._clear()

        top = ttk.Frame(self, style="TFrame")
        top.pack(fill="x", padx=16, pady=(14, 8))
        ttk.Label(top, text="Mock Trading Dashboard", style="Header.TLabel", background=self.bg).pack(side="left")
        ttk.Label(top, text="stdlib-only • Tkinter • HTTP", style="SubHeader.TLabel", background=self.bg).pack(side="left", padx=(12, 0))

        wrap = ttk.Frame(self, style="TFrame")
        wrap.pack(fill="both", expand=True, padx=16, pady=12)

        card = self._card(wrap, padx=18, pady=18)
        card.place(relx=0.5, rely=0.48, anchor="center")

        ttk.Label(card, text="Sign in", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Label(card, text="Server", style="Muted.TLabel").grid(row=1, column=0, sticky="e", pady=(14, 6))
        self.server_var = tk.StringVar(value=SERVER)
        ttk.Entry(card, width=34, textvariable=self.server_var).grid(row=1, column=1, sticky="w", pady=(14, 6))

        ttk.Label(card, text="Username", style="Muted.TLabel").grid(row=2, column=0, sticky="e", pady=6)
        self.user_var = tk.StringVar()
        ttk.Entry(card, width=34, textvariable=self.user_var).grid(row=2, column=1, sticky="w", pady=6)

        ttk.Label(card, text="Password", style="Muted.TLabel").grid(row=3, column=0, sticky="e", pady=6)
        self.pass_var = tk.StringVar()
        ttk.Entry(card, width=34, textvariable=self.pass_var, show="•").grid(row=3, column=1, sticky="w", pady=6)

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)
        ttk.Button(btns, text="Register", command=self._register_user).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(btns, text="Login", command=self._login).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(card, textvariable=self.status_var, style="Muted.TLabel").grid(row=5, column=0, columnspan=2, sticky="w", pady=(12, 0))

        self.bind("<Return>", lambda _e: self._login())

    def _register_user(self):
        global SERVER
        try:
            SERVER = self.server_var.get().strip()
            u = self.user_var.get().strip()
            p = self.pass_var.get().strip()
            if not u or not p:
                return messagebox.showwarning("Missing", "Enter username + password.")
            self.status_var.set("Registering…")
            api("/register", {"username": u, "password": p})
            self.status_var.set("Registered. You can login.")
            messagebox.showinfo("Registered", "Account created.")
        except Exception as e:
            self.status_var.set("Register failed.")
            messagebox.showerror("Register failed", str(e))

    def _login(self):
        global SERVER, TOKEN
        try:
            SERVER = self.server_var.get().strip()
            u = self.user_var.get().strip()
            p = self.pass_var.get().strip()
            if not u or not p:
                return messagebox.showwarning("Missing", "Enter username + password.")
            self.status_var.set("Logging in…")
            TOKEN = api("/login", {"username": u, "password": p})["token"]
            self.stop_evt.clear()
            self._build_dashboard(username=u)
        except Exception as e:
            self.status_var.set("Login failed.")
            messagebox.showerror("Login failed", str(e))

    # ---------- Dashboard ----------
    def _build_dashboard(self, username):
        self._clear()
        self.configure(bg=self.bg)

        # Top bar
        top = ttk.Frame(self, style="TFrame")
        top.pack(fill="x", padx=16, pady=(14, 8))
        ttk.Label(top, text="Dashboard", style="Header.TLabel", background=self.bg).pack(side="left")

        self.top_right = ttk.Frame(top, style="TFrame")
        self.top_right.pack(side="right")
        ttk.Label(self.top_right, text=f"User: {username}", foreground=self.muted, background=self.bg).pack(side="right")
        ttk.Label(self.top_right, text="  •  ", foreground=self.grid, background=self.bg).pack(side="right")
        ttk.Label(self.top_right, text=f"Server: {SERVER}", foreground=self.muted, background=self.bg).pack(side="right")

        # Main layout
        main = ttk.Frame(self, style="TFrame")
        main.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(1, weight=1)

        # KPI row (cards)
        kpis = ttk.Frame(main, style="TFrame")
        kpis.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        for i in range(4):
            kpis.columnconfigure(i, weight=1)

        self.cash_kpi = self._kpi_card(kpis, 0, "Cash", "—")
        self.pos_kpi = self._kpi_card(kpis, 1, "Positions Value", "—")
        self.eq_kpi = self._kpi_card(kpis, 2, "Total Equity", "—")
        self.pnl_kpi = self._kpi_card(kpis, 3, "P / L vs Start", "—")

        # Left: markets + chart
        left = ttk.Frame(main, style="TFrame")
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        markets_card = self._card(left)
        markets_card.grid(row=0, column=0, sticky="ew")
        ttk.Label(markets_card, text="Markets", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        table_card = self._card(left)
        table_card.grid(row=1, column=0, sticky="nsew", pady=(10, 10))
        table_card.rowconfigure(0, weight=1)
        table_card.columnconfigure(0, weight=1)

        self.market_tree = ttk.Treeview(
            table_card,
            columns=("symbol", "name", "price", "chg"),
            show="headings",
        )
        for c, w in [("symbol", 90), ("name", 220), ("price", 120), ("chg", 90)]:
            self.market_tree.heading(c, text=c.upper())
            self.market_tree.column(c, width=w, anchor="w" if c in ("symbol", "name") else "e")
        self.market_tree.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(table_card, orient="vertical", command=self.market_tree.yview)
        self.market_tree.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")

        self.market_tree.tag_configure("up", foreground=self.green)
        self.market_tree.tag_configure("down", foreground=self.red)

        self.market_tree.bind("<<TreeviewSelect>>", self._on_select_market)

        chart_card = self._card(left)
        chart_card.grid(row=2, column=0, sticky="ew")
        ttk.Label(chart_card, text="Mini Chart (last 60 updates)", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))
        self.canvas = tk.Canvas(chart_card, height=160, bg="#0a1020", highlightthickness=0)
        self.canvas.pack(fill="x")

        # Right: positions + order
        right = ttk.Frame(main, style="TFrame")
        right.grid(row=1, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        pos_card = self._card(right)
        pos_card.grid(row=0, column=0, sticky="ew")
        ttk.Label(pos_card, text="Positions", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        pos_table_card = self._card(right)
        pos_table_card.grid(row=1, column=0, sticky="nsew", pady=(10, 10))
        pos_table_card.rowconfigure(0, weight=1)
        pos_table_card.columnconfigure(0, weight=1)

        self.pos_tree = ttk.Treeview(pos_table_card, columns=("symbol", "qty", "mark"), show="headings")
        for c, w in [("symbol", 90), ("qty", 110), ("mark", 140)]:
            self.pos_tree.heading(c, text=c.upper())
            self.pos_tree.column(c, width=w, anchor="w" if c == "symbol" else "e")
        self.pos_tree.grid(row=0, column=0, sticky="nsew")
        psb = ttk.Scrollbar(pos_table_card, orient="vertical", command=self.pos_tree.yview)
        self.pos_tree.configure(yscrollcommand=psb.set)
        psb.grid(row=0, column=1, sticky="ns")

        order_card = self._card(right)
        order_card.grid(row=2, column=0, sticky="ew")
        ttk.Label(order_card, text="Trade Ticket", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(order_card, text="Selected", style="Muted.TLabel").grid(row=1, column=0, sticky="w")
        self.sel_var = tk.StringVar(value="(click a market)")
        ttk.Label(order_card, textvariable=self.sel_var).grid(row=1, column=1, sticky="e")

        ttk.Label(order_card, text="Side", style="Muted.TLabel").grid(row=2, column=0, sticky="w", pady=(10, 0))
        self.side_var = tk.StringVar(value="BUY")
        side = ttk.Combobox(order_card, values=("BUY", "SELL"), textvariable=self.side_var, state="readonly", width=10)
        side.grid(row=2, column=1, sticky="e", pady=(10, 0))

        ttk.Label(order_card, text="Qty", style="Muted.TLabel").grid(row=3, column=0, sticky="w", pady=(10, 0))
        self.qty_var = tk.StringVar(value="1")
        ttk.Entry(order_card, textvariable=self.qty_var, width=12).grid(row=3, column=1, sticky="e", pady=(10, 0))

        self.msg_var = tk.StringVar(value=f"Refresh: {POLL_SEC:.1f}s • Market tick: server-side")
        ttk.Label(order_card, textvariable=self.msg_var, style="Muted.TLabel").grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 0))

        ttk.Button(order_card, text="Submit Order", command=self._submit_order).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(order_card, text="Logout", command=self._logout).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        order_card.columnconfigure(0, weight=1)
        order_card.columnconfigure(1, weight=1)

        threading.Thread(target=self._poll_loop, daemon=True).start()

    def _kpi_card(self, parent, col, title, value):
        c = self._card(parent, padx=16, pady=14)
        c.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 10, 0))
        t = ttk.Label(c, text=title, foreground=self.muted, background=self.card)
        t.pack(anchor="w")
        v = ttk.Label(c, text=value, font=("Segoe UI", 16, "bold"), background=self.card)
        v.pack(anchor="w", pady=(6, 0))
        return v

    def _logout(self):
        global TOKEN
        self.stop_evt.set()
        TOKEN = None
        self.selected_symbol = None
        self.last_prices.clear()
        self.history.clear()
        self._build_login()

    def _on_select_market(self, _evt=None):
        sel = self.market_tree.selection()
        if not sel:
            return
        self.selected_symbol = sel[0]
        self.sel_var.set(self.selected_symbol)
        self._draw_chart()

    def _submit_order(self):
        if not self.selected_symbol:
            return messagebox.showwarning("No selection", "Select a market first.")
        try:
            qty = float(self.qty_var.get().strip())
            if qty <= 0:
                return messagebox.showwarning("Invalid qty", "Qty must be > 0.")
        except Exception:
            return messagebox.showwarning("Invalid qty", "Qty must be a number.")

        side = self.side_var.get().strip().upper()
        try:
            res = api("/order", {"symbol": self.selected_symbol, "side": side, "qty": qty})
            if not res.get("ok", True):
                messagebox.showerror("Rejected", res.get("message", "Order rejected"))
            else:
                self.msg_var.set(res.get("message", "Order placed"))
        except Exception as e:
            messagebox.showerror("Order failed", str(e))

    def _poll_loop(self):
        while not self.stop_evt.is_set():
            try:
                mk = api("/markets")["markets"]
                acct = api("/account")
                self.after(0, lambda mk=mk, acct=acct: self._apply_data(mk, acct))
            except Exception as e:
                self.after(0, lambda e=e: self.msg_var.set(f"Disconnected: {e}"))
            time.sleep(POLL_SEC)

    def _apply_data(self, markets, acct):
        # Update price history + change calc
        rows = []
        prices_map = {}
        for m in markets:
            sym = m["symbol"]
            price = float(m["price"])
            prices_map[sym] = price

            prev = self.last_prices.get(sym)
            chg = 0.0 if prev is None else ((price - prev) / prev * 100.0 if prev else 0.0)
            self.last_prices[sym] = price

            hist = self.history.setdefault(sym, [])
            hist.append(price)
            if len(hist) > 60:
                del hist[: len(hist) - 60]

            rows.append((sym, m.get("name", sym), price, chg))

        # Markets table (with color tags)
        self.market_tree.delete(*self.market_tree.get_children())
        for sym, name, price, chg in sorted(rows, key=lambda x: x[0]):
            tag = "up" if chg > 0 else ("down" if chg < 0 else "")
            self.market_tree.insert("", "end", iid=sym, values=(sym, name, f"{price:,.2f}", f"{chg:+.2f}%"), tags=(tag,) if tag else ())

        if self.selected_symbol and self.selected_symbol in prices_map:
            self.market_tree.selection_set(self.selected_symbol)
            self.market_tree.see(self.selected_symbol)

        # Positions table + KPI metrics
        cash = float(acct.get("cash", 0.0))
        positions = acct.get("positions", {}) or {}
        pos_value = 0.0

        self.pos_tree.delete(*self.pos_tree.get_children())
        for sym, qty in sorted(positions.items()):
            q = float(qty)
            px = prices_map.get(sym, 0.0)
            mv = q * px
            pos_value += mv
            self.pos_tree.insert("", "end", values=(sym, f"{q:g}", f"{mv:,.2f}"))

        equity = cash + pos_value
        pnl = equity - START_CASH

        self.cash_kpi.config(text=f"{cash:,.2f}")
        self.pos_kpi.config(text=f"{pos_value:,.2f}")
        self.eq_kpi.config(text=f"{equity:,.2f}")
        self.pnl_kpi.config(text=f"{pnl:+,.2f}", foreground=(self.green if pnl >= 0 else self.red), background=self.card)

        self._draw_chart()

    def _draw_chart(self):
        self.canvas.delete("all")
        sym = self.selected_symbol
        if not sym:
            self.canvas.create_text(12, 18, anchor="w", fill="#cbd5e1", text="Select a market to view its chart.")
            return
        hist = self.history.get(sym, [])
        if len(hist) < 2:
            self.canvas.create_text(12, 18, anchor="w", fill="#cbd5e1", text=f"{sym}: collecting data…")
            return

        w = max(1, self.canvas.winfo_width())
        h = max(1, self.canvas.winfo_height())
        pad = 14

        lo, hi = min(hist), max(hist)
        if abs(hi - lo) < 1e-12:
            lo -= 1
            hi += 1

        # grid
        for i in range(1, 4):
            y = pad + i * (h - 2 * pad) / 4
            self.canvas.create_line(pad, y, w - pad, y, fill="#1b2743")

        def X(i): return pad + i * (w - 2 * pad) / (len(hist) - 1)
        def Y(v): return pad + (hi - v) * (h - 2 * pad) / (hi - lo)

        # line
        for i in range(len(hist) - 1):
            self.canvas.create_line(X(i), Y(hist[i]), X(i + 1), Y(hist[i + 1]), fill=self.accent, width=2)

        last = hist[-1]
        prev = hist[-2]
        color = self.green if last >= prev else self.red
        self.canvas.create_text(pad, pad - 2, anchor="sw", fill="#cbd5e1", text=f"{sym}  {last:,.2f}")
        self.canvas.create_text(w - pad, pad - 2, anchor="se", fill=color, text=f"{(last-prev):+.2f}")

if __name__ == "__main__":
    App().mainloop()
