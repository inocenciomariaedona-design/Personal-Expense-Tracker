"""ttk theme (Combobox, Treeview, Scrollbar) matching the palette."""

from tkinter import ttk

from ..config import FONT, Palette as P


class ThemeStyles:
    @staticmethod
    def apply(root):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=P.PANEL2, background=P.PANEL2,
                        foreground=P.TEXT, arrowcolor=P.GOLD, bordercolor=P.TILE_LINE,
                        lightcolor=P.PANEL2, darkcolor=P.PANEL2,
                        selectbackground=P.PANEL2, selectforeground=P.TEXT)
        style.map("TCombobox", fieldbackground=[("readonly", P.PANEL2)],
                  foreground=[("readonly", P.TEXT)],
                  selectbackground=[("readonly", P.PANEL2)],
                  selectforeground=[("readonly", P.TEXT)])
        root.option_add("*TCombobox*Listbox.background", P.PANEL2)
        root.option_add("*TCombobox*Listbox.foreground", P.TEXT)
        root.option_add("*TCombobox*Listbox.selectBackground", P.OLIVE)
        root.option_add("*TCombobox*Listbox.selectForeground", P.CREAM)
        style.configure("Treeview", background=P.PANEL, fieldbackground=P.PANEL,
                        foreground=P.TEXT, rowheight=28, borderwidth=0, font=(FONT, 10),
                        bordercolor=P.PANEL, lightcolor=P.PANEL, darkcolor=P.PANEL)
        style.configure("Treeview.Heading", background=P.PANEL2, foreground=P.MUTED,
                        relief="flat", font=(FONT, 9, "bold"))
        style.map("Treeview", background=[("selected", P.OLIVE)],
                  foreground=[("selected", P.CREAM)])
        style.configure("Vertical.TScrollbar", background=P.PANEL2, troughcolor=P.BG,
                        bordercolor=P.BG, arrowcolor=P.MUTED,
                        lightcolor=P.PANEL2, darkcolor=P.PANEL2)
        style.map("Vertical.TScrollbar", background=[("disabled", P.BG), ("active", P.OLIVE)],
                  arrowcolor=[("disabled", P.BG)])
