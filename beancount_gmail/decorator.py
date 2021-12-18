from datetime import timedelta
from functools import wraps

import gmails
from beancount.core.data import Transaction

from beancount_gmail.downloading_and_matching import download_and_match_transactions
from beancount_gmail.email_parser_protocol import EmailParser

_RETRIEVER_CACHE = dict()


def _add_email_details(parser: EmailParser,
                       email_address: str,
                       credentials_directory: str,
                       postage_account: str,
                       transactions: list[Transaction],
                       search_delta: timedelta = timedelta()) -> None:
    retriever = _RETRIEVER_CACHE.setdefault((email_address, credentials_directory),
                                            gmails.retriever.Retriever('beancount-import-gmail',
                                                                       email_address,
                                                                       credentials_directory))
    download_and_match_transactions(parser, retriever, transactions, postage_account, search_delta)


def gmail_import(parser: EmailParser, email_address: str, credentials_directory: str, postage_account: str,
                 search_delta: timedelta = timedelta()):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            transactions = func(self, *args, **kwargs)
            _add_email_details(parser, email_address, credentials_directory,
                               postage_account, transactions, search_delta)
            return transactions

        return wrapper

    return decorator
