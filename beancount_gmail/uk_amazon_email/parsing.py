from datetime import datetime

import bs4

from beancount_gmail.common.parsing import extract_row_text
from beancount_gmail.receipt import Receipt, TOTAL


def index_containing(table_text, needle):
    for i, row in enumerate(table_text):
        if needle in row:
            return i
    return -1


def truncate_end_with_product_suggestions(table_text: list[list[str]]) -> list[list[str]]:
    end = index_containing(table_text, 'We hope to see you again soon.Amazon.co.uk')
    return table_text[0:end] if end > 0 else table_text


def extract_receipts(message_date: datetime, beautiful_soup: bs4.BeautifulSoup) -> list[Receipt]:
    receipts = list()

    table_text = [extract_row_text(table) for table in beautiful_soup.find_all('table')
                  if table.find('table') is None]

    order_only = truncate_end_with_product_suggestions(table_text)

    interesting = [row for row in order_only if len([entry for entry in row if '£' in entry]) > 0]
    if len(interesting) % 2 == 0:
        interesting_iter = iter(interesting)
        for t, d in zip(interesting_iter, interesting_iter):
            receipts.append(Receipt(message_date,
                                    [(d[1], "{} GBP".format(d[2]))],
                                    [(TOTAL, "{} GBP".format(t[1]))]))

    return receipts
