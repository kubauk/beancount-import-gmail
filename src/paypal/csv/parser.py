import csv
import datetime


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


def extract_paypal_transactions_from_csv(csv_transaction_file):
    dates = dict()
    with open(csv_transaction_file) as csv_file:
        csv_reader = csv_transaction_file.DictReader(csv_file, dialect="paypal")
        for row in csv_reader:
            transaction_date = datetime.datetime.strptime("%s %s %s" % (row['Date'], row['Time'], row['Time Zone']),
                                                          r"%d/%m/%Y %H:%M:%S %Z")
            print("%s %s" % (transaction_date, row))
            dates[transaction_date] = row
    return dates