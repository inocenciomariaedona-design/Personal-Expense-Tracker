"""
Run:  python procedural_tracker.py

  Ledger    your month at a glance, entries grouped by day
  Calendar  spent / earned per day, plus Day, Week, Month, Year or Custom summaries
  Charts    where the money went, by category
  Wallet    Cash, Bank, Digital Wallet (and your own). Everything starts at zero.
  New entry log an expense (deducted from an account) or income (added to one)

Data is saved automatically to expense_data.json next to this script.
"""

import calendar
import json
import os
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import messagebox, ttk

# ----------------------------------------------------------------------------
# Constants and palette (warm olive, soft cream, deep charcoal)
# ----------------------------------------------------------------------------
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expense_data.json")
CURRENCY = "₱"
FONT = "Segoe UI"

CATEGORIES = {          # expense categories, muted earthy tones
    "Food": "#e0a458",
    "Transport": "#8fb5a0",
    "Bills": "#c9b458",
    "Shopping": "#b98aa0",
    "Health": "#7fb07f",
    "Entertainment": "#d9826b",
    "Education": "#7fa3c4",
    "Other": "#9a988c",
}
INCOME_CATEGORIES = ["Salary", "Allowance", "Gift", "Refund", "Other income"]
DEFAULT_ACCOUNTS = ["Cash", "Bank", "Digital Wallet"]
PERIODS = ["Day", "Week", "Month", "Year", "Custom"]

BG = "#17181c"
SIDEBAR_BG = "#121316"
PANEL = "#25262b"
PANEL2 = "#303136"
TRACK = "#37383e"
HAIRLINE = "#34353b"
TILE_ON = "#3a3516"
TILE_LINE = "#3b3c42"

OLIVE_LIGHT = "#8a7d28"
OLIVE = "#786d22"
OLIVE_DEEP = "#5f5619"
OLIVE_RING = "#988c3c"
GOLD = "#ebdc4a"
CREAM = "#fbf6dd"
CREAM_SOFT = "#e6dfb0"

TEXT = "#ecebe4"
MUTED = "#8f8e88"
RED = "#e5484d"
RED_TEXT = "#ef5a5a"
GREEN = "#3f9d56"
GREEN_TEXT = "#58bb6e"

SIDEBAR_W = 200
HEADER_H = 170
CELL_W, CELL_H = 70, 54

# ----------------------------------------------------------------------------
# Global state
# ----------------------------------------------------------------------------
state = {"accounts": {}, "entries": []}
root = None
stage = None
stage_page = None
nav_labels = {}
scroll_registry = {}
current_page = "ledger"

selected_day = date.today()
cal_year, cal_month = date.today().year, date.today().month
cal_mode = "Total"
cal_period = "Day"
custom_range = [date.today().replace(day=1), date.today()]
ledger_year, ledger_month = date.today().year, date.today().month
chart_period = "Month"


# ----------------------------------------------------------------------------
# Data layer
# ----------------------------------------------------------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            state["accounts"] = {k: float(v) for k, v in loaded.get("accounts", {}).items()}
            entries = loaded.get("entries", loaded.get("expenses", []))   # old files use "expenses"
            for e in entries:
                e.setdefault("type", "expense")
            state["entries"] = entries
        except (json.JSONDecodeError, OSError, ValueError):
            pass
    for name in DEFAULT_ACCOUNTS:           # every account starts at zero
        state["accounts"].setdefault(name, 0.0)


def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except OSError as err:
        messagebox.showerror("Could not save", str(err))


def money(value, sign=False):
    body = f"{abs(value):,.2f}"
    if body.endswith(".00"):
        body = body[:-3]
    prefix = "-" if value < 0 else ("+" if sign and value > 0 else "")
    return f"{prefix}{CURRENCY}{body}"


def short_num(value):
    body = f"{abs(value):,.0f}" if abs(value) < 10000 else f"{abs(value) / 1000:.1f}k"
    return ("-" if value < 0 else "") + body


def parse_date(text):
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_amount(text):
    try:
        value = float(text.replace(",", "").strip())
    except ValueError:
        return None
    return value if value > 0 else None


def total_balance():
    return sum(state["accounts"].values())


def add_account(name):
    name = name.strip()
    if not name or name in state["accounts"]:
        return False
    state["accounts"][name] = 0.0
    save_data()
    return True


def add_funds(account, amount):
    state["accounts"][account] += amount
    save_data()


def set_balance(account, amount):
    state["accounts"][account] = amount
    save_data()


def add_entry(day, kind, category, account, amount, note):
    if kind == "expense":
        if state["accounts"].get(account, 0) < amount:
            return False
        state["accounts"][account] -= amount
    else:
        state["accounts"][account] += amount
    next_id = max([e["id"] for e in state["entries"]], default=0) + 1
    state["entries"].append({"id": next_id, "date": day.isoformat(), "type": kind,
                             "category": category, "account": account,
                             "amount": amount, "note": note})
    save_data()
    return True


def delete_entry(entry_id):
    for e in state["entries"]:
        if e["id"] == entry_id:
            acc = e["account"]
            if acc in state["accounts"]:
                if e["type"] == "expense":
                    state["accounts"][acc] += e["amount"]       # refund
                elif state["accounts"][acc] < e["amount"]:
                    return False                                # would go below zero
                else:
                    state["accounts"][acc] -= e["amount"]
            state["entries"].remove(e)
            save_data()
            return True
    return False


def period_range(period, ref):
    if period == "Day":
        return ref, ref
    if period == "Week":
        start = ref - timedelta(days=ref.weekday())
        return start, start + timedelta(days=6)
    if period == "Month":
        return ref.replace(day=1), ref.replace(day=calendar.monthrange(ref.year, ref.month)[1])
    if period == "Year":
        return date(ref.year, 1, 1), date(ref.year, 12, 31)
    if period == "Custom":
        return custom_range[0], custom_range[1]
    return date(1900, 1, 1), date(2999, 12, 31)          # "All"


