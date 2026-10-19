"""Persistence. The tracker talks to a repository, never to the file directly."""

import json
import os

from .models import Entry


class JsonRepository:
    def __init__(self, path):
        self._path = path

    def load(self):
        """Returns (accounts_dict, list_of_entries). Empty if missing or unreadable."""
        if not os.path.exists(self._path):
            return {}, []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            raw = data.get("entries", data.get("expenses", []))     # old files use "expenses"
            entries = [Entry.from_dict(item) for item in raw]
            return dict(data.get("accounts", {})), entries
        except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
            return {}, []

    def save(self, accounts, entries):
        """Raises OSError if the file can't be written."""
        payload = {"accounts": accounts, "entries": [e.to_dict() for e in entries]}
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
