import datetime
from datetime import tzinfo
from mailbox import Message

import bs4
import pytz

from beancount_gmail.debug_handling import maybe_write_debugging
from beancount_gmail.email_parser_protocol import EmailParser
from beancount_gmail.receipt import Receipt

TIMEZONE: tzinfo = pytz.timezone("Europe/London")


class NoCharsetException(Exception):
    pass


def extract_receipts_from_email(parser: EmailParser, message_date: datetime,
                                message: Message) -> list[Receipt]:
    return parser.extract_receipts(message_date, bs4.BeautifulSoup(message, "html.parser"))


def process_message_text(parser: EmailParser, message_date: datetime, message: Message) -> list[Receipt]:
    if message.get_content_type() == "text/html":
        return maybe_write_debugging(extract_receipts_from_email, "html", parser, message_date,
                                     message.get_payload(decode=True).decode(message.get_content_charset()))
    elif message.get_content_type() == "text/plain":
        return maybe_write_debugging(extract_receipts_from_email, "txt", parser, message_date,
                                     message.get_payload(decode=True).decode(message.get_content_charset()))
    else:
        return []


def process_message_payload(message: Message, parser: EmailParser, message_date: datetime) -> list[Receipt]:
    if message.is_multipart():
        receipts = []
        [receipts.extend(process_message_text(parser, message_date, part))
         for part in message.get_payload()
         if "text/html" in part.get_content_type()]
        return receipts
    else:
        return process_message_text(parser, message_date, message)


def get_message_date(message: Message) -> datetime:
    return datetime.datetime.strptime(message.get("Date"), "%a, %d %b %Y %H:%M:%S %z")


def extract_receipts(parser: EmailParser, message: Message) -> list[Receipt]:
    message_date = get_message_date(message)

    try:
        return process_message_payload(message, parser, message_date)
    except Exception:
        return []
