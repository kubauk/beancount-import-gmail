import datetime
import os
from datetime import timedelta
from typing import Optional, Union

import gmails.retriever
from beancount.core import data
from beancount.core.data import Account, Entries
from beangulp.importer import Importer

from beancount_gmail.downloading_and_matching import download_and_match_transactions
from beancount_gmail.email_parser_protocol import EmailParser


class GmailImporter(Importer):
    def __init__(self, delegate: Importer, parsers: Union[EmailParser, list[EmailParser]], postage_account: str, gmail_address: str,
                 secrets_directory: str = os.path.dirname(os.path.realpath(__file__)),
                 search_delta: timedelta = timedelta()) -> None:
        self._search_delta = search_delta
        self._delegate = delegate
        self._parsers = parsers
        self._postage_account = postage_account
        self._gmail_address = gmail_address
        self._retriever = gmails.retriever.Retriever('beancount-import-gmail', self._gmail_address, secrets_directory)

    def extract(self, filepath: str, existing_entries: Entries = None) -> Entries:
        transactions = self._delegate.extract(filepath, existing_entries)
        download_and_match_transactions(self._parsers, self._retriever, transactions,
                                        self._postage_account, self._search_delta)
        return transactions

    def account(self, filepath: str) -> data.Account:
        return self._delegate.account(filepath)

    def identify(self, filepath: str) -> bool:
        return self._delegate.identify(filepath)

    def date(self, filepath: str) -> Optional[datetime.date]:
        return self._delegate.date(filepath)

    def filename(self, filepath: str) -> Optional[str]:
        return self._delegate.filename(filepath)
