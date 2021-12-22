import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Union, Callable, Optional

from beancount.core.data import Transaction
from bs4 import BeautifulSoup

from beancount_gmail.receipt import Receipt


def re_filter(expression: str) -> Callable:
    return lambda transaction: re.search(expression, transaction.narration) is not None


def transaction_filter(filter_param: Optional[Union[str, Callable]], transaction: Optional[Transaction]) -> Any:
    if not isinstance(transaction, Transaction):
        return False

    if not filter_param:
        return True

    if isinstance(filter_param, str):
        return filter_param in transaction.narration

    if isinstance(filter_param, Callable):
        return filter_param(transaction)

    raise Exception("Do not understand transaction_filter which should be a string or a function")


class EmailParser(ABC):
    def __init__(self, filter_param: Union[str, Callable] = None):
        self._filter_param = filter_param

    @abstractmethod
    def extract_receipts(self, message_date: datetime, soup: BeautifulSoup) -> list[Receipt]:
        """ Given a soup instance, the parser is responsible for returning a list of Receipts """

    @abstractmethod
    def search_query(self) -> str:
        """ Returns the GMail search string """

    def transaction_filter(self, transaction: Transaction) -> Any:
        return transaction_filter(self._filter_param, transaction)
