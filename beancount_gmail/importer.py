import datetime
import os
from datetime import timedelta, date, datetime
from typing import Union

import gmails.retriever
from beancount.core.data import Transaction
from beangulp.importer import ImporterProtocol

from beancount_gmail.email_parser_protocol import EmailParser
from beancount_gmail.email_processing import extract_receipts
from beancount_gmail.receipt import Receipt
from beancount_gmail.uk_paypal_email import PayPalUKParser


def pairs_match(transaction: Transaction, receipt: Receipt) -> bool:
    if receipt and transaction.date == receipt.receipt_date.date():
        if transaction.postings[0].units == -receipt.total:
            return True
    return False


def date_or_datetime(transaction: Transaction) -> Union[datetime, date]:
    if 'time' in transaction.meta:
        return datetime.combine(transaction.date,
                                datetime.strptime(transaction.meta['time'], "%H:%M:%S").time())
    return transaction.date


def download_email_receipts(parser: EmailParser, transactions: list[Transaction],
                            retriever: gmails.retriever.Retriever) -> list[Receipt]:
    min_date, max_date = get_search_dates(transactions)

    return [receipt for email in
            retriever.get_messages_for_date_range('from:service@paypal.co.uk',
                                                  min_date, max_date)
            for receipt in extract_receipts(parser, email)]


def get_search_dates(transactions):
    dates = sorted({date_or_datetime(transaction) for transaction in transactions
                    if isinstance(transaction, Transaction)})
    return min(dates), max(dates) + timedelta(days=1)


class GmailImporter(ImporterProtocol):
    def __init__(self, delegate, postage_account, gmail_address,
                 secrets_directory=os.path.dirname(os.path.realpath(__file__))):
        self._delegate = delegate
        self._postage_account = postage_account
        self._gmail_address = gmail_address
        self._secrets_directory = secrets_directory
        self._retriever = gmails.retriever.Retriever('beancount-import-gmail', self._gmail_address,
                                                     self._secrets_directory)

    def extract(self, file, existing_entries=None):
        transactions = self._delegate.extract(file, existing_entries)

        parser = PayPalUKParser()

        receipts = []

        receipts.extend(download_email_receipts(parser, transactions, self._retriever))

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
