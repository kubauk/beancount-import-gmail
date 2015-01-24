import mailbox
import os
import tarfile
import tempfile

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


transactions = list()

with tarfile.open("paypal.tbz", "r") as tar_file:
    for member in tar_file.getmembers():
        extension = os.path.splitext(member.name)[1][1:].strip().lower()
        if extension == "mbox":
            extract_mbox(transactions, tar_file, member)

dates = extract_paypal_transactions_from_csv("test.csv")

total_found = 0
total_not_found = 0

def pairs_match(paypal_transaction, email_transaction):
    if paypal_transaction['Transaction Date'].date() == email_transaction.message_date.date():
        if money_string_to_decimal(paypal_transaction['Amount']) == -email_transaction.total:
            return True
    return False

for paypal_transaction in dates:
    found = False
    for email_transaction in transactions:
        if pairs_match(paypal_transaction, email_transaction):
            found = True
            total_found += 1

    if not found:
        total_not_found += 1

print("found %s, did not find %s" % (total_found, total_not_found))