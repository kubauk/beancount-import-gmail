import datetime
import os
import re
from mailbox import Message

import bs4
import pytz

from beancount_gmail.receipt import Receipt
from beancount_gmail.common_re import POSTAGE_AND_PACKAGING_RE

DONATION_DETAILS_RE = re.compile(r"Donation amount:(?P<Donation>£\d+\.\d\d [A-Z]{3}) +"
                                 r"Total:(?P<Total>£\d+\.\d\d [A-Z]{3}) +"
                                 r"Purpose:(?P<Purpose>[ \S]+\S) +"
                                 r"Contributor:")

CUT_OFF_DATE = datetime.datetime(2009, 1, 1, tzinfo=pytz.utc)

EXCLUDED_DATA_DIR = "./excluded"

UUID_PATTERN = r"[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}"

TIMEZONE = pytz.timezone("Europe/London")


class ParseException(Exception):
    pass


class NoReceiptsFoundException(ParseException):
    pass


class NoTableFoundException(ParseException):
    pass


class NoCharsetException(ParseException):
    pass


def parse_new_format(message_date, soup, tables, receipts):
    while len(tables) >= 1:
        receipts.append(extract_new_format_receipt(message_date, tables))


def parse_original_format(message_date, soup, tables, receipts):
    if len(tables) == 2:
        negate = soup.find(text=re.compile(".*refund .*", re.IGNORECASE)) is not None or \
                 soup.find(text=re.compile(".*You received a payment.*", re.IGNORECASE)) is not None

        receipts.append(extract_original_format_receipt(message_date, negate, tables))


def _extract_donation_details(text):
    return DONATION_DETAILS_RE.search(text).groupdict()


def parse_donation(message_date, table, receipts):
    details = _extract_donation_details(table.get_text().replace(u"\xa0", " ").replace("\n", " "))

    receipts.append(
        Receipt(message_date, [(details['Purpose'], details['Donation'])], [("Total", details['Total'])], False))


def find_receipts(message_date, soup):
    receipts = list()

    if soup.title is not None and soup.title.find(
            text=re.compile(r"Receipt for your donation", re.UNICODE)) is not None:
        parse_donation(message_date, soup.find("table", {"id": re.compile(UUID_PATTERN)}), receipts)
        return receipts

    tables = list()
    for table in soup.find_all("table"):

        if table.find("table") is not None:
            continue

        elif table.find("th"):
            table_element = table.tr.th
            parser = parse_new_format
        else:
            if hasattr(table.tr, 'td'):
                table_element = table.tr.td
                parser = parse_original_format
            else:
                raise NoTableFoundException

        if table_element is None:
            raise NoTableFoundException()

        if contains_interesting_table(table_element):
            tables.append(table)

        parser(message_date, soup, tables, receipts)

    if len(receipts) == 0:
        raise NoReceiptsFoundException("Did not find any receipts")

    return receipts


def extract_new_format_receipt(message_date, tables):
    receipt_details, totals = extract_new_format_receipt_details_from_table(tables.pop(0))
    return Receipt(message_date, receipt_details, totals, False)


def extract_original_format_receipt(message_date, negate, tables):
    receipt_details = extract_receipt_details_from_table(tables.pop(0), skip_header=True)
    totals = extract_receipt_details_from_table(tables.pop(0))
    return Receipt(message_date, receipt_details, totals, negate)


def contains_interesting_table(table_element):
    stripped_text = table_element.get_text(separator=u' ').strip()
    if "Description" in stripped_text or \
            POSTAGE_AND_PACKAGING_RE.match(stripped_text) or \
            "Subtotal" in stripped_text:
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


def extract_receipt_details_from_table(table, skip_header=False):
    sanitise_html(table)
    receipt_details = list()

    row = next_sibling_tag(table.tr) if skip_header else table.tr
    while row is not None:
        columns = row.find_all('td')
        description = columns[0].get_text(strip=True, separator=u' ')
        total = columns[len(columns) - 1].get_text(separator=u' ').strip()

        if (description is not None and description is not '') \
                and (total is not None and total is not ''):
            receipt_details.append((description, total))
        row = next_sibling_tag(row)

    return receipt_details


def extract_new_format_receipt_details_from_table(table):
    receipt_details = list()
    totals = list()
    for row in table.find_all('tr', class_="datarow"):
        columns = row.find_all('td')
        description = columns[0].get_text(separator=u' ').strip()
        total = columns[len(columns) - 1].get_text(strip=True, separator=u' ')
        if (description is not None and description is not '') \
                and (total is not None and total is not ''):
            receipt_details.append((description, total))

    for row in table.find_all('tr'):
        columns = row.find_all('td')
        if len(columns) == 0:
            continue
        description = columns[len(columns) - 2].get_text(separator=u' ').strip()
        total = columns[len(columns) - 1].get_text(separator=u' ').strip()
        if (description is not None and description is not '') \
                and (total is not None and total is not ''):
            totals.append((description, total))

    return receipt_details, totals


def extract_receipts_from_email(message_date, message_body):
    soup = bs4.BeautifulSoup(message_body, "html.parser")
    return find_receipts(message_date, soup)


def get_charset(message):
    if message.get_charset():
        return message.get_charset()

    if 'Content-Type' in message:
        return message.get('Content-Type').split("charset=")[1]

    raise NoCharsetException()


def process_message_text(message_date, message):
    if message.get_content_type() == "text/html":
        return write_debugging_file_on_exception(extract_receipts_from_email, "html", message_date,
                                                 message.get_payload(decode=True).decode(get_charset(message)))
    elif message.get_content_type == "text/plain:":
        return write_debugging_file_on_exception(extract_receipts_from_email, "txt", message_date, message)
    else:
        return list()


def process_message_payload(message_date, message):
    if message.is_multipart():
        for part in message.get_payload():
            receipts = process_message_text(message_date, part)
            if receipts:
                return receipts
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


def extract_receipts(message):
    local_message_date = datetime.datetime.strptime(message.get("Date"), "%a, %d %b %Y %H:%M:%S %z")
    message_date = TIMEZONE.normalize(local_message_date.astimezone(TIMEZONE))

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
    except Exception as e:
        write_debugging_data_to_file(e.__class__.__name__, extension, message_date, message)
        raise e
