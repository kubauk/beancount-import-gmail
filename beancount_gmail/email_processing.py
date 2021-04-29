import datetime

import bs4
import pytz

from beancount_gmail.debug_handling import maybe_write_debugging
from beancount_gmail.uk_paypal_email import PayPalUKParser

TIMEZONE = pytz.timezone("Europe/London")


class NoCharsetException(Exception):
    pass


def extract_receipts_from_email(message_date, message_body):
    soup = bs4.BeautifulSoup(message_body, "html.parser")

    parser = PayPalUKParser()
    return parser.extract_receipts(message_date, soup)


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


def extract_receipts(message):
    local_message_date = datetime.datetime.strptime(message.get("Date"), "%a, %d %b %Y %H:%M:%S %z")
    message_date = TIMEZONE.normalize(local_message_date.astimezone(TIMEZONE))

    try:
        return process_message_payload(message_date, message)
    except Exception:
        return []
