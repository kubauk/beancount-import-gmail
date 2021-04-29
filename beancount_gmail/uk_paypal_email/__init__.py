import re
from datetime import datetime

from bs4 import BeautifulSoup

from beancount_gmail import receipt as receipt
from beancount_gmail.email_parser_protocol import EmailParser
from beancount_gmail.receipt import Receipt
from beancount_gmail.uk_paypal_email.parsing import extract_receipt_details_from_donation, \
    extract_receipt_data_from_tables


class PayPalUKParser(EmailParser):
    def extract_receipts(self, message_date: datetime, soup: BeautifulSoup) -> list[Receipt]:
        receipt_data = extract_receipt_details_from_donation(soup) \
            if soup.title is not None and \
               soup.title.find(text=re.compile(r"Receipt for your donation", re.UNICODE)) is not None \
            else extract_receipt_data_from_tables(soup)

        receipts = []
        while len(receipt_data) > 0:
            receipt_details = [(detail[0], detail[3]) for detail in receipt_data.pop(0)[1:]]
            total_details = [(detail[0], detail[1]) for detail in receipt_data.pop(0) if len(detail) == 2]

            negate = soup.find(text=re.compile(".*refund .*", re.IGNORECASE)) is not None or \
                     soup.find(text=re.compile(".*You received a payment.*", re.IGNORECASE)) is not None

            receipts.append(receipt.Receipt(message_date, receipt_details, total_details, negate))

        if len(receipts) == 0:
            raise receipt.NoReceiptsFoundException("Did not find any receipts")

        return receipts