from datetime import datetime

import bs4

from beancount_gmail.common.parsing import extract_row_text
from beancount_gmail.receipt import Receipt, TOTAL


def extract_receipts(message_date: datetime, beautiful_soup: bs4.BeautifulSoup) -> list[Receipt]:
    table_text = [extract_row_text(table) for table in beautiful_soup.find_all('table')
                  if table.find('table') is None]

    return [Receipt(message_date,
                    [(table_text[6][1], "{} GBP".format(table_text[6][2]))],
                    [(TOTAL, "{} GBP".format(table_text[4][1]))])]