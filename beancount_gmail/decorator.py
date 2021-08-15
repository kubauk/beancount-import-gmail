from functools import wraps

import gmails

from beancount_gmail.importer import download_and_match_transactions


def _add_email_details(parser, email_address, credentials_directory, postage_account, transactions):
    retriever = gmails.retriever.Retriever('beancount-import-gmail', email_address, credentials_directory)
    return download_and_match_transactions(parser, retriever, transactions, postage_account)


def gmail_import(parser, email_address, credentials_directory, postage_account):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            transactions = func(self, *args, **kwargs)
            _add_email_details(parser, email_address, credentials_directory, postage_account, transactions)
            return transactions
        return wrapper
    return decorator
