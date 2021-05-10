from bs4 import BeautifulSoup
from hamcrest.core.base_matcher import BaseMatcher, T
from hamcrest.core.description import Description
from hamcrest.core.matcher import Matcher
from hamcrest.core.string_description import StringDescription


class _(object):
    def __init__(self, matcher: Matcher) -> None:
        super().__init__()
        self.matcher = matcher

    def __eq__(self, o: object) -> bool:
        return self.matcher.matches(o, StringDescription())

    def __ne__(self, o: object) -> bool:
        return not __eq__(o)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        description = StringDescription()
        self.matcher.describe_to(description)
        return description.__str__()


def beautiful_soup_containing_text(text: str) -> BaseMatcher[BeautifulSoup]:
    class BeautifulSoupWithText(BaseMatcher[BeautifulSoup]):
        def __init__(self) -> None:
            super().__init__()
            self._text = text

        def _matches(self, item: T) -> bool:
            return self._text in item.get_text()

        def describe_to(self, description: Description) -> None:
            description.append_description_of("BeautifulSoup text containing {}".format(self._text))

    return BeautifulSoupWithText()

