from functools import wraps

import gmails
from beancount.core.data import Transaction

from beancount_gmail.importer import download_and_match_transactions
from beancount_gmail.uk_ebay_email import UKeBayParser


def _interesting_transaction(transaction: Transaction):
    return isinstance(transaction, Transaction) and 'Luxembourg, eBay' in transaction.narration


_retriever = gmails.retriever.Retriever('beancount-import-gmail',
                                        'kuba.jamro@gmail.com', '/run/media/picasso/beancount.dm-crypt')


def _extract_email(transactions):
    return download_and_match_transactions(UKeBayParser(), _retriever,
                                           list(filter(_interesting_transaction, transactions)), "Postage")


def gmail_import(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        transactions = func(self, *args, **kwargs)
        _extract_email(transactions)
        return transactions

    return wrapper
