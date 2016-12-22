# coding: utf-8
"""Database model for representing an eWay Transaction."""

from __future__ import unicode_literals

from eisitirio.database import db

DB = db.DB

REALEX_RESULT_CODES = {
    None :  (None, 'Transaction not completed'),
    '0' : (True, 'Transaction approved'),
    '1' : (False, 'Transaction failed. Try again or a different payment method'),
    '2' : (False, 'Bank error. Try again later'),
    '3' : (False, 'Payment provider error. Try again later'),
    '5' : (False, 'Malformed message'),
    '6' : (False, 'Account deactivated')
}

class EwayTransaction(DB.Model):
    """Model for representing an eWay Transaction."""
    __tablename__ = 'eway_transaction'

    # This holds the order_id
    access_code = DB.Column(
        DB.Unicode(200),
        nullable=False
    )
    charged = DB.Column(
        DB.Integer(),
        nullable=False
    )

    completed = DB.Column(
        DB.DateTime(),
        nullable=True
    )
    result_code = DB.Column(
        DB.Unicode(2),
        nullable=True
    )
    # This holds the PASREF field for realex
    eway_id = DB.Column(
        DB.Integer(),
        nullable=True
    )
    refunded = DB.Column(
        DB.Integer(),
        nullable=False,
        default=0
    )

    def __init__(self, access_code, charged):
        self.access_code = access_code
        self.charged = charged

    @property
    def status(self):
        """Get a better representation of the status of this transaction.

        The eWay API returns statuses as 2 digit codes; this function provides
        a mapping from these codes to a boolean success value and associated
        explanation.

        Returns:
            (bool, str) pair of success value and explanation
        """
        try:
            return REALEX_RESULT_CODES[self.result_code[0]]
        except KeyError as err:
            return (False, 'Unknown response: {0}'.format(err.args[0]))

    @property
    def success(self):
        """Get whether the transaction was completed successfully."""
        success = self.status[0]
        if success is None:
            return 'Uncompleted'
        elif success:
            return 'Successful'
        else:
            return 'Unsuccessful'
