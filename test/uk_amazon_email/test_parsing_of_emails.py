from datetime import datetime
from hamcrest import assert_that, is_

from beancount_gmail.uk_amazon_email.parsing import extract_receipts
from test.test_receipt import assert_receipt_with_one_detail, assert_receipt_with_details


def test_parse_amazon_order_2020_09_15(soup):
    beautiful_soup = soup("sample_html/amazon-order-2020-09-15.html")
    receipts = extract_receipts(datetime(2020, 9, 15), beautiful_soup)

    assert_that(len(receipts), is_(0))


def test_parse_amazon_order_2020_09_28(soup):
    beautiful_soup = soup("sample_html/amazon-order-2020-09-28.html")
    receipts = extract_receipts(datetime(2020, 9, 28), beautiful_soup)

    assert_that(len(receipts), is_(0))


def test_parse_amazon_order_2021_03_11_no_order_details(soup):
    beautiful_soup = soup("sample_html/amazon-order-2021-03-11-no-order-details.html")
    receipts = extract_receipts(datetime(2021, 3, 11), beautiful_soup)

    assert_that(len(receipts), is_(0))


def test_parse_amazon_order_2021_11_24(soup):
    beautiful_soup = soup("sample_html/amazon-order-2021-11-24.html")
    receipts = extract_receipts(datetime(2021, 11, 24), beautiful_soup)

    assert_receipt_with_one_detail(receipts[0],
                                   "28.98",
                                   "Moongiantgo Coffee Grinder Manual Compact & Effortless, Stainless Steel & Glass, " \
                                   "Adjustable Coarseness Ceramic Burr - 5 Precise Levels, with Spoon & Brush | Make " \
                                   "Fresh Coffee Anytime & Anywhere Condition: NewSold by:Moongiantgo-Eu Fulfilled " \
                                   "by Amazon",
                                   "31.50")


def test_parse_amazon_order_2021_11_24_multiple(soup):
    beautiful_soup = soup("sample_html/amazon-order-2021-11-24-multiple.html")
    receipts = extract_receipts(datetime(2021, 11, 24), beautiful_soup)

    assert_that(len(receipts), is_(2))

    assert_receipt_with_one_detail(receipts[0],
                                   "3.99",
                                   'Chrome 1/2" BSP Thread Female Blanking End Cap Radiator Chrome Plug Water Pipe ' \
                                   'Condition: NewSold by:Stevenson Plumbing and Electrical Supplies',
                                   "3.99")

    assert_receipt_with_one_detail(receipts[1],
                                   "7.29",
                                   'Metal Adaptor Reduction Water Faucet Tap 24mm Male to 1/2" BSP Male Joiner ' \
                                   'Condition: NewSold by:plumbing4home',
                                   "7.29")


def test_parse_amazon_order_2021_11_30(soup):
    beautiful_soup = soup("sample_html/amazon-order-2021-11-30.html")
    receipts = extract_receipts(datetime(2021, 11, 30), beautiful_soup)

    assert_receipt_with_one_detail(receipts[0],
                                   "8.99",
                                   "Gukasxi Tabletop Christmas Tree,Mini Artificial Christmas Pine Trees with " \
                                   "Plastic Base Season Ornaments Tabletop Trees for Xmas Holiday Party Home " \
                                   "Decor,with 2M String Lights and Ornaments Condition: NewSold by:Feng_x Fulfilled " \
                                   "by Amazon",
                                   "8.99")
