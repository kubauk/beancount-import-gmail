import re
from datetime import datetime
from typing import Any, Optional

from beancount.core import data
from beancount.core.amount import add, Amount
from beancount.core.number import ZERO

ZERO_GBP = Amount(ZERO, "GBP")

POSTAGE_AND_PACKAGING = "Postage and Packaging"
DESCRIPTION = "Description"
UNIT_PRICE = "Unit Price"
QUANTITY = "Quantity"
AMOUNT = "Amount"
SUB_TOTAL = "Subtotal"
TOTAL = "Total"

POSTAGE_AND_PACKAGING_RE = re.compile("Postage and packaging(?! .)")


def field_value_or_none(field: Any) -> Optional[Any]:
    return lambda t: field if field in t else None


RECEIPT_DETAILS = [
    (POSTAGE_AND_PACKAGING, lambda t: POSTAGE_AND_PACKAGING_RE.match(t)),
    (DESCRIPTION, field_value_or_none(DESCRIPTION)),
    (SUB_TOTAL, field_value_or_none(SUB_TOTAL)),
    (TOTAL, field_value_or_none(TOTAL))
]


def money_string_to_amount(money_string: str, negate: bool) -> Amount:
    amount = Amount.from_string(re.match(r"([^-+0-9]+)?(.*)", money_string).group(2))
    if negate:
        amount = -amount
    return amount


def contain_interesting_receipt_fields(text: str) -> bool:
    for detail in RECEIPT_DETAILS:
        if detail[1](text) is not None:
            return True
    return False


def _strip_newlines(description: str) -> str:
    return description.replace('\n', ' ')


def _escape_double_quotes(description: str) -> str:
    return description.replace('"', '\\"')


def _sanitise_description(description: str) -> str:
    return _escape_double_quotes(_strip_newlines(description))


def _posting(account: str, amount: Amount) -> data.Posting:
    return data.Posting(account, amount, None, None, None, dict())


def _with_meta(amount: Amount, description: str) -> data.Posting:
    posting = _posting("ReplaceWithAccount", amount)
    posting.meta['description'] = _sanitise_description(description)
    return posting


class Receipt(object):
    def __init__(self, receipt_date: datetime, receipt_details: list[tuple[str, str]],
                 totals: list[tuple[str, str]], negate: bool) -> None:
        self.total = None
        self.postage_and_packing = None
        self.receipt_date = receipt_date
        self.receipt_details = list()

        self.sub_total = ZERO_GBP
        for description, amount in receipt_details:
            receipt_detail_amount = money_string_to_amount(amount, negate)
            self.receipt_details.append((description, receipt_detail_amount))
            if not self._currencies_match(self.sub_total, receipt_detail_amount) \
                    and self._amount_is_zero(self.sub_total):
                self.sub_total = receipt_detail_amount
            else:
                self.sub_total = add(self.sub_total, receipt_detail_amount)

        for description, amount_string in totals:
            if description.startswith("From amount") or "Total" in description or "Subtotal" in description:
                self.total = money_string_to_amount(amount_string, negate)
            if POSTAGE_AND_PACKAGING_RE.match(description):
                self.postage_and_packing = money_string_to_amount(amount_string, negate)

        if self.total is None:
            raise Exception("Failed to find total in receipt")

        if self.postage_and_packing is None:
            self.postage_and_packing = Amount(ZERO, self.total.currency)

    def _receipt_details_postings(self) -> list[data.Posting]:
        return [_with_meta(amount, description) for description, amount in
                self.receipt_details]

    def _postage_and_packing_posting(self, postage_account: str) -> data.Posting:
        return _posting(postage_account, self.postage_and_packing)

    @staticmethod
    def _currencies_match(sub_total: Amount, receipt_details_total: Amount) -> bool:
        return sub_total.currency == receipt_details_total.currency

    @staticmethod
    def _amount_is_zero(sub_total: Amount) -> bool:
        return sub_total is ZERO_GBP

    def append_postings(self, transaction: data.Transaction, postage_account: str):
        transaction.postings.extend(self._receipt_details_postings())
        if self.postage_and_packing != ZERO_GBP:
            transaction.postings.append(self._postage_and_packing_posting(postage_account))
        return transaction


class NoReceiptsFoundException(Exception):
    pass
