import tkinter as tk
from tkinter import messagebox
import random

# --- Theme (looks consistent on Mac/Windows because we draw everything) ---
BG = "#1e1e2f"
PANEL = "#151522"
CELL = "#2d2d44"
HOVER = "#3e3e66"
GRID = "#50507a"
TEXT = "#ffffff"
X_COLOR = "#4fc3f7"
O_COLOR = "#ff8a65"
BTN_RED = "#ff5252"
BTN_RED_HOVER = "#ff1744"

SIZE = 360          # board pixel size (square)
PAD = 18            # padding around board
CELL_GAP = 10       # gap between cells
LINE_W = 6          # X/O stroke width

class TicTacToeCanvas:
    def __init__(self, root):
        self.root = root
        self.root.title("Tic Tac Toe")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.board = [" "]*9
        self.game_over = False
        self.hover_cell = None

        # Top status
        self.status = tk.Label(
            root, text="Your turn (X)",
            font=("Arial", 16, "bold"),
            fg=TEXT, bg=BG
        )
        self.status.pack(pady=(14, 8))

        # Board canvas
        self.canvas = tk.Canvas(
            root, width=SIZE + PAD*2, height=SIZE + PAD*2,
            bg=BG, highlightthickness=0
        )
        self.canvas.pack()

        # Reset button (simple but consistent enough)
        self.reset_btn = tk.Label(
            root, text="Reset Game",
            font=("Arial", 12, "bold"),
            bg=BTN_RED, fg="white",
            padx=18, pady=10
        )
        self.reset_btn.pack(pady=(10, 16))
        self.reset_btn.bind("<Button-1>", lambda e: self.reset())
        self.reset_btn.bind("<Enter>", lambda e: self.reset_btn.config(bg=BTN_RED_HOVER))
        self.reset_btn.bind("<Leave>", lambda e: self.reset_btn.config(bg=BTN_RED))

        # Bindings
        self.canvas.bind("<Motion>", self.on_move)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<Button-1>", self.on_click)

        self.draw()

    # --- Game logic ---
    def wins(self):
        return [
            (0,1,2), (3,4,5), (6,7,8),
            (0,3,6), (1,4,7), (2,5,8),
            (0,4,8), (2,4,6)
        ]

    def is_winner(self, p):
        return any(self.board[a]==self.board[b]==self.board[c]==p for a,b,c in self.wins())

    def is_draw(self):
        return " " not in self.board

    def end_game(self, msg):
        self.game_over = True
        self.status.config(text=msg)
        messagebox.showinfo("Game Over", msg)

    # --- AI (win, block, else random) ---
    def computer_move(self):
        if self.game_over:
            return

        # win
        for i in range(9):
            if self.board[i] == " ":
                self.board[i] = "O"
                if self.is_winner("O"):
                    self.draw()
                    self.end_game("Computer wins!")
                    return
                self.board[i] = " "

        # block
        for i in range(9):
            if self.board[i] == " ":
                self.board[i] = "X"
                if self.is_winner("X"):
                    self.board[i] = "O"
                    self.draw()
                    self.status.config(text="Your turn (X)")
                    return
                self.board[i] = " "

        # random
        empties = [i for i in range(9) if self.board[i] == " "]
        if empties:
            self.board[random.choice(empties)] = "O"
            self.draw()

        if self.is_winner("O"):
            self.end_game("Computer wins!")
        elif self.is_draw():
            self.end_game("It's a draw!")
        else:
            self.status.config(text="Your turn (X)")

    # --- Board geometry helpers ---
    def cell_rect(self, idx):
        r = idx // 3
        c = idx % 3

        cell_size = (SIZE - 2*CELL_GAP) / 3.0
        x0 = PAD + c * (cell_size + CELL_GAP)
        y0 = PAD + r * (cell_size + CELL_GAP)
        x1 = x0 + cell_size
        y1 = y0 + cell_size
        return x0, y0, x1, y1

    def point_to_cell(self, x, y):
        # check each rect; simple & robust
        for i in range(9):
            x0,y0,x1,y1 = self.cell_rect(i)
            if x0 <= x <= x1 and y0 <= y <= y1:
                return i
        return None

    # --- Drawing ---
    def draw_x(self, x0,y0,x1,y1):
        margin = (x1-x0) * 0.22
        self.canvas.create_line(x0+margin, y0+margin, x1-margin, y1-margin,
                                width=LINE_W, fill=X_COLOR, capstyle="round")
        self.canvas.create_line(x1-margin, y0+margin, x0+margin, y1-margin,
                                width=LINE_W, fill=X_COLOR, capstyle="round")

    def draw_o(self, x0,y0,x1,y1):
        margin = (x1-x0) * 0.22
        self.canvas.create_oval(x0+margin, y0+margin, x1-margin, y1-margin,
                                width=LINE_W, outline=O_COLOR)

    def draw(self):
        self.canvas.delete("all")

        # Panel behind board
        self.canvas.create_rectangle(PAD-10, PAD-10, PAD+SIZE+10, PAD+SIZE+10,
                                     fill=PANEL, outline="")

        # Cells
        for i in range(9):
            x0,y0,x1,y1 = self.cell_rect(i)
            fill = HOVER if (self.hover_cell == i and not self.game_over and self.board[i]==" ") else CELL
            self.canvas.create_rectangle(x0,y0,x1,y1, fill=fill, outline=GRID, width=2)

            if self.board[i] == "X":
                self.draw_x(x0,y0,x1,y1)
            elif self.board[i] == "O":
                self.draw_o(x0,y0,x1,y1)

    # --- Events ---
    def on_move(self, event):
        cell = self.point_to_cell(event.x, event.y)
        if cell != self.hover_cell:
            self.hover_cell = cell
            self.draw()

    def on_leave(self, event):
        self.hover_cell = None
        self.draw()

    def on_click(self, event):
        if self.game_over:
            return
        cell = self.point_to_cell(event.x, event.y)
        if cell is None or self.board[cell] != " ":
            return

        self.board[cell] = "X"
        self.draw()

        if self.is_winner("X"):
            self.end_game("You win! 🎉")
            return
        if self.is_draw():
            self.end_game("It's a draw!")
            return

        self.status.config(text="Computer thinking...")
        self.root.after(250, self.computer_move)

    def reset(self):
        self.board = [" "]*9
        self.game_over = False
        self.status.config(text="Your turn (X)")
        self.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = TicTacToeCanvas(root)
    root.mainloop()
