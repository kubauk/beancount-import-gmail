from datetime import datetime

import bs4

from beancount_gmail.common.parsing import extract_row_text
from beancount_gmail.receipt import Receipt, TOTAL


def extract_receipts(message_date: datetime, beautiful_soup: bs4.BeautifulSoup) -> list[Receipt]:
    table_text = [extract_row_text(table) for table in beautiful_soup.find_all('table')
                  if table.find('table') is None]

    receipts = list()

    interesting = (row for row in table_text if len([entry for entry in row if '£' in entry]) > 0)
    for t, d in zip(interesting, interesting):
        receipts.append(Receipt(message_date,
                                [(d[1], "{} GBP".format(d[2]))],
                                [(TOTAL, "{} GBP".format(t[1]))]))

    return receipts
