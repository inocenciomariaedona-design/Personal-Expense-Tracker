"""Sidebar navigation."""

import tkinter as tk

from ..config import FONT, Layout, Palette as P
from .basic import StyledLabel


class Sidebar(tk.Frame):
    def __init__(self, parent, items, on_navigate):
        """items: iterable of (page_key, label). on_navigate(page_key) is called on click."""
        super().__init__(parent, bg=P.SIDEBAR_BG, width=Layout.SIDEBAR_W)
        self.pack_propagate(False)
        StyledLabel(self, "Spendly", 20, True, P.GOLD, P.SIDEBAR_BG).pack(anchor="w", padx=24, pady=(34, 2))
        StyledLabel(self, "Your money, calmly", 9, color=P.MUTED, bg=P.SIDEBAR_BG).pack(
            anchor="w", padx=24, pady=(0, 30))
        self._nav_items = {}
        for key, label in items:
            lab = tk.Label(self, text=label, anchor="w", bg=P.SIDEBAR_BG, fg=P.TEXT,
                           padx=24, pady=12, cursor="hand2", font=(FONT, 12))
            lab.pack(fill="x", padx=12, pady=2)
            lab.bind("<Button-1>", lambda _e, k=key: on_navigate(k))
            self._nav_items[key] = lab
        StyledLabel(self, "Saved automatically", 9, color=P.MUTED, bg=P.SIDEBAR_BG).pack(side="bottom", pady=20)

    def set_active(self, key):
        for name, lab in self._nav_items.items():
            on = name == key
            lab.config(bg=P.OLIVE if on else P.SIDEBAR_BG, fg=P.GOLD if on else P.TEXT)
