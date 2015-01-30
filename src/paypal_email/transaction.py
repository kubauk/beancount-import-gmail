from decimal import Decimal
from string_utils import money_string_to_decimal


class Transaction(object):
    def __init__(self, message_date, sub_transactions, totals):
        self.message_date = message_date
        self.sub_transactions = sub_transactions

        self.sub_total = Decimal("0.00")
        for description, amount in self.sub_transactions:
            sub_transaction_total = money_string_to_decimal(amount)
            self.sub_total += sub_transaction_total

        self.postage_and_packing = Decimal("0.00")
        for description, amount in totals:
            if description == "Total":
                self.total = money_string_to_decimal(amount)
            if description.startswith("Postage and pack"):
                self.postage_and_packing = money_string_to_decimal(amount)

    def __str__(self):
        transactions_string = "%s" % self.message_date
        for description, amount in self.sub_transactions:
            transactions_string += " | %s %s" % (description, amount)
        transactions_string += " | Subtotal %s  Postage %s  Total %s" % \
                               (self.sub_total, self.postage_and_packing, self.total)
        return transactions_string