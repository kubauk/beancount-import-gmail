import os

import gmailmessagessearch.retriever
from beancount.core import data
from beancount.ingest.importer import ImporterProtocol

import email_parser
from beancount_gmail.csv_parser import extract_paypal_transactions_from_csv
from string_utils import money_string_to_decimal


def pairs_match(paypal_data, email_data):
    if email_data and paypal_data['transaction date'].date() == email_data.message_date.date():
        if money_string_to_decimal("%s %s" % (paypal_data['amount'], paypal_data['currency'])) \
                == -email_data.total:
            return True
    return False


class GmailImporter(ImporterProtocol):
    def extract(self, file, existing_entries=None):
        paypal_transactions = extract_paypal_transactions_from_csv(file)

        retriever = gmailmessagessearch.retriever.Retriever(None, 'PayPal Quickened', 'kuba.jamro@gmail.com',
                                                            'from:service@paypal.co.uk',
                                                            os.path.dirname(os.path.realpath(__file__)))

        transactions = list()

        for paypal_transaction in paypal_transactions:
            currency = paypal_transaction['currency']
            if "GBP" == currency:
                transaction_date = paypal_transaction['transaction date']
                metadata = data.new_metadata(file.name, 0)
                for email in retriever.get_messages_for_date(transaction_date):
                    if email:
                        for transaction in email_parser.extract_transaction(email):
                            if pairs_match(paypal_transaction, transaction):
                                metadata['Transaction Details'] = transaction.__str__()
                                data_transaction = data.Transaction(meta=metadata, date=transaction_date,
                                                                    flag=self.FLAG,
                                                                    payee=paypal_transaction['name'],
                                                                    narration=paypal_transaction['type'], tags=set(),
                                                                    links=set(),
                                                                    postings=list())
                                data.create_simple_posting(data_transaction, self.file_account(file),
                                                           transaction.total.amount, transaction.total.currency)
                                transactions.append(data_transaction)

        return transactions

    def identify(self, file):
        return "paypal" in os.path.abspath(file.name)

    def file_account(self, file):
        return "Assets:PayPal"
