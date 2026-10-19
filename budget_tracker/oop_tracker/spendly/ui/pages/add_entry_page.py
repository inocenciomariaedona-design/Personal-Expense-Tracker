"""New entry page: log an expense (deducted from an account) or income (added to one)."""

import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from ...config import CATEGORIES, FONT, INCOME_CATEGORIES, Palette as P
from ...formatting import Formatter, Parser
from ..basic import StyledButton, StyledEntry, StyledLabel
from ..containers import RoundedPanel
from ..controls import CategoryTile, SegmentedControl
from .base import Page


class AddEntryPage(Page):
    key = "add"
    nav_label = None                       # reached via the "+ New entry" button
    title = "New entry"
    subtitle = "Take a moment to note it down."
    show_new_button = False

    FIELD_BG = "#4a4217"

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._kind = "expense"
        self._category = "Food"

    def build_body(self, body):
        wrap = tk.Frame(body, bg=P.BG)
        wrap.pack(fill="both", expand=True, padx=36, pady=(0, 20))

        self._tiles = tk.Frame(wrap, bg=P.BG)
        for c in range(4):
            self._tiles.columnconfigure(c, weight=1, uniform="tile")
        SegmentedControl(wrap, ["Expense", "Income"], "Expense", self._set_kind, P.BG).pack(
            anchor="w", pady=(0, 10))
        self._tiles.pack(fill="x")
        self._build_form(wrap)
        self._render_tiles()

    # ---- category tiles ----
    def _render_tiles(self):
        for w in self._tiles.winfo_children():
            w.destroy()
        cats = list(CATEGORIES) if self._kind == "expense" else INCOME_CATEGORIES
        if self._category not in cats:
            self._category = cats[0]
        for i, name in enumerate(cats):
            CategoryTile(self._tiles, name, name == self._category,
                         lambda n=name: self._pick(n)).grid(
                row=i // 4, column=i % 4, padx=6, pady=6, sticky="ew")

    def _pick(self, name):
        self._category = name
        self._render_tiles()

    def _set_kind(self, option):
        self._kind = option.lower()
        self._render_tiles()

    # ---- form ----
    def _build_form(self, wrap):
        outer = RoundedPanel(wrap, P.OLIVE_DEEP, radius=26, pad=22)
        outer.pack(fill="x", pady=(14, 0))
        panel = outer.body
        for i, text in enumerate(["Amount", "Account", "Date  (YYYY-MM-DD)"]):
            StyledLabel(panel, text, 9, color=P.CREAM_SOFT, bg=P.OLIVE_DEEP).grid(
                row=0, column=i, sticky="w", padx=6)

        self._amount_entry = StyledEntry(panel, 12, size=18, bg=self.FIELD_BG)
        self._amount_entry.grid(row=1, column=0, padx=6, pady=(4, 12), ipady=6, sticky="w")

        self._account_var = tk.StringVar(value=self.tracker.wallet.names[0])
        ttk.Combobox(panel, textvariable=self._account_var, state="readonly", width=16,
                     values=self.tracker.wallet.names, font=(FONT, 11)).grid(
            row=1, column=1, padx=6, pady=(4, 12), ipady=6, sticky="w")

        date_cell = tk.Frame(panel, bg=P.OLIVE_DEEP)
        date_cell.grid(row=1, column=2, padx=6, pady=(4, 12), sticky="w")
        self._date_entry = StyledEntry(date_cell, 12, date.today().isoformat(), bg=self.FIELD_BG)
        self._date_entry.pack(side="left", ipady=6)
        StyledButton(date_cell, "Today",
                     lambda: self._date_entry.set_text(date.today().isoformat()),
                     "quiet").pack(side="left", padx=(6, 0))

        StyledLabel(panel, "Note  (optional)", 9, color=P.CREAM_SOFT, bg=P.OLIVE_DEEP).grid(
            row=2, column=0, sticky="w", padx=6)
        self._note_entry = StyledEntry(panel, 40, bg=self.FIELD_BG)
        self._note_entry.grid(row=3, column=0, columnspan=2, padx=6, pady=(4, 0), ipady=6, sticky="ew")
        StyledButton(panel, "Save entry", self._save, "cream").grid(
            row=3, column=2, padx=6, pady=(4, 0), sticky="w")

    def _save(self):
        amount = Parser.amount(self._amount_entry.get())
        day = Parser.date(self._date_entry.get())
        if amount is None:
            messagebox.showwarning("Invalid amount", "Enter a number greater than 0.")
            return
        if day is None:
            messagebox.showwarning("Invalid date", "Use the format YYYY-MM-DD.")
            return
        account = self._account_var.get()
        if not self.tracker.add_entry(day, self._kind, self._category, account, amount,
                                      self._note_entry.get().strip()):
            messagebox.showwarning(
                "Not enough in this account",
                f"{account} has {Formatter.money(self.tracker.wallet.balance(account))}.\n"
                "Add money in Wallet first, or choose another account.")
            return
        self.view.show_month_of(day)
        self.navigate("ledger")
