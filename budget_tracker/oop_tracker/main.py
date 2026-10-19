"""Spendly - a calm desktop expense tracker.  Run:  python main.py"""

from spendly.config import DATA_FILE
from spendly.storage import JsonRepository
from spendly.tracker import ExpenseTracker
from spendly.ui.app import SpendlyApp


def main():
    tracker = ExpenseTracker(JsonRepository(DATA_FILE))
    tracker.load()
    SpendlyApp(tracker).run()


if __name__ == "__main__":
    main()
