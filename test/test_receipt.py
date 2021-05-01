import datetime

from beancount.core.data import Amount, D, Transaction
from hamcrest import assert_that, is_

from beancount_gmail.receipt import Receipt, TOTAL

RECEIPT_DATETIME = datetime.datetime(2020, 3, 14, 10, 10, 0)
NARRATION = 'Test Narration'
POSTAGE_ACCOUNT = 'Expenses:Postage'
ONE_POUND = Amount(D(1), 'GBP')


def test_simple_receipt_details_are_added_as_postings():
    transaction = Transaction(dict(), RECEIPT_DATETIME, '*', None, NARRATION, set(), set(), list())

    receipt = Receipt(RECEIPT_DATETIME, [('Detail 1', '1.00 GBP')], [(TOTAL, '1.00 GBP')], False)
    receipt.append_postings(transaction, POSTAGE_ACCOUNT)

    assert_that(len(transaction.postings), is_(1))
    assert_that(transaction.postings[0].units, is_(ONE_POUND))

    posting_meta = transaction.postings[0].meta
    assert_that('description' in posting_meta, is_(True))
    assert_that(posting_meta['description'], is_('Detail 1'))
