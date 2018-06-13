import hamcrest
from main import payee_and_memo


def test_payee_and_memo():
    _name = "Name"
    _type = "Type"
    hamcrest.assert_that(payee_and_memo("", _type), hamcrest.equal_to((_type, None)))
    hamcrest.assert_that(payee_and_memo(None, _type), hamcrest.equal_to((_type, None)))
    hamcrest.assert_that(payee_and_memo(_name, _type), hamcrest.equal_to((_name, _type)))
