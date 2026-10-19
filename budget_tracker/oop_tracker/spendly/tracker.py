"""ExpenseTracker: the application service the UI talks to."""

from typing import NamedTuple

from .config import DEFAULT_ACCOUNTS
from .models import Entry
from .wallet import Wallet


class Totals(NamedTuple):
    income: float
    expense: float

    @property
    def net(self):
        return self.income - self.expense


class ExpenseTracker:
    def __init__(self, repository, default_accounts=DEFAULT_ACCOUNTS):
        self._repo = repository
        self._entries = []
        self.wallet = Wallet(default_accounts)
        self.on_save_error = None          # optional callback(message)

    # ---- lifecycle ----
    def load(self):
        accounts, entries = self._repo.load()
        self.wallet.load(accounts)
        self._entries = entries

    def _save(self):
        try:
            self._repo.save(self.wallet.to_dict(), self._entries)
        except OSError as err:
            if self.on_save_error:
                self.on_save_error(str(err))

    # ---- wallet commands (each persists) ----
    @property
    def total_balance(self):
        return self.wallet.total

    @property
    def is_first_run(self):
        return not self._entries and self.wallet.total == 0

    def add_account(self, name):
        ok = self.wallet.add_account(name)
        if ok:
            self._save()
        return ok

    def add_funds(self, account, amount):
        self.wallet.deposit(account, amount)
        self._save()

    def set_balance(self, account, amount):
        self.wallet.set_balance(account, amount)
        self._save()

    # ---- entry commands ----
    def add_entry(self, day, kind, category, account, amount, note):
        next_id = max((e.id for e in self._entries), default=0) + 1
        entry = Entry.create(kind, id=next_id, date=day.isoformat(), category=category,
                             account=account, amount=amount, note=note)
        if not self.wallet.apply(entry):
            return False
        self._entries.append(entry)
        self._save()
        return True

    def delete_entry(self, entry_id):
        for entry in self._entries:
            if entry.id == entry_id:
                if not self.wallet.revert(entry):
                    return False
                self._entries.remove(entry)
                self._save()
                return True
        return False

    # ---- queries ----
    def entries_in_range(self, period, kind=None):
        lo, hi = period.iso_bounds
        return [e for e in self._entries
                if lo <= e.date <= hi and (kind is None or e.kind == kind)]

    def totals(self, period):
        income = expense = 0.0
        for e in self.entries_in_range(period):
            if e.is_expense:
                expense += e.amount
            else:
                income += e.amount
        return Totals(income, expense)

    def spent_by_category(self, period):
        data = {}
        for e in self.entries_in_range(period, "expense"):
            data[e.category] = data.get(e.category, 0.0) + e.amount
        return data
