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


def test_when_parsing_fails_no_receipts_are_returned(email_message):
    message = email_message("canned_messages/html.eml")
    parser = Mock(spec=EmailParser)
    parser.extract_receipts.side_effect = Exception("test")

    receipts = extract_receipts(parser, message)

    parser.extract_receipts.assert_called_once()
    assert_that(receipts, is_([]))


def test_multipart_message_with_no_text_or_html_content_type_returns_no_receipts(email_message):
    message = email_message('canned_messages/unknown-content-type-multipart.eml')
    parser = Mock(spec=EmailParser)

    receipts = extract_receipts(parser, message)

    parser.extract_receipts.assert_not_called()
    assert_that(receipts, is_([]))


def test_message_with_no_text_or_html_content_type_returns_no_receipts(email_message):
    message = email_message('canned_messages/unknown-content-type.eml')
    parser = Mock(spec=EmailParser)

    receipts = extract_receipts(parser, message)

    parser.extract_receipts.assert_not_called()
    assert_that(receipts, is_([]))
