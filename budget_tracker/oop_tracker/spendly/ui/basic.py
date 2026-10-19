"""Styled versions of the basic tk widgets."""

import tkinter as tk

from ..config import FONT, Palette as P
from .drawing import blend


class StyledLabel(tk.Label):
    def __init__(self, parent, text, size=11, bold=False, color=P.TEXT, bg=None):
        super().__init__(parent, text=text, bg=bg or parent["bg"], fg=color,
                         font=(FONT, size, "bold" if bold else "normal"))


class ClickableLabel(StyledLabel):
    """A label that behaves like a link: hand cursor, calls `command()` on click."""

    def __init__(self, parent, text, command, size=11, bold=False, color=P.TEXT, bg=None):
        super().__init__(parent, text, size, bold, color, bg)
        self.config(cursor="hand2")
        self.bind("<Button-1>", lambda _e: command())


class StyledButton(tk.Button):
    STYLES = {"primary": (P.OLIVE, P.CREAM), "quiet": (P.PANEL2, P.TEXT),
              "light": (P.CREAM, P.OLIVE_DEEP), "cream": (P.CREAM, P.OLIVE_DEEP)}

    def __init__(self, parent, text, command, kind="primary"):
        bg, fg = self.STYLES[kind]
        super().__init__(parent, text=text, command=command, bg=bg, fg=fg,
                         activebackground=blend(bg, "#ffffff", 0.12), activeforeground=fg,
                         relief="flat", bd=0, padx=18, pady=8, cursor="hand2",
                         highlightthickness=0, takefocus=0, font=(FONT, 10, "bold"))


class StyledEntry(tk.Entry):
    def __init__(self, parent, width=18, text="", size=11, bg=P.PANEL2):
        super().__init__(parent, width=width, bg=bg, fg=P.TEXT, insertbackground=P.TEXT,
                         relief="flat", font=(FONT, size), highlightthickness=1,
                         highlightbackground=P.TILE_LINE, highlightcolor=P.OLIVE_RING)
        self.insert(0, text)

    def set_text(self, text):
        self.delete(0, "end")
        self.insert(0, text)
