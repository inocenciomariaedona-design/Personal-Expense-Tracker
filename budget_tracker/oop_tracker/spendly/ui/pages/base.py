"""Page: abstract base for every screen. Subclasses implement build_body()."""

import tkinter as tk
from abc import ABC, abstractmethod

from ...config import Palette as P
from ..header import PageHeader


class Page(tk.Frame, ABC):
    key = ""                    # registry / navigation key
    nav_label = None            # sidebar text; None = not shown in the sidebar
    title = ""
    subtitle = ""
    show_new_button = True

    def __init__(self, parent, app):
        super().__init__(parent, bg=P.BG)
        self.app = app
        self.tracker = app.tracker
        self.view = app.view

    def heading(self):
        """(title, subtitle) for the header. Override when it is dynamic."""
        return self.title, self.subtitle

    def build(self, width):
        title, subtitle = self.heading()
        on_new = (lambda: self.navigate("add")) if self.show_new_button else None
        PageHeader(self, title, subtitle, width, on_new).pack(fill="x")
        body = tk.Frame(self, bg=P.BG)
        body.pack(fill="both", expand=True)
        self.build_body(body)

    @abstractmethod
    def build_body(self, body): ...

    def navigate(self, key):
        self.app.navigate(key)

    def refresh(self):
        self.app.refresh()
