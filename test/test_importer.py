import datetime
from unittest.mock import Mock, call

import gmails.retriever
import pytest
from beancount.core.data import Transaction, Open, Balance, Account, Amount, create_simple_posting, D
from beangulp.importer import ImporterProtocol
from hamcrest import assert_that, instance_of, is_

from beancount_gmail import GmailImporter
from beancount_gmail.email_parser_protocol import EmailParser
from beancount_gmail.email_processing import get_message_date
from beancount_gmail.importer import get_search_dates, download_email_receipts, pairs_match
from beancount_gmail.receipt import Receipt
from test.matchers import _, beautiful_soup_containing_text

ACCOUNT = "ACCOUNT"
CURRENCY = "CURRENCY"


def test_search_date_return_correct_range_for_single_transaction():
    min_date, max_date = get_search_dates([_mock_transaction(datetime.date(2020, 3, 14))])
    assert_that(min_date, is_(datetime.date(2020, 3, 14)))
    assert_that(max_date, is_(datetime.date(2020, 3, 15)))


def test_search_date_return_correct_range_for_multiple_transaction():
    min_date, max_date = get_search_dates([
        _mock_transaction(datetime.date(2020, 3, 14)),
        _mock_transaction(datetime.date(2019, 1, 2)),
        _mock_transaction(datetime.date(2020, 2, 3)),
        _mock_transaction(datetime.date(2019, 12, 15)),
    ])
    assert_that(min_date, is_(datetime.date(2019, 1, 2)))
    assert_that(max_date, is_(datetime.date(2020, 3, 15)))


def test_search_date_ignores_non_transactions():
    min_date, max_date = get_search_dates([
        _mock_directive(datetime.date(2020, 3, 14), Open),
        _mock_directive(datetime.date(2019, 1, 2), Balance),
        _mock_directive(datetime.date(2020, 2, 3), Open),
        _mock_directive(datetime.date(2019, 12, 15), Transaction),
    ])
    assert_that(min_date, is_(datetime.date(2019, 12, 15)))
    assert_that(max_date, is_(datetime.date(2019, 12, 16)))


def test_parser_is_called_for_every_retrieved_email(email_message):
    parser = Mock(spec=EmailParser)

    email1 = email_message('sample_emails/html.eml')
    email2 = email_message('sample_emails/html2.eml')
    email3 = email_message('sample_emails/html3.eml')

    date1 = get_message_date(email1)
    date2 = get_message_date(email2)
    date3 = get_message_date(email3)

    retriever = Mock(spec=gmails.retriever.Retriever)
    retriever.get_messages_for_date_range.return_value = [email1, email2, email3]

    min_date = datetime.date(2021, 1, 1)
    max_date = datetime.date(2021, 3, 14)

    download_email_receipts(parser, retriever, min_date, max_date)

    retriever.get_messages_for_date_range.assert_called_with('from:service@paypal.co.uk', min_date, max_date,
                                                             _(instance_of(datetime.tzinfo)))

    parser.extract_receipts.assert_has_calls([
        call(date1, _(beautiful_soup_containing_text("email1"))),
        call(date2, _(beautiful_soup_containing_text("email2"))),
        call(date3, _(beautiful_soup_containing_text("email3")))
    ])


def test_support_functions_call_delegate():
    delegate = Mock(spec=ImporterProtocol)

    importer = GmailImporter(delegate, 'POSTAGE', 'EMAIL')

    delegate.name.return_value = 'delegate_name'
    assert_that(importer.name(), is_('delegate_name'))

    delegate.identify.return_value = True
    assert_that(importer.identify('file'), is_(True))
    delegate.identify.assert_called_with('file')

    delegate.file_account.return_value = Account('EXPENSE')
    assert_that(importer.file_account('file2'), is_(Account('EXPENSE')))
    delegate.file_account.assert_called_with('file2')


def _mock_receipt(date: datetime, number: str = None) -> Receipt:
    receipt = Mock(spec=Receipt)
    receipt.receipt_date = date
    if number:
        receipt.total = Amount(D(number), CURRENCY)
    return receipt


def _mock_directive(date, z):
    transaction = Mock(spec=z)
    transaction.date = date
    transaction.meta = {}
    return transaction


def _mock_transaction(date: datetime.date) -> Transaction:
    transaction = _mock_directive(date, Transaction)
    transaction.postings = []
    return transaction


def _mock_transaction_with_posting(date: datetime.date, number: str) -> Transaction:
    transaction = _mock_transaction(date)
    create_simple_posting(transaction, ACCOUNT, number, CURRENCY)
    return transaction


@pytest.mark.parametrize("transaction, receipt, result",
                         [(_mock_transaction(datetime.date(2020, 12, 23)),
                           _mock_receipt(datetime.datetime(2021, 3, 14, 12, 32, 20)), False),
                          (_mock_transaction_with_posting(datetime.date(2020, 12, 23), "-1.00"),
                           _mock_receipt(datetime.datetime(2021, 3, 14, 12, 32, 20), "1.00"), False),
                          (_mock_transaction(datetime.date(2021, 12, 23)),
                           _mock_receipt(datetime.datetime(2021, 12, 23, 12, 32, 20), "1.00"), False),
                          (_mock_transaction(datetime.datetime(2020, 12, 23, 1, 2, 3)),
                           _mock_receipt(datetime.datetime(2021, 3, 14, 12, 32, 20), "1.00"), False),
                          (_mock_transaction_with_posting(datetime.date(2021, 3, 14), "-2.00"),
                           _mock_receipt(datetime.datetime(2021, 3, 14, 12, 32, 20), "1.00"), False),
                          (_mock_transaction_with_posting(datetime.date(2021, 3, 14), "-1.00"),
                           _mock_receipt(datetime.datetime(2021, 3, 14, 12, 32, 20), "1.00"), True)]
                         )
def test_transaction_and_receipt_pairs_match(transaction, receipt, result):
    assert_that(pairs_match(transaction, receipt), is_(result))
