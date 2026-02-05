import tkinter as tk
import random

BG_COLOR = "#1e1e2f"
BTN_COLOR = "#2d2d44"
HOVER_COLOR = "#3e3e66"
X_COLOR = "#4fc3f7"
O_COLOR = "#ff8a65"
TEXT_COLOR = "#ffffff"

class TicTacToeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Tic Tac Toe")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)

        self.board = [" " for _ in range(9)]
        self.buttons = []
        self.game_over = False

        self.status = tk.Label(
            root,
            text="Your turn (X)",
            font=("Segoe UI", 16, "bold"),
            fg=TEXT_COLOR,
            bg=BG_COLOR
        )
        self.status.grid(row=0, column=0, columnspan=3, pady=15)

        for i in range(9):
            btn = tk.Button(
                root,
                text="",
                font=("Segoe UI", 32, "bold"),
                width=4,
                height=2,
                bg=BTN_COLOR,
                fg=TEXT_COLOR,
                activebackground=HOVER_COLOR,
                borderwidth=0,
                command=lambda i=i: self.human_move(i)
            )
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=HOVER_COLOR) if b["state"] == "normal" else None)
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=BTN_COLOR))
            btn.grid(row=1 + i // 3, column=i % 3, padx=8, pady=8)
            self.buttons.append(btn)

        reset_btn = tk.Button(
            root,
            text="Reset Game",
            font=("Segoe UI", 12, "bold"),
            bg="#ff5252",
            fg="white",
            activebackground="#ff1744",
            borderwidth=0,
            command=self.reset
        )
        reset_btn.grid(row=4, column=0, columnspan=3, pady=15)

    def is_winner(self, player):
        wins = [
            (0,1,2), (3,4,5), (6,7,8),
            (0,3,6), (1,4,7), (2,5,8),
            (0,4,8), (2,4,6)
        ]
        return any(self.board[a] == self.board[b] == self.board[c] == player for a,b,c in wins)

    def is_draw(self):
        return " " not in self.board

    def set_button(self, i, char):
        self.board[i] = char
        color = X_COLOR if char == "X" else O_COLOR
        self.buttons[i].config(text=char, fg=color, state="disabled")

    # ✅ Custom popup centered over the app window
    def show_center_popup(self, title, msg):
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.configure(bg=BG_COLOR)
        popup.resizable(False, False)
        popup.transient(self.root)   # tie to main window
        popup.grab_set()             # modal

        label = tk.Label(
            popup, text=msg,
            font=("Segoe UI", 14, "bold"),
            fg=TEXT_COLOR, bg=BG_COLOR,
            padx=20, pady=15
        )
        label.pack()

        btn_frame = tk.Frame(popup, bg=BG_COLOR)
        btn_frame.pack(pady=(0, 15))

        ok_btn = tk.Button(
            btn_frame, text="OK",
            font=("Segoe UI", 11, "bold"),
            bg=BTN_COLOR, fg=TEXT_COLOR,
            activebackground=HOVER_COLOR,
            borderwidth=0,
            padx=18, pady=8,
            command=popup.destroy
        )
        ok_btn.pack(side="left", padx=8)

        play_btn = tk.Button(
            btn_frame, text="Play Again",
            font=("Segoe UI", 11, "bold"),
            bg="#ff5252", fg="white",
            activebackground="#ff1744",
            borderwidth=0,
            padx=18, pady=8,
            command=lambda: (popup.destroy(), self.reset())
        )
        play_btn.pack(side="left", padx=8)

        # center popup over root window
        self.root.update_idletasks()
        popup.update_idletasks()

        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()

        pw = popup.winfo_width()
        ph = popup.winfo_height()

        x = rx + (rw // 2) - (pw // 2)
        y = ry + (rh // 2) - (ph // 2)

        popup.geometry(f"+{x}+{y}")
        ok_btn.focus_set()

    # ✅ Delay popup so the last move visibly appears first
    def end_game(self, msg):
        if self.game_over:
            return
        self.game_over = True

        for b in self.buttons:
            b.config(state="disabled")
        self.status.config(text=msg)

        # force UI to render last move, then show popup
        self.root.update_idletasks()
        self.root.after(80, lambda: self.show_center_popup("Game Over", msg))

    def human_move(self, i):
        if self.game_over or self.board[i] != " ":
            return

        self.set_button(i, "X")

        if self.is_winner("X"):
            self.end_game("You win! 🎉")
            return
        if self.is_draw():
            self.end_game("It's a draw!")
            return

        self.status.config(text="Computer thinking...")
        self.root.after(300, self.computer_move)

    def computer_move(self):
        if self.game_over:
            return

        # 1) try to win
        for i in range(9):
            if self.board[i] == " ":
                self.board[i] = "O"
                if self.is_winner("O"):
                    self.board[i] = " "
                    self.set_button(i, "O")
                    self.end_game("Computer wins!")
                    return
                self.board[i] = " "

        # 2) try to block
        for i in range(9):
            if self.board[i] == " ":
                self.board[i] = "X"
                if self.is_winner("X"):
                    self.board[i] = " "
                    self.set_button(i, "O")
                    self.status.config(text="Your turn (X)")
                    return
                self.board[i] = " "

        # 3) random
        empty = [i for i in range(9) if self.board[i] == " "]
        i = random.choice(empty)
        self.set_button(i, "O")

        if self.is_winner("O"):
            self.end_game("Computer wins!")
            return
        if self.is_draw():
            self.end_game("It's a draw!")
            return

        self.status.config(text="Your turn (X)")

    def reset(self):
        self.game_over = False
        self.board = [" " for _ in range(9)]
        for b in self.buttons:
            b.config(text="", state="normal", fg=TEXT_COLOR, bg=BTN_COLOR)
        self.status.config(text="Your turn (X)")

if __name__ == "__main__":
    root = tk.Tk()
    app = TicTacToeGUI(root)
    root.mainloop()
