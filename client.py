# client.py
# Standard-library-only GUI trading client

import tkinter as tk
from tkinter import messagebox
import json
import urllib.request
import threading
import time

SERVER = "http://127.0.0.1:8000"
TOKEN = None
SELECTED = None


def api(path, data=None):
    req = urllib.request.Request(SERVER + path)
    if data:
        req.data = json.dumps(data).encode()
        req.add_header("Content-Type", "application/json")
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mock Trading Client")
        self.geometry("600x400")
        self.build_login()

    def build_login(self):
        self.clear()
        tk.Label(self, text="Username").pack()
        self.u = tk.Entry(self)
        self.u.pack()
        tk.Label(self, text="Password").pack()
        self.p = tk.Entry(self, show="*")
        self.p.pack()
        tk.Button(self, text="Register", command=self.register).pack()
        tk.Button(self, text="Login", command=self.login).pack()

    def build_main(self):
        self.clear()
        self.list = tk.Listbox(self)
        self.list.pack(fill="both", expand=True)
        self.list.bind("<<ListboxSelect>>", self.select)

        self.info = tk.Label(self)
        self.info.pack()

        self.qty = tk.Entry(self)
        self.qty.insert(0, "1")
        self.qty.pack()

        tk.Button(self, text="BUY", command=lambda: self.order("BUY")).pack()
        tk.Button(self, text="SELL", command=lambda: self.order("SELL")).pack()

        threading.Thread(target=self.poll, daemon=True).start()

    def clear(self):
        for w in self.winfo_children():
            w.destroy()

    def register(self):
        try:
            api("/register", {"username": self.u.get(), "password": self.p.get()})
            messagebox.showinfo("OK", "Registered")
        except:
            messagebox.showerror("Error", "Register failed")

    def login(self):
        global TOKEN
        try:
            TOKEN = api("/login", {"username": self.u.get(), "password": self.p.get()})["token"]
            self.build_main()
        except:
            messagebox.showerror("Error", "Login failed")

    def poll(self):
        while True:
            try:
                mk = api("/markets")["markets"]
                acct = api("/account")
                self.list.delete(0, "end")
                for m in mk:
                    self.list.insert("end", f"{m['symbol']}  {m['price']:.2f}")
                self.info.config(text=f"Cash: {acct['cash']:.2f}  Positions: {acct['positions']}")
            except:
                pass
            time.sleep(1)

    def select(self, _):
        global SELECTED
        SELECTED = self.list.get(self.list.curselection()).split()[0]

    def order(self, side):
        if not SELECTED:
            return
        api("/order", {"symbol": SELECTED, "side": side, "qty": float(self.qty.get())})


if __name__ == "__main__":
    App().mainloop()
