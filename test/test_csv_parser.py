from beancount.ingest import cache

import csv_parser


def file_memo(file_name):
    return cache._FileMemo(file_name)


def test_transactions_match_csv():

    memo = csv_parser.extract_paypal_transactions_from_csv(file_memo("test.csv"))
    pass
