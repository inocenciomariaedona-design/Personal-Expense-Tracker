"""Ledger page: your month at a glance, entries grouped by day."""

import calendar
import tkinter as tk
from tkinter import messagebox

from ...config import Palette as P
from ...date_range import DateRange
from ...formatting import Formatter, Parser
from ..basic import ClickableLabel, StyledButton, StyledLabel
from ..containers import RoundedPanel, ScrollArea
from .base import Page

money = Formatter.money


class LedgerPage(Page):
    key = "ledger"
    nav_label = "Ledger"
    subtitle = "Here's how your month is unfolding."

    def heading(self):
        return Formatter.greeting(), self.subtitle

    def build_body(self, body):
        wrap = tk.Frame(body, bg=P.BG)
        wrap.pack(fill="both", expand=True, padx=36, pady=(0, 20))
        if self.tracker.is_first_run:
            self._build_welcome(wrap)
        period = DateRange.month(self.view.ledger_year, self.view.ledger_month)
        self._build_summary_card(wrap, period)
        self._build_listing(wrap, period)

    # ---- sections ----
    def _build_welcome(self, wrap):
        panel = RoundedPanel(wrap, P.OLIVE_DEEP, radius=24, pad=22)
        panel.pack(fill="x", pady=(0, 14))
        card = panel.body
        StyledLabel(card, "Welcome. Let's begin gently.", 15, True, P.CREAM, P.OLIVE_DEEP).pack(anchor="w")
        StyledLabel(card, "Start by telling Spendly what you're holding in each account. "
                          "Everything begins at zero, and you can log your first entry whenever you're ready.",
                    10, color=P.CREAM_SOFT, bg=P.OLIVE_DEEP).pack(anchor="w", pady=(4, 12))
        for child in card.winfo_children():
            if isinstance(child, tk.Label):
                child.config(wraplength=760, justify="left")
        StyledButton(card, "Open Wallet", lambda: self.navigate("wallet"), "cream").pack(anchor="w")

    def _build_summary_card(self, wrap, period):
        totals = self.tracker.totals(period)
        panel = RoundedPanel(wrap, P.PANEL, radius=24, pad=20)
        panel.pack(fill="x", pady=(0, 14))
        card = panel.body

        nav = tk.Frame(card, bg=P.PANEL)
        nav.pack(fill="x")
        ClickableLabel(nav, "‹", lambda: self._shift_month(-1), 18, True, P.CREAM_SOFT).pack(side="left")
        StyledLabel(nav, f"{calendar.month_name[self.view.ledger_month]} {self.view.ledger_year}",
                    12).pack(side="left", padx=14)
        ClickableLabel(nav, "›", lambda: self._shift_month(1), 18, True, P.CREAM_SOFT).pack(side="left")
        StyledLabel(nav, f"All accounts  {money(self.tracker.total_balance)}", 10,
                    color=P.MUTED).pack(side="right")

        net = totals.net
        net_color = P.RED_TEXT if net < 0 else (P.GREEN_TEXT if net > 0 else P.TEXT)
        StyledLabel(card, money(net), 30, True, net_color).pack(anchor="w", pady=(8, 0))
        stats = tk.Frame(card, bg=P.PANEL)
        stats.pack(fill="x", pady=(2, 0))
        StyledLabel(stats, "Spent", 10, color=P.MUTED).pack(side="left")
        StyledLabel(stats, money(totals.expense), 11, True, P.RED_TEXT).pack(side="left", padx=(6, 26))
        StyledLabel(stats, "Earned", 10, color=P.MUTED).pack(side="left")
        StyledLabel(stats, money(totals.income), 11, True, P.GREEN_TEXT).pack(side="left", padx=6)

    def _build_listing(self, wrap, period):
        scroll = ScrollArea(wrap, P.BG)
        scroll.pack(fill="both", expand=True)
        listing = scroll.body
        entries = sorted(self.tracker.entries_in_range(period),
                         key=lambda e: (e.date, e.id), reverse=True)
        if not entries:
            StyledLabel(listing, "Nothing logged for this month yet.", 11, color=P.MUTED).pack(pady=40)
            return
        for day_text, items in self._group_by_day(entries).items():
            self._build_day_group(listing, day_text, items)

    def _build_day_group(self, listing, day_text, items):
        day = Parser.date(day_text)
        totals = self.tracker.totals(DateRange.single(day))
        panel = RoundedPanel(listing, P.PANEL, radius=20, pad=8)
        panel.pack(fill="x", pady=(0, 12), padx=(0, 10))
        group = panel.body

        head = tk.Frame(group, bg=P.PANEL)
        head.pack(fill="x", padx=10, pady=(8, 8))
        StyledLabel(head, day.strftime("%a, %m/%d"), 10, True, P.CREAM_SOFT).pack(side="left")
        parts = []
        if totals.income:
            parts.append(f"Income {money(totals.income)}")
        if totals.expense:
            parts.append(f"Expense {money(totals.expense)}")
        StyledLabel(head, "     ".join(parts), 9, color=P.MUTED).pack(side="right")
        for entry in items:
            self._build_entry_row(group, entry)

    def _build_entry_row(self, group, entry):
        tk.Frame(group, bg=P.HAIRLINE, height=1).pack(fill="x", padx=10)
        row = tk.Frame(group, bg=P.PANEL)
        row.pack(fill="x", padx=10, pady=9)

        left = tk.Frame(row, bg=P.PANEL)
        left.pack(side="left")
        StyledLabel(left, entry.category, 12).pack(anchor="w")
        if entry.note:
            StyledLabel(left, entry.note, 9, color=P.CREAM_SOFT).pack(anchor="w")

        ClickableLabel(row, "Remove", lambda eid=entry.id: self._confirm_delete(eid),
                       9, color=P.MUTED).pack(side="right", padx=(16, 0))
        right = tk.Frame(row, bg=P.PANEL)
        right.pack(side="right")
        color = P.RED_TEXT if entry.is_expense else P.GREEN_TEXT
        StyledLabel(right, money(entry.signed_amount, sign=True), 12, True, color).pack(anchor="e")
        StyledLabel(right, entry.account, 9, color=P.MUTED).pack(anchor="e")

    # ---- actions ----
    @staticmethod
    def _group_by_day(entries):
        groups = {}
        for e in entries:
            groups.setdefault(e.date, []).append(e)
        return groups

    def _shift_month(self, delta):
        self.view.shift_ledger_month(delta)
        self.refresh()

    def _confirm_delete(self, entry_id):
        if not messagebox.askyesno("Remove entry",
                                   "Remove this entry? The account balance will be adjusted back."):
            return
        if not self.tracker.delete_entry(entry_id):
            messagebox.showwarning("Cannot remove",
                                   "Removing this income would take that account below zero.")
        self.refresh()
