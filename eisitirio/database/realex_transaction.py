# coding: utf-8
"""Database model for representing a Realex Transaction."""

from __future__ import unicode_literals

from eisitirio.database import db

DB = db.DB

REALEX_RESULT_CODES = {
    None :  (None, 'Transaction not completed'),
    '00' : (True, 'Transaction approved'),
    '1xx' : (False, 'Transaction failed. Try again or a different payment method'),
    '2xx' : (False, 'Bank error. Try again later'),
    '3xx' : (False, 'Payment provider error. Try again later'),
    '5xx' : (False, 'Malformed message'),
    '666' : (False, 'Account deactivated')
}

class RealexTransaction(DB.model):
  """Model for representing a Realex transtion."""
  __tablename__ = 'realex_transaction'


