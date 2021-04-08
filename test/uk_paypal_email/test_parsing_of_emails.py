import datetime
import sys

import pytest
from beancount.core.amount import Amount
from beancount.core.number import D
from hamcrest import assert_that
from hamcrest.core.core.isequal import equal_to

from beancount_gmail.uk_paypal_email.parser import find_receipts

ZERO_GBP = Amount(D("0.00"), "GBP")


def test_refund_email_produces_correct_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("uk_paypal_email/samples/refund-nov-2015.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "12.98", "Electronic C TWIST Shisha Variable Voltage 1300mah Battery "
                                                         "HOOKAH PEN + FREE USB [Red] Item Number 252189791369",
                                   "12.98")


def test_merchant_purchase_produces_correct_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("uk_paypal_email/samples/merchant-purchase-nov-2015.html"))

    assert_that(len(receipts), equal_to(1))

    receipt = receipts[0]
    assert_that(receipt.total, equal_to(Amount(D("32.00"), "GBP")))
    assert_that(receipt.postage_and_packing, equal_to(ZERO_GBP))
    assert_receipt_with_one_detail(receipts[0], "32.00", "", "32.00")


def test_mar_2019_selling_produces_correct_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("uk_paypal_email/samples/mar-2019-selling.html"))

    assert_that(len(receipts), equal_to(1))

    assert_receipt_with_one_detail(receipts[0], "-3.41",
                                   "The Secret Life of Pets DVD (2016) Chris Renaud Item Number 254143897831",
                                   "-2.01",
                                   "-1.40")


def test_new_format_dec_2015_email_produces_correct_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("uk_paypal_email/samples/new-format-dec-2015.html"))

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
    receipts = find_receipts(datetime.datetime.now(), soup("uk_paypal_email/samples/new-format-feb-2017.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "1.15",
                                   "Mini Household Sealing Machine Sealer Impulse Sealer Poly Food "
                                   "Jewelry Item Number 272490036626", "0.99", "0.16")


def test_donation_format_dec_2017_produces_correct_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("uk_paypal_email/samples/donation-dec-2017.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "50.00", "Anxiety UK Donation", "50.00")


def test_format_june_2018_produces_correct_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("uk_paypal_email/samples/june-2018.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "4.49",
                                   "Derby Premium Black Stainless | Double Edge Razor Blades | "
                                   "Premium Safety DE [50 (10 packs of 5)] Item Number 132213313603", "4.49")


def test_dec_2018_with_suprious_postage_message_produces_correct_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("uk_paypal_email/samples/dec-2018-with-extra-postage-message.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "13.98", "Selected:", "13.98", "3.99")


def test_nov_2020_sent_payment_produces_correct_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("uk_paypal_email/samples/nov-2020-sent-payment.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "5.00", "AdBlock Item No X0G0 FEOWSI wabsiec39704501", "5.00")


def test_totals_in_usd_do_not_produce_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("uk_paypal_email/samples/totals-in-usd-2020.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "12.71", "Porkbun.com Order ID: 657601", "12.71", "0", "USD")


def test_facebook_donation_produces_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("uk_paypal_email/samples/facebook-donation-2020-07.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_totals(receipts[0], "10.00")


def test_nov_2020_payment_processes_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("uk_paypal_email/samples/nov-2020-payment.html"))

    assert_that(len(receipts), equal_to(2))
    assert_receipt_with_one_detail(receipts[0], "8.49", "Korean GINSENG MAX 3125mg Tablets (90) EXTRA POTENCY "
                                                        "Ginsenosides (PANAX)322883226060", "8.49")

    assert_receipt_with_one_detail(receipts[1], "7.99", "GINKGO BILOBA 6000MG TABLETS HIGH STRENGTH "
                                                        "✅UK Made ✅Letterbox Friendly [90]121738405227", "7.99")


def test_jan_2021_payment_in_pln_processes_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("uk_paypal_email/samples/jan-2021-01-PLN.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "6.00", "Trip authorization request", "6.00", currency="PLN")


def test_mar_2021_payment_processes_receipt(soup):
    receipts = find_receipts(datetime.datetime.now(), soup("uk_paypal_email/samples/mar-2021.html"))

    assert_that(len(receipts), equal_to(1))
    assert_receipt_with_one_detail(receipts[0], "14.95", "Purchase amount", "14.95")


def assert_receipt_with_one_detail(receipt, total, detail, detail_amount, postage='0', currency="GBP"):
    assert_receipt_totals(receipt, total, postage, currency)
    assert_that(receipt.receipt_details[0][0],
                equal_to(detail))
    assert_that(receipt.receipt_details[0][1], equal_to(Amount(D(detail_amount), currency)))


def assert_receipt_totals(receipt, total, postage='0', currency="GBP"):
    assert_that(receipt.total, equal_to(Amount(D(total), currency)))
    assert_that(receipt.postage_and_packing, equal_to(Amount(D(postage), currency)))


if __name__ == "__name__":
    pytest.main(sys.argv)
