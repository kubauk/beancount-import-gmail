from hamcrest.core import assert_that, is_

from beancount_gmail.uk_paypal_email.parser import contains_interesting_table


def mock_soup_table_with_row(row_text):
    class MockSoupElement(object):
        def get_text(self, separator):
            return row_text

    return MockSoupElement()


def test_postage_in_interesting_table():
    assert_that(contains_interesting_table(mock_soup_table_with_row("Description")), is_(True))
    assert_that(contains_interesting_table(mock_soup_table_with_row("Subtotal")), is_(True))
    assert_that(contains_interesting_table(mock_soup_table_with_row("Postage and packaging")), is_(True))
    assert_that(
        contains_interesting_table(mock_soup_table_with_row("Postage and packaging  charges are estimated rates.")),
        is_(False))
