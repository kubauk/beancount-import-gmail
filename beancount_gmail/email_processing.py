import datetime
import os
from mailbox import Message

import bs4
import jsonpickle
import pytz

from beancount_gmail.uk_paypal_email.parser import find_receipts

EXCLUDED_DATA_DIR = "./excluded"

DEBUGGING_DATA_DIR = "./debugging"

TIMEZONE = pytz.timezone("Europe/London")

WRITE_DEBUG = False


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
        return maybe_write_debugging(extract_receipts_from_email, "html", message_date,
                                     message.get_payload(decode=True).decode(get_charset(message)))
    elif message.get_content_type == "text/plain:":
        return maybe_write_debugging(extract_receipts_from_email, "txt", message_date, message)
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


def write_email_to_file(reason, extension, message_date, message, file_dir):
    def data_handler(out):
        if isinstance(message, Message):
            out.write(message.as_string())
        else:
            out.write(message)

    write_data_to_file(reason, extension, message_date, data_handler, file_dir)


def write_receipts_to_file(receipts, message_date):
    def data_handler(out):
        encode = jsonpickle.encode(receipts, unpicklable=True, indent=2)
        out.write(encode)

    write_data_to_file(None, "json", message_date, data_handler, DEBUGGING_DATA_DIR)


def write_data_to_file(reason, extension, message_date, data_handler, file_dir):
    if not os.path.exists(file_dir):
        os.mkdir(file_dir)

    file = os.path.join(file_dir, "%s.%s.%s" % (message_date, reason, extension))
    with open(file, "w") as out:
        data_handler(out)


def extract_receipts(message):
    local_message_date = datetime.datetime.strptime(message.get("Date"), "%a, %d %b %Y %H:%M:%S %z")
    message_date = TIMEZONE.normalize(local_message_date.astimezone(TIMEZONE))

    try:
        return process_message_payload(message_date, message)
    except Exception:
        return []


def maybe_write_debugging(fn, extension, message_date, message):
    if WRITE_DEBUG:
        write_email_to_file(None, extension, message_date, message, DEBUGGING_DATA_DIR)

    receipts = write_email_file_on_exception(fn, extension, message_date, message)

    if WRITE_DEBUG:
        write_receipts_to_file(receipts, message_date)

    return receipts


def write_email_file_on_exception(fn, extension, message_date, message):
    try:
        return fn(message_date, message)
    except Exception as e:
        write_email_to_file(e.__class__.__name__, extension, message_date, message, EXCLUDED_DATA_DIR)
        raise e
