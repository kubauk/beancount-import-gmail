from datetime import datetime

import bs4

from beancount_gmail.common.parsing import extract_row_text
from beancount_gmail.receipt import Receipt


def test_parse_amazon_order_2021_11_24(soup):
    beautiful_soup = soup("sample_html/amazon-order-2021-11-24.html")
    receipts = extract_receipts(datetime.now(), beautiful_soup)

    pass


def extract_receipts(message_date: datetime, beautiful_soup: bs4.BeautifulSoup) -> list[Receipt]:
    table_text = [extract_row_text(table) for table in beautiful_soup.find_all('table')
                  if table.find('table') is None]

    return [Receipt(message_date, [(table_text[6][1], "{} GBP".format(table_text[6][2]))])]

