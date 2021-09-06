import datetime
from unittest.mock import Mock

from beancount.core.data import Transaction, Account, Amount, create_simple_posting, D
from beangulp.importer import ImporterProtocol
from hamcrest import assert_that, is_

from beancount_gmail import GmailImporter
from beancount_gmail.receipt import Receipt

ACCOUNT = "ACCOUNT"
CURRENCY = "CURRENCY"


def test_support_functions_call_delegate():
    delegate = Mock(spec=ImporterProtocol)

    importer = GmailImporter(delegate, 'POSTAGE', 'EMAIL')

    delegate.name.return_value = 'delegate_name'
    assert_that(importer.name(), is_('delegate_name'))

    delegate.identify.return_value = True
    assert_that(importer.identify('file'), is_(True))
    delegate.identify.assert_called_with('file')

    delegate.file_account.return_value = Account('EXPENSE')
    assert_that(importer.file_account('file2'), is_(Account('EXPENSE')))
    delegate.file_account.assert_called_with('file2')


def _mock_receipt(date: datetime, number: str = None) -> Receipt:
    receipt = Mock(spec=Receipt)
    receipt.receipt_date = date
    if number:
        receipt.total = Amount(D(number), CURRENCY)
    return receipt


def _mock_directive(date, z):
    transaction = Mock(spec=z)
    transaction.date = date
    transaction.meta = {}
    return transaction


def _mock_transaction(date: datetime.date) -> Transaction:
    transaction = _mock_directive(date, Transaction)
    transaction.postings = []
    return transaction


def _mock_transaction_with_posting(date: datetime.date, number: str) -> Transaction:
    transaction = _mock_transaction(date)
    create_simple_posting(transaction, ACCOUNT, number, CURRENCY)
    return transaction
