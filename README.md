# Personal Expense Tracker

A calm desktop expense tracker built with Python and tkinter only (no third-party packages).

There are two versions of the same app:

| Version | Entry point | Style |
|---|---|---|
| **Procedural** | `expense_tracker.py` | One file, functions plus a few global state variables |
| **OOP** | `main.py` + `spendly/` package | Classes split across modules, one job per file |

Both look and behave the same and read and write the same data file.

## Features

- **Ledger**: your month at a glance, entries grouped by day, with spent, earned and net totals
- **Calendar**: spent / earned per day, plus Day, Week, Month, Year or Custom summaries
- **Charts**: where the money went, by category (donut and bars)
- **Wallet**: Cash, Bank, Digital Wallet and your own accounts, all starting at zero
- **New entry**: log an expense (deducted from an account) or income (added to one)
- Data saves automatically; expenses can't overdraw an account, and removing an entry adjusts the balance back

## Requirements

- Python 3.8 or newer
- tkinter (bundled with most Python installs)
  - Ubuntu / Debian: `sudo apt install python3-tk`
  - Windows / macOS: included with the python.org installer
- The Segoe UI font is used; other systems fall back to a default font

## Running

**Procedural version**

```
python expense_tracker.py
```

**OOP version**

```
python main.py
```

Run it from the folder that contains `main.py` and the `spendly/` folder.

## Data

Entries and balances are stored in `expense_data.json` next to the script (next to `main.py` for the OOP version). The format is shared, so you can switch between versions without losing anything. Older files that use an `"expenses"` key are loaded too. Delete the file to start fresh.

```json
{
  "accounts": { "Cash": 100.0, "Bank": 0.0, "Digital Wallet": 0.0 },
  "entries": [
    { "id": 1, "date": "2026-10-20", "type": "expense", "category": "Food",
      "account": "Cash", "amount": 30.0, "note": "lunch" }
  ]
}
```

## Procedural version

Everything lives in `expense_tracker.py`, in labelled sections:

1. Constants and palette
2. Global state (`state`, selected month, selected period, etc.)
3. Data layer (load, save, add and delete entries, totals)
4. Drawing and widget helpers
5. One `build_*` function per page (ledger, calendar, charts, wallet, add)
6. Navigation (`show_page`) and window setup

Good for reading top to bottom or for small tweaks.

## OOP version

```
main.py                     entry point (wires things together)
spendly/
  config.py                 Palette, Layout, categories, constants
  formatting.py             Formatter (money, greeting), Parser (dates, amounts)
  date_range.py             DateRange (Day/Week/Month/Year/Custom)
  models.py                 Entry (abstract) -> ExpenseEntry, IncomeEntry
  wallet.py                 Wallet (owns all account balances)
  storage.py                JsonRepository (the only code that touches the file)
  tracker.py                ExpenseTracker (the service the UI talks to)
  ui/
    app.py                  SpendlyApp (window + navigation)
    sidebar.py, header.py   Sidebar, PageHeader
    basic.py                StyledLabel, ClickableLabel, StyledButton, StyledEntry
    containers.py           RoundedPanel, ScrollArea
    controls.py             SegmentedControl, CategoryTile
    charts.py               CategoryChart (abstract) -> BreakdownChart, DonutChart
    view_state.py           ViewState (selected month, period, etc.)
    pages/
      base.py               Page (abstract)
      ledger_page.py, calendar_page.py, calendar_widgets.py,
      charts_page.py, wallet_page.py, add_entry_page.py
      __init__.py           PAGES registry
```

### Layers

- **Domain** (`models`, `wallet`, `tracker`, `storage`, `date_range`): the rules and data. It never imports tkinter, so it can be tested or reused with another UI.
- **UI** (`spendly/ui`): reusable widgets, charts and pages built on the domain layer.
- **Entry point** (`main.py`): creates the repository and tracker, then starts the app.

### OOP concepts used

- **Abstraction**: `Entry`, `CategoryChart` and `Page` are abstract base classes
- **Inheritance**: `ExpenseEntry` / `IncomeEntry`, `BreakdownChart` / `DonutChart`, every page extends `Page`
- **Polymorphism**: each entry type knows how it changes a balance (`apply`, `revert`, `can_apply`, `can_revert`), so there are no `if type == ...` checks
- **Encapsulation**: `Wallet` keeps balances private, `JsonRepository` owns the file, `ViewState` replaces global variables
- **Composition**: `CalendarPage` is built from `MonthGrid`, `DayCell` and `SummaryPanel`

### Adding a new page

1. Create a class that extends `Page` in `spendly/ui/pages/`
2. Set `key`, `nav_label`, `title`, `subtitle` and implement `build_body(self, body)`
3. Add it to the tuple in `spendly/ui/pages/__init__.py`

The sidebar picks it up automatically.

## Which one should I use?

- **Procedural**: a single file, quick to read, easy to hand around
- **OOP**: easier to extend, test and maintain as the app grows

## Notes

- Page changes rebuild the page off-screen and then reveal it, to avoid flicker.
- Currency is set by `CURRENCY` (default `₱`) in the constants (`config.py` in the OOP version).
