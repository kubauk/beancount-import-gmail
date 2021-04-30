import re

from beancount.core.amount import Amount
from beancount.core.number import D

MONEY = re.compile(r"(-?\d{1,3}(?:,\d{3})*\.\d{2})\s+([A-Z]{3})")


def _negate(value: int, negate: bool) -> int:
    return (-1 if negate else 1) * value


def money_string_to_amount(string: str, negate: bool = False) -> Amount:
    match = MONEY.search(string)
    if not match:
        raise Exception("No money value found in string \"%s\" to convert to decimal" % string)
    return Amount(_negate(D(match.group(1)), negate), match.group(2))
