import os

import gmails.retriever
from beancount.core.data import Account, Entries
from beangulp.importer import ImporterProtocol

from beancount_gmail.downloading_and_matching import download_and_match_transactions
from beancount_gmail.email_parser_protocol import EmailParser


class GmailImporter(ImporterProtocol):
    def __init__(self, delegate: ImporterProtocol, parser: EmailParser, postage_account: str, gmail_address: str,
                 secrets_directory: str = os.path.dirname(os.path.realpath(__file__))) -> None:
        self._delegate = delegate
        self.parser = parser
        self._postage_account = postage_account
        self._gmail_address = gmail_address
        self._retriever = gmails.retriever.Retriever('beancount-import-gmail', self._gmail_address, secrets_directory)

    def extract(self, file, existing_entries: Entries = None) -> Entries:
        transactions = self._delegate.extract(file, existing_entries)
        download_and_match_transactions(self.parser, self._retriever, transactions, self._postage_account)
        return transactions

    def name(self) -> str:
        return self._delegate.name()

    def identify(self, file) -> bool:
        return self._delegate.identify(file)

    def file_account(self, file) -> Account:
        return self._delegate.file_account(file)
