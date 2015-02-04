__author__ = 'picasso'


class Money(tuple):
    def __str__(self):
        return "%s %s" % (self[0], self[1])

    def __add__(self, y):
        return Money((self[0] + y[0], self[1]))