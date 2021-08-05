import datetime

from hamcrest import assert_that, is_

from beancount_gmail.uk_ebay_email.parsing import first_price, extract_receipt, replace_with_currency_code
from test.test_receipt import assert_receipt_with_one_detail


def test_append_iso_currency_replaces_pound_symbol():
    assert_that(replace_with_currency_code(['row 1', '£1.23', 'row 4', 'price 2 £4.56', 'row 5']),
                is_(['row 1', '1.23 GBP', 'row 4', '4.56 GBP', 'row 5']))
    assert_that(replace_with_currency_code(['row 1', 'price £1.23']),
                is_(['row 1', '1.23 GBP']))
    assert_that(replace_with_currency_code(['1.23 GBP']),
                is_(['1.23 GBP']))
    assert_that(replace_with_currency_code(['£1.23', 'row 4', '4.56 GBP']),
                is_(['1.23 GBP', 'row 4', '4.56 GBP']))


def test_first_price_is_extracted():
    assert_that(first_price(['row 1', '1.23 GBP', 'row 4', 'price 2 £4.56', 'row 5']), is_('1.23 GBP'))
    assert_that(first_price(['row 1', 'price £1.23']), is_(None))
    assert_that(first_price(['1.23 GBP']), is_('1.23 GBP'))
    assert_that(first_price(['£1.23', 'row 4', '4.56 GBP']), is_('4.56 GBP'))


def test_ebay_2019_produces_receipt(soup):
    receipt = extract_receipt(datetime.datetime.now(), soup("sample_html/ebay-2019.eml.html"))

    assert_receipt_with_one_detail(receipt, '2.99',
                                   'G9 Halogen 28w 370 Lumen Capsule Bulb Long Life Dimmable Energy Saving', '2.99')


def test_ebay_2021_produces_receipt(soup):
    receipt = extract_receipt(datetime.datetime.now(), soup("sample_html/ebay-2021.eml.html"))

    assert_receipt_with_one_detail(receipt, '13.50',
                                   'ZURU ROBO ALIVE Robo Alive Snake Battery Robotic Toy Grey', '13.50')


def test_ebay_2021_2_produces_receipt(soup):
    receipt = extract_receipt(datetime.datetime.now(), soup("sample_html/ebay-2021-2.eml.html"))

    assert_receipt_with_one_detail(receipt, '8.89',
                                   'Electric Aroma Diffuser Essential Oil 7 Colour Changing Air Humidifier L...',
                                   '8.89')

# def tables_without_presentation_role(tag: Tag) -> bool:
#     if tag.name == 'table':
#         if 'role' in tag.attrs and tag.attrs['role'] == 'presentation':
#             return False
#         return True
#     return False


# def extract_row_text2(tag: Tag) -> list[list[set[str]]]:
#     remove_comments(tag)
#
#     tables = []
#     for table in tag.find_all(tables_without_presentation_role):
#         if table.find("table") is not None:
#             continue
#
#         rows = list()
#         for row in table.find_all('tr'):
#             cell_text = set()
#             for cell in row.find_all(['td', 'th']):
#                 cell_text.add(extract_text(cell))
#             rows.append(cell_text)
#         tables.append(rows)
#     return tables


# def extract_row() -> list[set[str]]:
#     pass


# def recurse_depth_first(tag: Tag) -> list:
#     result = []
#     if getattr(tag, 'children', None) is not None:
#         for child in tag.children:
#             result.append(recurse_depth_first(child))
#
#     result.append(extract_text(tag))
#     return result


# def find_order_details(html):
#     receipt_details = []
#     items = (tag for tag in html.find_all("table", id=re.compile("itemtitle|itemdetails")))
#     for item in zip(items, items):
#         item_text = extract_row_text(item[1].find(text=re.compile('Item price|Total')).find_parent('tr'))
#         receipt_details.append((extract_text(item[0]), ('{} GBP'.format(item_text[0].split('£')[1]))))
#     return receipt_details


# def find_order_totals(html) -> list[tuple[str, str]]:
#     tr = html.find(text=re.compile("Order total:"))
#     table = tr.find_parent("table")
#     text = extract_row_text(table)
#     text.pop(0)
#
#     i = append_iso_currency_code(text)
#     return list(filter(lambda j: "GBP" in j[1], zip(i, i)))
