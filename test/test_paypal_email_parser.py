import datetime
from hamcrest import assert_that
from hamcrest.core.core.isequal import equal_to
from hamcrest.core.core.isnone import not_none
from money.money import Money

from email_parser import extract_transactions_from_html
from transaction import ZERO_GBP


def test_refund_email_produces_correct_sub_transactions(soup):
    html = soup("refund-nov-2015.html")
    transactions = extract_transactions_from_html(datetime.datetime.now(), html)
    assert_that(len(transactions), equal_to(1))
    transaction = transactions[0]
    assert_that(transaction.total, equal_to(Money("12.98", "GBP")))
    assert_that(transaction.sub_transactions[0][0],
                equal_to("Electronic C TWIST Shisha Variable Voltage 1300mah Battery\n"
                         "                                            "
                         "HOOKAH PEN + FREE USB [Red] Item Number 252189791369"))
    assert_that(transaction.sub_transactions[0][1], equal_to("£12.98\n"
                                                             "                                            GBP"))
    assert_that(transaction.postage_and_packing, equal_to(ZERO_GBP))


def test_new_format_email_produces_correct_sub_transactions(soup):
    html = soup("new-format.html")
    transactions = extract_transactions_from_html(datetime.datetime.now(), html)
    assert_that(len(transactions), equal_to(3))
    pass
