import datetime

from hamcrest import assert_that, contains_inanyorder

from transaction import Transaction, ZERO_GBP

MESSAGE_DATE = datetime.datetime.utcfromtimestamp(1542699976)
PAYEE = "payee"
NARRATION = "narration"
POSTAGE_ACCOUNT = "postage:account"
TOTAL_ACCOUNT = "total:account"


def test_newlines_from_descriptions_are_stripped_out():
    transaction = Transaction(MESSAGE_DATE,
                              [("Description without newline", "0.00 GBP"), ("Description with\nnewline", "0.00 GBP")],
                              [("Total", "0.00 GBP")], False)

    beancount_transaction = transaction.as_beancount_transaction(None, PAYEE, NARRATION, POSTAGE_ACCOUNT, TOTAL_ACCOUNT)
    assert_that([posting.meta['Description'] for posting in beancount_transaction.postings
                 if "Description" in posting.meta],
                contains_inanyorder("Description without newline", "Description with newline"))