def entries_in_range(start, end, kind=None):
    lo, hi = start.isoformat(), end.isoformat()
    return [e for e in state["entries"]
            if lo <= e["date"] <= hi and (kind is None or e["type"] == kind)]


def totals(start, end):
    """Returns (income, expense) for a date range."""
    inc = sum(e["amount"] for e in entries_in_range(start, end, "income"))
    exp = sum(e["amount"] for e in entries_in_range(start, end, "expense"))
    return inc, exp


def spent_by_category(start, end):
    data = {}
    for e in entries_in_range(start, end, "expense"):
        data[e["category"]] = data.get(e["category"], 0.0) + e["amount"]
    return data


def greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


# ----------------------------------------------------------------------------
# Drawing helpers
# ----------------------------------------------------------------------------
def blend(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def round_rect(c, x1, y1, x2, y2, r, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


def cat_color(name):
    return CATEGORIES.get(name, "#9a988c")


def draw_breakdown(c, data):
    """Soft horizontal bars: name and amount on one line, thin bar underneath."""
    c.delete("all")
    w = c.winfo_width()
    w = w if w > 60 else 320
    rows = sorted([(k, v) for k, v in data.items() if v > 0], key=lambda kv: -kv[1])
    if not rows:
        c.configure(height=90)
        c.create_text(w / 2, 45, text="Nothing spent in this period yet.",
                      fill=MUTED, font=(FONT, 11))
        return
    total = sum(v for _, v in rows)
    top = rows[0][1]
    y = 6
    for name, amount in rows:
        c.create_text(4, y + 10, text=name, anchor="w", fill=TEXT, font=(FONT, 10))
        c.create_text(w - 4, y + 10, anchor="e", fill=MUTED, font=(FONT, 10),
                      text=f"{money(amount)}   {amount / total * 100:.0f}%")
        round_rect(c, 4, y + 24, w - 4, y + 30, 3, fill=TRACK, outline="")
        round_rect(c, 4, y + 24, 4 + max((w - 8) * amount / top, 7), y + 30, 3,
                   fill=cat_color(name), outline="")
        y += 42
    c.configure(height=y + 4)


def draw_donut(c, data, size=240):
    c.delete("all")
    pad = 24
    box = (pad, pad, size - pad, size - pad)
    total = sum(data.values())
    if total <= 0:
        c.create_arc(*box, start=90, extent=359.9, style="arc", outline=TRACK, width=26)
    else:
        start = 90
        for name, amount in sorted(data.items(), key=lambda kv: -kv[1]):
            if amount <= 0:
                continue
            extent = -min(amount / total * 360, 359.9)       # negative = clockwise
            c.create_arc(*box, start=start, extent=extent, style="arc",
                         outline=cat_color(name), width=26)
            start += extent
    c.create_text(size / 2, size / 2 - 10, text=money(total), fill=TEXT, font=(FONT, 17, "bold"))
    c.create_text(size / 2, size / 2 + 16, text="spent", fill=MUTED, font=(FONT, 10))


# ----------------------------------------------------------------------------
# Widget helpers
# ----------------------------------------------------------------------------
def make_label(parent, text, size=11, bold=False, color=TEXT, bg=None):
    return tk.Label(parent, text=text, bg=bg or parent["bg"], fg=color,
                    font=(FONT, size, "bold" if bold else "normal"))


def make_button(parent, text, command, kind="primary"):
    styles = {"primary": (OLIVE, CREAM), "quiet": (PANEL2, TEXT),
              "light": (CREAM, OLIVE_DEEP), "cream": (CREAM, OLIVE_DEEP)}
    bg, fg = styles[kind]
    return tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                     activebackground=blend(bg, "#ffffff", 0.12), activeforeground=fg,
                     relief="flat", bd=0, padx=18, pady=8, cursor="hand2",
                     highlightthickness=0, takefocus=0, font=(FONT, 10, "bold"))


def make_entry(parent, width=18, text="", size=11, bg=PANEL2):
    entry = tk.Entry(parent, width=width, bg=bg, fg=TEXT, insertbackground=TEXT,
                     relief="flat", font=(FONT, size), highlightthickness=1,
                     highlightbackground=TILE_LINE, highlightcolor=OLIVE_RING)
    entry.insert(0, text)
    return entry


def rounded_panel(parent, fill=PANEL, radius=22, pad=18, stretch=False):
    """A rounded card. Returns (outer, inner): place `outer`, fill `inner`."""
    outer = tk.Canvas(parent, bg=parent["bg"], highlightthickness=0, bd=0, height=40)
    inner = tk.Frame(outer, bg=fill)
    win = outer.create_window(pad, pad, window=inner, anchor="nw")

    def redraw(_event=None):
        w, h = outer.winfo_width(), outer.winfo_height()
        if w < 4 or h < 4:
            return
        outer.delete("shape")
        round_rect(outer, 1, 1, w - 1, h - 1, radius, fill=fill, outline="", tags="shape")
        outer.tag_lower("shape")
        if stretch:
            outer.itemconfigure(win, width=max(w - 2 * pad, 1), height=max(h - 2 * pad, 1))
        else:
            outer.itemconfigure(win, width=max(w - 2 * pad, 1))

    def fit(_event=None):
        if not stretch:
            want = inner.winfo_reqheight() + 2 * pad
            if int(float(outer.cget("height"))) != want:
                outer.configure(height=want)

    outer.bind("<Configure>", redraw)
    inner.bind("<Configure>", fit)
    return outer, inner


def segmented(parent, options, value, command, bg):
    """Pill-style option switcher (Expenses | Income | Total)."""
    frame = tk.Frame(parent, bg=TILE_LINE, padx=1, pady=1)
    buttons = {}

    def select(option, fire=True):
        for name, lab in buttons.items():
            on = name == option
            lab.config(bg=OLIVE if on else bg, fg=GOLD if on else TEXT)
        if fire:
            command(option)

    for i, option in enumerate(options):
        lab = tk.Label(frame, text=option, padx=13, pady=6, cursor="hand2", font=(FONT, 10))
        lab.grid(row=0, column=i, padx=(0 if i == 0 else 1, 0))
        lab.bind("<Button-1>", lambda _e, o=option: select(o))
        buttons[option] = lab
    select(value, fire=False)
    return frame


def make_scroll(parent, bg):
    """Scrollable area. Returns the inner frame to fill."""
    box = tk.Frame(parent, bg=bg)
    box.pack(fill="both", expand=True)
    canvas = tk.Canvas(box, bg=bg, highlightthickness=0, bd=0)
    bar = ttk.Scrollbar(box, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=bar.set)
    bar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    inner = tk.Frame(canvas, bg=bg)
    win = canvas.create_window(0, 0, window=inner, anchor="nw")
    inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win, width=e.width))
    scroll_registry[str(canvas)] = canvas
    canvas.bind("<Destroy>", lambda _e: scroll_registry.pop(str(canvas), None))
    return inner


