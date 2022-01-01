import datetime
from typing import Any

from beancount.core.amount import Amount
from beancount.core.data import Transaction
from beancount.core.number import D, ONE
from hamcrest import assert_that, is_, equal_to
from hamcrest.core.base_matcher import BaseMatcher, T
from hamcrest.core.description import Description
from hamcrest.core.string_description import StringDescription

from beancount_gmail.receipt import Receipt, TOTAL

RECEIPT_DATETIME = datetime.datetime(2020, 3, 14, 10, 10, 0)
NARRATION = 'Test Narration'
POSTAGE_ACCOUNT = 'Expenses:Postage'
ONE_POUND = Amount(ONE, 'GBP')
TWO_POUNDS = Amount(D(2), 'GBP')


def test_simple_receipt_details_are_added_as_postings() -> None:
    transaction = _simple_transaction()

    receipt = Receipt(RECEIPT_DATETIME, [('Detail 1', '1.00 GBP')], [(TOTAL, '1.00 GBP')], negate=False)
    receipt.append_postings(transaction, POSTAGE_ACCOUNT)

    _assert_posting_details(transaction, [{'description': 'Detail 1', 'unit': ONE_POUND}])


def test_multiple_receipt_details_are_added_as_postings() -> None:
    transaction = _simple_transaction()

    receipt_details = [('Detail 1', '1.00 GBP'), ('Detail 2', '2.00 GBP'), ('Detail 3', '1.00 GBP')]

    receipt = Receipt(RECEIPT_DATETIME, receipt_details, [(TOTAL, '1.00 GBP')], negate=False)
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

    receipt = Receipt(RECEIPT_DATETIME, receipt_details, totals, negate=False)
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


def assert_receipt_with_one_detail(receipt, total, detail, detail_amount, postage='0', currency='GBP'):
    if isinstance(receipt, list):
        if len(receipt) != 1:
            raise Exception("Passed a list, but expecting only one Receipt")
        receipt = receipt[0]
    assert_receipt_with_details(receipt, total, [(detail, detail_amount)], postage, currency)


def assert_receipt_with_details(receipt, total, details, postage='0', currency='GBP'):
    assert_receipt_totals(receipt, total, postage, currency)
    assert_that(len(receipt.receipt_details), is_(len(details)))
    for i, detail in enumerate(details):
        assert_that(receipt.receipt_details[i][0], equal_to(detail[0]))
        assert_that(receipt.receipt_details[i][1], equal_to(Amount(D(detail[1]), currency)))


def receipt_with_one_detail(param: dict):
    class ReceiptWithDetailMatcher(BaseMatcher):
        def _matches(self, item: T) -> bool:
            return self.check_receipt(item, StringDescription())

        def describe_to(self, description: Description) -> None:
            description.append_text(
                "Receipt with description {} and total {}".format(param['description'], param['total']))

        def describe_mismatch(self, item: T, mismatch_description: Description) -> None:
            self.check_receipt(item, mismatch_description)

        @staticmethod
        def check_receipt(item: T, mismatch_description: Description) -> bool:
            if not isinstance(item, Receipt):
                mismatch_description.append_text("But item was not a Receipt.")
                return False
            if Amount(D(param['total']), "GBP") != item.total:
                mismatch_description.append_text("But total was {}".format(item.total))
                return False
            if param['description'][0] != item.receipt_details[0][0]:
                mismatch_description.append_text("But description was {}".format(item.receipt_details[0][0]))
                return False
            if Amount(D(param['description'][1]), "GBP") != item.receipt_details[0][1]:
                mismatch_description.append_text(
                    "But the description total was {}\nfor description {}".format(item.receipt_details[0][1],
                                                                                  item.receipt_details[0][0]))
                return False
            return True

    return ReceiptWithDetailMatcher()
