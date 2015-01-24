from decimal import Decimal
import re


MONEY = re.compile("-?\d{1,3}(?:,\d{3})*\.\d{2}")


def money_string_to_decimal(string):
    match = MONEY.search(string)
    if not match:
        raise Exception("No money value found in string \"%s\" to convert to decimal" % string)
    return Decimal(match.group(0))