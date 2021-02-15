import re

from beancount.core import data
from beancount.core.amount import add, Amount
from beancount.core.number import ZERO

from beancount_gmail.string_utils import money_string_to_amount

ZERO_GBP = Amount(ZERO, "GBP")

POSTAGE_AND_PACKAGING = "Postage and Packaging"
DESCRIPTION = "Description"
UNIT_PRICE = "Unit Price"
QUANTITY = "Quantity"
AMOUNT = "Amount"
SUB_TOTAL = "Subtotal"
TOTAL = "Total"

POSTAGE_AND_PACKAGING_RE = re.compile("Postage and packaging(?! .)")


def match_field_lambda(field):
    return lambda t: field if field in t else None


RECEIPT_DETAILS = [
    (POSTAGE_AND_PACKAGING, lambda t: POSTAGE_AND_PACKAGING_RE.match(t)),
    (DESCRIPTION, match_field_lambda(DESCRIPTION)),
    (SUB_TOTAL, match_field_lambda(SUB_TOTAL)),
    (TOTAL, match_field_lambda(TOTAL))
]


def contain_interesting_receipt_fields(text):
    for detail in RECEIPT_DETAILS:
        if detail[1](text) is not None:
            return True
    return False


def _strip_newlines(description):
    return description.replace('\n', ' ')


def _escape_double_quotes(description):
    return description.replace('"', '\\"')


def _sanitise_description(description):
    return _escape_double_quotes(_strip_newlines(description))


def _posting(account, amount):
    return data.Posting(account, amount, None, None, None, dict())


def _with_meta(amount, description):
    posting = _posting("ReplaceWithAccount", amount)
    posting.meta['description'] = _sanitise_description(description)
    return posting


class Receipt(object):
    def __init__(self, message_date, receipt_details, totals, negate):
        self.total = None
        self.postage_and_packing = None
        self.message_date = message_date
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

    def _receipt_details_postings(self):
        return [_with_meta(amount, description) for description, amount in
                self.receipt_details]

    def _postage_and_packing_posting(self, postage_account):
        return _posting(postage_account, self.postage_and_packing)

    @staticmethod
    def _currencies_match(sub_total, receipt_details_total):
        return sub_total.currency == receipt_details_total.currency

    @staticmethod
    def _amount_is_zero(sub_total):
        return sub_total is ZERO_GBP

    def append_postings(self, transaction, postage_account):
        transaction.postings.extend(self._receipt_details_postings())
        if self.postage_and_packing != ZERO_GBP:
            transaction.postings.append(self._postage_and_packing_posting(postage_account))
        return transaction


class NoReceiptsFoundException(Exception):
    pass
