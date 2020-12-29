import datetime
import os
import re
from mailbox import Message

import bs4
import pytz
from bs4 import NavigableString

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


class NoCharsetException(ParseException):
    pass


def _extract_donation_details(text):
    return DONATION_DETAILS_RE.search(text).groupdict()


def contains_interesting_table(table_element):
    stripped_text = table_element.get_text(separator=u' ').strip()
    return "Description" in stripped_text or \
           POSTAGE_AND_PACKAGING_RE.match(stripped_text) is not None or \
           "Subtotal" in stripped_text or \
           "Total" in stripped_text


def extract_text(element):
    text = ''
    to_append = None

    def remove_unwanted_white_spaces(s):
        return re.sub(r' {2,}', ' ', re.sub(r'[\n\t]', r' ', re.sub(u'\xa0', ' ', s.strip())))

    for elem in element.children:
        if isinstance(elem, NavigableString):
            if elem.strip():
                s = remove_unwanted_white_spaces(elem.string.strip())
                text += to_append + " " + s if to_append else s
                to_append = None
        elif elem.name == 'a' or elem.name == 'span':
            to_append = to_append + " " + remove_unwanted_white_spaces(elem.text) if to_append \
                else remove_unwanted_white_spaces(elem.text)
        else:
            extracted = extract_text(elem)
            if to_append and extracted:
                extracted = to_append + ' ' + extracted
                to_append = None
            text += extracted

    if to_append:
        text += to_append

    return text


def extract_row_text(row):
    cell_text = []
    for cell in row.find_all(['td', 'th']):
        cell_text.append(extract_text(cell))
    return cell_text


def post_process_for_alternate_format(receipt_table_data):
    result = [[]]
    for row in receipt_table_data:
        if len(row) == 3:
            continue
        if len(row) == 4 and row[1] == '':
            if len(result) == 1:
                result.append([])
            result[1].append([row[2], row[3]])
        else:
            result[0].append(row)
    return result


def extract_receipt_data_from_tables(soup):
    receipt_data = []
    for table in soup.find_all("table"):
        if table.find("table") is not None:
            continue
        if contains_interesting_table(table):
            receipt_table_data = []
            for row in table.find_all("tr"):
                if row.get_text().strip():
                    extracted_text = extract_row_text(row)
                    if len(extracted_text) == 2 or len(extracted_text) == 4:
                        receipt_table_data.append(extracted_text)
            receipt_data.extend(post_process_for_alternate_format(receipt_table_data))
    return receipt_data


def extract_receipt_details_from_donation(soup):
    table = soup.find("table", {"id": re.compile(UUID_PATTERN)})
    dontation_details = _extract_donation_details(table.get_text().replace(u"\xa0", " ").replace("\n", " "))
    receipt_details = [['Description', 'Unit Price', 'Quantity', 'Amount'],
                       [dontation_details['Purpose'], '', '', dontation_details['Donation']]]
    total_details = [["Total", dontation_details['Total']]]
    return [receipt_details, total_details]


def find_receipts(message_date, soup):
    receipt_data = extract_receipt_details_from_donation(soup) \
        if soup.title is not None and \
           soup.title.find(text=re.compile(r"Receipt for your donation", re.UNICODE)) is not None \
        else extract_receipt_data_from_tables(soup)

    receipts = []
    while len(receipt_data) > 0:
        receipt_details = [(detail[0], detail[3]) for detail in receipt_data.pop(0)[1:]]
        total_details = [(detail[0], detail[1]) for detail in receipt_data.pop(0) if len(detail) == 2]

        negate = soup.find(text=re.compile(".*refund .*", re.IGNORECASE)) is not None or \
                 soup.find(text=re.compile(".*You received a payment.*", re.IGNORECASE)) is not None

        receipts.append(Receipt(message_date, receipt_details, total_details, negate))

    if len(receipts) == 0:
        raise NoReceiptsFoundException("Did not find any receipts")

    return receipts


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
