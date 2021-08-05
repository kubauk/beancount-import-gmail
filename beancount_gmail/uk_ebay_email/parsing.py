import datetime

from bs4.element import Comment

from beancount_gmail.receipt import Receipt
from beancount_gmail.common.parsing import extract_row_text


def remove_comments(tag):
    for c in tag.find_all(text=lambda t: isinstance(t, Comment)):
        c.extract()


def description_details(details):
    return details[0], first_price(details)


def total_details(rows):
    rows_iter = iter(rows[1:])
    return list(filter(lambda k: 'GBP' in k[1], zip(rows_iter, rows_iter)))


def description_and_total_details(details):
    return description_details(details[0]), total_details(details[1])


def first_price(rows):
    prices = [row for row in rows if 'GBP' in row]
    return None if len(prices) == 0 else prices[0]


def extract_receipt(message_date, soup):
    remove_comments(soup)
    table_text = [replace_with_currency_code(extract_row_text(table)) for table in soup.find_all('table')
                  if table.find('table') is None]
    descriptions, totals = description_and_total_details(list(filter(interesting_row, table_text)))
    return Receipt(message_date, [descriptions], totals, False)


def replace_with_currency_code(rows):
    def append_iso_currency_code(row):
        split = row.split('£')
        if len(split) > 1:
            return '{} GBP'.format(split[1])
        else:
            return row

    return [append_iso_currency_code(row) for row in rows]


def interesting_row(rows):
    if len(rows) > 1:
        return any("Order" in s for s in rows)
    return False