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


def test_refund_email_produces_correct_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("refund-nov-2015.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "12.98", "Electronic C TWIST Shisha Variable Voltage 1300mah Battery\n"
                                                         "                                            "
                                                         "HOOKAH PEN + FREE USB [Red] Item Number 252189791369",
                                   "12.98")


def test_merchant_purchase_produces_correct_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("merchant-purchase-nov-2015.html"))

    assert_that(len(receipts), equal_to(1))

    receipt = receipts[0]
    assert_that(receipt.total, equal_to(Amount(D("32.00"), "GBP")))
    assert_that(receipt.postage_and_packing, equal_to(ZERO_GBP))
    assert_that(len(receipt.receipt_details), equal_to(0))


def test_new_format_dec_2015_email_produces_correct_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("new-format-dec-2015.html"))

    assert_that(len(receipts), equal_to(3))

    assert_receipt_with_one_detail(receipts[0], "1.99",
                                   "Qi Wireless Power Charger plate Charging Pad For Samsung Galaxy S6 & S6 Edge",
                                   "1.99")

    assert_receipt_with_one_detail(receipts[1], "3.75",
                                   "Universal Qi Wireless Charging Receiver for All Micro-USB"
                                   " Android Mobile UK [PORT B (Wide interface Top)]",
                                   "3.75")

    assert_receipt_with_one_detail(receipts[2], "3.49",
                                   "Universal Qi Wireless Charging Receiver Pad Kit for All Micro-USB Android Mobile",
                                   "3.49")


def test_new_format_feb_2017_email_produces_correct_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("new-format-feb-2017.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "1.15",
                                   "Mini Household Sealing Machine Sealer Impulse Sealer Poly Food "
                                   "Jewelry Item Number 272490036626", "0.99", "0.16")


def test_donation_format_dec_2017_produces_correct_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("donation-dec-2017.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "50.00", "Anxiety UK Donation", "50.00")


def test_donation_format_june_2018_produces_correct_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("june-2018.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "4.49",
                                   "Derby Premium Black Stainless | Double Edge Razor Blades |  "
                                   "Premium Safety DE [50 (10 packs of 5)] Item Number\n\n\n132213313603", "4.49")


def assert_receipt_with_one_detail(receipt, total, detail, detail_amount, postage='0'):
    assert_that(receipt.total, equal_to(Amount(D(total), "GBP")))
    assert_that(receipt.postage_and_packing, equal_to(Amount(D(postage), "GBP")))
    assert_that(receipt.receipt_details[0][0],
                equal_to(detail))
    assert_that(receipt.receipt_details[0][1], equal_to(Amount(D(detail_amount), "GBP")))


if __name__ == "__name__":
    pytest.main(sys.argv)
