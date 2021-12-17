from datetime import datetime

from beancount_gmail.uk_amazon_email.parsing import extract_receipts
from test.test_receipt import assert_receipt_with_one_detail


def test_parse_amazon_order_2021_11_24(soup):
    beautiful_soup = soup("sample_html/amazon-order-2021-11-24.html")
    receipts = extract_receipts(datetime.now(), beautiful_soup)

    assert_receipt_with_one_detail(receipts[0],
                                   "28.98",
                                   "Moongiantgo Coffee Grinder Manual Compact & Effortless, Stainless Steel & Glass, "\
                                   "Adjustable Coarseness Ceramic Burr - 5 Precise Levels, with Spoon & Brush | Make "\
                                   "Fresh Coffee Anytime & Anywhere Condition: NewSold by:Moongiantgo-Eu Fulfilled by "\
                                   "Amazon",
                                   "31.50",
                                   currency="GBP")