def on_mousewheel(event):
    """Scrolls whichever scroll area is under the mouse pointer."""
    try:
        widget = root.winfo_containing(event.x_root, event.y_root)
    except (KeyError, tk.TclError):
        return
    while widget is not None:
        canvas = scroll_registry.get(str(widget))
        if canvas is not None:
            up = getattr(event, "delta", 0) > 0 or event.num == 4
            canvas.yview_scroll(-3 if up else 3, "units")
            return
        widget = widget.master


def make_tile(parent, text, selected, command):
    c = tk.Canvas(parent, height=66, bg=BG, highlightthickness=0, cursor="hand2")

    def draw(_event=None):
        w = c.winfo_width()
        w = w if w > 10 else 160
        c.delete("all")
        if selected:
            round_rect(c, 2, 2, w - 2, 64, 18, fill=TILE_ON, outline=GOLD, width=2)
        else:
            round_rect(c, 2, 2, w - 2, 64, 18, fill=PANEL, outline=TILE_LINE, width=1)
        c.create_text(w / 2, 33, text=text, fill=GOLD if selected else TEXT,
                      font=(FONT, 11, "bold" if selected else "normal"))

    c.bind("<Configure>", draw)
    c.bind("<Button-1>", lambda _e: command())
    draw()
    return c


def build_header(parent, title, subtitle, show_new, width):
    """Warm olive band with a soft greeting, melting into the dark sheet below."""
    c = tk.Canvas(parent, height=HEADER_H, bg=OLIVE, highlightthickness=0, bd=0)
    c.pack(fill="x")
    win = None
    if show_new:
        btn = make_button(c, "+  New entry", lambda: show_page("add"), "light")
        win = c.create_window(width - 44, 74, window=btn, anchor="e")

    def redraw(w):
        c.delete("hdr")
        steps = 36
        for i in range(steps):
            c.create_rectangle(0, i * HEADER_H / steps, w, (i + 1) * HEADER_H / steps + 1,
                               fill=blend(OLIVE_LIGHT, OLIVE_DEEP, i / (steps - 1)),
                               outline="", tags="hdr")
        c.create_oval(w - 560, -240, w - 120, 200, outline=OLIVE_RING, tags="hdr")
        c.create_oval(w - 430, -150, w - 200, 90, outline=OLIVE_RING, tags="hdr")
        round_rect(c, 0, HEADER_H - 34, w, HEADER_H + 80, 34, fill=BG, outline="", tags="hdr")
        today = date.today().strftime("%A, %B %d").replace(" 0", " ")
        c.create_text(44, 34, text=today, anchor="w", fill=CREAM_SOFT, font=(FONT, 10), tags="hdr")
        c.create_text(44, 74, text=title, anchor="w", fill=CREAM, font=(FONT, 26, "bold"), tags="hdr")
        c.create_text(44, 112, text=subtitle, anchor="w", fill=CREAM_SOFT, font=(FONT, 11), tags="hdr")
        if win:
            c.coords(win, w - 44, 74)

    redraw(width)
    c.bind("<Configure>", lambda e: redraw(e.width))
    return c


# ----------------------------------------------------------------------------
# Page: Ledger
# ----------------------------------------------------------------------------
def shift_ledger_month(delta):
    global ledger_year, ledger_month
    ledger_month += delta
    if ledger_month < 1:
        ledger_month, ledger_year = 12, ledger_year - 1
    elif ledger_month > 12:
        ledger_month, ledger_year = 1, ledger_year + 1
    show_page("ledger")


def confirm_delete(entry_id):
    if not messagebox.askyesno("Remove entry", "Remove this entry? The account balance will be adjusted back."):
        return
    if not delete_entry(entry_id):
        messagebox.showwarning("Cannot remove", "Removing this income would take that account below zero.")
    show_page(current_page)


