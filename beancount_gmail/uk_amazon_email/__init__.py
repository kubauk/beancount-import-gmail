from datetime import datetime

from bs4 import BeautifulSoup

from beancount_gmail.email_parser_protocol import EmailParser
from beancount_gmail.receipt import Receipt


class UKAmazonParser(EmailParser):
    def extract_receipts(self, message_date: datetime, soup: BeautifulSoup) -> list[Receipt]:
        raise Exception

    def search_query(self) -> str:
        return r'"Your Amazon.co.uk order" auto-confirm@amazon.co.uk'
