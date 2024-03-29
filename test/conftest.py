import email
import os

from pytest import fixture


@fixture
def test_file(request):
    def open_file(file_name):
        handle = open(file_name)
        request.addfinalizer(lambda: handle.close())
        return handle

    return open_file


@fixture
def email_message(test_file):
    return lambda file_name: email.message_from_string(
        test_file(os.path.join(os.path.dirname(__file__), file_name)).read())
