from datetime import datetime

from hamcrest import assert_that, calling, raises, is_
from hamcrest.library.collection import contains_inanyorder

from beancount_gmail.receipt import NoReceiptsFoundException
from beancount_gmail.uk_amazon_email.parsing import extract_receipts
from test.test_receipt import assert_receipt_with_one_detail, receipt_with_one_detail


def test_parse_amazon_order_2018_02_10(soup):
    beautiful_soup = soup("sample_html/amazon-order-2018-02-10.html")
    receipts = extract_receipts(datetime(2018, 2, 10), beautiful_soup)

    assert_that(len(receipts), is_(1))
    assert_that(receipts[0],
                receipt_with_one_detail({'total': '21.20',
                                         'description': ('Forthglade 100% Natural Complete Meal Senior Dog Pet Food '
                                                         'Chicken, Brown Rice & Vegetables 395g (18 Pack) Sold by '
                                                         'Amazon EU S.a.r.L.', '21.20')}))


def test_parse_amazon_order_2018_12_11(soup):
    beautiful_soup = soup("sample_html/amazon-order-2018-12-11-multiple.html")
    receipts = extract_receipts(datetime(2018, 12, 11), beautiful_soup)

    assert_that(len(receipts), is_(2))

    assert_that(receipts, contains_inanyorder(
        receipt_with_one_detail(
            {'total': '69.95',
             'description': (
                 'Sylvanian Families Beechwood Hall Gift Set Condition: NewSold by:Jadlam Toys & Models', '69.95')}),
        receipt_with_one_detail(
            {'total': '15.99',
             'description': (
                 'Sylvanian Families Chocolate Rabbit Family Sylvanian FamiliesSold by: Amazon EU S.a.r.L.',
                 '15.99')})))


def test_parse_amazon_order_2020_09_15(soup):
    beautiful_soup = soup("sample_html/amazon-order-2020-09-15.html")
    assert_that(calling(extract_receipts).with_args(datetime(2020, 9, 15), beautiful_soup),
                raises(NoReceiptsFoundException))


def test_parse_amazon_order_2020_09_28(soup):
    beautiful_soup = soup("sample_html/amazon-order-2020-09-28.html")
    assert_that(calling(extract_receipts).with_args(datetime(2020, 9, 28), beautiful_soup),
                raises(NoReceiptsFoundException))


def test_parse_amazon_order_2021_03_11_no_order_details(soup):
    beautiful_soup = soup("sample_html/amazon-order-2021-03-11-no-order-details.html")

    assert_that(calling(extract_receipts).with_args(datetime(2021, 3, 11), beautiful_soup),
                raises(NoReceiptsFoundException))


def test_parse_amazon_order_2021_11_24(soup):
    beautiful_soup = soup("sample_html/amazon-order-2021-11-24.html")
    receipts = extract_receipts(datetime(2021, 11, 24), beautiful_soup)

    assert_that(len(receipts), is_(1))
    assert_that(receipts[0],
                receipt_with_one_detail({'total': '28.98',
                                         'description': ('Moongiantgo Coffee Grinder Manual Compact & Effortless, '
                                                         'Stainless Steel & Glass, Adjustable Coarseness Ceramic Burr '
                                                         '- 5 Precise Levels, with Spoon & Brush | Make Fresh Coffee '
                                                         'Anytime & Anywhere Condition: NewSold by:Moongiantgo-Eu '
                                                         'Fulfilled by Amazon', '31.50')}))


def test_parse_amazon_order_2021_11_30(soup):
    beautiful_soup = soup("sample_html/amazon-order-2021-11-30.html")
    receipts = extract_receipts(datetime(2021, 11, 30), beautiful_soup)

    assert_that(receipts[0],
                receipt_with_one_detail({'total': "8.99",
                                         'description': (
                                             'Gukasxi Tabletop Christmas Tree,Mini Artificial Christmas Pine Trees '
                                             'with Plastic Base Season Ornaments Tabletop Trees for Xmas Holiday Party '
                                             'Home Decor,with 2M String Lights and Ornaments Condition: NewSold '
                                             'by:Feng_x Fulfilled by Amazon',
                                             '8.99')}))


def test_parse_amazon_order_2021_11_24_multiple(soup):
    beautiful_soup = soup("sample_html/amazon-order-2021-11-24-multiple.html")
    receipts = extract_receipts(datetime(2021, 11, 24), beautiful_soup)

    assert_that(len(receipts), is_(2))

    assert_that(receipts, contains_inanyorder(
        receipt_with_one_detail(
            {'total': '3.99', 'description': (
                'Chrome 1/2" BSP Thread Female Blanking End Cap Radiator Chrome Plug Water Pipe '
                'Condition: NewSold by:Stevenson Plumbing and Electrical Supplies', '3.99')}),
        receipt_with_one_detail(
            {'total': '7.29', 'description': (
                'Metal Adaptor Reduction Water Faucet Tap 24mm Male to 1/2" BSP Male Joiner '
                'Condition: NewSold by:plumbing4home',
                '7.29')})))
