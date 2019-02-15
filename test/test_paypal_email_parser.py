import datetime

import pytest
import sys

from beancount.core.amount import Amount
from beancount.core.number import D
from hamcrest import assert_that
from hamcrest.core.core.isequal import equal_to
from money.money import Money

from email_parser import find_receipts

ZERO_GBP = Amount(D("0.00"), "GBP")


def test_refund_email_produces_correct_sub_transactions(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("refund-nov-2015.html"))

    assert_that(len(receipts), equal_to(1))

    receipt = receipts[0]
    assert_that(receipt.total, equal_to(Amount(D("12.98"), "GBP")))
    assert_that(receipt.postage_and_packing, equal_to(ZERO_GBP))
    assert_that(receipt.sub_transactions[0][0],
                equal_to("Electronic C TWIST Shisha Variable Voltage 1300mah Battery\n"
                         "                                            "
                         "HOOKAH PEN + FREE USB [Red] Item Number 252189791369"))
    assert_that(receipt.sub_transactions[0][1], equal_to(Amount(D("12.98"), "GBP")))


def test_merchant_purchase_produces_correct_sub_transactions(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("merchant-purchase-nov-2015.html"))

    assert_that(len(receipts), equal_to(1))

    receipt = receipts[0]
    assert_that(receipt.total, equal_to(Amount(D("32.00"), "GBP")))
    assert_that(receipt.postage_and_packing, equal_to(ZERO_GBP))
    assert_that(len(receipt.sub_transactions), equal_to(0))


def test_new_format_dec_2015_email_produces_correct_sub_transactions(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("new-format-dec-2015.html"))

    assert_that(len(receipts), equal_to(3))

    assert_that(receipts[0].total, equal_to(Amount(D("1.99"), "GBP")))
    assert_that(receipts[0].postage_and_packing, equal_to(ZERO_GBP))
    assert_that(receipts[0].sub_transactions[0][0],
                equal_to("Qi Wireless Power Charger plate Charging Pad For Samsung Galaxy S6 & S6 Edge"))
    assert_that(receipts[0].sub_transactions[0][1], equal_to(Amount(D("1.99"), "GBP")))

    assert_that(receipts[1].total, equal_to(Amount(D("3.75"), "GBP")))
    assert_that(receipts[1].postage_and_packing, equal_to(ZERO_GBP))
    assert_that(receipts[1].sub_transactions[0][0],
                equal_to("Universal Qi Wireless Charging Receiver for All Micro-USB"
                         " Android Mobile UK [PORT B (Wide interface Top)]"))
    assert_that(receipts[1].sub_transactions[0][1], equal_to(Amount(D("3.75"), "GBP")))

    assert_that(receipts[2].total, equal_to(Amount(D("3.49"), "GBP")))
    assert_that(receipts[2].postage_and_packing, equal_to(ZERO_GBP))
    assert_that(receipts[2].sub_transactions[0][0],
                equal_to("Universal Qi Wireless Charging Receiver Pad Kit for All Micro-USB Android Mobile"))
    assert_that(receipts[2].sub_transactions[0][1], equal_to(Amount(D("3.49"), "GBP")))


def test_new_format_feb_2017_email_produces_correct_sub_transactions(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("new-format-feb-2017.html"))

    assert_that(len(receipts), equal_to(1))

    assert_that(receipts[0].total, equal_to(Amount(D("1.15"), "GBP")))
    assert_that(receipts[0].postage_and_packing, equal_to(Amount(D("0.16"), "GBP")))
    assert_that(receipts[0].sub_transactions[0][0],
                equal_to("Mini Household Sealing Machine Sealer Impulse Sealer Poly Food Jewelry Item Number 272490036626"))
    assert_that(receipts[0].sub_transactions[0][1], equal_to(Amount(D("0.99"), "GBP")))


def test_donation_format_dec_2017_produces_correct_sub_transactions(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("donation-dec-2017.html"))

    assert_that(len(receipts), equal_to(1))

    assert_that(receipts[0].total, equal_to(Amount(D("50.00"), "GBP")))
    assert_that(receipts[0].sub_transactions[0][0],
                equal_to("Anxiety UK Donation"))
    assert_that(receipts[0].sub_transactions[0][1], equal_to(Amount(D("50.00"), "GBP")))

    pass


if __name__ == "__name__":
    pytest.main(sys.argv)
