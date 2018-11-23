import datetime
import os
import re
from mailbox import Message

import bs4
import pytz

from beancount_gmail.transaction import Transaction

DONATION_DETAILS_RE = re.compile(u"Donation amount:(?P<Donation>£\d+\.\d\d [A-Z]{3}) +"
                                 u"Total:(?P<Total>£\d+\.\d\d [A-Z]{3}) +"
                                 u"Purpose:(?P<Purpose>[ \S]+\S) +"
                                 u"Contributor:")

CUT_OFF_DATE = datetime.datetime(2009, 1, 1, tzinfo=pytz.utc)

EXCLUDED_DATA_DIR = "./excluded"

UUID_PATTERN = r"[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}"


class ParseException(Exception):
    pass


class NoTransactionFoundException(ParseException):
    pass


class NoCharsetException(ParseException):
    pass


def parse_new_format(message_date, soup, tables, transactions):
    while len(tables) >= 1:
        transactions.append(extract_new_format_transactions(message_date, tables))


def parse_original_format(message_date, soup, tables, transactions):
    if len(tables) == 2:
        refund = soup.find(text=re.compile(".*refund.*", re.IGNORECASE)) is not None
        transactions.append(extract_original_format_transaction(message_date, refund, tables))


def _extract_transactions_details(text):
    return DONATION_DETAILS_RE.search(text).groupdict()


def parse_donation(message_date, table, transactions):
    details = _extract_transactions_details(table.get_text().replace(u"\xa0", " ").replace("\n", " "))

    transactions.append(
        Transaction(message_date, [(details['Purpose'], details['Donation'])],
                    [("Total", details['Total'])], False))


def find_transaction_tables(message_date, soup):
    transactions = list()

    if soup.title is not None and soup.title.find(
            text=re.compile(r"Receipt for your donation", re.UNICODE)) is not None:
        parse_donation(message_date, soup.find("table", {"id": re.compile(UUID_PATTERN)}), transactions)
        return transactions

    tables = list()
    for table in soup.find_all("table"):

        if table.find("table") is not None:
            continue

        elif table.find("th"):
            table_element = table.tr.th
            parser = parse_new_format
        else:
            table_element = table.tr.td
            parser = parse_original_format

        if contains_interesting_table(table_element):
            tables.append(table)

        parser(message_date, soup, tables, transactions)

    if len(transactions) == 0:
        raise NoTransactionFoundException("Did not find any transactions")

    return transactions


def extract_new_format_transactions(message_date, tables):
    sub_transactions, totals = extract_new_format_sub_transactions_from_table(tables.pop(0))
    return Transaction(message_date, sub_transactions, totals, False)


def extract_original_format_transaction(message_date, refund, tables):
    sub_transactions = extract_sub_transactions_from_table(tables.pop(0), skip_header=True)
    totals = extract_sub_transactions_from_table(tables.pop(0))
    return Transaction(message_date, sub_transactions, totals, refund)


def contains_interesting_table(table_element):
    first_td_text = table_element.get_text(separator=u' ').strip()
    if first_td_text == "Description":
        return True
    elif first_td_text.startswith("Postage and pack") or first_td_text == "Subtotal":
        return True

    return False


def next_sibling_tag(first):
    sibling = first.next_sibling
    while type(sibling) is not bs4.Tag and sibling is not None:
        sibling = sibling.next_sibling
    return sibling


def sanitise_html(soup):
    for tag in ["div", "span"]:
        [div.unwrap() for div in soup.find_all(tag)]


def extract_sub_transactions_from_table(table, skip_header=False):
    sanitise_html(table)
    sub_transactions = list()

    row = next_sibling_tag(table.tr) if skip_header else table.tr
    while row is not None:
        columns = row.find_all('td')
        description = columns[0].get_text(strip=True, separator=u' ')
        total = columns[len(columns) - 1].get_text(separator=u' ').strip()

        if (description is not None and description is not '') \
                and (total is not None and total is not ''):
            sub_transactions.append((description, total))
        row = next_sibling_tag(row)

    return sub_transactions


def extract_new_format_sub_transactions_from_table(table):
    sub_transactions = list()
    totals = list()
    for row in table.find_all('tr', class_="datarow"):
        columns = row.find_all('td')
        description = columns[0].get_text(separator=u' ').strip()
        total = columns[len(columns) - 1].get_text(strip=True, separator=u' ')
        if (description is not None and description is not '') \
                and (total is not None and total is not ''):
            sub_transactions.append((description, total))

    for row in table.find_all('tr'):
        columns = row.find_all('td')
        if len(columns) == 0:
            continue
        description = columns[len(columns) - 2].get_text(separator=u' ').strip()
        total = columns[len(columns) - 1].get_text(separator=u' ').strip()
        if (description is not None and description is not '') \
                and (total is not None and total is not ''):
            totals.append((description, total))

    return sub_transactions, totals


def extract_transactions_from_email(message_date, message_body):
    soup = bs4.BeautifulSoup(message_body, "html.parser")
    return find_transaction_tables(message_date, soup)


def get_charset(message):
    if message.get_charset():
        return message.get_charset()

    if 'Content-Type' in message:
        return message.get('Content-Type').split("charset=")[1]

    raise NoCharsetException()


def process_message_text(message_date, message):
    if message.get_content_type() == "text/html":
        return write_debugging_file_on_exception(extract_transactions_from_email, "html", message_date,
                                                 message.get_payload(decode=True).decode(get_charset(message)))
    elif message.get_content_type == "text/plain:":
        return write_debugging_file_on_exception(extract_transactions_from_email, "txt", message_date, message)
    else:
        return list()


def process_message_payload(message_date, message):
    if message.is_multipart():
        for part in message.get_payload():
            transaction = process_message_text(message_date, part)
            if transaction:
                return transaction
        return list()
    else:
        return process_message_text(message_date, message)


def write_debugging_data_to_file(reason, extension, message_date, message):
    if not os.path.exists(EXCLUDED_DATA_DIR):
        os.mkdir(EXCLUDED_DATA_DIR)

    file = os.path.join(EXCLUDED_DATA_DIR, "%s.%s.%s" % (message_date, reason, extension))
    with open(file, "w") as out:
        if isinstance(message, Message):
            out.write(message.as_string())
        else:
            out.write(message)


def extract_transaction(message):
    local_message_date = datetime.datetime.strptime(message.get("Date"), "%a, %d %b %Y %H:%M:%S %z")
    message_date = pytz.utc.normalize(local_message_date.astimezone(pytz.utc))

    if message_date < CUT_OFF_DATE:
        write_debugging_data_to_file("TooOld", "eml", message_date, message)
        return list()

    try:
        return process_message_payload(message_date, message)
    except ParseException:
        return list()


def write_debugging_file_on_exception(fn, extension, message_date, message):
    try:
        return fn(message_date, message)
    except NoTransactionFoundException as e:
        write_debugging_data_to_file("NoTransactionsFound", extension, message_date, message)
        raise e
    except NoCharsetException as e:
        write_debugging_data_to_file("NoCharset", extension, message_date, message)
        raise e
