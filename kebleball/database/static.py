# coding: utf-8
"""Helper module giving direct access to static constants declared with models.

The database models are defined in modules which sometimes include constants.
Because we have the separate |models| module for accessing the models together,
we have this module for accessing all the constants.
"""

from kebleball.database import affiliation
from kebleball.database import college

AFFILIATIONS = affiliation.AFFILIATIONS
COLLEGES = college.COLLEGES
