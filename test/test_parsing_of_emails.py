import datetime
import sys

import pytest
from beancount.core.amount import Amount
from beancount.core.number import D
from hamcrest import assert_that, calling, raises
from hamcrest.core.core.isequal import equal_to

from email_parser import find_receipts, NoTableFoundException, find_receipts_new

ZERO_GBP = Amount(D("0.00"), "GBP")


def test_refund_email_produces_correct_receipt(soup):
    receipts = find_receipts_new(datetime.datetime.now(), soup("refund-nov-2015.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "12.98", "Electronic C TWIST Shisha Variable Voltage 1300mah Battery "
                                                         "HOOKAH PEN + FREE USB [Red] Item Number 252189791369",
                                   "12.98")


def test_merchant_purchase_produces_correct_receipt(soup):
    receipts = find_receipts_new(datetime.datetime.now(), soup("merchant-purchase-nov-2015.html"))

    assert_that(len(receipts), equal_to(1))

    receipt = receipts[0]
    assert_that(receipt.total, equal_to(Amount(D("32.00"), "GBP")))
    assert_that(receipt.postage_and_packing, equal_to(ZERO_GBP))
    assert_receipt_with_one_detail(receipts[0], "32.00", "", "32.00")


def test_mar_2019_selling_produces_correct_receipt(soup):
    receipts = find_receipts_new(datetime.datetime.now(), soup("mar-2019-selling.html"))

    assert_that(len(receipts), equal_to(1))

    assert_receipt_with_one_detail(receipts[0], "-3.41",
                                   "The Secret Life of Pets DVD (2016) Chris Renaud Item Number 254143897831",
                                   "-2.01",
                                   "-1.40")


def test_new_format_dec_2015_email_produces_correct_receipt(soup):
    receipts = find_receipts_new(datetime.datetime.now(), soup("new-format-dec-2015.html"))

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
    receipts = find_receipts_new(datetime.datetime.now(), soup("new-format-feb-2017.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "1.15",
                                   "Mini Household Sealing Machine Sealer Impulse Sealer Poly Food "
                                   "Jewelry Item Number 272490036626", "0.99", "0.16")


def test_donation_format_dec_2017_produces_correct_receipt(soup):
    receipts = find_receipts_new(datetime.datetime.now(), soup("donation-dec-2017.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "50.00", "Anxiety UK Donation", "50.00")


def test_format_june_2018_produces_correct_receipt(soup):
    receipts = find_receipts_new(datetime.datetime.now(), soup("june-2018.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "4.49",
                                   "Derby Premium Black Stainless | Double Edge Razor Blades | "
                                   "Premium Safety DE [50 (10 packs of 5)] Item Number 132213313603", "4.49")


def test_dec_2018_with_suprious_postage_message_produces_correct_receipt(soup):
    receipts = find_receipts_new(datetime.datetime.now(), soup("dec-2018-with-extra-postage-message.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "13.98", "Selected:", "13.98", "3.99")


def test_totals_in_usd_do_not_produce_receipt(soup):
    receipts = find_receipts_new(datetime.datetime.now(), soup("totals-in-usd-2020.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "12.71", "Porkbun.com Order ID: 657601", "12.71", "0", "USD")


def test_facebook_donation_does_not_produce_receipt(soup):
    assert_that(calling(find_receipts, ).with_args(datetime.datetime.now(), soup("facebook-donation-2020-07.html")),
                raises(NoTableFoundException))


def assert_receipt_with_one_detail(receipt, total, detail, detail_amount, postage='0', currency="GBP"):
    assert_that(receipt.total, equal_to(Amount(D(total), currency)))
    assert_that(receipt.postage_and_packing, equal_to(Amount(D(postage), currency)))
    assert_that(receipt.receipt_details[0][0],
                equal_to(detail))
    assert_that(receipt.receipt_details[0][1], equal_to(Amount(D(detail_amount), currency)))


if __name__ == "__name__":
    pytest.main(sys.argv)
