import datetime
from typing import Any

from beancount.core.amount import Amount
from beancount.core.data import Transaction
from beancount.core.number import D, ONE
from hamcrest import assert_that, is_, equal_to

from beancount_gmail.receipt import Receipt, TOTAL

RECEIPT_DATETIME = datetime.datetime(2020, 3, 14, 10, 10, 0)
NARRATION = 'Test Narration'
POSTAGE_ACCOUNT = 'Expenses:Postage'
ONE_POUND = Amount(ONE, 'GBP')
TWO_POUNDS = Amount(D(2), 'GBP')


def test_simple_receipt_details_are_added_as_postings() -> None:
    transaction = _simple_transaction()

    receipt = Receipt(RECEIPT_DATETIME, [('Detail 1', '1.00 GBP')], [(TOTAL, '1.00 GBP')], False)
    receipt.append_postings(transaction, POSTAGE_ACCOUNT)

    _assert_posting_details(transaction, [{'description': 'Detail 1', 'unit': ONE_POUND}])


def test_multiple_receipt_details_are_added_as_postings() -> None:
    transaction = _simple_transaction()

    receipt_details = [('Detail 1', '1.00 GBP'), ('Detail 2', '2.00 GBP'), ('Detail 3', '1.00 GBP')]

    receipt = Receipt(RECEIPT_DATETIME, receipt_details, [(TOTAL, '1.00 GBP')], False)
    receipt.append_postings(transaction, POSTAGE_ACCOUNT)

    _assert_posting_details(transaction,
                            [
                                {'description': 'Detail 1', 'unit': ONE_POUND},
                                {'description': 'Detail 2', 'unit': TWO_POUNDS},
                                {'description': 'Detail 3', 'unit': ONE_POUND},
                            ])


def test_postage_posting_is_added() -> None:
    transaction = _simple_transaction()

    receipt_details = [('Detail 1', '1.00 GBP'), ('Detail 2', '2.00 GBP')]
    totals = [('Postage and packaging', '1.00 GBP'), (TOTAL, '3.00 GBP')]

    receipt = Receipt(RECEIPT_DATETIME, receipt_details, totals, False)
    receipt.append_postings(transaction, POSTAGE_ACCOUNT)

    _assert_posting_details(transaction,
                            [
                                {'description': 'Detail 1', 'unit': ONE_POUND},
                                {'description': 'Detail 2', 'unit': TWO_POUNDS},
                                {'account': POSTAGE_ACCOUNT, 'unit': ONE_POUND},
                            ])


def _assert_posting_details(transaction: Transaction, posting_details: list[dict[str, Any]]) -> None:
    assert_that(len(transaction.postings), is_(len(posting_details)))
    for index, posting_detail in enumerate(posting_details):
        if 'unit' in posting_detail:
            assert_that(transaction.postings[index].units, is_(posting_detail['unit']))
        if 'description' in posting_detail:
            posting_meta = transaction.postings[index].meta
            assert_that('description' in posting_meta, is_(True))
            assert_that(posting_meta['description'], is_(posting_detail['description']))
        if 'account' in posting_detail:
            assert_that(transaction.postings[index].account, is_(posting_detail['account']))


def _simple_transaction() -> Transaction:
    return Transaction(dict(), RECEIPT_DATETIME, '*', None, NARRATION, set(), set(), list())


def assert_receipt_totals(receipt, total, postage='0', currency="GBP"):
    assert_that(receipt.total, equal_to(Amount(D(total), currency)))
    assert_that(receipt.postage_and_packing, equal_to(Amount(D(postage), currency)))


def assert_receipt_with_one_detail(receipt, total, detail, detail_amount, postage='0', currency="GBP"):
    assert_receipt_totals(receipt, total, postage, currency)
    assert_that(receipt.receipt_details[0][0],
                equal_to(detail))
    assert_that(receipt.receipt_details[0][1], equal_to(Amount(D(detail_amount), currency)))