"""Text formatting and parsing helpers (no UI, no state)."""

from datetime import datetime

from .config import CURRENCY


class Formatter:
    @staticmethod
    def money(value, sign=False):
        body = f"{abs(value):,.2f}"
        if body.endswith(".00"):
            body = body[:-3]
        prefix = "-" if value < 0 else ("+" if sign and value > 0 else "")
        return f"{prefix}{CURRENCY}{body}"

    @staticmethod
    def short_num(value):
        body = f"{abs(value):,.0f}" if abs(value) < 10000 else f"{abs(value) / 1000:.1f}k"
        return ("-" if value < 0 else "") + body

    @staticmethod
    def greeting():
        hour = datetime.now().hour
        if hour < 12:
            return "Good morning"
        if hour < 18:
            return "Good afternoon"
        return "Good evening"


class Parser:
    @staticmethod
    def date(text):
        try:
            return datetime.strptime(text.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None

    @staticmethod
    def number(text):
        try:
            return float(text.replace(",", "").strip())
        except ValueError:
            return None

    @staticmethod
    def amount(text):
        """A strictly positive number, or None."""
        value = Parser.number(text)
        return value if value is not None and value > 0 else None
