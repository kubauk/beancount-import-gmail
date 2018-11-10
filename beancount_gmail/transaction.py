from decimal import Decimal

from beancount.core import data
from beancount.core.amount import Amount
from money import Money
from string_utils import money_string_to_decimal

ZERO_GBP = Money(Decimal("0.00"), "GBP")


class Transaction(object):
    total = None

    def __init__(self, message_date, sub_transactions, totals, refund):
        self.message_date = message_date
        self.sub_transactions = sub_transactions

        self.sub_total = ZERO_GBP
        for description, amount in self.sub_transactions:
            sub_transaction_total = money_string_to_decimal(amount, refund)
            if not self._currencies_match(self.sub_total, sub_transaction_total) \
                    and self._amount_is_zero(self.sub_total):
                self.sub_total = sub_transaction_total
            else:
                self.sub_total += sub_transaction_total

        self.postage_and_packing = ZERO_GBP
        for description, amount_string in totals:
            if description.startswith("From amount") or "Total" in description or "Subtotal" in description:
                amount = money_string_to_decimal(amount_string, refund)
                if "GBP" in amount.currency:
                    self.total = amount
            if description.startswith("Postage and pack"):
                self.postage_and_packing = money_string_to_decimal(amount_string, refund)

        if self.total is None:
            raise Exception("Failed to find GBP total in transactions")

    def __str__(self):
        transactions_string = "%s" % self.message_date
        for description, amount in self.sub_transactions:
            transactions_string += " | %s %s" % (description, amount)

        transactions_string += " | Subtotal %s  Postage %s  Total %s" % \
                               (self.sub_total, self.postage_and_packing, self.total)
        return transactions_string

    def postage_and_packing_posting(self, postage_account):
        return data.Posting(postage_account,
                            Amount(self.postage_and_packing.amount, self.postage_and_packing.currency),
                            None, None, None, dict())

    @staticmethod
    def _currencies_match(sub_total, sub_transaction_total):
        return sub_total.currency == sub_transaction_total.currency

    @staticmethod
    def _amount_is_zero(sub_total):
        return sub_total is ZERO_GBP
