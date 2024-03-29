from datetime import datetime

from bs4 import BeautifulSoup

from beancount_gmail.email_parser_protocol import EmailParser
from beancount_gmail.receipt import Receipt
from beancount_gmail.uk_amazon_email.parsing import extract_receipts


class UKAmazonParser(EmailParser):
    def extract_receipts(self, message_date: datetime, soup: BeautifulSoup) -> list[Receipt]:
        return extract_receipts(message_date, soup)

    def search_query(self) -> str:
        return r'\'Your Amazon.co.uk order confirmation\' auto-confirm@amazon.co.uk'
