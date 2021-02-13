import datetime
import os
from mailbox import Message

import bs4
import pytz

from beancount_gmail.uk_paypal_email.parser import find_receipts

CUT_OFF_DATE = datetime.datetime(2009, 1, 1, tzinfo=pytz.utc)

EXCLUDED_DATA_DIR = "./excluded"

TIMEZONE = pytz.timezone("Europe/London")


class NoCharsetException(Exception):
    pass


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
    except Exception:
        return list()


def write_debugging_file_on_exception(fn, extension, message_date, message):
    try:
        return fn(message_date, message)
    except Exception as e:
        write_debugging_data_to_file(e.__class__.__name__, extension, message_date, message)
        raise e
