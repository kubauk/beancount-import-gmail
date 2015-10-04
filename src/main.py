import argparse
import os

from oauth2client import tools
from qifparse import qif
from qifparse.qif import Qif
import gmailmessagessearch.retriever

from paypal_csv.parser import extract_paypal_transactions_from_csv
from paypal_email.parser import extract_transaction
from string_utils import money_string_to_decimal


def pairs_match(paypal_data, email_data):
    if email_data and paypal_data['Transaction Date'].date() == email_data.message_date.date():
        if money_string_to_decimal("%s %s" % (paypal_data['Amount'], paypal_data['Currency']))[0] \
                == -email_data.total[0]:
            return True
    return False


argument_parser = argparse.ArgumentParser(parents=[tools.argparser])
argument_parser.add_argument("--paypal_csv", dest="paypal_csv",
                             help="balance affecting transaction csv from paypal")
argument_parser.add_argument("--email_tar", dest="email_tar", help="(un)compressed tar of the email mbox. \
more than one mbox within the tarball is supported")
argument_parser.add_argument("--email_address", dest="email_address", help="gmail email address")

args = argument_parser.parse_args()

if (args.paypal_csv is None or args.email_tar is None) and \
        (args.email_address is None or args.paypal_csv is None):
    argument_parser.print_usage()
    exit(1)

# email_transactions = list()

# with tarfile.open(args.email_tar, "r") as tar_file:
# for member in tar_file.getmembers():
# extension = os.path.splitext(member.name)[1][1:].strip().lower()
# if extension == "mbox":
#             extract_mbox(email_transactions, tar_file, member)

paypal_transactions = extract_paypal_transactions_from_csv(args.paypal_csv)

retriever = gmailmessagessearch.retriever.Retriever(args, 'PayPal Quickened', args.email_address,
                                                    'from:service@paypal.co.uk',
                                                    os.path.dirname(os.path.realpath(__file__)))
qif_result = Qif()
for paypal_transaction in paypal_transactions:
    currency = paypal_transaction['Currency']
    if "GBP" == currency:
        amount = "%s %s" % (paypal_transaction['Amount'], currency)
        transaction_date = paypal_transaction['Transaction Date']
        qif_transaction = qif.Transaction(date=transaction_date,
                                          payee=paypal_transaction['Name'],
                                          amount=money_string_to_decimal(amount)[0])
        emails = retriever.get_messages_for_date(transaction_date)

        for email in emails:
            if email:
                transactions = extract_transaction(email)
                for transaction in transactions:
                    if pairs_match(paypal_transaction, transaction):
                        qif_transaction.memo = transaction

        qif_result.add_transaction(qif_transaction, header='!Type:Cash')

print(qif_result)