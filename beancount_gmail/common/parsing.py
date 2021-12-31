import re

from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString


def extract_row_text(row: Tag) -> list[str]:
    copy = BeautifulSoup(str(row), "html.parser")
    cell_text = []
    for cell in copy.find_all(['td', 'th']):
        [table.decompose() for table in cell.find_all('table')]
        cell_text.append(extract_text(cell))
    return cell_text


def extract_text(element: Tag) -> str:
    text = ''
    to_append = None

    def remove_unwanted_white_spaces(s: str) -> str:
        return re.sub(r' {2,}', ' ', re.sub(r'[\n\t]', r' ', re.sub(u'\xa0', ' ', s.strip())))

    for elem in element.children:
        if isinstance(elem, NavigableString):
            if elem.strip():
                s = remove_unwanted_white_spaces(elem.string.strip())
                text += to_append + " " + s if to_append else s
                to_append = None
        elif elem.name == 'a' or elem.name == 'span':
            to_append = to_append + " " + remove_unwanted_white_spaces(elem.text) if to_append \
                else remove_unwanted_white_spaces(elem.text)
        else:
            extracted = extract_text(elem)
            if to_append and extracted:
                extracted = to_append + ' ' + extracted
                to_append = None
            text += extracted

    if to_append:
        text += to_append

    return text
