import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec

DATA_FILE = "budget_data.json"

# ── Palette ──────────────────────────────────────────────────────────────────
BG        = "#0f0f14"
CARD      = "#1a1a24"
BORDER    = "#2a2a3a"
INCOME_C  = "#00e5a0"
EXPENSE_C = "#ff4d6d"
ACCENT    = "#7c6af7"
TEXT      = "#e8e8f0"
MUTED     = "#6b6b80"
FONT_MAIN = ("Courier New", 10)
FONT_HEAD = ("Courier New", 12, "bold")
FONT_BIG  = ("Courier New", 22, "bold")

CATEGORIES = {
    "income":  ["Salary", "Freelance", "Investment", "Gift", "Other Income"],
    "expense": ["Food", "Rent", "Transport", "Entertainment", "Health",
                "Shopping", "Utilities", "Education", "Other Expense"],
}

# ── Data helpers ──────────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── App ───────────────────────────────────────────────────────────────────────
class BudgetApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("◈ BUDGET TRACKER")
        self.geometry("1200x780")
        self.configure(bg=BG)
        self.resizable(True, True)

        self.transactions = load_data()
        self.type_var     = tk.StringVar(value="expense")
        self.cat_var      = tk.StringVar()
        self.amount_var   = tk.StringVar()
        self.desc_var     = tk.StringVar()
        self.date_var     = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))

        self._build_ui()
        self._refresh()

    # ── UI layout ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG, pady=16)
        hdr.pack(fill="x", padx=24)
        tk.Label(hdr, text="◈ BUDGET TRACKER", font=("Courier New", 18, "bold"),
                 bg=BG, fg=ACCENT).pack(side="left")
        tk.Label(hdr, text="track · analyse · improve", font=FONT_MAIN,
                 bg=BG, fg=MUTED).pack(side="left", padx=12)

        # Main panes
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        left  = tk.Frame(body, bg=BG, width=340)
        left.pack(side="left", fill="y", padx=(0, 14))
        left.pack_propagate(False)

        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_form(left)
        self._build_summary(left)
        self._build_table(right)
        self._build_charts(right)

    def _card(self, parent, **kw):
        f = tk.Frame(parent, bg=CARD, relief="flat", **kw)
        f.pack(fill="x", pady=(0, 12))
        return f

    # ── Form ──────────────────────────────────────────────────────────────────
    def _build_form(self, parent):
        card = self._card(parent, pady=16, padx=16)
        tk.Label(card, text="NEW TRANSACTION", font=FONT_HEAD,
                 bg=CARD, fg=TEXT).pack(anchor="w", pady=(0, 12))

        # Type toggle
        trow = tk.Frame(card, bg=CARD)
        trow.pack(fill="x", pady=(0, 10))
        for val, color, lbl in [("income", INCOME_C, "▲ INCOME"),
                                 ("expense", EXPENSE_C, "▼ EXPENSE")]:
            rb = tk.Radiobutton(trow, text=lbl, variable=self.type_var,
                                value=val, bg=CARD, fg=color,
                                selectcolor=CARD, activebackground=CARD,
                                activeforeground=color,
                                font=("Courier New", 10, "bold"),
                                indicatoron=0, width=12,
                                relief="flat", bd=1, cursor="hand2",
                                command=self._update_categories)
            rb.pack(side="left", padx=(0, 8))

        # Fields
        for label, var in [("AMOUNT (₹)", self.amount_var),
                            ("DESCRIPTION", self.desc_var),
                            ("DATE (YYYY-MM-DD)", self.date_var)]:
            tk.Label(card, text=label, font=("Courier New", 8),
                     bg=CARD, fg=MUTED).pack(anchor="w")
            e = tk.Entry(card, textvariable=var, bg=BORDER, fg=TEXT,
                         insertbackground=TEXT, font=FONT_MAIN,
                         relief="flat", bd=6)
            e.pack(fill="x", pady=(2, 8))

        # Category
        tk.Label(card, text="CATEGORY", font=("Courier New", 8),
                 bg=CARD, fg=MUTED).pack(anchor="w")
        self.cat_menu = ttk.Combobox(card, textvariable=self.cat_var,
                                     font=FONT_MAIN, state="readonly")
        self.cat_menu.pack(fill="x", pady=(2, 12))
        self._update_categories()

        # Add button
        btn = tk.Button(card, text="+ ADD TRANSACTION",
                        bg=ACCENT, fg=TEXT, font=FONT_HEAD,
                        relief="flat", bd=0, pady=10, cursor="hand2",
                        command=self._add_transaction,
                        activebackground="#9b8fff", activeforeground=TEXT)
        btn.pack(fill="x")

    def _update_categories(self):
        cats = CATEGORIES[self.type_var.get()]
        self.cat_menu["values"] = cats
        self.cat_var.set(cats[0])

    # ── Summary cards ─────────────────────────────────────────────────────────
    def _build_summary(self, parent):
        card = self._card(parent, pady=16, padx=16)
        tk.Label(card, text="SUMMARY", font=FONT_HEAD,
                 bg=CARD, fg=TEXT).pack(anchor="w", pady=(0, 10))

        self.lbl_income  = self._stat_row(card, "INCOME",  INCOME_C)
        self.lbl_expense = self._stat_row(card, "EXPENSE", EXPENSE_C)
        self.lbl_balance = self._stat_row(card, "BALANCE", ACCENT)

    def _stat_row(self, parent, label, color):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label, font=("Courier New", 8),
                 bg=CARD, fg=MUTED, width=10, anchor="w").pack(side="left")
        lbl = tk.Label(row, text="₹0.00", font=("Courier New", 11, "bold"),
                       bg=CARD, fg=color, anchor="e")
        lbl.pack(side="right")
        return lbl

    # ── Table ─────────────────────────────────────────────────────────────────
    def _build_table(self, parent):
        frame = tk.Frame(parent, bg=CARD, pady=12, padx=12)
        frame.pack(fill="x", pady=(0, 12))

        hdr = tk.Frame(frame, bg=CARD)
        hdr.pack(fill="x")
        tk.Label(hdr, text="RECENT TRANSACTIONS", font=FONT_HEAD,
                 bg=CARD, fg=TEXT).pack(side="left")
        tk.Button(hdr, text="✕ DELETE SELECTED", bg=BORDER, fg=EXPENSE_C,
                  font=("Courier New", 8), relief="flat", cursor="hand2",
                  command=self._delete_selected,
                  activebackground=EXPENSE_C, activeforeground=TEXT
                  ).pack(side="right")

        cols = ("date", "type", "category", "description", "amount")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("BT.Treeview", background=BORDER, foreground=TEXT,
                        fieldbackground=BORDER, font=FONT_MAIN,
                        rowheight=26, borderwidth=0)
        style.configure("BT.Treeview.Heading", background=CARD, foreground=MUTED,
                        font=("Courier New", 8, "bold"), relief="flat")
        style.map("BT.Treeview", background=[("selected", ACCENT)])

        self.tree = ttk.Treeview(frame, columns=cols, show="headings",
                                 style="BT.Treeview", height=6)
        for col, w in zip(cols, [90, 70, 110, 170, 90]):
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=w, anchor="center")

        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="x", expand=True, pady=(8, 0))
        sb.pack(side="right", fill="y", pady=(8, 0))

    # ── Charts ────────────────────────────────────────────────────────────────
    def _build_charts(self, parent):
        self.chart_frame = tk.Frame(parent, bg=BG)
        self.chart_frame.pack(fill="both", expand=True)

    def _draw_charts(self):
        for w in self.chart_frame.winfo_children():
            w.destroy()

        fig = Figure(figsize=(8, 3.6), facecolor=BG)
        gs  = gridspec.GridSpec(1, 3, figure=fig,
                                left=0.05, right=0.97, wspace=0.4)

        income_by_cat  = {}
        expense_by_cat = {}
        monthly        = {}

        for t in self.transactions:
            cat = t["category"]
            amt = t["amount"]
            mo  = t["date"][:7]
            if t["type"] == "income":
                income_by_cat[cat] = income_by_cat.get(cat, 0) + amt
            else:
                expense_by_cat[cat] = expense_by_cat.get(cat, 0) + amt
            if mo not in monthly:
                monthly[mo] = {"income": 0, "expense": 0}
            monthly[mo][t["type"]] += amt

        # ── Pie: expenses ─────────────────────────────────────────────────────
        ax1 = fig.add_subplot(gs[0])
        ax1.set_facecolor(CARD)
        if expense_by_cat:
            vals  = list(expense_by_cat.values())
            lbls  = list(expense_by_cat.keys())
            colors = plt.cm.RdPu([0.4 + 0.5 * i / max(len(vals)-1, 1)
                                   for i in range(len(vals))])
            wedges, _, autotexts = ax1.pie(
                vals, labels=None, autopct="%1.0f%%",
                colors=colors, startangle=140,
                pctdistance=0.78, wedgeprops=dict(width=0.55, linewidth=0))
            for at in autotexts:
                at.set_color(TEXT); at.set_fontsize(7)
            ax1.legend(wedges, lbls, loc="lower center",
                       fontsize=6, facecolor=BG, labelcolor=TEXT,
                       framealpha=0, ncol=2,
                       bbox_to_anchor=(0.5, -0.18))
        ax1.set_title("Expenses by Category", color=TEXT,
                      fontsize=8, fontfamily="Courier New", pad=8)

        # ── Pie: income ───────────────────────────────────────────────────────
        ax2 = fig.add_subplot(gs[1])
        ax2.set_facecolor(CARD)
        if income_by_cat:
            vals  = list(income_by_cat.values())
            lbls  = list(income_by_cat.keys())
            colors = plt.cm.BuGn([0.4 + 0.5 * i / max(len(vals)-1, 1)
                                   for i in range(len(vals))])
            wedges, _, autotexts = ax2.pie(
                vals, labels=None, autopct="%1.0f%%",
                colors=colors, startangle=140,
                pctdistance=0.78, wedgeprops=dict(width=0.55, linewidth=0))
            for at in autotexts:
                at.set_color(TEXT); at.set_fontsize(7)
            ax2.legend(wedges, lbls, loc="lower center",
                       fontsize=6, facecolor=BG, labelcolor=TEXT,
                       framealpha=0, ncol=2,
                       bbox_to_anchor=(0.5, -0.18))
        ax2.set_title("Income by Category", color=TEXT,
                      fontsize=8, fontfamily="Courier New", pad=8)

        # ── Bar: monthly ──────────────────────────────────────────────────────
        ax3 = fig.add_subplot(gs[2])
        ax3.set_facecolor(CARD)
        if monthly:
            months  = sorted(monthly.keys())
            inc_vals = [monthly[m]["income"]  for m in months]
            exp_vals = [monthly[m]["expense"] for m in months]
            x = range(len(months))
            w = 0.35
            ax3.bar([i - w/2 for i in x], inc_vals,  width=w,
                    color=INCOME_C,  alpha=0.85, linewidth=0)
            ax3.bar([i + w/2 for i in x], exp_vals, width=w,
                    color=EXPENSE_C, alpha=0.85, linewidth=0)
            ax3.set_xticks(list(x))
            ax3.set_xticklabels([m[5:] for m in months],
                                fontsize=7, color=MUTED,
                                fontfamily="Courier New")
            ax3.tick_params(axis="y", colors=MUTED, labelsize=7)
            ax3.spines[:].set_visible(False)
            ax3.set_facecolor(CARD)
            ax3.tick_params(axis="x", colors=MUTED)
            patch_i = mpatches.Patch(color=INCOME_C,  label="Income")
            patch_e = mpatches.Patch(color=EXPENSE_C, label="Expense")
            ax3.legend(handles=[patch_i, patch_e], fontsize=6,
                       facecolor=BG, labelcolor=TEXT, framealpha=0)
        ax3.set_title("Monthly Overview", color=TEXT,
                      fontsize=8, fontfamily="Courier New", pad=8)

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ── Actions ───────────────────────────────────────────────────────────────
    def _add_transaction(self):
        try:
            amt = float(self.amount_var.get().replace(",", ""))
            if amt <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Enter a valid positive amount.")
            return

        try:
            datetime.strptime(self.date_var.get(), "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Date must be YYYY-MM-DD.")
            return

        self.transactions.append({
            "date":        self.date_var.get(),
            "type":        self.type_var.get(),
            "category":    self.cat_var.get(),
            "description": self.desc_var.get().strip() or "—",
            "amount":      amt,
        })
        save_data(self.transactions)
        self.amount_var.set("")
        self.desc_var.set("")
        self._refresh()

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Select a transaction to delete.")
            return
        for iid in sel:
            idx = self.tree.index(iid)
            del self.transactions[-(idx + 1)]  # table shows newest-first
        save_data(self.transactions)
        self._refresh()

    def _refresh(self):
        # Summary
        total_in  = sum(t["amount"] for t in self.transactions if t["type"] == "income")
        total_out = sum(t["amount"] for t in self.transactions if t["type"] == "expense")
        balance   = total_in - total_out
        self.lbl_income.config( text=f"₹{total_in:,.2f}")
        self.lbl_expense.config(text=f"₹{total_out:,.2f}")
        self.lbl_balance.config(text=f"₹{balance:,.2f}",
                                fg=INCOME_C if balance >= 0 else EXPENSE_C)

        # Table (newest first)
        for row in self.tree.get_children():
            self.tree.delete(row)
        for t in reversed(self.transactions):
            color = INCOME_C if t["type"] == "income" else EXPENSE_C
            sign  = "+" if t["type"] == "income" else "-"
            self.tree.insert("", "end", values=(
                t["date"], t["type"].upper(), t["category"],
                t["description"], f'{sign}₹{t["amount"]:,.2f}'
            ), tags=(t["type"],))
        self.tree.tag_configure("income",  foreground=INCOME_C)
        self.tree.tag_configure("expense", foreground=EXPENSE_C)

        # Charts
        self._draw_charts()


if __name__ == "__main__":
    app = BudgetApp()
    app.mainloop()
