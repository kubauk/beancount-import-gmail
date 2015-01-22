import datetime
import html
import html.parser
import html.entities
import mailbox
import os
import tarfile
import tempfile

import bs4

from src.paypal.csv.parser import extract_paypal_transactions_from_csv


CUT_OFF_DATE = datetime.datetime(2009, 1, 1, tzinfo=datetime.timezone.utc)

EXCLUDED_EMAILS_DIR = "./excluded"


class Transaction(object):
    def __init__(self, message_date, sub_transactions):
        self.message_date = message_date
        self.sub_transactions = sub_transactions

    def __str__(self):
        transactions_string = ""
        for description, amount in self.sub_transactions:
            transactions_string += "%s | %s | %s\n" % (self.message_date, description, amount)
        return transactions_string


class HtmlTable(object):
    def __init__(self, message_date):
        super().__init__()
        self._data = list()
        self._message_date = message_date
        self._transaction = None

    def starttag(self, tag):
        if "tr" == tag:
            self._data.append(list())

        if "td" == tag:
            row = self._data[len(self._data) - 1]
            row.append(list())

    def endtag(self, tag):
        pass

    def data(self, data):
        if len(self._data) > 0:
            row = self._data[len(self._data) - 1]
            if len(row) > 0:
                column = row[len(row) - 1]
                column.append(data)

    def has_transaction_details(self):
        data = self.get_data_for_row(0)
        if not data or "Description" != data[0]:
            return False

        other_data = self.get_other_data()
        self._transaction = Transaction(self._message_date, other_data)
        print(self._transaction)
        return True

    def get_transaction(self):
        return self._transaction

    def get_data_for_row(self, index):
        if len(self._data) <= index:
            return None

        row = self._data[index]
        description = None
        if len(row) > 0:
            if len(row[0]) > 0:
                description = " ".join(row[0]).strip()
        if len(row) > 1:
            column = row[len(row) - 1]
            if len(column) > 0:
                amount = column[0].strip()
                return description, amount

        return None

    def get_other_data(self):
        data = list()
        index = 1
        row = self.get_data_for_row(index)
        while row:
            data.append(row)
            index += 1
            row = self.get_data_for_row(index)

        return data


class NonTable(object):
    def starttag(self, tag):
        pass

    def endtag(self, tag):
        pass

    def data(self, data):
        pass


class NoTransactionFoundException(Exception):
    pass


class PayPalHtmlParser(html.parser.HTMLParser):
    def __init__(self, message_date):
        super().__init__()
        self._current = list()
        self._current.append(NonTable())
        self._message_date = message_date
        self._transaction = None

    def handle_starttag(self, tag, attributes):
        if "table" == tag:
            self._current.append(HtmlTable(self._message_date))
        else:
            current = self._current[len(self._current) - 1]
            current.starttag(tag)

    def handle_endtag(self, tag):
        if "table" == tag:
            table = self._current.pop()
            if table.has_transaction_details():
                self._transaction = table.get_transaction()
            pass
        else:
            current = self._current[len(self._current) - 1]
            current.endtag(tag)

    def handle_data(self, data):
        current = self._current[len(self._current) - 1]
        current.data(data)

    def handle_entityref(self, name):
        current = self._current[len(self._current) - 1]
        current.data(html.entities.entitydefs[name])

    def get_transaction(self):
        if not self._transaction:
            raise NoTransactionFoundException()

        return self._transaction


_transactions = dict()


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
    if len(tables) % 2 != 0:
        raise ParseException("Failed to find correct number of transaction tables, i.e. 2 per transaction")
    return tables


def next_sibling_tag(first):
    sibling = first.next_sibling
    while type(sibling) is not bs4.Tag and sibling is not None:
        sibling = sibling.next_sibling
    return sibling


def extract_sub_transactions_from_table(table):
    sub_transactions = list()

    row = next_sibling_tag(table.tr)
    while row is not None:
        columns = row.find_all('td')
        description = columns[0].get_text().strip()
        total = columns[len(columns) - 1].get_text()

        sub_transactions.append((description, total))
        row = next_sibling_tag(row)

    return sub_transactions


def extract_transaction_from_html(message_date, message_body):
    soup = bs4.BeautifulSoup(message_body)

    transactions = list()

    tables = find_transaction_tables(soup)
    while len(tables) > 0:
        sub_transactions = extract_sub_transactions_from_table(tables.pop(0))
        totals = tables.pop(0)

        transactions.append(Transaction(message_date, None))

    parser = PayPalHtmlParser(message_date)
    parser.feed(message_body)
    try:
        transaction = parser.get_transaction()
        _transactions[transaction.message_date] = transaction
    except NoTransactionFoundException:
        raise NoTransactionFoundException


class NoCharsetException(Exception):
    pass


def get_charset(message):
    if message.get_charset():
        return message.get_charset()

    if 'Content-Type' in message:
        return message.get('Content-Type').split("charset=")[1]

    raise NoCharsetException()


def process_message_text(message_date, message):
    if message.get_content_type() == "text/html":
        extract_transaction_from_html(message_date, message.get_payload(decode=True).decode(get_charset(message)))
    elif message.get_content_type == "text/plain:":
        extract_transaction_from_html(message_date, message)


def process_message_payload(message, message_date):
    if message.is_multipart():
        for part in message.get_payload():
            process_message_text(message_date, part)
    else:
        process_message_text(message_date, message)


def write_email_to_file(message_date, message):
    if not os.path.exists(EXCLUDED_EMAILS_DIR):
        os.mkdir(EXCLUDED_EMAILS_DIR)

    file = os.path.join(EXCLUDED_EMAILS_DIR, "%s.eml" % message_date)
    with open(file, "w") as out:
        out.write(message.as_string())


def process_message(message):
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

    process_message_payload(message, message_date)


def process_mbox(mbox_path):
    mail_box = mailbox.mbox(mbox_path)
    for key, message in mail_box.items():
        if key == 145:
            continue
        print(key)
        process_message(message)


def extract_mbox(tar, mbox_file):
    with tempfile.TemporaryDirectory() as temp_dir:
        tar.extract(mbox_file, temp_dir)
        extracted_mbox = os.path.join(temp_dir, mbox_file.name)
        process_mbox(extracted_mbox)


with tarfile.open("paypal.tbz", "r") as tar_file:
    for member in tar_file.getmembers():
        extension = os.path.splitext(member.name)[1][1:].strip().lower()
        if "mbox" == extension:
            extract_mbox(tar_file, member)

dates = extract_paypal_transactions_from_csv("test.csv")

for date in dates.keys():
    found = False
    for transaction_date in _transactions.keys():
        if date.date() == transaction_date.date():
            print(dates[date])
            print(_transactions[transaction_date])
            found = True
    if not found:
        print("nothing found for ", date)
        print(dates[date])