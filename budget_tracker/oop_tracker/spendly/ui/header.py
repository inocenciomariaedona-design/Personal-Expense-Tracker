"""PageHeader: warm olive band that melts into the dark sheet below."""

import tkinter as tk
from datetime import date

from ..config import FONT, Layout, Palette as P
from .basic import StyledButton
from .drawing import blend, round_rect


class PageHeader(tk.Canvas):
    GRADIENT_STEPS = 36
    BUTTON_Y = 74

    def __init__(self, parent, title, subtitle, width, on_new=None):
        super().__init__(parent, height=Layout.HEADER_H, bg=P.OLIVE, highlightthickness=0, bd=0)
        self._heading, self._subheading = title, subtitle
        self._new_window = None
        if on_new:
            button = StyledButton(self, "+  New entry", on_new, "light")
            self._new_window = self.create_window(width - 44, self.BUTTON_Y, window=button, anchor="e")
        self._redraw(width)
        self.bind("<Configure>", lambda e: self._redraw(e.width))

    def _redraw(self, w):
        self.delete("hdr")
        self._draw_gradient(w)
        self._draw_rings(w)
        self._draw_sheet_edge(w)
        self._draw_texts()
        if self._new_window:
            self.coords(self._new_window, w - 44, self.BUTTON_Y)

    def _draw_gradient(self, w):
        h, steps = Layout.HEADER_H, self.GRADIENT_STEPS
        for i in range(steps):
            self.create_rectangle(0, i * h / steps, w, (i + 1) * h / steps + 1,
                                  fill=blend(P.OLIVE_LIGHT, P.OLIVE_DEEP, i / (steps - 1)),
                                  outline="", tags="hdr")

    def _draw_rings(self, w):
        self.create_oval(w - 560, -240, w - 120, 200, outline=P.OLIVE_RING, tags="hdr")
        self.create_oval(w - 430, -150, w - 200, 90, outline=P.OLIVE_RING, tags="hdr")

    def _draw_sheet_edge(self, w):
        h = Layout.HEADER_H
        round_rect(self, 0, h - 34, w, h + 80, 34, fill=P.BG, outline="", tags="hdr")

    def _draw_texts(self):
        today = date.today().strftime("%A, %B %d").replace(" 0", " ")
        self.create_text(44, 34, text=today, anchor="w", fill=P.CREAM_SOFT, font=(FONT, 10), tags="hdr")
        self.create_text(44, 74, text=self._heading, anchor="w", fill=P.CREAM,
                         font=(FONT, 26, "bold"), tags="hdr")
        self.create_text(44, 112, text=self._subheading, anchor="w", fill=P.CREAM_SOFT,
                         font=(FONT, 11), tags="hdr")
