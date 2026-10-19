"""Widgets used by the calendar page: DayCell, MonthGrid and SummaryPanel."""

import calendar
import tkinter as tk
from datetime import date
from tkinter import ttk

from ...config import FONT, Layout, PERIODS, Palette as P
from ...date_range import DateRange
from ...formatting import Formatter, Parser
from ..basic import ClickableLabel, StyledButton, StyledEntry, StyledLabel
from ..charts import BreakdownChart
from ..containers import ScrollArea
from ..controls import SegmentedControl
from ..drawing import round_rect

money = Formatter.money


def _net_color(income, expense):
    return P.RED_TEXT if income < expense else P.GREEN_TEXT if income > expense else P.TEXT


class DayCell(tk.Canvas):
    """One day in the month grid: the number plus a small spent/earned badge."""

    def __init__(self, parent, day, totals, selected, mode, on_click):
        super().__init__(parent, width=Layout.CELL_W, height=Layout.CELL_H, bg=P.PANEL,
                         highlightthickness=0, cursor="hand2")
        self._draw_number(day, selected)
        self._draw_badge(totals, mode)
        self.bind("<Button-1>", lambda _e: on_click(day))

    def _draw_number(self, day, selected):
        mid = Layout.CELL_W / 2
        if selected:
            round_rect(self, mid - 22, 3, mid + 22, 33, 14, fill=P.OLIVE, outline="")
        color = P.TEXT
        if day.weekday() in (5, 6):                      # Sat / Sun
            color = P.RED_TEXT
        if day == day.today() and not selected:
            color = P.GOLD
        if selected:
            color = P.CREAM
        self.create_text(mid, 18, text=str(day.day), fill=color, font=(FONT, 13 if selected else 11))

    def _draw_badge(self, totals, mode):
        value = {"Expenses": -totals.expense, "Income": totals.income}.get(mode, totals.net)
        if not value:
            return
        mid = Layout.CELL_W / 2
        label = Formatter.short_num(value)
        half = len(label) * 3.3 + 6
        self.create_rectangle(mid - half, 38, mid + half, 52,
                              fill=P.GREEN if value > 0 else P.RED, outline="")
        self.create_text(mid, 45, text=label, fill="white", font=(FONT, 8, "bold"))


