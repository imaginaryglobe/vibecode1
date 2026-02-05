# client.py
# Mock Trading Platform Client (GUI)
# - Tkinter UI
# - REST API calls to a local server
#
# Install dependency:
#   pip install requests

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import requests


# -----------------------------
# Configuration
# -----------------------------
DEFAULT_BASE_URL = "http://127.0.0.1:8000"
POLL_INTERVAL_SEC = 1.0
REQUEST_TIMEOUT = 3.5


# -----------------------------
# API Client
# -----------------------------
class ApiError(Exception):
    pass


@dataclass
class ApiClient:
    base_url: str = DEFAULT_BASE_URL
    token: Optional[str] = None
    username: Optional[str] = None

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def register(self, username: str, password: str) -> None:
        url = f"{self.base_url}/register"
        r = requests.post(url, json={"username": username, "password": password}, timeout=REQUEST_TIMEOUT)
        if r.status_code != 200:
            raise ApiError(self._pretty_error(r))
        data = r.json()
        if not data.get("ok", True):
            raise ApiError(data.get("message", "Registration failed."))

    def login(self, username: str, password: str) -> None:
        url = f"{self.base_url}/login"
        r = requests.post(url, json={"username": username, "password": password}, timeout=REQUEST_TIMEOUT)
        if r.status_code != 200:
            raise ApiError(self._pretty_error(r))
        data = r.json()
        token = data.get("token")
        if not token:
            raise ApiError(data.get("message", "Login failed (no token)."))
        self.token = token
        self.username = username

    def markets(self) -> List[Dict]:
        url = f"{self.base_url}/markets"
        r = requests.get(url, headers=self._headers(), timeout=REQUEST_TIMEOUT)
        if r.status_code != 200:
            raise ApiError(self._pretty_error(r))
        data = r.json()
        return data.get("markets", [])

    def account(self) -> Dict:
        url = f"{self.base_url}/account"
        r = requests.get(url, headers=self._headers(), timeout=REQUEST_TIMEOUT)
        if r.status_code != 200:
            raise ApiError(self._pretty_error(r))
        return r.json()

    def order(self, symbol: str, side: str, qty: float) -> Dict:
        url = f"{self.base_url}/order"
        r = requests.post(
            url,
            headers=self._headers(),
            json={"symbol": symbol, "side": side, "qty": qty},
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code != 200:
            raise ApiError(self._pretty_error(r))
        return r.json()

    @staticmethod
    def _pretty_error(r: requests.Response) -> str:
        try:
            j = r.json()
            return j.get("message") or j.get("error") or f"HTTP {r.status_code}"
        except Exception:
            return f"HTTP {r.status_code}: {r.text[:200]}"


# -----------------------------
# App State
# -----------------------------
@dataclass
class AppState:
    markets: List[Dict] = field(default_factory=list)
    cash: float = 0.0
    positions: Dict[str, float] = field(default_factory=dict)
    selected_symbol: Optional[str] = None
    price_history: Dict[str, List[float]] = field(default_factory=dict)  # symbol -> [prices]


# -----------------------------
# GUI
# -----------------------------
class TradingClientApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mock Trading Platform (Client)")
        self.geometry("1100x650")
        self.minsize(980, 600)

        self.api = ApiClient()
        self.state = AppState()

        self._poll_thread = None
        self._stop_poll = threading.Event()

        self._build_styles()
        self._build_ui()
        self._show_login()

    # ---------- Styling ----------
    def _build_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("Header.TLabel", font=("Segoe UI", 13, "bold"))
        style.configure("SubHeader.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("Mono.TLabel", font=("Consolas", 10))

    # ---------- UI Layout ----------
    def _build_ui(self):
        # Container frames
        self.container = ttk.Frame(self, padding=12)
        self.container.pack(fill="both", expand=True)

        self.topbar = ttk.Frame(self.container)
        self.topbar.pack(fill="x")

        self.content = ttk.Frame(self.container)
        self.content.pack(fill="both", expand=True, pady=(10, 0))

        # Topbar widgets (dynamic)
        self.lbl_title = ttk.Label(self.topbar, text="Mock Trading Platform", style="Header.TLabel")
        self.lbl_title.pack(side="left")

        self.lbl_user = ttk.Label(self.topbar, text="", style="Mono.TLabel")
        self.lbl_user.pack(side="left", padx=(16, 0))

        self.base_url_var = tk.StringVar(value=DEFAULT_BASE_URL)
        ttk.Label(self.topbar, text="Server:", style="Mono.TLabel").pack(side="right")
        self.base_url_entry = ttk.Entry(self.topbar, width=30, textvariable=self.base_url_var)
        self.base_url_entry.pack(side="right", padx=(6, 10))

        self.btn_logout = ttk.Button(self.topbar, text="Logout", command=self._logout)
        self.btn_logout.pack(side="right")
        self.btn_logout.configure(state="disabled")

        # Cards/Views (login vs main)
        self.login_frame = ttk.Frame(self.content)
        self.main_frame = ttk.Frame(self.content)

        self._build_login_view()
        self._build_main_view()

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.pack_forget()

    # ---------- Login View ----------
    def _build_login_view(self):
        f = self.login_frame

        card = ttk.Frame(f, padding=18, relief="ridge")
        card.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(card, text="Sign in", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Label(card, text="Username").grid(row=1, column=0, sticky="e", pady=(10, 4))
        ttk.Label(card, text="Password").grid(row=2, column=0, sticky="e", pady=4)

        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()

        self.user_entry = ttk.Entry(card, width=26, textvariable=self.user_var)
        self.pass_entry = ttk.Entry(card, width=26, textvariable=self.pass_var, show="•")
        self.user_entry.grid(row=1, column=1, sticky="w", pady=(10, 4))
        self.pass_entry.grid(row=2, column=1, sticky="w", pady=4)

        btns = ttk.Frame(card)
        btns.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)

        self.btn_login = ttk.Button(btns, text="Login", command=self._login)
        self.btn_register = ttk.Button(btns, text="Register", command=self._register)
        self.btn_login.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.btn_register.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        tip = ttk.Label(
            card,
            text="Tip: Set your server URL (top-right) to match the server.\nDefault: http://127.0.0.1:8000",
            style="Mono.TLabel",
        )
        tip.grid(row=4, column=0, columnspan=2, sticky="w", pady=(14, 0))

        # Enter triggers login
        self.user_entry.bind("<Return>", lambda e: self._login())
        self.pass_entry.bind("<Return>", lambda e: self._login())

    def _show_login(self):
        self._stop_polling()
        self._clear_content()
        self.login_frame.pack(fill="both", expand=True)
        self.btn_logout.configure(state="disabled")
        self.lbl_user.configure(text="")
        self.after(100, lambda: self.user_entry.focus_set())

    # ---------- Main View ----------
    def _build_main_view(self):
        root = self.main_frame
        root.pack(fill="both", expand=True)

        # Two-column layout
        left = ttk.Frame(root)
        right = ttk.Frame(root)
        left.pack(side="left", fill="both", expand=True)
        right.pack(side="right", fill="y")

        # --- Left: Markets table + chart ---
        markets_card = ttk.LabelFrame(left, text="Markets", padding=10)
        markets_card.pack(fill="both", expand=True)

        self.market_tree = ttk.Treeview(
            markets_card,
            columns=("symbol", "name", "price"),
            show="headings",
            height=16,
        )
        self.market_tree.heading("symbol", text="Symbol")
        self.market_tree.heading("name", text="Name")
        self.market_tree.heading("price", text="Price")
        self.market_tree.column("symbol", width=120, anchor="w")
        self.market_tree.column("name", width=360, anchor="w")
        self.market_tree.column("price", width=140, anchor="e")

        vsb = ttk.Scrollbar(markets_card, orient="vertical", command=self.market_tree.yview)
        self.market_tree.configure(yscrollcommand=vsb.set)
        self.market_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        markets_card.rowconfigure(0, weight=1)
        markets_card.columnconfigure(0, weight=1)

        self.market_tree.bind("<<TreeviewSelect>>", self._on_select_market)

        chart_card = ttk.LabelFrame(left, text="Mini Price Chart (last ~60 ticks)", padding=10)
        chart_card.pack(fill="x", pady=(10, 0))

        self.chart = tk.Canvas(chart_card, height=160, background="#111827", highlightthickness=0)
        self.chart.pack(fill="x", expand=True)

        # --- Right: Account + Order Entry ---
        acct_card = ttk.LabelFrame(right, text="Account", padding=10)
        acct_card.pack(fill="x")

        self.cash_var = tk.StringVar(value="Cash: —")
        self.pos_var = tk.StringVar(value="Positions: —")
        ttk.Label(acct_card, textvariable=self.cash_var, style="SubHeader.TLabel").pack(anchor="w")
        ttk.Label(acct_card, textvariable=self.pos_var, style="Mono.TLabel").pack(anchor="w", pady=(6, 0))

        self.status_var = tk.StringVar(value="Status: Not connected")
        ttk.Label(acct_card, textvariable=self.status_var, style="Mono.TLabel").pack(anchor="w", pady=(8, 0))

        order_card = ttk.LabelFrame(right, text="Place Order", padding=10)
        order_card.pack(fill="x", pady=(10, 0))

        self.sel_symbol_var = tk.StringVar(value="(select a market)")
        ttk.Label(order_card, text="Selected:", style="Mono.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(order_card, textvariable=self.sel_symbol_var, style="SubHeader.TLabel").grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )

        ttk.Label(order_card, text="Side:", style="Mono.TLabel").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.side_var = tk.StringVar(value="BUY")
        self.side_box = ttk.Combobox(order_card, values=["BUY", "SELL"], state="readonly", width=10, textvariable=self.side_var)
        self.side_box.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(10, 0))

        ttk.Label(order_card, text="Quantity:", style="Mono.TLabel").grid(row=2, column=0, sticky="w", pady=(10, 0))
        self.qty_var = tk.StringVar(value="1")
        self.qty_entry = ttk.Entry(order_card, width=12, textvariable=self.qty_var)
        self.qty_entry.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(10, 0))

        self.btn_order = ttk.Button(order_card, text="Submit Order", command=self._submit_order)
        self.btn_order.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        order_card.columnconfigure(0, weight=0)
        order_card.columnconfigure(1, weight=1)

        actions_card = ttk.LabelFrame(right, text="Actions", padding=10)
        actions_card.pack(fill="x", pady=(10, 0))

        ttk.Button(actions_card, text="Refresh Now", command=self._refresh_once).pack(fill="x")
        ttk.Button(actions_card, text="Clear Chart", command=self._clear_chart).pack(fill="x", pady=(8, 0))

    def _show_main(self):
        self._clear_content()
        self.main_frame.pack(fill="both", expand=True)
        self.btn_logout.configure(state="normal")
        self._start_polling()

    # ---------- Auth handlers ----------
    def _apply_base_url(self):
        url = self.base_url_var.get().strip()
        if not url.startswith("http"):
            raise ValueError("Base URL must start with http:// or https://")
        self.api.base_url = url

    def _register(self):
        try:
            self._apply_base_url()
            u = self.user_var.get().strip()
            p = self.pass_var.get().strip()
            if not u or not p:
                messagebox.showwarning("Missing fields", "Please enter username and password.")
                return
            self._set_status("Registering…")
            self.api.register(u, p)
            messagebox.showinfo("Registered", "Account created. You can login now.")
            self._set_status("Ready")
        except Exception as e:
            self._set_status("Register failed")
            messagebox.showerror("Register failed", str(e))

    def _login(self):
        try:
            self._apply_base_url()
            u = self.user_var.get().strip()
            p = self.pass_var.get().strip()
            if not u or not p:
                messagebox.showwarning("Missing fields", "Please enter username and password.")
                return
            self._set_status("Logging in…")
            self.api.login(u, p)
            self.lbl_user.configure(text=f" | User: {self.api.username}")
            self._set_status("Connected")
            self._show_main()
        except Exception as e:
            self._set_status("Login failed")
            messagebox.showerror("Login failed", str(e))

    def _logout(self):
        self.api.token = None
        self.api.username = None
        self.state = AppState()
        self._show_login()

    # ---------- Polling ----------
    def _start_polling(self):
        self._stop_poll.clear()
        if self._poll_thread and self._poll_thread.is_alive():
            return
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def _stop_polling(self):
        self._stop_poll.set()

    def _poll_loop(self):
        # background thread: fetch data then schedule UI updates
        while not self._stop_poll.is_set():
            try:
                mkts = self.api.markets()
                acct = self.api.account()
                self.after(0, lambda mkts=mkts, acct=acct: self._apply_data(mkts, acct))
                self.after(0, lambda: self._set_status("Connected"))
            except Exception as e:
                self.after(0, lambda e=e: self._set_status(f"Disconnected: {e}"))
            time.sleep(POLL_INTERVAL_SEC)

    def _refresh_once(self):
        def worker():
            try:
                mkts = self.api.markets()
                acct = self.api.account()
                self.after(0, lambda: self._apply_data(mkts, acct))
                self.after(0, lambda: self._set_status("Connected (manual refresh)"))
            except Exception as e:
                self.after(0, lambda: self._set_status(f"Refresh failed: {e}"))

        threading.Thread(target=worker, daemon=True).start()

    # ---------- Data -> UI ----------
    def _apply_data(self, markets: List[Dict], account: Dict):
        self.state.markets = markets
        self.state.cash = float(account.get("cash", 0.0))
        self.state.positions = account.get("positions", {}) or {}

        # update history for chart
        for m in markets:
            sym = m.get("symbol")
            price = float(m.get("price", 0.0))
            if not sym:
                continue
            hist = self.state.price_history.setdefault(sym, [])
            hist.append(price)
            if len(hist) > 60:
                del hist[0 : len(hist) - 60]

        self._render_markets()
        self._render_account()
        self._render_chart()

    def _render_markets(self):
        # keep selection if possible
        selected = self.state.selected_symbol

        self.market_tree.delete(*self.market_tree.get_children())
        for m in self.state.markets:
            sym = m.get("symbol", "")
            name = m.get("name", sym)
            price = float(m.get("price", 0.0))
            self.market_tree.insert("", "end", iid=sym, values=(sym, name, f"{price:,.4f}"))

        if selected and selected in [m.get("symbol") for m in self.state.markets]:
            self.market_tree.selection_set(selected)
            self.market_tree.see(selected)

    def _render_account(self):
        self.cash_var.set(f"Cash: {self.state.cash:,.2f}")

        if not self.state.positions:
            self.pos_var.set("Positions: (none)")
            return

        # compact positions display
        parts = []
        for sym, qty in sorted(self.state.positions.items()):
            try:
                q = float(qty)
            except Exception:
                continue
            if abs(q) < 1e-9:
                continue
            parts.append(f"{sym}={q:g}")
        self.pos_var.set("Positions: " + (", ".join(parts) if parts else "(none)"))

    def _render_chart(self):
        sym = self.state.selected_symbol
        self.chart.delete("all")

        if not sym:
            self.chart.create_text(10, 18, anchor="w", fill="#cbd5e1", text="Select a market to view its price chart.")
            return

        hist = self.state.price_history.get(sym, [])
        if len(hist) < 2:
            self.chart.create_text(10, 18, anchor="w", fill="#cbd5e1", text=f"{sym}: not enough data yet.")
            return

        w = max(1, self.chart.winfo_width())
        h = max(1, self.chart.winfo_height())
        pad = 12

        lo, hi = min(hist), max(hist)
        if abs(hi - lo) < 1e-9:
            lo -= 1.0
            hi += 1.0

        # grid lines
        for y in (0.25, 0.5, 0.75):
            yy = pad + y * (h - 2 * pad)
            self.chart.create_line(pad, yy, w - pad, yy, fill="#1f2937")

        # map data
        def x(i):
            return pad + i * (w - 2 * pad) / (len(hist) - 1)

        def y(v):
            return pad + (hi - v) * (h - 2 * pad) / (hi - lo)

        # line
        for i in range(len(hist) - 1):
            self.chart.create_line(x(i), y(hist[i]), x(i + 1), y(hist[i + 1]), fill="#22c55e", width=2)

        # labels
        last = hist[-1]
        self.chart.create_text(pad, pad - 2, anchor="sw", fill="#cbd5e1", text=f"{sym}  last={last:,.4f}")
        self.chart.create_text(w - pad, pad - 2, anchor="se", fill="#94a3b8", text=f"range {lo:,.4f}–{hi:,.4f}")

    def _clear_chart(self):
        if self.state.selected_symbol:
            self.state.price_history[self.state.selected_symbol] = []
        self._render_chart()

    # ---------- Interaction ----------
    def _on_select_market(self, _evt=None):
        sel = self.market_tree.selection()
        if not sel:
            return
        sym = sel[0]
        self.state.selected_symbol = sym
        self.sel_symbol_var.set(sym)
        self._render_chart()

    def _submit_order(self):
        sym = self.state.selected_symbol
        if not sym:
            messagebox.showwarning("No market selected", "Please select a market first.")
            return

        side = self.side_var.get().strip().upper()
        if side not in ("BUY", "SELL"):
            messagebox.showwarning("Invalid side", "Side must be BUY or SELL.")
            return

        try:
            qty = float(self.qty_var.get().strip())
        except Exception:
            messagebox.showwarning("Invalid quantity", "Quantity must be a number.")
            return

        if qty <= 0:
            messagebox.showwarning("Invalid quantity", "Quantity must be > 0.")
            return

        self.btn_order.configure(state="disabled")
        self._set_status(f"Submitting {side} {qty:g} {sym}…")

        def worker():
            try:
                res = self.api.order(sym, side, qty)
                ok = res.get("ok", True)
                msg = res.get("message", "Order submitted.")
                self.after(0, lambda: self._set_status("Connected"))
                self.after(0, lambda: messagebox.showinfo("Order result", msg) if ok else messagebox.showerror("Order rejected", msg))
                # trigger a refresh quickly after an order
                self.after(0, self._refresh_once)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Order failed", str(e)))
                self.after(0, lambda: self._set_status(f"Order failed: {e}"))
            finally:
                self.after(0, lambda: self.btn_order.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    # ---------- Status ----------
    def _set_status(self, msg: str):
        self.status_var.set(f"Status: {msg}")

    # ---------- Window close ----------
    def destroy(self):
        self._stop_polling()
        super().destroy()


if __name__ == "__main__":
    app = TradingClientApp()
    app.mainloop()