import os

import gmailmessagessearch.retriever
from beancount.core import data
from beancount.ingest.importer import ImporterProtocol

from beancount_gmail.csv_parser import extract_paypal_transactions_from_csv
from beancount_gmail.email_parser import extract_transaction
from beancount_gmail.string_utils import money_string_to_decimal


def pairs_match(paypal_data, email_data):
    if email_data and paypal_data['transaction date'].date() == email_data.message_date.date():
        if money_string_to_decimal("%s %s" % (paypal_data['amount'], paypal_data['currency'])) \
                == -email_data.total:
            return True
    return False


class GmailImporter(ImporterProtocol):
    def __init__(self, postage_account, gmail_address, secrets_directory=os.path.dirname(os.path.realpath(__file__))):
        self._postage_account = postage_account
        self._gmail_address = gmail_address
        self._secrets_directory = secrets_directory

    def extract(self, file, existing_entries=None):
        paypal_transactions = extract_paypal_transactions_from_csv(file)

        retriever = gmailmessagessearch.retriever.Retriever('beancount-import-gmail-paypal', self._gmail_address,
                                                            'from:service@paypal.co.uk', self._secrets_directory)

        dates = [transaction['transaction date'] for transaction in paypal_transactions]

        messages = retriever.get_messages_for_date_range(min(dates), max(dates))

        transactions = list()

        for paypal_transaction in paypal_transactions:
            currency = paypal_transaction['currency']
            if "GBP" == currency:
                metadata = data.new_metadata(file.name, 0)
                for email in messages:
                    for email_transaction in extract_transaction(email):
                        if pairs_match(paypal_transaction, email_transaction):
                            transactions.append(email_transaction.
                                                as_beancount_transaction(metadata,
                                                                         paypal_transaction['name'],
                                                                         paypal_transaction['type'],
                                                                         self._postage_account,
                                                                         self.file_account(file)))

        return transactions

    def identify(self, file):
        return "paypal" in os.path.abspath(file.name)

    def file_account(self, file):
        return "Assets:PayPal"
