from builtins import isinstance
from datetime import datetime, timedelta, date
from typing import Union

import gmails.retriever
import pytz as pytz
from beancount.core.data import Transaction

from beancount_gmail.email_parser_protocol import EmailParser
from beancount_gmail.email_processing import extract_receipts
from beancount_gmail.receipt import Receipt


def download_and_match_transactions(parsers: Union[EmailParser, list[EmailParser]],
                                    retriever: gmails.retriever.Retriever,
                                    transactions: list[Transaction],
                                    postage_account: str,
                                    search_delta: timedelta = timedelta()) -> None:
    if isinstance(parsers, list):
        for parser in parsers:
            download_and_match_transactions_for_parser(parser, retriever, transactions, postage_account, search_delta)
    elif isinstance(parsers, EmailParser):
        download_and_match_transactions_for_parser(parsers, retriever, transactions, postage_account, search_delta)


def download_and_match_transactions_for_parser(parser: EmailParser,
                                               retriever: gmails.retriever.Retriever,
                                               transactions: list[Transaction],
                                               postage_account: str,
                                               search_delta: timedelta = timedelta()) -> None:
    filtered_transactions = list(filter(parser.transaction_filter, transactions))
    if len(filtered_transactions) == 0:
        return

    min_date, max_date = get_search_dates(filtered_transactions, search_delta)

    receipts = download_email_receipts(parser, retriever, min_date, max_date)
    for transaction in filtered_transactions:
        for receipt in receipts.copy():
            if isinstance(transaction, Transaction) and pairs_match(transaction, receipt, search_delta):
                receipts.remove(receipt)
                receipt.append_postings(transaction, postage_account)

    if len(receipts) > 0:
        print("Warning: Failed to match {} receipts".format(len(receipts)))
        for receipt in receipts:
            print('{} ({})'.format(receipt.receipt_date, ";".join(
                ["; ".join([str(detail) for detail in receipt_details])
                 for receipt_details in receipt.receipt_details])))

    unmatched_transactions = [transaction for transaction in filtered_transactions if len(transaction.postings) < 2]
    if unmatched_transactions:
        print('Warning: failed to match {} transactions'.format(len(unmatched_transactions)))
        for transaction in unmatched_transactions:
            print('{} ({}; {})'.format(transaction.date, transaction.narration,
                                       transaction.postings[0].units if transaction.postings else None))


def get_search_dates(transactions: list[Transaction], search_delta: timedelta = timedelta()) \
        -> tuple[datetime.date, datetime.date]:
    dates = sorted({transaction.date for transaction in transactions
                    if isinstance(transaction, Transaction)})
    return min(dates) - search_delta, max(dates) + timedelta(days=1) + search_delta


def download_email_receipts(parser: EmailParser, retriever: gmails.retriever.Retriever,
                            min_date: Union[date, datetime], max_date: Union[date, datetime]) -> list[Receipt]:
    return [receipt for email in
            retriever.get_messages_for_date_range(parser.search_query(), min_date, max_date, _EUROPE_LONDON_TZ)
            for receipt in extract_receipts(parser, email)]


_EUROPE_LONDON_TZ: pytz.tzinfo = pytz.timezone('Europe/London')


def pairs_match(transaction: Transaction, receipt: Receipt, search_delta: timedelta = timedelta()) -> bool:
    t_dates = {transaction.date}
    r_dates = {receipt.receipt_date.date()}
    while search_delta.days > 0:
        r_dates.add(receipt.receipt_date.date() + search_delta)
        r_dates.add(receipt.receipt_date.date() - search_delta)
        search_delta = search_delta - timedelta(days=1)

    if len(t_dates.intersection(r_dates)) > 0:
        if transaction.postings and transaction.postings[0].units == -receipt.total:
            return True
    return False
