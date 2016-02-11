import datetime
import os
import re

import bs4
import pytz

from transaction import Transaction

CUT_OFF_DATE = datetime.datetime(2009, 1, 1, tzinfo=pytz.utc)

EXCLUDED_EMAILS_DIR = "./excluded"


class ParseException(Exception):
    pass


class NoTransactionFoundException(Exception):
    pass


class NoCharsetException(Exception):
    pass


def find_transaction_tables(message_date, soup):
    transactions = list()

    tables = list()
    for table in soup.find_all("table"):
        if table.find("table") is not None:
            continue
        if table.find("th"):
            table_element = table.tr.th
            new_format = True
        else:
            table_element = table.tr.td
            new_format = False

        if contains_interesting_table(table_element):
            tables.append(table)

        if not new_format and len(tables) == 2:
            refund = soup.find(text=re.compile(".*refund.*", re.IGNORECASE)) is not None
            transactions.append(extract_original_format_transaction(message_date, refund, tables))
        elif new_format and len(tables) == 1:
            transactions.append(extract_new_format_transactions(message_date, tables))

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


def extract_sub_transactions_from_table(table, skip_header=False):
    sub_transactions = list()

    row = next_sibling_tag(table.tr) if skip_header else table.tr
    while row is not None:
        columns = row.find_all('td')
        description = columns[0].get_text(separator=u' ').strip()
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
        total = columns[len(columns) - 1].get_text(separator=u' ').strip()
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
        return extract_transactions_from_email(message_date,
                                               message.get_payload(decode=True).decode(get_charset(message)))
    elif message.get_content_type == "text/plain:":
        return extract_transactions_from_email(message_date, message)
    else:
        return list()


def process_message_payload(message, message_date):
    if message.is_multipart():
        for part in message.get_payload():
            transaction = process_message_text(message_date, part)
            if transaction:
                return transaction
        return list()
    else:
        return process_message_text(message_date, message)


def write_email_to_file(message_date, message):
    if not os.path.exists(EXCLUDED_EMAILS_DIR):
        os.mkdir(EXCLUDED_EMAILS_DIR)

    file = os.path.join(EXCLUDED_EMAILS_DIR, "%s.eml" % message_date)
    with open(file, "w") as out:
        out.write(message.as_string())


def extract_transaction(message):
    local_message_date = datetime.datetime.strptime(message.get("Date"), "%a, %d %b %Y %H:%M:%S %z")
    message_date = pytz.utc.normalize(local_message_date.astimezone(pytz.utc))

    if message_date < CUT_OFF_DATE:
        write_email_to_file(message_date, message)
        return list()

    try:
        return process_message_payload(message, message_date)
    except NoTransactionFoundException:
        write_email_to_file(message_date, message)
    except NoCharsetException:
        write_email_to_file(message_date, message)

    return list()