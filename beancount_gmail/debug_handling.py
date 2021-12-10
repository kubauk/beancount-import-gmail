import datetime
from os import PathLike
from typing import Union, AnyStr, Callable, IO, Optional

import jsonpickle
import os
from mailbox import Message

from beancount_gmail.email_parser_protocol import EmailParser
from beancount_gmail.receipt import Receipt

DEBUGGING_DATA_DIR: str = "debugging"

EXCLUDED_DATA_DIR: str = "excluded"

WRITE_DEBUG: bool = False


def write_email_to_file(reason: Optional[str], extension: str, message_date: datetime,
                        message: Message, file_dir: Union[AnyStr, PathLike]) -> None:
    def data_handler(out):
        if isinstance(message, Message):
            out.write(message.as_string())
        else:
            out.write(message)

    write_data_to_file(reason, extension, message_date, data_handler, file_dir)


def write_receipts_to_file(receipts: list[Receipt], message_date: datetime) -> None:
    def data_handler(out):
        encode = jsonpickle.encode(receipts, unpicklable=True, indent=2)
        out.write(encode)

    write_data_to_file(None, "json", message_date, data_handler, DEBUGGING_DATA_DIR)


def write_data_to_file(reason: Optional[str], extension: str, message_date: datetime,
                       data_handler: Callable[[IO], None], file_dir: Union[AnyStr, PathLike]) -> None:
    if not os.path.exists(file_dir):
        os.mkdir(file_dir)

    file = os.path.join(file_dir, "%s.%s.%s" % (message_date, reason, extension))
    with open(file, "w") as out:
        data_handler(out)


def maybe_write_debugging(fn: Callable[[EmailParser, datetime, Message], list[Receipt]],
                          extension: str, parser: EmailParser,
                          message_date: datetime.datetime, message: Message) -> list[Receipt]:
    if WRITE_DEBUG:
        write_email_to_file(None, extension, message_date, message, os.path.join(os.getcwd(), DEBUGGING_DATA_DIR))

    receipts = write_email_file_on_exception(fn, extension, parser, message_date, message)

    if WRITE_DEBUG:
        write_receipts_to_file(receipts, message_date)

    return receipts


def write_email_file_on_exception(fn: Callable[[EmailParser, datetime, Message], list[Receipt]],
                                  extension: str, parser: EmailParser,
                                  message_date: datetime.datetime, message: Message) -> list[Receipt]:
    try:
        return fn(parser, message_date, message)
    except Exception as e:
        write_email_to_file(e.__class__.__name__, extension, message_date, message,
                            os.path.join(os.getcwd(), EXCLUDED_DATA_DIR))
        raise e
