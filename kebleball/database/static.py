# coding: utf-8
"""Helper module giving direct access to static constants declared with models.

The database models are defined in modules which sometimes include constants.
Because we have the separate |models| module for accessing the models together,
we have this module for accessing all the constants.
"""

# We make an exception to the usual rule of only importing modules here for
# neatness.
#
# pylint: disable=unused-import

from kebleball.database.affiliation import AFFILIATIONS
from kebleball.database.college import COLLEGES
