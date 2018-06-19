import hamcrest
from main import payee_and_memo

paypal = "PayPal"
paypal_credit = "PayPal Credit"

def test_payee_and_memo():
    _type = "Type"
    _credit_type = "This type has Credit in it"
    hamcrest.assert_that(payee_and_memo("", _type), hamcrest.equal_to((paypal, _type)))
    hamcrest.assert_that(payee_and_memo(None, _type), hamcrest.equal_to((paypal, _type)))
    hamcrest.assert_that(payee_and_memo("", _credit_type), hamcrest.equal_to((paypal_credit, _credit_type)))
    hamcrest.assert_that(payee_and_memo(None, _credit_type), hamcrest.equal_to((paypal_credit, _credit_type)))


def test_payee_and_memo_with_unwanted_payees():
    _type = "Type"
    hamcrest.assert_that(payee_and_memo("To get contact details, please visit your order details on My eBay", _type),
                         hamcrest.equal_to(("PayPal", _type)))

