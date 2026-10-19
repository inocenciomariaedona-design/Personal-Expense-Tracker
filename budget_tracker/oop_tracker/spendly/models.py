"""Entry models. Expense and income are polymorphic: each knows how it
affects an account balance, so no one needs to `if kind == ...` elsewhere."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar


@dataclass
class Entry(ABC):
    id: int
    date: str            # ISO string, e.g. "2026-10-20"
    category: str
    account: str
    amount: float
    note: str = ""

    kind: ClassVar[str] = ""

    # ---- construction / serialisation ----
    @classmethod
    def create(cls, kind, **fields):
        return ENTRY_TYPES[kind](**fields)

    @classmethod
    def from_dict(cls, data):
        return cls.create(
            data.get("type", ExpenseEntry.kind),      # old files have no "type"
            id=data["id"], date=data["date"], category=data["category"],
            account=data["account"], amount=float(data["amount"]),
            note=data.get("note", ""))

    def to_dict(self):
        return {"id": self.id, "date": self.date, "type": self.kind,
                "category": self.category, "account": self.account,
                "amount": self.amount, "note": self.note}

    @property
    def is_expense(self):
        return self.kind == ExpenseEntry.kind

    # ---- behaviour that differs per subclass ----
    @property
    @abstractmethod
    def signed_amount(self): ...

    @abstractmethod
    def can_apply(self, balance): ...

    @abstractmethod
    def apply(self, balance): ...

    @abstractmethod
    def can_revert(self, balance): ...

    @abstractmethod
    def revert(self, balance): ...


class ExpenseEntry(Entry):
    kind = "expense"

    @property
    def signed_amount(self):
        return -self.amount

    def can_apply(self, balance):
        return balance >= self.amount

    def apply(self, balance):
        return balance - self.amount

    def can_revert(self, balance):
        return True

    def revert(self, balance):
        return balance + self.amount


class IncomeEntry(Entry):
    kind = "income"

    @property
    def signed_amount(self):
        return self.amount

    def can_apply(self, balance):
        return True

    def apply(self, balance):
        return balance + self.amount

    def can_revert(self, balance):
        return balance >= self.amount

    def revert(self, balance):
        return balance - self.amount


ENTRY_TYPES = {ExpenseEntry.kind: ExpenseEntry, IncomeEntry.kind: IncomeEntry}
