import os.path

import bs4
from pytest import fixture


@fixture
def soup(test_file):
    return lambda file_name: bs4.BeautifulSoup(
        test_file(os.path.join(os.path.dirname(__file__), file_name)).read(), "html.parser")
