"""DateRange: an inclusive start/end pair and the common ways to build one."""

import calendar
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class DateRange:
    start: date
    end: date

    @classmethod
    def single(cls, day):
        return cls(day, day)

    @classmethod
    def month(cls, year, month):
        return cls(date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1]))

    @classmethod
    def for_period(cls, period, ref, custom=None):
        if period == "Day":
            return cls.single(ref)
        if period == "Week":
            start = ref - timedelta(days=ref.weekday())
            return cls(start, start + timedelta(days=6))
        if period == "Month":
            return cls.month(ref.year, ref.month)
        if period == "Year":
            return cls(date(ref.year, 1, 1), date(ref.year, 12, 31))
        if period == "Custom" and custom:
            return cls(*custom)
        return cls(date(1900, 1, 1), date(2999, 12, 31))        # "All"

    @property
    def iso_bounds(self):
        return self.start.isoformat(), self.end.isoformat()

    def label(self):
        if self.start == self.end:
            return self.start.strftime("%b %d, %Y")
        return f"{self.start.strftime('%b %d, %Y')}  to  {self.end.strftime('%b %d, %Y')}"
