import os

from beancount.ingest.importer import ImporterProtocol

from beancount_gmail.csv_parser import extract_paypal_transactions_from_csv


class Importer(ImporterProtocol):
    def extract(self, file, existing_entries=None):
        paypal_transactions = extract_paypal_transactions_from_csv(file)
        for p in paypal_transactions:
            print(p)

    def identify(self, file):
        return "paypal" in os.path.abspath(file.name)

    def file_account(self, file):
        return "Assets:PayPal"