class MonthGrid(tk.Frame):
    """Month navigation, day grid, display-mode switch and month totals."""

    def __init__(self, parent, app, on_select):
        super().__init__(parent, bg=P.PANEL)
        self._tracker, self._view, self._on_select = app.tracker, app.view, on_select
        self._build_header()
        self._cells_frame = tk.Frame(self, bg=P.PANEL)
        self._cells_frame.pack(pady=(6, 4))
        self._build_mode_row()
        self._build_totals_row()
        self.render()

    def _build_header(self):
        head = tk.Frame(self, bg=P.PANEL)
        head.pack(fill="x")
        ClickableLabel(head, "‹", lambda: self._change_month(-1), 18, True, P.CREAM_SOFT).pack(side="left")
        self._month_lbl = StyledLabel(head, "", 12)
        self._month_lbl.pack(side="left", expand=True)
        ClickableLabel(head, "›", lambda: self._change_month(1), 18, True, P.CREAM_SOFT).pack(side="right")

    def _build_mode_row(self):
        row = tk.Frame(self, bg=P.PANEL)
        row.pack(pady=(6, 8))
        SegmentedControl(row, ["Expenses", "Income", "Total"], self._view.cal_mode,
                         self._set_mode, P.PANEL).pack()

    def _build_totals_row(self):
        row = tk.Frame(self, bg=P.PANEL)
        row.pack(fill="x", pady=(4, 0))
        self._month_totals = {}
        for key, title in [("total", "Total"), ("income", "Income"), ("expense", "Expense")]:
            cell = tk.Frame(row, bg=P.PANEL)
            cell.pack(side="left", expand=True)
            self._month_totals[key] = StyledLabel(cell, "", 13, True)
            self._month_totals[key].pack()
            StyledLabel(cell, title, 9, color=P.MUTED).pack()

    def render(self):
        v = self._view
        for w in self._cells_frame.winfo_children():
            w.destroy()
        self._month_lbl.config(text=f"{calendar.month_name[v.cal_month]} {v.cal_year}")
        for i, name in enumerate(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
            StyledLabel(self._cells_frame, name, 9, True, P.RED_TEXT if i in (0, 6) else P.MUTED).grid(
                row=0, column=i, pady=(2, 6), sticky="ew")
            self._cells_frame.columnconfigure(i, minsize=Layout.CELL_W)
        weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(v.cal_year, v.cal_month)
        for r, week in enumerate(weeks, start=1):
            for col, num in enumerate(week):
                if num:
                    day = date(v.cal_year, v.cal_month, num)
                    totals = self._tracker.totals(DateRange.single(day))
                    DayCell(self._cells_frame, day, totals, day == v.selected_day,
                            v.cal_mode, self._select_day).grid(row=r, column=col)
        self._update_month_totals()

    def _update_month_totals(self):
        t = self._tracker.totals(DateRange.month(self._view.cal_year, self._view.cal_month))
        self._month_totals["total"].config(text=money(t.net), fg=_net_color(t.income, t.expense))
        self._month_totals["income"].config(text=money(t.income), fg=P.GREEN_TEXT)
        self._month_totals["expense"].config(text=money(t.expense), fg=P.RED_TEXT)

    def _select_day(self, day):
        self._view.selected_day = day
        self.render()
        self._on_select()

    def _change_month(self, delta):
        self._view.shift_cal_month(delta)
        self.render()

    def _set_mode(self, option):
        self._view.cal_mode = option
        self.render()


class SummaryPanel(tk.Frame):
    """Day / Week / Month / Year / Custom summary with category bars and an entry table."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=P.PANEL)
        self._tracker, self._view = app.tracker, app.view
        StyledLabel(self, "Summary", 13, True).pack(anchor="w")
        holder = tk.Frame(self, bg=P.PANEL)
        holder.pack(fill="both", expand=True, pady=(8, 0))
        scroll = ScrollArea(holder, P.PANEL)
        scroll.pack(fill="both", expand=True)
        inner = scroll.body

        self._build_period_selector(inner)
        self._build_custom_row(inner)
        self._build_stats(inner)
        self._build_chart_and_table(inner)
        self.refresh()

    # ---- construction ----
    def _build_period_selector(self, inner):
        self._period_row = tk.Frame(inner, bg=P.PANEL)
        self._period_row.pack(fill="x")
        SegmentedControl(self._period_row, PERIODS, self._view.cal_period,
                         self._set_period, P.PANEL).pack(anchor="w")

    def _build_custom_row(self, inner):
        self._custom_row = tk.Frame(inner, bg=P.PANEL)       # shown only for "Custom"
        start, end = self._view.custom_range
        StyledLabel(self._custom_row, "From", 9, color=P.MUTED).pack(side="left")
        self._start_entry = StyledEntry(self._custom_row, 11, start.isoformat(), 10)
        self._start_entry.pack(side="left", padx=6, ipady=3)
        StyledLabel(self._custom_row, "To", 9, color=P.MUTED).pack(side="left")
        self._end_entry = StyledEntry(self._custom_row, 11, end.isoformat(), 10)
        self._end_entry.pack(side="left", padx=6, ipady=3)
        StyledButton(self._custom_row, "Apply", self.refresh).pack(side="left", padx=6)

    def _build_stats(self, inner):
        self._range_lbl = StyledLabel(inner, "", 10, color=P.MUTED)
        self._range_lbl.pack(anchor="w", pady=(12, 4))
        row = tk.Frame(inner, bg=P.PANEL)
        row.pack(fill="x", pady=(0, 10))
        self._stats = {}
        for key, title in [("income", "Income"), ("expense", "Expense"), ("net", "Net")]:
            cell = tk.Frame(row, bg=P.PANEL)
            cell.pack(side="left", expand=True, anchor="w")
            self._stats[key] = StyledLabel(cell, "", 13, True)
            self._stats[key].pack(anchor="w")
            StyledLabel(cell, title, 9, color=P.MUTED).pack(anchor="w")

    def _build_chart_and_table(self, inner):
        self._chart = BreakdownChart(inner)
        self._chart.pack(fill="x", pady=6)
        self._tree = ttk.Treeview(inner, columns=("date", "cat", "acc", "amt"),
                                  show="headings", height=6)
        for col, title, w in [("date", "Date", 84), ("cat", "Category", 90),
                              ("acc", "Account", 90), ("amt", "Amount", 80)]:
            self._tree.heading(col, text=title)
            self._tree.column(col, width=w, anchor="w")
        self._tree.tag_configure("exp", foreground=P.RED_TEXT)
        self._tree.tag_configure("inc", foreground=P.GREEN_TEXT)
        self._tree.pack(fill="x", pady=(6, 4))

    # ---- behaviour ----
    def _set_period(self, option):
        self._view.cal_period = option
        self.refresh()

    def _resolve_period(self):
        """DateRange for the current choice, or None (with a message) if Custom dates are bad."""
        if self._view.cal_period != "Custom":
            self._custom_row.pack_forget()
        else:
            self._custom_row.pack(fill="x", pady=(10, 0), after=self._period_row)
            start, end = Parser.date(self._start_entry.get()), Parser.date(self._end_entry.get())
            if start is None or end is None or start > end:
                self._range_lbl.config(text="Enter valid dates (YYYY-MM-DD), start before end.")
                return None
            self._view.custom_range = (start, end)
        return DateRange.for_period(self._view.cal_period, self._view.selected_day,
                                    self._view.custom_range)

    def refresh(self):
        period = self._resolve_period()
        if period is None:
            return
        totals = self._tracker.totals(period)
        self._range_lbl.config(text=period.label())
        self._stats["income"].config(text=money(totals.income), fg=P.GREEN_TEXT)
        self._stats["expense"].config(text=money(totals.expense), fg=P.RED_TEXT)
        self._stats["net"].config(text=money(totals.net), fg=_net_color(totals.income, totals.expense))
        self._chart.set_data(self._tracker.spent_by_category(period))
        self._fill_table(period)

    def _fill_table(self, period):
        self._tree.delete(*self._tree.get_children())
        entries = sorted(self._tracker.entries_in_range(period),
                         key=lambda e: (e.date, e.id), reverse=True)
        for e in entries:
            self._tree.insert("", "end", tags=("exp" if e.is_expense else "inc",),
                              values=(e.date, e.category, e.account,
                                      money(e.signed_amount, sign=True)))
