from decimal import Decimal
import re

from money import Money


MONEY = re.compile(r"(-?\d{1,3}(?:,\d{3})*\.\d{2}) ([A-Z]{3})")


def money_string_to_decimal(string):
    match = MONEY.search(string)
    if not match:
        raise Exception("No money value found in string \"%s\" to convert to decimal" % string)
    return Money(Decimal(match.group(1)), match.group(2))
