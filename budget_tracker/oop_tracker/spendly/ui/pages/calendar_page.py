"""Calendar page: spent / earned per day plus period summaries."""

import tkinter as tk

from ...config import Layout, Palette as P
from ..containers import RoundedPanel
from .base import Page
from .calendar_widgets import MonthGrid, SummaryPanel


class CalendarPage(Page):
    key = "calendar"
    nav_label = "Calendar"
    title = "Calendar"
    subtitle = "Look back, one day at a time."

    def build_body(self, body):
        wrap = tk.Frame(body, bg=P.BG)
        wrap.pack(fill="both", expand=True, padx=36, pady=(0, 22))
        wrap.columnconfigure(1, weight=1)
        wrap.rowconfigure(0, weight=1)

        left = RoundedPanel(wrap, P.PANEL, radius=24, pad=18, stretch=True)
        left.configure(width=Layout.CELL_W * 7 + 40)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 16))
        right = RoundedPanel(wrap, P.PANEL, radius=24, pad=18, stretch=True)
        right.grid(row=0, column=1, sticky="nsew")

        summary = SummaryPanel(right.body, self.app)
        summary.pack(fill="both", expand=True)
        MonthGrid(left.body, self.app, on_select=summary.refresh).pack(fill="x")
