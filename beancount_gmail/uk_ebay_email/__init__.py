from datetime import datetime

from bs4 import BeautifulSoup

from beancount_gmail.email_parser_protocol import EmailParser
from beancount_gmail.receipt import Receipt
from beancount_gmail.uk_ebay_email.parsing import extract_receipt


class UKeBayParser(EmailParser):
    def extract_receipts(self, message_date: datetime, soup: BeautifulSoup) -> list[Receipt]:
        return [extract_receipt(message_date, soup)]

    def search_query(self):
        return 'from:ebay@ebay.com'
