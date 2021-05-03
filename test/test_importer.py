import datetime
from unittest.mock import Mock

from beancount.core.data import Transaction, Open, Balance
from hamcrest import assert_that, is_

from beancount_gmail.importer import get_search_dates


def test_search_date_return_correct_range_for_single_transaction():
    min_date, max_date = get_search_dates([_mock_directive(datetime.date(2020, 3, 14), Transaction)])
    assert_that(min_date, is_(datetime.date(2020, 3, 14)))
    assert_that(max_date, is_(datetime.date(2020, 3, 15)))


def test_search_date_return_correct_range_for_multiple_transaction():
    min_date, max_date = get_search_dates([
        _mock_directive(datetime.date(2020, 3, 14), Transaction),
        _mock_directive(datetime.date(2019, 1, 2), Transaction),
        _mock_directive(datetime.date(2020, 2, 3), Transaction),
        _mock_directive(datetime.date(2019, 12, 15), Transaction),
    ])
    assert_that(min_date, is_(datetime.date(2019, 1, 2)))
    assert_that(max_date, is_(datetime.date(2020, 3, 15)))


def test_search_date_ignores_non_transactions():
    min_date, max_date = get_search_dates([
        _mock_directive(datetime.date(2020, 3, 14), Open),
        _mock_directive(datetime.date(2019, 1, 2), Balance),
        _mock_directive(datetime.date(2020, 2, 3), Open),
        _mock_directive(datetime.date(2019, 12, 15), Transaction),
    ])
    assert_that(min_date, is_(datetime.date(2019, 12, 15)))
    assert_that(max_date, is_(datetime.date(2019, 12, 16)))


def _mock_directive(date, z):
    transaction = Mock(spec=z)
    transaction.date = date
    transaction.meta = {}
    return transaction
