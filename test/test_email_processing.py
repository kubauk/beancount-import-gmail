from hamcrest import assert_that, is_
from unittest.mock import Mock

from beancount_gmail.email_parser_protocol import EmailParser
from beancount_gmail.email_processing import extract_receipts
from beancount_gmail.receipt import Receipt

RECEIPT_ONE = Mock(spec=Receipt)
RECEIPT_TWO = Mock(spec=Receipt)
RECEIPTS = [RECEIPT_ONE, RECEIPT_TWO]


def test_html_is_favoured_over_text_and_parser_is_called_once(email_message):
    message = email_message("canned_messages/html.eml")
    parser = Mock(spec=EmailParser)
    parser.extract_receipts.return_value = RECEIPTS

    receipts = extract_receipts(parser, message)

    parser.extract_receipts.assert_called_once()
    assert_that(receipts, is_(RECEIPTS))
    pass


def test_text_is_given_to_parse_in_absence_of_html(email_message):
    message = email_message("canned_messages/text.eml")
    parser = Mock(spec=EmailParser)
    parser.extract_receipts.return_value = RECEIPTS

    receipts = extract_receipts(parser, message)

    parser.extract_receipts.assert_called_once()
    assert_that(receipts, is_(RECEIPTS))
    pass
