import re


POSTAGE_AND_PACKAGING_RE = re.compile("Postage and packaging(?! .)")

DONATION_DETAILS_RE = re.compile(r"Donation amount:(?P<Donation>£\d+\.\d\d [A-Z]{3}) +"
                                 r"Total:(?P<Total>£\d+\.\d\d [A-Z]{3}) +"
                                 r"Purpose:(?P<Purpose>[ \S]+\S) +"
                                 r"Contributor:")

UUID_PATTERN = r"[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}"
