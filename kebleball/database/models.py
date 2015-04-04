# coding: utf-8
"""Helper module giving direct access to all the database models.

Because the modules containing the definition of each model are named for the
model, importing them tends to introduce name conflicts between the module and
variables/parameters containing instances of the model.

To avoid this, this module provides a quick way to access all the models with a
name that is less likely to conflict.
"""

# We make an exception to the usual rule of only importing modules here for
# neatness.

from kebleball.database.affiliation import Affiliation  # pylint: disable=unused-import
from kebleball.database.announcement import Announcement  # pylint: disable=unused-import
from kebleball.database.battels import Battels  # pylint: disable=unused-import
from kebleball.database.card_transaction import CardTransaction  # pylint: disable=unused-import
from kebleball.database.college import College  # pylint: disable=unused-import
from kebleball.database.log import Log  # pylint: disable=unused-import
from kebleball.database.statistic import Statistic  # pylint: disable=unused-import
from kebleball.database.ticket import Ticket  # pylint: disable=unused-import
from kebleball.database.user import User  # pylint: disable=unused-import
from kebleball.database.voucher import Voucher  # pylint: disable=unused-import
from kebleball.database.waiting import Waiting  # pylint: disable=unused-import
