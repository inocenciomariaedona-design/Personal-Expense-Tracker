"""Wallet page: Cash, Bank, Digital Wallet (and your own). Everything starts at zero."""

import tkinter as tk
from tkinter import messagebox, ttk

from ...config import FONT, Palette as P
from ...formatting import Formatter, Parser
from ..basic import StyledButton, StyledEntry, StyledLabel
from ..containers import RoundedPanel, ScrollArea
from .base import Page

money = Formatter.money


class WalletPage(Page):
    key = "wallet"
    nav_label = "Wallet"
    title = "Wallet"
    subtitle = "Everything you're holding, in one place."

    def build_body(self, body):
        wrap = tk.Frame(body, bg=P.BG)
        wrap.pack(fill="both", expand=True, padx=36, pady=(0, 10))
        scroll = ScrollArea(wrap, P.BG)
        scroll.pack(fill="both", expand=True)
        page = scroll.body
        self._build_total(page)
        self._build_account_cards(page)
        self._build_fund_form(page)
        self._build_new_account_form(page)

    def _build_total(self, page):
        total = self.tracker.total_balance
        panel = RoundedPanel(page, P.PANEL, radius=24, pad=20)
        panel.pack(fill="x", pady=(0, 14), padx=(0, 10))
        StyledLabel(panel.body, "Total balance", 10, color=P.MUTED).pack(anchor="w")
        StyledLabel(panel.body, money(total), 30, True, P.GREEN_TEXT if total > 0 else P.TEXT).pack(anchor="w")
        if total == 0:
            StyledLabel(panel.body, "Everything starts at zero. Add what you're holding in each account below.",
                        10, color=P.MUTED).pack(anchor="w", pady=(2, 0))

    def _build_account_cards(self, page):
        cards = tk.Frame(page, bg=P.BG)
        cards.pack(fill="x", padx=(0, 4))
        for c in range(3):
            cards.columnconfigure(c, weight=1, uniform="acc")
        for i, (name, balance) in enumerate(self.tracker.wallet.items()):
            panel = RoundedPanel(cards, P.PANEL, radius=20, pad=18)
            panel.grid(row=i // 3, column=i % 3, sticky="ew", padx=6, pady=6)
            StyledLabel(panel.body, name, 10, color=P.MUTED).pack(anchor="w")
            StyledLabel(panel.body, money(balance), 18, True,
                        P.GREEN_TEXT if balance > 0 else P.TEXT).pack(anchor="w")

    def _build_fund_form(self, page):
        panel = RoundedPanel(page, P.PANEL, radius=22, pad=20)
        panel.pack(fill="x", pady=(14, 0), padx=(0, 10))
        form = panel.body
        StyledLabel(form, "Add or set money", 12, True).grid(row=0, column=0, columnspan=4, sticky="w")
        self._account_var = tk.StringVar(value=self.tracker.wallet.names[0])
        ttk.Combobox(form, textvariable=self._account_var, state="readonly", width=20,
                     values=self.tracker.wallet.names, font=(FONT, 11)).grid(
            row=1, column=0, pady=12, padx=(0, 10))
        self._amount_entry = StyledEntry(form, 14)
        self._amount_entry.grid(row=1, column=1, padx=(0, 10), ipady=5)
        StyledButton(form, "Add money", self._add_money).grid(row=1, column=2, padx=(0, 8))
        StyledButton(form, "Set exact balance", self._set_balance, "quiet").grid(row=1, column=3)

    def _build_new_account_form(self, page):
        panel = RoundedPanel(page, P.PANEL, radius=22, pad=20)
        panel.pack(fill="x", pady=(14, 14), padx=(0, 10))
        form = panel.body
        StyledLabel(form, "New account  (for example GCash, Maya, Savings)", 12, True).grid(
            row=0, column=0, columnspan=2, sticky="w")
        self._name_entry = StyledEntry(form, 26)
        self._name_entry.grid(row=1, column=0, pady=12, padx=(0, 10), ipady=5)
        StyledButton(form, "Create account", self._create_account).grid(row=1, column=1)

    # ---- actions ----
    def _add_money(self):
        amount = Parser.amount(self._amount_entry.get())
        if amount is None:
            messagebox.showwarning("Invalid amount", "Enter a number greater than 0.")
            return
        self.tracker.add_funds(self._account_var.get(), amount)
        self.refresh()

    def _set_balance(self):
        amount = Parser.number(self._amount_entry.get())
        if amount is None:
            messagebox.showwarning("Invalid amount", "Enter a valid number.")
            return
        if amount < 0:
            messagebox.showwarning("Invalid amount", "A balance cannot be negative.")
            return
        self.tracker.set_balance(self._account_var.get(), amount)
        self.refresh()

    def _create_account(self):
        if self.tracker.add_account(self._name_entry.get()):
            self.refresh()
        else:
            messagebox.showwarning("Cannot add", "Enter a unique, non-empty account name.")
