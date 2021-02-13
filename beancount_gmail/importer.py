import datetime
import os
from datetime import timedelta

import gmailmessagessearch.retriever
from beancount.core.data import Transaction
from beangulp.importer import ImporterProtocol

from beancount_gmail.email_parser import extract_receipts


def pairs_match(transaction, receipt):
    if receipt and transaction.date == receipt.message_date.date():
        if transaction.postings[0].units == -receipt.total:
            return True
    return False


def date_or_datetime(transaction):
    if 'time' in transaction.meta:
        return datetime.datetime.combine(transaction.date,
                                         datetime.datetime.strptime(transaction.meta['time'], "%H:%M:%S").time())
    return transaction.date


class GmailImporter(ImporterProtocol):
    def __init__(self, delegate, postage_account, gmail_address,
                 secrets_directory=os.path.dirname(os.path.realpath(__file__))):
        self._delegate = delegate
        self._postage_account = postage_account
        self._gmail_address = gmail_address
        self._secrets_directory = secrets_directory

    def extract(self, file, existing_entries=None):
        transactions = self._delegate.extract(file, existing_entries)

        retriever = gmailmessagessearch.retriever.Retriever('beancount-import-gmail-paypal', self._gmail_address,
                                                            'from:service@paypal.co.uk', self._secrets_directory)

        dates = sorted({date_or_datetime(transaction) for transaction in transactions
                 if isinstance(transaction, Transaction)})
        receipts = [receipt for email in retriever.get_messages_for_date_range(min(dates), max(dates) + timedelta(days=1))
                    for receipt in extract_receipts(email)]

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
