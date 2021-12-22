import re
from typing import Callable
from unittest.mock import Mock

from beancount.core.data import Transaction
from hamcrest import assert_that, is_

from beancount_gmail.email_parser_protocol import transaction_filter, re_filter

mock_transaction = Mock(spec=Transaction)


def test_transaction_filter_boundary_cases():
    assert_that(transaction_filter(None, None), is_(False))
    assert_that(transaction_filter(None, mock_transaction), is_(True))


def test_transaction_filter_matches_string_when_set():
    mock_transaction.narration = "should match"
    assert_that(transaction_filter("it should not match", mock_transaction), is_(False))
    assert_that(transaction_filter("don't match", mock_transaction), is_(False))
    assert_that(transaction_filter("should match", mock_transaction), is_(True))
    assert_that(transaction_filter("match", mock_transaction), is_(True))


def test_transaction_filter_uses_callable_when_set():
    filter_param_true = Mock(spec=Callable)
    filter_param_true.return_value = True

    assert_that(transaction_filter(filter_param_true, mock_transaction), is_(True))
    filter_param_true.assert_called_once()

    filter_param_false = Mock(spec=Callable)
    filter_param_false.return_value = False

    assert_that(transaction_filter(filter_param_false, mock_transaction), is_(False))
    filter_param_false.assert_called_once()


def test_re_filter():
    mock_transaction.narration = 'A needle in a haystack'
    assert_that(re_filter('Do not found')(mock_transaction), is_(False))
    assert_that(re_filter('needle')(mock_transaction), is_(True))
    assert_that(re_filter('thimble|needle')(mock_transaction), is_(True))

    assert_that(re_filter('NEEDLE', re.IGNORECASE)(mock_transaction), is_(True))
