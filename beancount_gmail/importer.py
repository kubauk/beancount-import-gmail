import os
from datetime import timedelta, datetime

import gmails.retriever
import pytz as pytz
from beancount.core.data import Transaction
from beangulp.importer import ImporterProtocol

from beancount_gmail.email_parser_protocol import EmailParser
from beancount_gmail.email_processing import extract_receipts
from beancount_gmail.receipt import Receipt
from beancount_gmail.uk_paypal_email import PayPalUKParser

_EUROPE_LONDON_TZ = pytz.timezone('Europe/London')


def pairs_match(transaction: Transaction, receipt: Receipt) -> bool:
    if receipt and transaction.date == receipt.receipt_date.date():
        if transaction.postings[0].units == -receipt.total:
            return True
    return False


def download_email_receipts(parser: EmailParser, retriever: gmails.retriever.Retriever,
                            min_date: datetime, max_date: datetime) -> list[Receipt]:
    return [receipt for email in
            retriever.get_messages_for_date_range('from:service@paypal.co.uk', min_date, max_date, _EUROPE_LONDON_TZ)
            for receipt in extract_receipts(parser, email)]


def get_search_dates(transactions):
    dates = sorted({transaction.date for transaction in transactions
                    if isinstance(transaction, Transaction)})
    return min(dates), max(dates) + timedelta(days=1)


class GmailImporter(ImporterProtocol):
    def __init__(self, delegate, postage_account, gmail_address,
                 secrets_directory=os.path.dirname(os.path.realpath(__file__))):
        self._delegate = delegate
        self._postage_account = postage_account
        self._gmail_address = gmail_address
        self._retriever = gmails.retriever.Retriever('beancount-import-gmail', self._gmail_address, secrets_directory)

    def extract(self, file, existing_entries=None):
        transactions = self._delegate.extract(file, existing_entries)
        min_date, max_date = get_search_dates(transactions)

        parser = PayPalUKParser()

        receipts = []

        receipts.extend(download_email_receipts(parser, self._retriever, min_date, max_date))

        for transaction in transactions:
            for receipt in receipts.copy():
                if isinstance(transaction, Transaction) and pairs_match(transaction, receipt):
                    receipts.remove(receipt)
                    receipt.append_postings(transaction, self._postage_account)

        return transactions

    def name(self):
        return self._delegate.name()

    def identify(self, file):
        return self._delegate.identify(file)

    def file_account(self, file):
        return self._delegate.file_account(file)
