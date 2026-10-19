"""Page registry. To add a screen: subclass Page and list it here."""

from .add_entry_page import AddEntryPage
from .calendar_page import CalendarPage
from .charts_page import ChartsPage
from .ledger_page import LedgerPage
from .wallet_page import WalletPage

PAGES = {cls.key: cls for cls in (LedgerPage, CalendarPage, ChartsPage, WalletPage, AddEntryPage)}
