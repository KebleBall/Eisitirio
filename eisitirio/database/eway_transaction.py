# coding: utf-8
"""Database model for representing an eWay Transaction."""

from __future__ import unicode_literals

from eisitirio.database import db

DB = db.DB

EWAY_RESULT_CODES = {
    None: (None, 'Transaction not completed'),
    '00': (True, 'Transaction Approved'),
    '01': (False, 'Refer to Issuer'),
    '02': (False, 'Refer to Issuer, special'),
    '03': (False, 'No Merchant'),
    '04': (False, 'Pick Up Card'),
    '05': (False, 'Do Not Honour'),
    '06': (False, 'Error'),
    '07': (False, 'Pick Up Card, Special'),
    '08': (True, 'Honour With Identification'),
    '09': (False, 'Request In Progress'),
    '10': (True, 'Approved For Partial Amount'),
    '11': (True, 'Approved, VIP'),
    '12': (False, 'Invalid Transaction'),
    '13': (False, 'Invalid Amount'),
    '14': (False, 'Invalid Card Number'),
    '15': (False, 'No Issuer'),
    '16': (True, 'Approved, Update Track 3'),
    '19': (False, 'Re-enter Last Transaction'),
    '21': (False, 'No Action Taken'),
    '22': (False, 'Suspected Malfunction'),
    '23': (False, 'Unacceptable Transaction Fee'),
    '25': (False, 'Unable to Locate Record On File'),
    '30': (False, 'Format Error'),
    '31': (False, 'Bank Not Supported By Switch'),
    '33': (False, 'Expired Card, Capture'),
    '34': (False, 'Suspected Fraud, Retain Card'),
    '35': (False, 'Card Acceptor, Contact Acquirer, Retain Card'),
    '36': (False, 'Restricted Card, Retain Card'),
    '37': (False, 'Contact Acquirer Security Department, Retain Card'),
    '38': (False, 'PIN Tries Exceeded, Capture'),
    '39': (False, 'No Credit Account'),
    '40': (False, 'Function Not Supported'),
    '41': (False, 'Lost Card'),
    '42': (False, 'No Universal Account'),
    '43': (False, 'Stolen Card'),
    '44': (False, 'No Investment Account'),
    '51': (False, 'Insufficient Funds'),
    '52': (False, 'No Cheque Account'),
    '53': (False, 'No Savings Account'),
    '54': (False, 'Expired Card'),
    '55': (False, 'Incorrect PIN'),
    '56': (False, 'No Card Record'),
    '57': (False, 'Function Not Permitted to Cardholder'),
    '58': (False, 'Function Not Permitted to Terminal'),
    '59': (False, 'Suspected Fraud'),
    '60': (False, 'Acceptor Contact Acquirer'),
    '61': (False, 'Exceeds Withdrawal Limit'),
    '62': (False, 'Restricted Card'),
    '63': (False, 'Security Violation'),
    '64': (False, 'Original Amount Incorrect'),
    '66': (False, 'Acceptor Contact Acquirer, Security'),
    '67': (False, 'Capture Card'),
    '75': (False, 'PIN Tries Exceeded'),
    '82': (False, 'CVV Validation Error'),
    '90': (False, 'Cutoff In Progress'),
    '91': (False, 'Card Issuer Unavailable'),
    '92': (False, 'Unable To Route Transaction'),
    '93': (False, 'Cannot Complete, Violation Of The Law'),
    '94': (False, 'Duplicate Transaction'),
    '96': (False, 'System Error'),
    'CX': (False, 'Customer Cancelled Transaction')
}

class EwayTransaction(DB.Model):
    """Model for representing an eWay Transaction."""
    __tablename__ = 'eway_transaction'

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
            return EWAY_RESULT_CODES[self.result_code]
        except KeyError as err:
            return (False, 'Unknown response: {0}'.format(err.args[0]))

    @property
    def success(self):
        """Get whether the transaction was completed successfully."""
        success = self.get_status()[0]
        if success is None:
            return 'Uncompleted'
        elif success:
            return 'Successful'
        else:
            return 'Unsuccessful'
