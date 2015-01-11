import datetime
from html.parser import HTMLParser
import os
import quopri
import tarfile
import tempfile
from mailbox import mbox


class Transaction(object):
    def __init__(self, date, data):
        self.date = date
        self.description = data[0]
        self.amount = data[1]

    def __str__(self):
        return "%s %s %s" % (self.date, self.description, self.amount)


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
        if not data:
            return False

        self._transaction = Transaction(self._date, self.get_data_for_row(1))
        print(self._transaction)
        return True

    def get_transaction(self):
        return self._transaction

    def get_data_for_row(self, index):
        row = self._data[index]
        description = None
        if len(row) > 0:
            if len(row[0]) > 0:
                description = row[0][0].strip()
        if len(row) > 3:
            if len(row[3]) > 0:
                amount = row[3][0].strip()
                return description, amount

        return None


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

    def get_transaction(self):
        if not self._transaction:
            raise NoTransactionFoundException()

        return self._transaction

_transactions = list()


def process_email(date, payload):
    html = quopri.decodestring(payload)
    parser = Parser(date)
    parser.feed(str(html))
    _transactions.append(parser.get_transaction())


def parse_date(date_string):
    return datetime.datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %z")


def process_message(message):
    date = parse_date(message.get("Date"))
    if message.is_multipart():
        for part in message.get_payload():
            if part.get_content_type() == "text/html":
                process_email(date, part.get_payload())
    else:
        process_email(date, message.get_payload())


def process_mbox(mbox_path):
    mailbox = mbox(mbox_path)
    # for key, message in mailbox.items():
    #     print(key)
    #     process_message(message)
    process_message(mailbox.get(61))

    # for transaction in _transactions:
    #     print(transaction)


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

