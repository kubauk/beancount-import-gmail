from unittest.mock import Mock

from bs4.element import Tag
from hamcrest.core import assert_that, is_

from beancount_gmail.uk_paypal_email.parsing import contains_interesting_table


def tag_with_text(row_text):
    tag = Mock(spec=Tag)
    tag.get_text.return_value = row_text
    return tag


def test_postage_in_interesting_table():
    assert_that(contains_interesting_table(tag_with_text("Description")), is_(True))
    assert_that(contains_interesting_table(tag_with_text("Subtotal")), is_(True))
    assert_that(contains_interesting_table(tag_with_text("Postage and packaging")), is_(True))
    assert_that(
        contains_interesting_table(tag_with_text("Postage and packaging  charges are estimated rates.")),
        is_(False))
