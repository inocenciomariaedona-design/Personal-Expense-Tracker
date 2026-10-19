"""SpendlyApp: owns the window, the sidebar and page navigation."""

import tkinter as tk
from tkinter import messagebox

from ..config import Palette as P
from .containers import ScrollArea
from .pages import PAGES
from .sidebar import Sidebar
from .styles import ThemeStyles
from .view_state import ViewState


class SpendlyApp:
    DEFAULT_PAGE = "ledger"

    def __init__(self, tracker):
        self.tracker = tracker
        self.view = ViewState()
        self.current_key = self.DEFAULT_PAGE
        self._page = None
        tracker.on_save_error = lambda msg: messagebox.showerror("Could not save", msg)

        self.root = tk.Tk()
        self.root.title("Spendly")
        self.root.geometry("1240x800")
        self.root.minsize(1100, 760)
        self.root.configure(bg=P.BG)
        ThemeStyles.apply(self.root)
        self._build_layout()

    def _build_layout(self):
        items = [(key, cls.nav_label) for key, cls in PAGES.items() if cls.nav_label]
        self.sidebar = Sidebar(self.root, items, self.navigate)
        self.sidebar.pack(side="left", fill="y")
        self.stage = tk.Frame(self.root, bg=P.BG)
        self.stage.pack(side="left", fill="both", expand=True)
        wheel = lambda event: ScrollArea.route_mousewheel(self.root, event)
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.root.bind_all(sequence, wheel)

    def run(self):
        self.navigate(self.DEFAULT_PAGE)
        self.root.mainloop()

    def refresh(self):
        self.navigate(self.current_key)

    def navigate(self, key):
        """Build the page off-screen, let it finish drawing, then reveal it (no flicker)."""
        self.current_key = key
        self.root.update_idletasks()
        w = max(self.stage.winfo_width(), 900)
        h = max(self.stage.winfo_height(), 600)
        page = PAGES[key](self.stage, self)
        page.build(w)
        page.place(x=-20000, y=0, width=w, height=h)
        self.root.update()
        page.place_forget()
        page.place(x=0, y=0, relwidth=1, relheight=1)
        if self._page is not None:
            self._page.destroy()
        self._page = page
        self.sidebar.set_active(key)
