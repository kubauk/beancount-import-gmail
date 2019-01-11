from decimal import Decimal

from beancount.core import data, flags
from beancount.core.amount import Amount
from money import Money

from beancount_gmail.string_utils import money_string_to_decimal

ZERO_GBP = Money(Decimal("0.00"), "GBP")


def _strip_newlines(description):
    return description.replace('\n', ' ')


class Transaction(object):
    total = None
    postage_and_packing = ZERO_GBP

    def __init__(self, message_date, sub_transactions, totals, refund):
        self.message_date = message_date
        self.sub_transactions = list()

        self.sub_total = ZERO_GBP
        for description, amount in sub_transactions:
            sub_transaction_total = money_string_to_decimal(amount, refund)
            self.sub_transactions.append((description, sub_transaction_total))
            if not self._currencies_match(self.sub_total, sub_transaction_total) \
                    and self._amount_is_zero(self.sub_total):
                self.sub_total = sub_transaction_total
            else:
                self.sub_total += sub_transaction_total

        for description, amount_string in totals:
            if description.startswith("From amount") or "Total" in description or "Subtotal" in description:
                amount = money_string_to_decimal(amount_string, refund)
                if "GBP" in amount.currency:
                    self.total = amount
            if description.startswith("Postage and pack"):
                self.postage_and_packing = money_string_to_decimal(amount_string, refund)

        if self.total is None:
            raise Exception("Failed to find GBP total in transactions")

    def sub_transaction_postings(self):
        return [self._with_meta(amount, description) for description, amount in
                self.sub_transactions]

    def _with_meta(self, amount, description):
        posting = self._posting("ReplaceWithAccount", amount)
        posting.meta['description'] = _strip_newlines(description)
        return posting

    def postage_and_packing_posting(self, postage_account):
        return self._posting(postage_account, self.postage_and_packing)

    def total_posting(self, total_account):
        return self._posting(total_account, -self.total)

    @staticmethod
    def _posting(account, money):
        return data.Posting(account,
                            Amount(money.amount, money.currency),
                            None, None, None, dict())

    @staticmethod
    def _currencies_match(sub_total, sub_transaction_total):
        return sub_total.currency == sub_transaction_total.currency

    @staticmethod
    def _amount_is_zero(sub_total):
        return sub_total is ZERO_GBP

    def as_beancount_transaction(self, metadata, payee, narration, postage_account, total_account):
        data_transaction = data.Transaction(meta=metadata, date=self.message_date.date(),
                                            flag=flags.FLAG_OKAY,
                                            payee=payee,
                                            narration=narration,
                                            tags=set(),
                                            links=set(),
                                            postings=list())
        data_transaction.postings.extend(self.sub_transaction_postings())
        if self.postage_and_packing != ZERO_GBP:
            data_transaction.postings.append(self.postage_and_packing_posting(postage_account))
        data_transaction.postings.append(self.total_posting(total_account))
        return data_transaction
