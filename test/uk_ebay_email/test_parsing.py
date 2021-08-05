import datetime
import re

from bs4.element import Tag, Comment
from hamcrest import assert_that, is_

from beancount_gmail.receipt import Receipt
from beancount_gmail.uk_paypal_email.parsing import extract_text, extract_row_text


def tables_without_presentation_role(tag: Tag) -> bool:
    if tag.name == 'table':
        if 'role' in tag.attrs and tag.attrs['role'] == 'presentation':
            return False
        return True
    return False


def remove_comments(tag):
    for c in tag.find_all(text=lambda t: isinstance(t, Comment)):
        c.extract()


def extract_row_text2(tag: Tag) -> list[list[set[str]]]:
    remove_comments(tag)

    tables = []
    for table in tag.find_all(tables_without_presentation_role):
        if table.find("table") is not None:
            continue

        rows = list()
        for row in table.find_all('tr'):
            cell_text = set()
            for cell in row.find_all(['td', 'th']):
                cell_text.add(extract_text(cell))
            rows.append(cell_text)
        tables.append(rows)
    return tables


def extract_row() -> list[set[str]]:
    pass


def recurse_depth_first(tag: Tag) -> list:
    result = []
    if getattr(tag, 'children', None) is not None:
        for child in tag.children:
            result.append(recurse_depth_first(child))

    result.append(extract_text(tag))
    return result


def replace_with_currency_code(rows):
    def append_iso_currency_code(row):
        split = row.split('£')
        if len(split) > 1:
            return '{} GBP'.format(split[1])
        else:
            return row

    return [append_iso_currency_code(row) for row in rows]


def first_price(rows):
    prices = [row for row in rows if 'GBP' in row]
    return None if len(prices) == 0 else prices[0]


# def test_parsing_html_produces_receipt(soup):
#     html = soup("sample_html/ebay-2018.eml.html")
#
#     remove_comments(html)
#
#     totals = find_order_totals(html)
#
#     receipt_details = find_order_details(html)
#
#     receipt = Receipt(datetime.datetime.now(), receipt_details, totals, False)
#
#     convert = soup2dict.convert(html)
#
#     pass


def interesting_row(rows):
    if len(rows) > 1:
        return any("Order" in s for s in rows)
    return False


def description(details):
    return details[0], first_price(details)


def totals(rows):
    rows_iter = iter(rows[1:])
    return list(filter(lambda k: 'GBP' in k[1], zip(rows_iter, rows_iter)))


def description_and_total(details):
    return description(details[0]), totals(details[1])


def test_append_iso_currency():
    assert_that(replace_with_currency_code(['row 1', '£1.23', 'row 4', 'price 2 £4.56', 'row 5']),
                is_(['row 1', '1.23 GBP', 'row 4', '4.56 GBP', 'row 5']))
    assert_that(replace_with_currency_code(['row 1', 'price £1.23']),
                is_(['row 1', '1.23 GBP']))
    assert_that(replace_with_currency_code(['1.23 GBP']),
                is_(['1.23 GBP']))
    assert_that(replace_with_currency_code(['£1.23', 'row 4', '4.56 GBP']),
                is_(['1.23 GBP', 'row 4', '4.56 GBP']))


def test_first_price():
    assert_that(first_price(['row 1', '1.23 GBP', 'row 4', 'price 2 £4.56', 'row 5']), is_('1.23 GBP'))
    assert_that(first_price(['row 1', 'price £1.23']), is_(None))
    assert_that(first_price(['1.23 GBP']), is_('1.23 GBP'))
    assert_that(first_price(['£1.23', 'row 4', '4.56 GBP']), is_('4.56 GBP'))


def test_parsing_html_produces_receipt2(soup):
    html = soup("sample_html/ebay-2019.eml.html")

    remove_comments(html)

    table_text = [replace_with_currency_code(extract_row_text(table)) for table in html.find_all('table')
                  if table.find('table') is None]
    descriptions, totals = description_and_total(list(filter(interesting_row, table_text)))

    receipt = Receipt(datetime.datetime.now(), [descriptions], totals, False)

    pass


def find_order_details(html):
    receipt_details = []
    items = (tag for tag in html.find_all("table", id=re.compile("itemtitle|itemdetails")))
    for item in zip(items, items):
        item_text = extract_row_text(item[1].find(text=re.compile('Item price|Total')).find_parent('tr'))
        receipt_details.append((extract_text(item[0]), ('{} GBP'.format(item_text[0].split('£')[1]))))
    return receipt_details

# def find_order_totals(html) -> list[tuple[str, str]]:
#     tr = html.find(text=re.compile("Order total:"))
#     table = tr.find_parent("table")
#     text = extract_row_text(table)
#     text.pop(0)
#
#     i = append_iso_currency_code(text)
#     return list(filter(lambda j: "GBP" in j[1], zip(i, i)))
