from __future__ import annotations

from datetime import datetime
from typing import Optional

import bs4

from beancount_gmail.common.parsing import extract_row_text
from beancount_gmail.receipt import Receipt, NoReceiptsFoundException


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

    table_text = [extract_row_text(row) for row in beautiful_soup.find_all('tr')]

    order_only = truncate_end_with_product_suggestions(table_text)

    interesting = [row for row in order_only if len([entry for entry in row if '£' in entry]) > 0]
    expected_receipts = len([cell for cell in interesting if 'Order Total:' in cell])

    class PotentialReceipt(object):
        def __init__(self) -> None:
            super().__init__()
            self.descriptions: list[tuple[str, str]] = []
            self.total: Optional[str] = None
            self.postage_and_packaging: Optional[str] = None

        def add_description(self, row) -> PotentialReceipt:
            descriptions = [cell for cell in row if len(cell) > 0]
            self.descriptions.append((descriptions[0], self.amount_string(descriptions[1])))
            return self

        def add_total(self, string) -> PotentialReceipt:
            if self.total is not None:
                other = PotentialReceipt()
                return other.add_total(string)
            else:
                self.total = self.amount_string(string)
                return self

        def add_postage(self, string) -> PotentialReceipt:
            self.postage_and_packaging = self.amount_string(string)
            return self

        def maybe_add_receipt(self, receipt_list) -> None:
            if self.descriptions and self.total:
                receipt_list.append(Receipt(message_date, self.descriptions, total=self.total,
                                            postage_and_packing=self.postage_and_packaging))

        @staticmethod
        def amount_string(string) -> str:
            return "{} GBP".format(string)

    potential_receipt = PotentialReceipt()
    potential_receipts = {potential_receipt}
    for row in interesting:
        if len(row) > 2:
            potential_receipt = potential_receipt.add_description(row)
        elif 'Order Total:' in row:
            potential_receipt = potential_receipt.add_total(row[1])
        elif 'Postage & Packing:' in row:
            potential_receipt = potential_receipt.add_postage(row[1])

        potential_receipts.add(potential_receipt)

    for potential_receipt in potential_receipts:
        potential_receipt.maybe_add_receipt(receipts)

    if not len(receipts):
        raise NoReceiptsFoundException(
            "Found email but could not extract details. {} interesting rows found.".format(len(interesting)))

    if len(receipts) != expected_receipts:
        raise UnexpectedNumberOfReceiptsFoundException(
            "Found {} receipts but expected {}.".format(len(receipts), expected_receipts))

    return receipts


class UnexpectedNumberOfReceiptsFoundException(Exception):
    pass
