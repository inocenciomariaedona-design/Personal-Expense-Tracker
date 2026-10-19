"""Wallet: owns every account balance and nothing else."""


class Wallet:
    def __init__(self, default_accounts=()):
        self._defaults = list(default_accounts)
        self._balances = {}
        self._ensure_defaults()

    def _ensure_defaults(self):
        for name in self._defaults:                 # every account starts at zero
            self._balances.setdefault(name, 0.0)

    def load(self, balances):
        self._balances = {k: float(v) for k, v in balances.items()}
        self._ensure_defaults()

    def to_dict(self):
        return dict(self._balances)

    # ---- queries ----
    @property
    def names(self):
        return list(self._balances)

    def items(self):
        return list(self._balances.items())

    def balance(self, name):
        return self._balances.get(name, 0.0)

    @property
    def total(self):
        return sum(self._balances.values())

    # ---- commands ----
    def add_account(self, name):
        name = name.strip()
        if not name or name in self._balances:
            return False
        self._balances[name] = 0.0
        return True

    def deposit(self, name, amount):
        self._balances[name] += amount

    def set_balance(self, name, amount):
        self._balances[name] = amount

    def apply(self, entry):
        """Apply an entry to its account. False if the account can't afford it."""
        balance = self.balance(entry.account)
        if not entry.can_apply(balance):
            return False
        self._balances[entry.account] = entry.apply(balance)
        return True

    def revert(self, entry):
        """Undo an entry. False if that would push the account below zero."""
        if entry.account not in self._balances:
            return True
        balance = self._balances[entry.account]
        if not entry.can_revert(balance):
            return False
        self._balances[entry.account] = entry.revert(balance)
        return True
