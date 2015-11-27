# coding: utf-8
"""Model for a postage option."""

from __future__ import unicode_literals

import collections

_PostageOption = collections.namedtuple(
    "PostageOption",
    [
        "name",
        "slug",
        "price",
        "description",
        "needs_address"
    ]
)


class PostageOption(_PostageOption):
    """Namedtuple model for postage options.

    Attributes:
        name: (str) Human readable name for the postage option.
        slug: (str) Machine readable slug for the postage option.
        price: (int) Price for the postage in pence.
        description: (str) A longer description of how the postage will work.
        needs_address: (bool) Whether this postage option needs an address to be
            entered.
    """

    @property
    def price_pounds(self):
        """Return the price in pounds.pence format."""
        price = '{0:03d}'.format(self.price)
        return price[:-2] + '.' + price[-2:]
