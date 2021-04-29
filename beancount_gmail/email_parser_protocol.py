from datetime import datetime
from typing import Protocol

from bs4 import BeautifulSoup

from beancount_gmail.receipt import Receipt


class EmailParser(Protocol):
    def extract_receipts(self, message_date: datetime, soup: BeautifulSoup) -> list[Receipt]:
        """ Given a soup instance, the parser is responsible for returning a list of Receipts """