def build_ledger(body):
    wrap = tk.Frame(body, bg=BG)
    wrap.pack(fill="both", expand=True, padx=36, pady=(0, 20))

    first_run = not state["entries"] and total_balance() == 0
    if first_run:
        wo, welcome = rounded_panel(wrap, OLIVE_DEEP, radius=24, pad=22)
        wo.pack(fill="x", pady=(0, 14))
        make_label(welcome, "Welcome. Let's begin gently.", 15, True, CREAM, OLIVE_DEEP).pack(anchor="w")
        make_label(welcome, "Start by telling Spendly what you're holding in each account. "
                            "Everything begins at zero, and you can log your first entry whenever you're ready.",
                   10, color=CREAM_SOFT, bg=OLIVE_DEEP).pack(anchor="w", pady=(4, 12))
        for child in welcome.winfo_children():
            if isinstance(child, tk.Label):
                child.config(wraplength=760, justify="left")
        make_button(welcome, "Open Wallet", lambda: show_page("wallet"), "cream").pack(anchor="w")

    start = date(ledger_year, ledger_month, 1)
    end = date(ledger_year, ledger_month, calendar.monthrange(ledger_year, ledger_month)[1])
    inc, exp = totals(start, end)
    net = inc - exp

    co, card = rounded_panel(wrap, PANEL, radius=24, pad=20)
    co.pack(fill="x", pady=(0, 14))
    nav = tk.Frame(card, bg=PANEL)
    nav.pack(fill="x")
    prev_b = make_label(nav, "‹", 18, True, CREAM_SOFT)
    prev_b.pack(side="left")
    prev_b.config(cursor="hand2")
    prev_b.bind("<Button-1>", lambda _e: shift_ledger_month(-1))
    make_label(nav, f"{calendar.month_name[ledger_month]} {ledger_year}", 12, color=TEXT).pack(side="left", padx=14)
    next_b = make_label(nav, "›", 18, True, CREAM_SOFT)
    next_b.pack(side="left")
    next_b.config(cursor="hand2")
    next_b.bind("<Button-1>", lambda _e: shift_ledger_month(1))
    make_label(nav, f"All accounts  {money(total_balance())}", 10, color=MUTED).pack(side="right")

    net_color = RED_TEXT if net < 0 else (GREEN_TEXT if net > 0 else TEXT)
    make_label(card, money(net), 30, True, net_color).pack(anchor="w", pady=(8, 0))
    stats = tk.Frame(card, bg=PANEL)
    stats.pack(fill="x", pady=(2, 0))
    make_label(stats, "Spent", 10, color=MUTED).pack(side="left")
    make_label(stats, money(exp), 11, True, RED_TEXT).pack(side="left", padx=(6, 26))
    make_label(stats, "Earned", 10, color=MUTED).pack(side="left")
    make_label(stats, money(inc), 11, True, GREEN_TEXT).pack(side="left", padx=6)

    listing = make_scroll(wrap, BG)
    month_entries = sorted(entries_in_range(start, end), key=lambda e: (e["date"], e["id"]), reverse=True)
    if not month_entries:
        make_label(listing, "Nothing logged for this month yet.", 11, color=MUTED).pack(pady=40)
        return

    days = []
    for e in month_entries:
        if not days or days[-1][0] != e["date"]:
            days.append((e["date"], []))
        days[-1][1].append(e)

    for day_text, items in days:
        day = parse_date(day_text)
        d_inc, d_exp = totals(day, day)
        go, group = rounded_panel(listing, PANEL, radius=20, pad=8)
        go.pack(fill="x", pady=(0, 12), padx=(0, 10))
        head = tk.Frame(group, bg=PANEL)
        head.pack(fill="x", padx=10, pady=(8, 8))
        make_label(head, day.strftime("%a, %m/%d"), 10, True, CREAM_SOFT).pack(side="left")
        parts = []
        if d_inc:
            parts.append(f"Income {money(d_inc)}")
        if d_exp:
            parts.append(f"Expense {money(d_exp)}")
        make_label(head, "     ".join(parts), 9, color=MUTED).pack(side="right")
        for e in items:
            tk.Frame(group, bg=HAIRLINE, height=1).pack(fill="x", padx=10)
            row = tk.Frame(group, bg=PANEL)
            row.pack(fill="x", padx=10, pady=9)
            left = tk.Frame(row, bg=PANEL)
            left.pack(side="left")
            make_label(left, e["category"], 12).pack(anchor="w")
            if e["note"]:
                make_label(left, e["note"], 9, color=CREAM_SOFT).pack(anchor="w")
            remove = make_label(row, "Remove", 9, color=MUTED)
            remove.pack(side="right", padx=(16, 0))
            remove.config(cursor="hand2")
            remove.bind("<Button-1>", lambda _e, eid=e["id"]: confirm_delete(eid))
            right = tk.Frame(row, bg=PANEL)
            right.pack(side="right")
            if e["type"] == "expense":
                make_label(right, money(-e["amount"]), 12, True, RED_TEXT).pack(anchor="e")
            else:
                make_label(right, money(e["amount"], sign=True), 12, True, GREEN_TEXT).pack(anchor="e")
            make_label(right, e["account"], 9, color=MUTED).pack(anchor="e")


