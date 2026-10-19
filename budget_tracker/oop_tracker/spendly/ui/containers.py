"""Container widgets: RoundedPanel (a card) and ScrollArea."""

import tkinter as tk
from tkinter import ttk

from ..config import Palette as P
from .drawing import round_rect


class RoundedPanel(tk.Canvas):
    """A rounded card. Place the panel itself; put children in `panel.body`."""

    def __init__(self, parent, fill=P.PANEL, radius=22, pad=18, stretch=False):
        super().__init__(parent, bg=parent["bg"], highlightthickness=0, bd=0, height=40)
        self._fill, self._radius, self._pad, self._stretch = fill, radius, pad, stretch
        self.body = tk.Frame(self, bg=fill)
        self._body_window = self.create_window(pad, pad, window=self.body, anchor="nw")
        self.bind("<Configure>", self._redraw)
        self.body.bind("<Configure>", self._fit)

    def _redraw(self, _event=None):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4 or h < 4:
            return
        self.delete("shape")
        round_rect(self, 1, 1, w - 1, h - 1, self._radius, fill=self._fill, outline="", tags="shape")
        self.tag_lower("shape")
        inner_w = max(w - 2 * self._pad, 1)
        if self._stretch:
            self.itemconfigure(self._body_window, width=inner_w, height=max(h - 2 * self._pad, 1))
        else:
            self.itemconfigure(self._body_window, width=inner_w)

    def _fit(self, _event=None):
        if not self._stretch:
            want = self.body.winfo_reqheight() + 2 * self._pad
            if int(float(self.cget("height"))) != want:
                self.configure(height=want)


class ScrollArea(tk.Frame):
    """Vertically scrollable frame. Fill `scroll.body`. Mouse wheel is routed by
    `ScrollArea.route_mousewheel`, which scrolls whichever area is under the pointer."""

    _registry = {}          # str(canvas) -> canvas, shared by every ScrollArea

    def __init__(self, parent, bg):
        super().__init__(parent, bg=bg)
        canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        bar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self.body = tk.Frame(canvas, bg=bg)
        window = canvas.create_window(0, 0, window=self.body, anchor="nw")
        self.body.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))
        key = str(canvas)
        ScrollArea._registry[key] = canvas
        canvas.bind("<Destroy>", lambda _e: ScrollArea._registry.pop(key, None))

    @classmethod
    def route_mousewheel(cls, root, event):
        try:
            widget = root.winfo_containing(event.x_root, event.y_root)
        except (KeyError, tk.TclError):
            return
        while widget is not None:
            canvas = cls._registry.get(str(widget))
            if canvas is not None:
                up = getattr(event, "delta", 0) > 0 or event.num == 4
                canvas.yview_scroll(-3 if up else 3, "units")
                return
            widget = widget.master
