"""Category charts. CategoryChart is abstract; subclasses decide how to draw."""

import tkinter as tk
from abc import ABC, abstractmethod

from ..config import FONT, Palette as P, category_color
from ..formatting import Formatter
from .drawing import round_rect


class CategoryChart(tk.Canvas, ABC):
    def __init__(self, parent, bg=P.PANEL, **kwargs):
        super().__init__(parent, bg=bg, highlightthickness=0, **kwargs)
        self._data = {}
        self.bind("<Configure>", self.redraw)

    def set_data(self, data):
        self._data = dict(data)
        self.redraw()

    def redraw(self, _event=None):
        self.delete("all")
        self._draw(self._data)

    @abstractmethod
    def _draw(self, data): ...


class BreakdownChart(CategoryChart):
    """Soft horizontal bars: name and amount on one line, thin bar underneath."""

    def __init__(self, parent, bg=P.PANEL):
        super().__init__(parent, bg, height=90)

    def _draw(self, data):
        w = self.winfo_width()
        w = w if w > 60 else 320
        rows = sorted([(k, v) for k, v in data.items() if v > 0], key=lambda kv: -kv[1])
        if not rows:
            self.configure(height=90)
            self.create_text(w / 2, 45, text="Nothing spent in this period yet.",
                             fill=P.MUTED, font=(FONT, 11))
            return
        total = sum(v for _, v in rows)
        top = rows[0][1]
        y = 6
        for name, amount in rows:
            self.create_text(4, y + 10, text=name, anchor="w", fill=P.TEXT, font=(FONT, 10))
            self.create_text(w - 4, y + 10, anchor="e", fill=P.MUTED, font=(FONT, 10),
                             text=f"{Formatter.money(amount)}   {amount / total * 100:.0f}%")
            round_rect(self, 4, y + 24, w - 4, y + 30, 3, fill=P.TRACK, outline="")
            round_rect(self, 4, y + 24, 4 + max((w - 8) * amount / top, 7), y + 30, 3,
                       fill=category_color(name), outline="")
            y += 42
        self.configure(height=y + 4)


class DonutChart(CategoryChart):
    def __init__(self, parent, size=240, bg=P.PANEL):
        super().__init__(parent, bg, width=size, height=size)
        self._size = size

    def _draw(self, data):
        size, pad = self._size, 24
        box = (pad, pad, size - pad, size - pad)
        total = sum(data.values())
        if total <= 0:
            self.create_arc(*box, start=90, extent=359.9, style="arc", outline=P.TRACK, width=26)
        else:
            start = 90
            for name, amount in sorted(data.items(), key=lambda kv: -kv[1]):
                if amount <= 0:
                    continue
                extent = -min(amount / total * 360, 359.9)      # negative = clockwise
                self.create_arc(*box, start=start, extent=extent, style="arc",
                                outline=category_color(name), width=26)
                start += extent
        self.create_text(size / 2, size / 2 - 10, text=Formatter.money(total),
                         fill=P.TEXT, font=(FONT, 17, "bold"))
        self.create_text(size / 2, size / 2 + 16, text="spent", fill=P.MUTED, font=(FONT, 10))
