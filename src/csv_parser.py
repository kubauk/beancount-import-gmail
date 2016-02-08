import csv
from datetime import datetime
from decimal import Decimal

import pytz
from string_utils import money_string_to_decimal


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
    amount_string = "%s %s" % (x['Amount'], x['Currency'])
    return money_string_to_decimal(amount_string)[0] < Decimal("0")


def foreign_amount_is_negative(x):
    return foreign_currency(x) and amount_is_negative(x)


def foreign_currency(x):
    return "GBP" not in x['Currency']


def squash_foreign_currency_transactions(foreign_currency_dates, dates):
    for date in foreign_currency_dates:
        transaction_list = dates[date]

        foreign_transaction = [x for x in transaction_list if foreign_amount_is_negative(x)]
        if len(foreign_transaction) != 1:
            raise Exception("Only expected one foreign transaction to be found")

        actual_transaction = [x for x in transaction_list if not foreign_currency(x) and amount_is_negative(x)]
        if len(actual_transaction) != 1:
            raise Exception("Only expected one GBP transaction to be found")
        actual_transaction[0]['Name'] = foreign_transaction[0]['Name']

        squashed_transactions = [x for x in transaction_list if not foreign_currency(x)]

        dates[date] = squashed_transactions


def time_zone_is_british(row):
    return "GMT" in row['Time Zone'] or "BST" in row['Time Zone']


def extract_paypal_transactions_from_csv(csv_transaction_file):
    dates = dict()
    with open(csv_transaction_file) as csv_file:
        csv_reader = csv.DictReader(csv_file, dialect="paypal")

        foreign_currency_dates = set()

        for row in csv_reader:
            europe_london_tz = pytz.timezone('Europe/London')
            if not time_zone_is_british(row):
                raise Exception("Did not expect %s as time zone. Only expecting GMT and BST" % row['Time Zone'])

            naive_date = datetime.strptime("%s %s" % (row['Date'], row['Time']), r"%d/%m/%Y %H:%M:%S")
            local_date = europe_london_tz.localize(naive_date)
            transaction_date = pytz.utc.normalize(local_date.astimezone(pytz.utc))
            row['Transaction Date'] = transaction_date

            if "GBP" not in row['Currency']:
                foreign_currency_dates.add(transaction_date)

            transactions_for_date = dates.get(transaction_date, list())
            transactions_for_date.append(row)
            dates[transaction_date] = transactions_for_date

    squash_foreign_currency_transactions(foreign_currency_dates, dates)

    return [x for y in dates.keys() for x in dates[y]]