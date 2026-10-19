"""ViewState: UI choices that must survive page rebuilds (selected month, tab, etc.)."""

from dataclasses import dataclass, field
from datetime import date


def _today():
    return date.today()


@dataclass
class ViewState:
    selected_day: date = field(default_factory=_today)
    cal_year: int = field(default_factory=lambda: _today().year)
    cal_month: int = field(default_factory=lambda: _today().month)
    cal_mode: str = "Total"
    cal_period: str = "Day"
    custom_range: tuple = field(default_factory=lambda: (_today().replace(day=1), _today()))
    ledger_year: int = field(default_factory=lambda: _today().year)
    ledger_month: int = field(default_factory=lambda: _today().month)
    chart_period: str = "Month"

    @staticmethod
    def _shift(year, month, delta):
        year, month0 = divmod(year * 12 + (month - 1) + delta, 12)
        return year, month0 + 1

    def shift_ledger_month(self, delta):
        self.ledger_year, self.ledger_month = self._shift(self.ledger_year, self.ledger_month, delta)

    def shift_cal_month(self, delta):
        self.cal_year, self.cal_month = self._shift(self.cal_year, self.cal_month, delta)

    def show_month_of(self, day):
        self.ledger_year, self.ledger_month = day.year, day.month
