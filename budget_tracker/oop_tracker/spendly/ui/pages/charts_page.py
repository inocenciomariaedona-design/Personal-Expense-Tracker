"""Charts page: where the money went, by category."""

import tkinter as tk
from datetime import date

from ...config import Palette as P
from ...date_range import DateRange
from ...formatting import Formatter
from ..basic import StyledLabel
from ..charts import BreakdownChart, DonutChart
from ..containers import RoundedPanel, ScrollArea
from ..controls import SegmentedControl
from .base import Page


class ChartsPage(Page):
    key = "charts"
    nav_label = "Charts"
    title = "Charts"
    subtitle = "Where it all went, gently laid out."

    def build_body(self, body):
        wrap = tk.Frame(body, bg=P.BG)
        wrap.pack(fill="both", expand=True, padx=36, pady=(0, 22))
        wrap.columnconfigure(1, weight=1)
        wrap.rowconfigure(1, weight=1)

        SegmentedControl(wrap, ["Day", "Week", "Month", "Year", "All"], self.view.chart_period,
                         self._set_period, P.BG).grid(row=0, column=0, columnspan=2,
                                                      sticky="w", pady=(0, 14))
        self._build_donut_card(wrap)
        self._build_bars_card(wrap)
        self._update()

    def _build_donut_card(self, wrap):
        panel = RoundedPanel(wrap, P.PANEL, radius=24, pad=20, stretch=True)
        panel.configure(width=320)
        panel.grid(row=1, column=0, sticky="ns", padx=(0, 16))
        card = panel.body
        StyledLabel(card, "Spending mix", 13, True).pack(anchor="w")
        self._range_lbl = StyledLabel(card, "", 9, color=P.MUTED)
        self._range_lbl.pack(anchor="w", pady=(2, 10))
        self._donut = DonutChart(card)
        self._donut.pack()
        tally = tk.Frame(card, bg=P.PANEL)
        tally.pack(fill="x", pady=(16, 0))
        self._tally = {}
        for key, title, color in [("spent", "Spent", P.RED_TEXT), ("earned", "Earned", P.GREEN_TEXT)]:
            cell = tk.Frame(tally, bg=P.PANEL)
            cell.pack(side="left", expand=True)
            self._tally[key] = StyledLabel(cell, "", 14, True, color)
            self._tally[key].pack()
            StyledLabel(cell, title, 9, color=P.MUTED).pack()

    def _build_bars_card(self, wrap):
        panel = RoundedPanel(wrap, P.PANEL, radius=24, pad=20, stretch=True)
        panel.grid(row=1, column=1, sticky="nsew")
        StyledLabel(panel.body, "By category", 13, True).pack(anchor="w", pady=(0, 8))
        scroll = ScrollArea(panel.body, P.PANEL)
        scroll.pack(fill="both", expand=True)
        self._bars = BreakdownChart(scroll.body)
        self._bars.pack(fill="x")

    def _set_period(self, option):
        self.view.chart_period = option
        self._update()

    def _update(self):
        period = DateRange.for_period(self.view.chart_period, date.today())
        totals = self.tracker.totals(period)
        data = self.tracker.spent_by_category(period)
        self._range_lbl.config(text="All time" if self.view.chart_period == "All" else period.label())
        self._tally["spent"].config(text=Formatter.money(totals.expense))
        self._tally["earned"].config(text=Formatter.money(totals.income))
        self._donut.set_data(data)
        self._bars.set_data(data)
