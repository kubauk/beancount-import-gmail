import datetime

import jsonpickle
import os
from mailbox import Message

from beancount_gmail.email_parser_protocol import EmailParser
from beancount_gmail.receipt import Receipt

DEBUGGING_DATA_DIR = "debugging"

EXCLUDED_DATA_DIR = "excluded"

WRITE_DEBUG = False


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


def maybe_write_debugging(fn, extension: str, parser: EmailParser,
                          message_date: datetime.datetime, message: Message) -> list[Receipt]:
    if WRITE_DEBUG:
        write_email_to_file(None, extension, message_date, message, os.path.join(os.getcwd(), DEBUGGING_DATA_DIR))

    receipts = write_email_file_on_exception(fn, extension, parser, message_date, message)

    if WRITE_DEBUG:
        write_receipts_to_file(receipts, message_date)

    return receipts


def write_email_file_on_exception(fn, extension: str, parser: EmailParser,
                                  message_date: datetime.datetime, message: Message) -> list[Receipt]:
    try:
        return fn(parser, message_date, message)
    except Exception as e:
        write_email_to_file(e.__class__.__name__, extension, message_date, message,
                            os.path.join(os.getcwd(), EXCLUDED_DATA_DIR))
        raise e
