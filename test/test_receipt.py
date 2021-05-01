import datetime
from typing import Sequence

from beancount.core.data import Amount, D, Transaction
from hamcrest import assert_that, is_

from beancount_gmail.receipt import Receipt, TOTAL

RECEIPT_DATETIME = datetime.datetime(2020, 3, 14, 10, 10, 0)
NARRATION = 'Test Narration'
POSTAGE_ACCOUNT = 'Expenses:Postage'
ONE_POUND = Amount(D(1), 'GBP')
TWO_POUNDS = Amount(D(2), 'GBP')


def test_simple_receipt_details_are_added_as_postings():
    transaction = _simple_transaction()

    receipt = Receipt(RECEIPT_DATETIME, [('Detail 1', '1.00 GBP')], [(TOTAL, '1.00 GBP')], False)
    receipt.append_postings(transaction, POSTAGE_ACCOUNT)

    assert_that(len(transaction.postings), is_(1))
    _assert_posting_units_are(transaction, [ONE_POUND])

    _assert_posting_descriptions_are(transaction, ['Detail 1'])


def _assert_posting_descriptions_are(transaction: Transaction, details: Sequence[str]):
    for index, detail in enumerate(details):
        posting_meta = transaction.postings[index].meta
        assert_that('description' in posting_meta, is_(True))
        assert_that(posting_meta['description'], is_(detail))


def test_multiple_receipt_details_are_added_as_postings():
    transaction = _simple_transaction()

    receipt_details = [('Detail 1', '1.00 GBP'), ('Detail 2', '2.00 GBP'), ('Detail 3', '1.00 GBP')]

    receipt = Receipt(RECEIPT_DATETIME, receipt_details, [(TOTAL, '1.00 GBP')], False)
    receipt.append_postings(transaction, POSTAGE_ACCOUNT)

    assert_that(len(transaction.postings), is_(3))
    _assert_posting_units_are(transaction, [ONE_POUND, TWO_POUNDS, ONE_POUND])
    _assert_posting_descriptions_are(transaction, ['Detail 1', 'Detail 2', 'Detail 3'])


def _assert_posting_units_are(transaction: Transaction, units: Sequence):
    for index, unit in enumerate(units):
        assert_that(transaction.postings[index].units, is_(unit))


def _simple_transaction():
    return Transaction(dict(), RECEIPT_DATETIME, '*', None, NARRATION, set(), set(), list())
