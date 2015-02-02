import argparse
import mailbox
import os
import tarfile
import tempfile

from qifparse import qif
from qifparse.qif import Qif

from paypal_csv.parser import extract_paypal_transactions_from_csv
from paypal_email.parser import process_email
from string_utils import money_string_to_decimal


def process_mbox(transactions, mbox_path):
    mail_box = mailbox.mbox(mbox_path)
    for key, message in mail_box.items():
        if key == 145:
            continue
        process_email(transactions, message)


def extract_mbox(transactions, tar, mbox_file):
    with tempfile.TemporaryDirectory() as temp_dir:
        tar.extract(mbox_file, temp_dir)
        extracted_mbox = os.path.join(temp_dir, mbox_file.name)
        process_mbox(transactions, extracted_mbox)


def pairs_match(paypal_data, email_data):
    if paypal_data['Transaction Date'].date() == email_data.message_date.date():
        if money_string_to_decimal("%s %s" % (paypal_data['Amount'], paypal_data['Currency']))[0] \
                == -email_data.total[0]:
            return True
    return False


argument_parser = argparse.ArgumentParser()
argument_parser.add_argument("--paypal_csv", "-p", dest="paypal_csv",
                             help="balance affecting transaction csv from paypal")
argument_parser.add_argument("--email_tar", "-e", dest="email_tar", help="(un)compressed tar of the email mbox. \
more than one mbox within the tarball is supported")

args = argument_parser.parse_args()

if args.email_tar is None or args.paypal_csv is None:
    argument_parser.print_usage()
    exit(1)

email_transactions = list()

with tarfile.open(args.email_tar, "r") as tar_file:
    for member in tar_file.getmembers():
        extension = os.path.splitext(member.name)[1][1:].strip().lower()
        if extension == "mbox":
            extract_mbox(email_transactions, tar_file, member)

paypal_transactions = extract_paypal_transactions_from_csv(args.paypal_csv)

qif_result = Qif()
for paypal_transaction in paypal_transactions:
    currency = paypal_transaction['Currency']
    if "GBP" == currency:
        amount = "%s %s" % (paypal_transaction['Amount'], currency)
        qif_transaction = qif.Transaction(date=paypal_transaction['Transaction Date'],
                                          payee=paypal_transaction['Name'],
                                          amount=money_string_to_decimal(amount)[0])

        found = False
        for email_transaction in email_transactions:
            if pairs_match(paypal_transaction, email_transaction):
                found = True
                qif_transaction.memo = email_transaction

        qif_result.add_transaction(qif_transaction, header='!Type:Cash')

print(qif_result)