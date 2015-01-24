import datetime
from decimal import Decimal
import mailbox
import os
import re
import tarfile
import tempfile
import bs4

from src.paypal.csv.parser import extract_paypal_transactions_from_csv


CUT_OFF_DATE = datetime.datetime(2009, 1, 1, tzinfo=datetime.timezone.utc)

EXCLUDED_EMAILS_DIR = "./excluded"

MONEY = re.compile("-?\d{1,3}(?:,\d{3})*\.\d{2}")


def money_string_to_decimal(string):
    match = MONEY.search(string)
    if not match:
        raise Exception("No money value found in string \"%s\" to convert to decimal" % string)
    return Decimal(match.group(0))


class Transaction(object):
    def __init__(self, message_date, sub_transactions, totals):
        self.message_date = message_date
        self.sub_transactions = sub_transactions

        self.sub_total = Decimal("0.00")
        for description, amount in self.sub_transactions:
            sub_transaction_total = money_string_to_decimal(amount)
            self.sub_total += sub_transaction_total

        self.postage_and_packing = Decimal("0.00")
        for description, amount in totals:
            if description == "Total":
                self.total = money_string_to_decimal(amount)
            if description.startswith("Postage and pack"):
                self.postage_and_packing = money_string_to_decimal(amount)

    def __str__(self):
        transactions_string = "%s\n" % self.message_date
        for description, amount in self.sub_transactions:
            transactions_string += "%s | %s\n" % (description, amount)
        transactions_string += "Subtotal %s  Postage %s  Total %s" % (self.sub_total, self.postage_and_packing, self.total)
        return transactions_string


class NoTransactionFoundException(Exception):
    pass


class ParseException(Exception):
    pass


def find_transaction_tables(soup):
    tables = list()
    for table in soup.find_all("table"):
        first_td_text = table.tr.td.get_text().strip()
        if first_td_text == "Description":
            tables.append(table)
        elif first_td_text.startswith("Postage and pack") or first_td_text == "Subtotal":
            tables.append(table)
    if len(tables) == 0:
        raise NoTransactionFoundException("Did not find any transactions")
    if len(tables) % 2 != 0:
        raise ParseException("Failed to find correct number of transaction tables, i.e. 2 per transaction")
    return tables


def next_sibling_tag(first):
    sibling = first.next_sibling
    while type(sibling) is not bs4.Tag and sibling is not None:
        sibling = sibling.next_sibling
    return sibling


def extract_sub_transactions_from_table(table, skip_header=False):
    sub_transactions = list()

    row = next_sibling_tag(table.tr) if skip_header else table.tr
    while row is not None:
        columns = row.find_all('td')
        description = columns[0].get_text().strip()
        total = columns[len(columns) - 1].get_text()

        sub_transactions.append((description, total))
        row = next_sibling_tag(row)

    return sub_transactions


def extract_transactions_from_html(transactions, message_date, message_body):
    soup = bs4.BeautifulSoup(message_body)

    tables = find_transaction_tables(soup)
    while len(tables) > 0:
        sub_transactions = extract_sub_transactions_from_table(tables.pop(0), skip_header=True)
        totals = extract_sub_transactions_from_table(tables.pop(0))
        transactions.append(Transaction(message_date, sub_transactions, totals))


class NoCharsetException(Exception):
    pass


def get_charset(message):
    if message.get_charset():
        return message.get_charset()

    if 'Content-Type' in message:
        return message.get('Content-Type').split("charset=")[1]

    raise NoCharsetException()


def process_message_text(transactions, message_date, message):
    if message.get_content_type() == "text/html":
        extract_transactions_from_html(transactions, message_date,
                                       message.get_payload(decode=True).decode(get_charset(message)))
    elif message.get_content_type == "text/plain:":
        extract_transactions_from_html(transactions, message_date, message)


def process_message_payload(transactions, message, message_date):
    if message.is_multipart():
        for part in message.get_payload():
            process_message_text(transactions, message_date, part)
    else:
        process_message_text(transactions, message_date, message)


def write_email_to_file(message_date, message):
    if not os.path.exists(EXCLUDED_EMAILS_DIR):
        os.mkdir(EXCLUDED_EMAILS_DIR)

    file = os.path.join(EXCLUDED_EMAILS_DIR, "%s.eml" % message_date)
    with open(file, "w") as out:
        out.write(message.as_string())


def process_message(transactions, message):
    message_date = datetime.datetime.strptime(message.get("Date"), "%a, %d %b %Y %H:%M:%S %z")

    gmail_labels = message.get('X-Gmail-Labels').split(',')
    if not 'paypal receipt' in gmail_labels:
        print("Skipping as not a receipt, %s, labels: %s, from: %s" % (message_date, gmail_labels, message.get('From')))
        write_email_to_file(message_date, message)
        return

    if message_date < CUT_OFF_DATE:
        print("Skipping message as before 2013, %s, from: %s" % (message_date, message.get('From')))
        write_email_to_file(message_date, message)
        return

    process_message_payload(transactions, message, message_date)


def process_mbox(transactions, mbox_path):
    mail_box = mailbox.mbox(mbox_path)
    for key, message in mail_box.items():
        if key == 145:
            continue
        process_message(transactions, message)


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

print()
print()

dates = extract_paypal_transactions_from_csv("test.csv")

print()
print()

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
        print("-> nothing found for ", paypal_transaction)
        total_not_found += 1

print("found %s, did not find %s" % (total_found, total_not_found))