from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup
from bs4.element import Comment, Tag

from beancount_gmail.common.parsing import extract_row_text
from beancount_gmail.receipt import Receipt, _sum_up_sub_total


def remove_comments(tag: Tag) -> None:
    for c in tag.find_all(text=lambda t: isinstance(t, Comment)):
        c.extract()


def description_details(details: list[str]) -> tuple[str, Optional[str]]:
    return details[0], first_price(details)


def total_details(rows: list[str]) -> list[tuple[str, str]]:
    rows_iter = iter(rows[1:])
    return list(filter(lambda k: 'GBP' in k[1], zip(rows_iter, rows_iter)))


def description_and_total_details(details: list[list[str]]) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    totals = details.pop()

    return [description_details(detail) for detail in details], total_details(totals)


def first_price(rows: list[str]) -> str:
    prices = [row for row in rows if 'GBP' in row]
    return None if len(prices) == 0 else prices[0]


def extract_receipts(message_date: datetime, soup: BeautifulSoup) -> list[Receipt]:
    remove_comments(soup)
    table_text = [replace_with_currency_code(extract_row_text(table)) for table in soup.find_all('table')
                  if table.find('table') is None]
    descriptions, totals = description_and_total_details(list(filter(interesting_row, table_text)))

    receipts = list()
    receipt_details = list()
    for description, amount in descriptions:
        if 'Your seller' in description:
            if len(receipt_details) > 0:
                receipts.append(Receipt(message_date, receipt_details,
                                        total=_sum_up_sub_total(receipt_details, False)))
            receipt_details = list()
        else:
            receipt_details.append((description, amount))

    if len(receipts) == 0:
        receipts.append(Receipt(message_date, descriptions, totals))

    return receipts


def replace_with_currency_code(rows: list[str]) -> list[str]:
    def append_iso_currency_code(row: str) -> str:
        split = row.split('£')
        if len(split) > 1:
            return '{} GBP'.format(split[1])
        else:
            return row

    return [append_iso_currency_code(row) for row in rows]


def interesting_row(rows: list[str]) -> bool:
    if len(rows) > 1:
        return any(("Order" in s) or ("Your seller" in s) for s in rows)
    return False