# ----------------------------------------------------------------------------
# Page: Calendar
# ----------------------------------------------------------------------------
def build_calendar(body):
    global cal_period
    wrap = tk.Frame(body, bg=BG)
    wrap.pack(fill="both", expand=True, padx=36, pady=(0, 22))
    wrap.columnconfigure(1, weight=1)
    wrap.rowconfigure(0, weight=1)

    left_o, left = rounded_panel(wrap, PANEL, radius=24, pad=18, stretch=True)
    left_o.configure(width=CELL_W * 7 + 40)
    left_o.grid(row=0, column=0, sticky="ns", padx=(0, 16))
    right_o, right = rounded_panel(wrap, PANEL, radius=24, pad=18, stretch=True)
    right_o.grid(row=0, column=1, sticky="nsew")

    # ---------------- left: month grid ----------------
    head = tk.Frame(left, bg=PANEL)
    head.pack(fill="x")
    prev_b = make_label(head, "‹", 18, True, CREAM_SOFT)
    prev_b.pack(side="left")
    prev_b.config(cursor="hand2")
    month_lbl = make_label(head, "", 12)
    month_lbl.pack(side="left", expand=True)
    next_b = make_label(head, "›", 18, True, CREAM_SOFT)
    next_b.pack(side="right")
    next_b.config(cursor="hand2")

    grid = tk.Frame(left, bg=PANEL)
    grid.pack(pady=(6, 4))

    mode_row = tk.Frame(left, bg=PANEL)
    mode_row.pack(pady=(6, 8))
    totals_row = tk.Frame(left, bg=PANEL)
    totals_row.pack(fill="x", pady=(4, 0))
    month_totals = {}
    for i, (key, title) in enumerate([("total", "Total"), ("income", "Income"), ("expense", "Expense")]):
        cell = tk.Frame(totals_row, bg=PANEL)
        cell.pack(side="left", expand=True)
        month_totals[key] = make_label(cell, "", 13, True)
        month_totals[key].pack()
        make_label(cell, title, 9, color=MUTED).pack()

    # ---------------- right: summary ----------------
    make_label(right, "Summary", 13, True).pack(anchor="w")
    holder = tk.Frame(right, bg=PANEL)
    holder.pack(fill="both", expand=True, pady=(8, 0))
    inner = make_scroll(holder, PANEL)

    seg_row = tk.Frame(inner, bg=PANEL)
    seg_row.pack(fill="x")
    custom_row = tk.Frame(inner, bg=PANEL)
    make_label(custom_row, "From", 9, color=MUTED).pack(side="left")
    start_e = make_entry(custom_row, 11, custom_range[0].isoformat(), 10)
    start_e.pack(side="left", padx=6, ipady=3)
    make_label(custom_row, "To", 9, color=MUTED).pack(side="left")
    end_e = make_entry(custom_row, 11, custom_range[1].isoformat(), 10)
    end_e.pack(side="left", padx=6, ipady=3)

    range_lbl = make_label(inner, "", 10, color=MUTED)
    range_lbl.pack(anchor="w", pady=(12, 4))
    stat_row = tk.Frame(inner, bg=PANEL)
    stat_row.pack(fill="x", pady=(0, 10))
    stats = {}
    for key, title in [("income", "Income"), ("expense", "Expense"), ("net", "Net")]:
        cell = tk.Frame(stat_row, bg=PANEL)
        cell.pack(side="left", expand=True, anchor="w")
        stats[key] = make_label(cell, "", 13, True)
        stats[key].pack(anchor="w")
        make_label(cell, title, 9, color=MUTED).pack(anchor="w")

    chart = tk.Canvas(inner, bg=PANEL, highlightthickness=0, height=90)
    chart.pack(fill="x", pady=6)

    tree = ttk.Treeview(inner, columns=("date", "cat", "acc", "amt"), show="headings", height=6)
    for col, title, w in [("date", "Date", 84), ("cat", "Category", 90), ("acc", "Account", 90), ("amt", "Amount", 80)]:
        tree.heading(col, text=title)
        tree.column(col, width=w, anchor="w")
    tree.tag_configure("exp", foreground=RED_TEXT)
    tree.tag_configure("inc", foreground=GREEN_TEXT)
    tree.pack(fill="x", pady=(6, 4))

    current = {"data": {}}

    def refresh_summary():
        if cal_period == "Custom":
            custom_row.pack(fill="x", pady=(10, 0), after=seg_row)
            s, e = parse_date(start_e.get()), parse_date(end_e.get())
            if s is None or e is None or s > e:
                range_lbl.config(text="Enter valid dates (YYYY-MM-DD), start before end.")
                return
            custom_range[0], custom_range[1] = s, e
        else:
            custom_row.pack_forget()
        start, end = period_range(cal_period, selected_day)
        inc, exp = totals(start, end)
        range_lbl.config(text=start.strftime("%b %d, %Y") if start == end
                         else f"{start.strftime('%b %d, %Y')}  to  {end.strftime('%b %d, %Y')}")
        stats["income"].config(text=money(inc), fg=GREEN_TEXT)
        stats["expense"].config(text=money(exp), fg=RED_TEXT)
        stats["net"].config(text=money(inc - exp), fg=RED_TEXT if inc < exp else GREEN_TEXT if inc > exp else TEXT)
        current["data"] = spent_by_category(start, end)
        draw_breakdown(chart, current["data"])
        tree.delete(*tree.get_children())
        for e in sorted(entries_in_range(start, end), key=lambda x: (x["date"], x["id"]), reverse=True):
            sign = -e["amount"] if e["type"] == "expense" else e["amount"]
            tree.insert("", "end", tags=("exp" if e["type"] == "expense" else "inc",),
                        values=(e["date"], e["category"], e["account"], money(sign, sign=True)))

    def set_period(option):
        global cal_period
        cal_period = option
        refresh_summary()

    seg = segmented(seg_row, PERIODS, cal_period, set_period, PANEL)
    seg.pack(anchor="w")
    make_button(custom_row, "Apply", refresh_summary).pack(side="left", padx=6)
    chart.bind("<Configure>", lambda _e: draw_breakdown(chart, current["data"]))

    # ---------------- grid rendering ----------------
    def select_day(day):
        global selected_day
        selected_day = day
        render_grid()
        refresh_summary()

    def draw_cell(num, col, day):
        c = tk.Canvas(grid, width=CELL_W, height=CELL_H, bg=PANEL, highlightthickness=0, cursor="hand2")
        inc, exp = totals(day, day)
        selected = day == selected_day
        if selected:
            round_rect(c, CELL_W / 2 - 22, 3, CELL_W / 2 + 22, 33, 14, fill=OLIVE, outline="")
        color = TEXT
        if col in (0, 6):
            color = RED_TEXT
        if day == date.today() and not selected:
            color = GOLD
        if selected:
            color = CREAM
        c.create_text(CELL_W / 2, 18, text=str(num), fill=color, font=(FONT, 13 if selected else 11))
        value = {"Expenses": -exp, "Income": inc}.get(cal_mode, inc - exp)
        if value:
            label = short_num(value)
            half = len(label) * 3.3 + 6
            c.create_rectangle(CELL_W / 2 - half, 38, CELL_W / 2 + half, 52,
                               fill=GREEN if value > 0 else RED, outline="")
            c.create_text(CELL_W / 2, 45, text=label, fill="white", font=(FONT, 8, "bold"))
        c.bind("<Button-1>", lambda _e: select_day(day))
        return c

    def render_grid():
        for w in grid.winfo_children():
            w.destroy()
        month_lbl.config(text=f"{calendar.month_name[cal_month]} {cal_year}")
        for i, name in enumerate(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
            make_label(grid, name, 9, True, RED_TEXT if i in (0, 6) else MUTED).grid(
                row=0, column=i, pady=(2, 6), sticky="ew")
            grid.columnconfigure(i, minsize=CELL_W)
        weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(cal_year, cal_month)
        for r, week in enumerate(weeks, start=1):
            for col, num in enumerate(week):
                if num:
                    draw_cell(num, col, date(cal_year, cal_month, num)).grid(row=r, column=col)
        m_start = date(cal_year, cal_month, 1)
        m_end = date(cal_year, cal_month, calendar.monthrange(cal_year, cal_month)[1])
        inc, exp = totals(m_start, m_end)
        month_totals["total"].config(text=money(inc - exp), fg=RED_TEXT if inc < exp else GREEN_TEXT if inc > exp else TEXT)
        month_totals["income"].config(text=money(inc), fg=GREEN_TEXT)
        month_totals["expense"].config(text=money(exp), fg=RED_TEXT)

    def change_month(delta):
        global cal_year, cal_month
        cal_month += delta
        if cal_month < 1:
            cal_month, cal_year = 12, cal_year - 1
        elif cal_month > 12:
            cal_month, cal_year = 1, cal_year + 1
        render_grid()

    def set_mode(option):
        global cal_mode
        cal_mode = option
        render_grid()

    prev_b.bind("<Button-1>", lambda _e: change_month(-1))
    next_b.bind("<Button-1>", lambda _e: change_month(1))
    segmented(mode_row, ["Expenses", "Income", "Total"], cal_mode, set_mode, PANEL).pack()

    render_grid()
    refresh_summary()


# ----------------------------------------------------------------------------
# Page: Charts
# ----------------------------------------------------------------------------
def build_charts(body):
    wrap = tk.Frame(body, bg=BG)
    wrap.pack(fill="both", expand=True, padx=36, pady=(0, 22))
    wrap.columnconfigure(1, weight=1)
    wrap.rowconfigure(1, weight=1)

    box = {}

    def refresh():
        start, end = period_range(chart_period, date.today())
        data = spent_by_category(start, end)
        inc, exp = totals(start, end)
        box["range"].config(text="All time" if chart_period == "All" else
                            (start.strftime("%b %d, %Y") if start == end else
                             f"{start.strftime('%b %d, %Y')}  to  {end.strftime('%b %d, %Y')}"))
        box["spent"].config(text=money(exp))
        box["earned"].config(text=money(inc))
        box["data"] = data
        draw_donut(box["donut"], data)
        draw_breakdown(box["bars"], data)

    def set_period(option):
        global chart_period
        chart_period = option
        refresh()

    segmented(wrap, ["Day", "Week", "Month", "Year", "All"], chart_period, set_period, BG).grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

    donut_o, donut_in = rounded_panel(wrap, PANEL, radius=24, pad=20, stretch=True)
    donut_o.configure(width=320)
    donut_o.grid(row=1, column=0, sticky="ns", padx=(0, 16))
    make_label(donut_in, "Spending mix", 13, True).pack(anchor="w")
    box["range"] = make_label(donut_in, "", 9, color=MUTED)
    box["range"].pack(anchor="w", pady=(2, 10))
    box["donut"] = tk.Canvas(donut_in, width=240, height=240, bg=PANEL, highlightthickness=0)
    box["donut"].pack()
    tally = tk.Frame(donut_in, bg=PANEL)
    tally.pack(fill="x", pady=(16, 0))
    for key, title, color in [("spent", "Spent", RED_TEXT), ("earned", "Earned", GREEN_TEXT)]:
        cell = tk.Frame(tally, bg=PANEL)
        cell.pack(side="left", expand=True)
        box[key] = make_label(cell, "", 14, True, color)
        box[key].pack()
        make_label(cell, title, 9, color=MUTED).pack()

    bars_o, bars_in = rounded_panel(wrap, PANEL, radius=24, pad=20, stretch=True)
    bars_o.grid(row=1, column=1, sticky="nsew")
    make_label(bars_in, "By category", 13, True).pack(anchor="w", pady=(0, 8))
    scroll_in = make_scroll(bars_in, PANEL)
    box["bars"] = tk.Canvas(scroll_in, bg=PANEL, highlightthickness=0, height=90)
    box["bars"].pack(fill="x")
    box["bars"].bind("<Configure>", lambda _e: draw_breakdown(box["bars"], box.get("data", {})))
    refresh()


# ----------------------------------------------------------------------------
# Page: Wallet
# ----------------------------------------------------------------------------
def build_wallet(body):
    wrap = tk.Frame(body, bg=BG)
    wrap.pack(fill="both", expand=True, padx=36, pady=(0, 10))
    page = make_scroll(wrap, BG)

    to, top = rounded_panel(page, PANEL, radius=24, pad=20)
    to.pack(fill="x", pady=(0, 14), padx=(0, 10))
    make_label(top, "Total balance", 10, color=MUTED).pack(anchor="w")
    make_label(top, money(total_balance()), 30, True, GREEN_TEXT if total_balance() > 0 else TEXT).pack(anchor="w")
    if total_balance() == 0:
        make_label(top, "Everything starts at zero. Add what you're holding in each account below.",
                   10, color=MUTED).pack(anchor="w", pady=(2, 0))

    cards = tk.Frame(page, bg=BG)
    cards.pack(fill="x", padx=(0, 4))
    for c in range(3):
        cards.columnconfigure(c, weight=1, uniform="acc")
    for i, (name, bal) in enumerate(state["accounts"].items()):
        co, card = rounded_panel(cards, PANEL, radius=20, pad=18)
        co.grid(row=i // 3, column=i % 3, sticky="ew", padx=6, pady=6)
        make_label(card, name, 10, color=MUTED).pack(anchor="w")
        make_label(card, money(bal), 18, True, GREEN_TEXT if bal > 0 else TEXT).pack(anchor="w")

    fo, form = rounded_panel(page, PANEL, radius=22, pad=20)
    fo.pack(fill="x", pady=(14, 0), padx=(0, 10))
    make_label(form, "Add or set money", 12, True).grid(row=0, column=0, columnspan=4, sticky="w")
    acc_var = tk.StringVar(value=next(iter(state["accounts"])))
    ttk.Combobox(form, textvariable=acc_var, state="readonly", width=20,
                 values=list(state["accounts"]), font=(FONT, 11)).grid(row=1, column=0, pady=12, padx=(0, 10))
    amount_e = make_entry(form, 14)
    amount_e.grid(row=1, column=1, padx=(0, 10), ipady=5)

    def do_add():
        amount = parse_amount(amount_e.get())
        if amount is None:
            messagebox.showwarning("Invalid amount", "Enter a number greater than 0.")
            return
        add_funds(acc_var.get(), amount)
        show_page("wallet")

    def do_set():
        try:
            amount = float(amount_e.get().replace(",", ""))
        except ValueError:
            messagebox.showwarning("Invalid amount", "Enter a valid number.")
            return
        if amount < 0:
            messagebox.showwarning("Invalid amount", "A balance cannot be negative.")
            return
        set_balance(acc_var.get(), amount)
        show_page("wallet")

    make_button(form, "Add money", do_add).grid(row=1, column=2, padx=(0, 8))
    make_button(form, "Set exact balance", do_set, "quiet").grid(row=1, column=3)

    no, new = rounded_panel(page, PANEL, radius=22, pad=20)
    no.pack(fill="x", pady=(14, 14), padx=(0, 10))
    make_label(new, "New account  (for example GCash, Maya, Savings)", 12, True).grid(row=0, column=0, columnspan=2, sticky="w")
    name_e = make_entry(new, 26)
    name_e.grid(row=1, column=0, pady=12, padx=(0, 10), ipady=5)

    def do_new():
        if add_account(name_e.get()):
            show_page("wallet")
        else:
            messagebox.showwarning("Cannot add", "Enter a unique, non-empty account name.")

    make_button(new, "Create account", do_new).grid(row=1, column=1)


# ----------------------------------------------------------------------------
# Page: New entry
# ----------------------------------------------------------------------------
def build_add(body):
    form = {"kind": "expense", "category": "Food"}
    wrap = tk.Frame(body, bg=BG)
    wrap.pack(fill="both", expand=True, padx=36, pady=(0, 20))

    tiles = tk.Frame(wrap, bg=BG)
    for c in range(4):
        tiles.columnconfigure(c, weight=1, uniform="tile")

    def render_tiles():
        for w in tiles.winfo_children():
            w.destroy()
        cats = list(CATEGORIES) if form["kind"] == "expense" else INCOME_CATEGORIES
        if form["category"] not in cats:
            form["category"] = cats[0]
        for i, name in enumerate(cats):
            make_tile(tiles, name, name == form["category"], lambda n=name: pick(n)).grid(
                row=i // 4, column=i % 4, padx=6, pady=6, sticky="ew")

    def pick(name):
        form["category"] = name
        render_tiles()

    def set_kind(option):
        form["kind"] = option.lower()
        render_tiles()

    segmented(wrap, ["Expense", "Income"], "Expense", set_kind, BG).pack(anchor="w", pady=(0, 10))
    tiles.pack(fill="x")

    po, panel = rounded_panel(wrap, OLIVE_DEEP, radius=26, pad=22)
    po.pack(fill="x", pady=(14, 0))
    field_bg = "#4a4217"
    for i, text in enumerate(["Amount", "Account", "Date  (YYYY-MM-DD)"]):
        make_label(panel, text, 9, color=CREAM_SOFT, bg=OLIVE_DEEP).grid(row=0, column=i, sticky="w", padx=6)
    amount_e = make_entry(panel, 12, size=18, bg=field_bg)
    amount_e.grid(row=1, column=0, padx=6, pady=(4, 12), ipady=6, sticky="w")
    acc_var = tk.StringVar(value=next(iter(state["accounts"])))
    ttk.Combobox(panel, textvariable=acc_var, state="readonly", width=16, values=list(state["accounts"]),
                 font=(FONT, 11)).grid(row=1, column=1, padx=6, pady=(4, 12), ipady=6, sticky="w")
    date_cell = tk.Frame(panel, bg=OLIVE_DEEP)
    date_cell.grid(row=1, column=2, padx=6, pady=(4, 12), sticky="w")
    date_e = make_entry(date_cell, 12, date.today().isoformat(), bg=field_bg)
    date_e.pack(side="left", ipady=6)
    make_button(date_cell, "Today", lambda: (date_e.delete(0, "end"), date_e.insert(0, date.today().isoformat())),
                "quiet").pack(side="left", padx=(6, 0))
    make_label(panel, "Note  (optional)", 9, color=CREAM_SOFT, bg=OLIVE_DEEP).grid(row=2, column=0, sticky="w", padx=6)
    note_e = make_entry(panel, 40, bg=field_bg)
    note_e.grid(row=3, column=0, columnspan=2, padx=6, pady=(4, 0), ipady=6, sticky="ew")

    def save():
        global ledger_year, ledger_month
        amount = parse_amount(amount_e.get())
        day = parse_date(date_e.get())
        if amount is None:
            messagebox.showwarning("Invalid amount", "Enter a number greater than 0.")
            return
        if day is None:
            messagebox.showwarning("Invalid date", "Use the format YYYY-MM-DD.")
            return
        if not add_entry(day, form["kind"], form["category"], acc_var.get(), amount, note_e.get().strip()):
            messagebox.showwarning(
                "Not enough in this account",
                f"{acc_var.get()} has {money(state['accounts'][acc_var.get()])}.\n"
                "Add money in Wallet first, or choose another account.")
            return
        ledger_year, ledger_month = day.year, day.month
        show_page("ledger")

    make_button(panel, "Save entry", save, "cream").grid(row=3, column=2, padx=6, pady=(4, 0), sticky="w")
    render_tiles()


# ----------------------------------------------------------------------------
# Navigation and window
# ----------------------------------------------------------------------------
PAGES = {
    "ledger": {"nav": "Ledger", "build": build_ledger},
    "calendar": {"nav": "Calendar", "build": build_calendar},
    "charts": {"nav": "Charts", "build": build_charts},
    "wallet": {"nav": "Wallet", "build": build_wallet},
    "add": {"nav": None, "build": build_add},
}


def page_header(name):
    if name == "ledger":
        return greeting(), "Here's how your month is unfolding."
    return {
        "calendar": ("Calendar", "Look back, one day at a time."),
        "charts": ("Charts", "Where it all went, gently laid out."),
        "wallet": ("Wallet", "Everything you're holding, in one place."),
        "add": ("New entry", "Take a moment to note it down."),
    }[name]


def show_page(name):
    """Build the page off-screen, let it finish drawing, then reveal it (no flicker)."""
    global current_page, stage_page
    current_page = name
    root.update_idletasks()
    w, h = max(stage.winfo_width(), 900), max(stage.winfo_height(), 600)
    page = tk.Frame(stage, bg=BG)
    title, subtitle = page_header(name)
    build_header(page, title, subtitle, name != "add", w)
    body = tk.Frame(page, bg=BG)
    body.pack(fill="both", expand=True)
    PAGES[name]["build"](body)
    page.place(x=-20000, y=0, width=w, height=h)
    root.update()                               # layout and drawing happen out of sight
    page.place_forget()
    page.place(x=0, y=0, relwidth=1, relheight=1)
    if stage_page is not None:
        stage_page.destroy()
    stage_page = page
    for key, lab in nav_labels.items():
        on = key == name
        lab.config(bg=OLIVE if on else SIDEBAR_BG, fg=GOLD if on else TEXT)


def setup_styles():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TCombobox", fieldbackground=PANEL2, background=PANEL2, foreground=TEXT,
                    arrowcolor=GOLD, bordercolor=TILE_LINE, lightcolor=PANEL2, darkcolor=PANEL2,
                    selectbackground=PANEL2, selectforeground=TEXT)
    style.map("TCombobox", fieldbackground=[("readonly", PANEL2)], foreground=[("readonly", TEXT)],
              selectbackground=[("readonly", PANEL2)], selectforeground=[("readonly", TEXT)])
    root.option_add("*TCombobox*Listbox.background", PANEL2)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", OLIVE)
    root.option_add("*TCombobox*Listbox.selectForeground", CREAM)
    style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT,
                    rowheight=28, borderwidth=0, font=(FONT, 10),
                    bordercolor=PANEL, lightcolor=PANEL, darkcolor=PANEL)
    style.configure("Treeview.Heading", background=PANEL2, foreground=MUTED, relief="flat",
                    font=(FONT, 9, "bold"))
    style.map("Treeview", background=[("selected", OLIVE)], foreground=[("selected", CREAM)])
    style.configure("Vertical.TScrollbar", background=PANEL2, troughcolor=BG, bordercolor=BG,
                    arrowcolor=MUTED, lightcolor=PANEL2, darkcolor=PANEL2)
    style.map("Vertical.TScrollbar", background=[("disabled", BG), ("active", OLIVE)],
              arrowcolor=[("disabled", BG)])


def build_window():
    global root, stage
    root = tk.Tk()
    root.title("Spendly")
    root.geometry("1240x800")
    root.minsize(1100, 760)
    root.configure(bg=BG)
    setup_styles()

    side = tk.Frame(root, bg=SIDEBAR_BG, width=SIDEBAR_W)
    side.pack(side="left", fill="y")
    side.pack_propagate(False)
    make_label(side, "Spendly", 20, True, GOLD, SIDEBAR_BG).pack(anchor="w", padx=24, pady=(34, 2))
    make_label(side, "Your money, calmly", 9, color=MUTED, bg=SIDEBAR_BG).pack(anchor="w", padx=24, pady=(0, 30))

    for key, info in PAGES.items():
        if info["nav"] is None:
            continue
        lab = tk.Label(side, text=info["nav"], anchor="w", bg=SIDEBAR_BG, fg=TEXT, padx=24, pady=12,
                       cursor="hand2", font=(FONT, 12))
        lab.pack(fill="x", padx=12, pady=2)
        lab.bind("<Button-1>", lambda _e, k=key: show_page(k))
        nav_labels[key] = lab

    make_label(side, "Saved automatically", 9, color=MUTED, bg=SIDEBAR_BG).pack(side="bottom", pady=20)

    stage = tk.Frame(root, bg=BG)
    stage.pack(side="left", fill="both", expand=True)
    root.bind_all("<MouseWheel>", on_mousewheel)
    root.bind_all("<Button-4>", on_mousewheel)
    root.bind_all("<Button-5>", on_mousewheel)


def main():
    load_data()
    build_window()
    show_page("ledger")
    root.mainloop()


if __name__ == "__main__":
    main()