from datetime import datetime

from beancount.core.data import Amount, D
from hamcrest import assert_that, calling, raises, is_
from hamcrest.core.base_matcher import BaseMatcher, T
from hamcrest.core.description import Description
from hamcrest.library.collection import contains_inanyorder

from beancount_gmail.receipt import Receipt, NoReceiptsFoundException
from beancount_gmail.uk_amazon_email.parsing import extract_receipts
from test.test_receipt import assert_receipt_with_one_detail


def test_parse_amazon_order_2018_02_10(soup):
    beautiful_soup = soup("sample_html/amazon-order-2018-02-10.html")
    receipts = extract_receipts(datetime(2018, 2, 10), beautiful_soup)

    assert_receipt_with_one_detail(receipts[0],
                                   "21.20",
                                   "Forthglade 100% Natural Complete Meal Senior Dog Pet Food Chicken, Brown Rice & "
                                   "Vegetables 395g (18 Pack) Sold by Amazon EU S.a.r.L.",
                                   "21.20")


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

    assert_receipt_with_one_detail(receipts[0],
                                   "28.98",
                                   "Moongiantgo Coffee Grinder Manual Compact & Effortless, Stainless Steel & Glass, "
                                   "Adjustable Coarseness Ceramic Burr - 5 Precise Levels, with Spoon & Brush | Make "
                                   "Fresh Coffee Anytime & Anywhere Condition: NewSold by:Moongiantgo-Eu Fulfilled "
                                   "by Amazon",
                                   "31.50")


def receipt_with_one_detail(param: dict):
    class ReceiptWithDetailMatcher(BaseMatcher):
        def _matches(self, item: T) -> bool:
            if not isinstance(item, Receipt):
                return False

            if Amount(D(param['total']), "GBP") != item.total:
                return False

            if param['description'][0] != item.receipt_details[0][0]:
                return False

            if Amount(D(param['description'][1]), "GBP") != item.receipt_details[0][1]:
                return False

            return True

        def describe_to(self, description: Description) -> None:
            description.append_text(
                "Receipt with description {} and total {}".format(param['description'], param['total']))

    return ReceiptWithDetailMatcher()


def test_parse_amazon_order_2021_11_30(soup):
    beautiful_soup = soup("sample_html/amazon-order-2021-11-30.html")
    receipts = extract_receipts(datetime(2021, 11, 30), beautiful_soup)

    assert_receipt_with_one_detail(receipts[0],
                                   "8.99",
                                   "Gukasxi Tabletop Christmas Tree,Mini Artificial Christmas Pine Trees with "
                                   "Plastic Base Season Ornaments Tabletop Trees for Xmas Holiday Party Home "
                                   "Decor,with 2M String Lights and Ornaments Condition: NewSold by:Feng_x Fulfilled "
                                   "by Amazon",
                                   "8.99")


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
