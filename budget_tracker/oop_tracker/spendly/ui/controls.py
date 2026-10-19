"""Interactive controls: SegmentedControl and CategoryTile."""

import tkinter as tk

from ..config import FONT, Palette as P
from .drawing import round_rect


class SegmentedControl(tk.Frame):
    """Pill-style option switcher (Expenses | Income | Total)."""

    def __init__(self, parent, options, value, command, bg):
        super().__init__(parent, bg=P.TILE_LINE, padx=1, pady=1)
        self._idle_bg = bg
        self._on_select = command
        self._choice_labels = {}
        for i, option in enumerate(options):
            lab = tk.Label(self, text=option, padx=13, pady=6, cursor="hand2", font=(FONT, 10))
            lab.grid(row=0, column=i, padx=(0 if i == 0 else 1, 0))
            lab.bind("<Button-1>", lambda _e, o=option: self.select(o))
            self._choice_labels[option] = lab
        self.select(value, fire=False)

    def select(self, option, fire=True):
        for name, lab in self._choice_labels.items():
            on = name == option
            lab.config(bg=P.OLIVE if on else self._idle_bg, fg=P.GOLD if on else P.TEXT)
        if fire:
            self._on_select(option)


class CategoryTile(tk.Canvas):
    def __init__(self, parent, text, selected, command):
        super().__init__(parent, height=66, bg=P.BG, highlightthickness=0, cursor="hand2")
        self._caption, self._selected = text, selected
        self.bind("<Configure>", self._draw)
        self.bind("<Button-1>", lambda _e: command())
        self._draw()

    def _draw(self, _event=None):
        w = self.winfo_width()
        w = w if w > 10 else 160
        self.delete("all")
        if self._selected:
            round_rect(self, 2, 2, w - 2, 64, 18, fill=P.TILE_ON, outline=P.GOLD, width=2)
        else:
            round_rect(self, 2, 2, w - 2, 64, 18, fill=P.PANEL, outline=P.TILE_LINE, width=1)
        self.create_text(w / 2, 33, text=self._caption,
                         fill=P.GOLD if self._selected else P.TEXT,
                         font=(FONT, 11, "bold" if self._selected else "normal"))
