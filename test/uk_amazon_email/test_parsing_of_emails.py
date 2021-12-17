from datetime import datetime

import bs4

from beancount_gmail.common.parsing import extract_row_text
from beancount_gmail.receipt import Receipt, TOTAL
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


def extract_receipts(message_date: datetime, beautiful_soup: bs4.BeautifulSoup) -> list[Receipt]:
    table_text = [extract_row_text(table) for table in beautiful_soup.find_all('table')
                  if table.find('table') is None]

    return [Receipt(message_date,
                    [(table_text[6][1], "{} GBP".format(table_text[6][2]))],
                    [(TOTAL, "{} GBP".format(table_text[4][1]))])]
