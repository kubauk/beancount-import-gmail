import csv
from datetime import datetime

import pytz


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
    dates = list()
    with open(csv_transaction_file) as csv_file:
        csv_reader = csv.DictReader(csv_file, dialect="paypal")
        for row in csv_reader:
            europe_london_tz = pytz.timezone('Europe/London')
            row_time_zone = row['Time Zone']
            if not "GMT" in row_time_zone and not "BST" in row_time_zone:
                raise Exception("Did not expect %s as time zone. Only expecting GMT and BST" % row_time_zone)
            naive_date = datetime.strptime("%s %s" % (row['Date'], row['Time']), r"%d/%m/%Y %H:%M:%S")
            local_date = europe_london_tz.localize(naive_date)
            transaction_date = pytz.utc.normalize(local_date.astimezone(pytz.utc))
            row['Transaction Date'] = transaction_date
            dates.append(row)
    return dates