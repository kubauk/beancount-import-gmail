from decimal import Decimal
import re

from money import Money


MONEY = re.compile(r"(-?\d{1,3}(?:,\d{3})*\.\d{2})\s+([A-Z]{3})")


def _negate(value, negate):
    return (-1 if negate else 1) * value


def money_string_to_decimal(string, negate=False):
    match = MONEY.search(string)
    if not match:
        raise Exception("No money value found in string \"%s\" to convert to decimal" % string)
    return _negate(Money(Decimal(match.group(1)), match.group(2)), negate)