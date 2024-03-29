import re

from bs4.element import Tag

import beancount_gmail.receipt as receipt
from beancount_gmail.common.parsing import extract_row_text
from beancount_gmail.uk_paypal_email.common_re import DONATION_DETAILS_RE, UUID_PATTERN


def contains_interesting_table(table_element: Tag) -> bool:
    stripped_text = table_element.get_text(u' ').strip()
    return receipt.contain_interesting_receipt_fields(stripped_text)


def _extract_donation_details(text: str) -> dict[str, str]:
    return DONATION_DETAILS_RE.search(text).groupdict()


def extract_receipt_details_from_donation(soup: Tag) -> list[list[list[str]]]:
    table = soup.find("table", {"id": re.compile(UUID_PATTERN)})
    donation_details = _extract_donation_details(table.get_text().replace(u"\xa0", " ").replace("\n", " "))
    receipt_details = [[receipt.DESCRIPTION, receipt.UNIT_PRICE, receipt.QUANTITY, receipt.AMOUNT],
                       [donation_details['Purpose'], '', '', donation_details['Donation']]]
    total_details = [["Total", donation_details['Total']]]
    return [receipt_details, total_details]


def post_process_for_alternate_format(receipt_table_data: list[list[str]]) -> list[list[list[str]]]:
    result = [[]]
    for row in receipt_table_data:
        if len(row) == 3:
            continue
        if len(row) == 4 and row[1] == '':
            if len(result) == 1:
                result.append([])
            result[1].append([row[2], row[3]])
        else:
            result[0].append(row)
    return result


def extract_receipt_data_from_tables(soup: Tag) -> list[list[list[str]]]:
    receipt_data = []
    for table in soup.find_all("table"):
        if table.find("table") is not None:
            continue
        if contains_interesting_table(table):
            receipt_table_data = []
            for row in table.find_all("tr"):
                if row.get_text().strip():
                    extracted_text = extract_row_text(row)
                    if len(extracted_text) == 2 or len(extracted_text) == 4:
                        receipt_table_data.append(extracted_text)
            receipt_data.extend(post_process_for_alternate_format(receipt_table_data))
    return receipt_data
