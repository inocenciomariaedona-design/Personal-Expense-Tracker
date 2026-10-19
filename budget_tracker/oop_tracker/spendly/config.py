"""Static configuration: paths, categories, palette and layout constants."""

import os

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "expense_data.json")
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
FALLBACK_CATEGORY_COLOR = "#9a988c"
INCOME_CATEGORIES = ["Salary", "Allowance", "Gift", "Refund", "Other income"]
DEFAULT_ACCOUNTS = ["Cash", "Bank", "Digital Wallet"]
PERIODS = ["Day", "Week", "Month", "Year", "Custom"]


def category_color(name):
    return CATEGORIES.get(name, FALLBACK_CATEGORY_COLOR)


class Palette:
    """Warm olive, soft cream, deep charcoal."""
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


class Layout:
    SIDEBAR_W = 200
    HEADER_H = 170
    CELL_W = 70
    CELL_H = 54
