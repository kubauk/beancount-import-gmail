import datetime
from html import entities
from html.parser import HTMLParser
import os
import tarfile
import tempfile
from mailbox import mbox


class Transaction(object):
    def __init__(self, date, sub_transactions):
        self.date = date
        self.sub_transactions = sub_transactions

    def __str__(self):
        transactions_string = ""
        for description, amount in self.sub_transactions:
            transactions_string += "%s | %s | %s\n" % (self.date, description, amount)
        return transactions_string


class HtmlTable:
    def __init__(self, date):
        super().__init__()
        self._data = list()
        self._date = date
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
        self._transaction = Transaction(self._date, other_data)
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


class NonTable:
    def starttag(self, tag):
        pass

    def endtag(self, tag):
        pass

    def data(self, data):
        pass


class NoTransactionFoundException(Exception):
    pass


class Parser(HTMLParser):
    def __init__(self, date):
        super().__init__()
        self._current = list()
        self._current.append(NonTable())
        self._date = date
        self._transaction = None

    def handle_starttag(self, tag, attributes):
        if "table" == tag:
            self._current.append(HtmlTable(self._date))
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
        current.data(entities.entitydefs[name])

    def get_transaction(self):
        if not self._transaction:
            raise NoTransactionFoundException()

        return self._transaction


_transactions = list()


def process_email(date, charset, payload):
    html = str(payload.decode(charset))
    parser = Parser(date)
    parser.feed(html)
    _transactions.append(parser.get_transaction())


def parse_date(date_string):
    return datetime.datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %z")


class NoCharsetException(Exception):
    pass


def get_charset(message):
    if message.get_charset():
        return message.get_charset()

    if 'Content-Type' in message:
        return message.get('Content-Type').split("charset=")[1]

    raise NoCharsetException()


def process_message(message):
    gmail_labels = message.get('X-Gmail-Labels').split(',')
    if not 'paypal receipt' in gmail_labels:
        print("Not a receipt")
        return

    date = parse_date(message.get("Date"))
    if message.is_multipart():
        for part in message.get_payload():
            if part.get_content_type() == "text/html":
                process_email(date, get_charset(part), part.get_payload(decode=True))
    else:
        process_email(date, get_charset(message), message.get_payload(decode=True))


def process_mbox(mbox_path):
    mailbox = mbox(mbox_path)
    for key, message in mailbox.items():
        print(key)
        process_message(message)

        # for transaction in _transactions:
        # print(transaction)


def extract_mbox(tar, mbox_file):
    with tempfile.TemporaryDirectory() as temp_dir:
        tar.extract(mbox_file, temp_dir)
        extracted_mbox = os.path.join(temp_dir, mbox_file.name)
        process_mbox(extracted_mbox)


with tarfile.open("paypal.tbz", "r") as tar:
    for member in tar.getmembers():
        extension = os.path.splitext(member.name)[1][1:].strip().lower()
        if "mbox" == extension:
            extract_mbox(tar, member)

