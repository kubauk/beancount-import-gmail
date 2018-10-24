import csv
import os
import tempfile
from csv import Sniffer
from datetime import datetime
from decimal import Decimal

import pytz
from beancount_gmail.string_utils import money_string_to_decimal


class PayPalDialect(csv.Dialect):
    delimiter = ','
    doublequote = False
    escapechar = None
    quotechar = '"'
    quoting = csv.QUOTE_MINIMAL
    lineterminator = "\n"
    skipinitialspace = True
    strict = True


csv.register_dialect("paypal", PayPalDialect)


def amount_is_negative(x):
    amount_string = "%s %s" % (x['amount'], x['currency'])
    return money_string_to_decimal(amount_string)[0] < Decimal("0")


def foreign_amount_is_negative(x):
    return foreign_currency(x) and amount_is_negative(x)


def foreign_currency(x):
    return "GBP" not in x['currency']


def squash_foreign_currency_transactions(foreign_currency_dates, dates):
    for date in foreign_currency_dates:
        transaction_list = dates[date]

        foreign_transaction = [x for x in transaction_list if foreign_amount_is_negative(x)]
        if len(foreign_transaction) != 1:
            raise Exception("Only expected one foreign transaction to be found")

        actual_transaction = [x for x in transaction_list if not foreign_currency(x) and amount_is_negative(x)]
        if len(actual_transaction) != 1:
            raise Exception("Only expected one GBP transaction to be found")
        actual_transaction[0]['name'] = foreign_transaction[0]['name']

        squashed_transactions = [x for x in transaction_list if not foreign_currency(x)]

        dates[date] = squashed_transactions


def time_zone_is_british(row):
    return "GMT" in row['time zone'] or "BST" in row['time zone']


def extract_paypal_transactions_from_csv(csv_file_memo):
    dates = dict()

    foreign_currency_dates = set()

    dialect = Sniffer().sniff(csv_file_memo.head())
    for row in LowerCaseFieldDictReader(csv_file_memo.contents().splitlines(), dialect=dialect):
        europe_london_tz = pytz.timezone('Europe/London')
        if not time_zone_is_british(row):
            raise Exception("Did not expect %s as time zone. Only expecting GMT and BST" % row['time zone'])

        naive_date = datetime.strptime("%s %s" % (row['date'], row['time']), r"%d/%m/%Y %H:%M:%S")
        local_date = europe_london_tz.localize(naive_date)
        transaction_date = pytz.utc.normalize(local_date.astimezone(pytz.utc))
        row['transaction date'] = transaction_date

        if foreign_currency(row):
            foreign_currency_dates.add(transaction_date)

        transactions_for_date = dates.get(transaction_date, list())
        transactions_for_date.append(row)
        dates[transaction_date] = transactions_for_date

    squash_foreign_currency_transactions(foreign_currency_dates, dates)

    return [x for y in dates.keys() for x in dates[y]]


class LowerCaseFieldDictReader(csv.DictReader):
    @property
    def fieldnames(self):
        return [field.lower() for field in super(LowerCaseFieldDictReader, self).fieldnames]
