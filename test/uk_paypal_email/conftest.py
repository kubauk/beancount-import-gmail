import os.path

import bs4
from pytest import fixture


@fixture
def test_html(request):
    def open_file(file_name):
        handle = open(file_name)
        request.addfinalizer(lambda: handle.close())
        return handle

    return open_file


@fixture
def soup(test_html):
    return lambda file_name: bs4.BeautifulSoup(
        test_html(os.path.join(os.path.dirname(__file__), file_name)).read(), "html.parser")