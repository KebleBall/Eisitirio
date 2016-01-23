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
#
# pylint: disable=unused-import

from eisitirio.database.affiliation import Affiliation
from eisitirio.database.announcement import Announcement
from eisitirio.database.battels import Battels
from eisitirio.database.battels_transaction import BattelsTransaction
from eisitirio.database.card_transaction import CardTransaction
from eisitirio.database.college import College
from eisitirio.database.eway_transaction import EwayTransaction
from eisitirio.database.group_purchase_request import GroupPurchaseRequest
from eisitirio.database.generic_transaction_item import GenericTransactionItem
from eisitirio.database.log import Log
from eisitirio.database.old_card_transaction import OldCardTransaction
from eisitirio.database.photo import Photo
from eisitirio.database.postage import Postage
from eisitirio.database.postage_transaction_item import PostageTransactionItem
from eisitirio.database.purchase_group import PurchaseGroup
from eisitirio.database.statistic import Statistic
from eisitirio.database.ticket import Ticket
from eisitirio.database.ticket_transaction_item import TicketTransactionItem
from eisitirio.database.transaction import DummyTransaction
from eisitirio.database.transaction import FreeTransaction
from eisitirio.database.transaction import Transaction
from eisitirio.database.user import User
from eisitirio.database.voucher import Voucher
from eisitirio.database.waiting import Waiting
