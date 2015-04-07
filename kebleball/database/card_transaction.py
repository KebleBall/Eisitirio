# coding: utf-8
"""Database model for information about Card Transactions performed via eWay."""

from __future__ import unicode_literals

import datetime
import json
import requests

from flask.ext import login
import flask

from kebleball import app
from kebleball.database import db

APP = app.APP
DB = db.DB

class CardTransaction(DB.Model):
    """Model for information about Card Transactions performed via eWay."""
    object_id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    commenced = DB.Column(
        DB.DateTime(),
        nullable=False
    )
    completed = DB.Column(
        DB.DateTime(),
        nullable=True
    )
    access_code = DB.Column(
        DB.Unicode(200),
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

    user_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable=False
    )
    user = DB.relationship(
        'User',
        backref=DB.backref(
            'transactions',
            lazy='dynamic'
        )
    )

    def __init__(self, user, tickets):
        if hasattr(user, 'object_id'):
            self.user_id = user.object_id
        else:
            self.user_id = user

        self.tickets = tickets
        self.commenced = datetime.datetime.utcnow()

    def __repr__(self):
        status = self.get_status()
        if status[0] is None:
            status_str = 'Uncompleted'
        else:
            status_str = 'Successful' if status[0] else 'Failed'

        return '<{0} CardTransaction: {1}, {2}'.format(
            status_str,
            self.object_id,
            status[1]
        )

    def get_value(self):
        """Get the total value of the transaction."""
        return sum([ticket.price for ticket in self.tickets])

    def get_status(self):
        """Get a better representation of the status of this transaction.

        The eWay API returns statuses as 2 digit codes; this function provides
        a mapping from these codes to a boolean success value and associated
        explanation.

        Returns:
            (bool, str) pair of success value and explanation
        """
        try:
            return {
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
                '37': (False,
                       'Contact Acquirer Security Department, Retain Card'),
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
            }[self.result_code]
        except KeyError as err:
            return (False, 'Unknown response: {0}'.format(err.args[0]))

    def get_success(self):
        """Get whether the transaction was completed successfully."""
        success = self.get_status()[0]
        if success is None:
            return 'Incomplete'
        elif success:
            return 'Successful'
        else:
            return 'Unsuccessful'

    def _send_request(self, endpoint, data=None):
        """Helper to send requests to the eWay API.

        Formats the data payload, sets up authorisation headers, and sends the
        request to the eWay API.

        Args:
            endpoint: (str) the API endpoint to send the request to
            data: (dict or None) a dictionary of data to serialise and send to
                eWay

        Returns:
            (bool, dict) whether the request was successful, and any data
            returned by the API
        """
        url = APP.config['EWAY_API_BASE'] + endpoint + '.json'
        payload = json.dumps(data)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic {0}'.format(
                APP.config['EWAY_API_PASSCODE']
            )
        }

        request = requests.post(url, data=payload, headers=headers)

        if request.status_code == 200:
            return (True, request.json())
        else:
            APP.log_manager.log_event(
                (
                    'Failed request to eWay endpoint {0} returning status {1}'
                ).format(
                    endpoint,
                    request.status_code
                ),
                [],
                None,
                self
            )
            return (False, None)

    def get_eway_url(self):
        """Get a URL for the payment gateway.

        Sends a request to eWay with the users information and transaction
        amount, and returns the URL generated by eWay that the user should be
        redirected to to carry out payment.

        Returns:
            (str) What URL the user should be redirected to to carry out payment
        """
        data = {
            'Customer': {
                'Reference': 'U{0:05d}'.format(self.user.object_id),
                'FirstName': self.user.forenames,
                'LastName': self.user.surname,
                'Email': self.user.email
            },
            'Payment': {
                'TotalAmount': self.get_value(),
                'InvoiceReference': 'Trans{0:05d}'.format(self.object_id),
                'CurrencyCode': 'GBP'
            },
            'RedirectUrl': flask.url_for('purchase.eway_success',
                                         object_id=self.object_id,
                                         _external=True),
            'CancelUrl': flask.url_for('purchase.eway_cancel',
                                       object_id=self.object_id,
                                       _external=True),
            'Method': 'ProcessPayment',
            'TransactionType': 'Purchase',
            'LogoUrl': 'https://www.kebleball.com/assets/building_big.jpg',
            'HeaderText': 'Keble Ball {0}'.format(
                APP.config['START_TIME'].strftime('%Y')
            ),
            'Language': 'EN',
            'CustomerReadOnly': True
        }

        (success, response) = self._send_request('CreateAccessCodeShared', data)

        if success:
            self.access_code = response['AccessCode']
            DB.session.commit()

            APP.log_manager.log_event(
                'Started Card Payment',
                self.tickets,
                login.current_user,
                self
            )

            return response['SharedPaymentUrl']
        else:
            flask.flash(
                (
                    'There is a problem with our payment provider, please '
                    'try again later'
                ),
                'error'
            )
            return None

    def process_eway_payment(self):
        """Check if the transaction has been completed, and update the database.

        Intended to be called by the eWay callback, queries the eWay API for the
        result of the transaction (whether payment was completed) and updates
        the persisted state of this transaction object and related ticket
        objects
        """
        if self.access_code is not None:
            data = {'AccessCode': self.access_code}

            (success, response) = self._send_request('GetAccessCodeResult',
                                                     data)

            if success:
                self.completed = datetime.datetime.utcnow()
                self.result_code = response['ResponseCode']
                self.eway_id = response['TransactionID']
                DB.session.commit()

                status = self.get_status()

                if status[0]:
                    if self.result_code == '10':
                        APP.log_manager.log_event(
                            (
                                'Partial eWay payment for transaction {0} '
                                'with value {1}'
                            ).format(
                                self.object_id,
                                response['TotalAmount']
                            ),
                            self.tickets,
                            login.current_user,
                            self
                        )

                        refund_success = self.process_refund(
                            response['TotalAmount'])

                        if refund_success:
                            flask.flash(
                                (
                                    'Your card payment was only authorised '
                                    'for a partial amount, and has '
                                    'subsequently been automatically '
                                    'reversed. Please check that you have '
                                    'enough available funds in your account, '
                                    'and then attempt payment again. If in '
                                    'doubt, pay for your tickets one-by-one '
                                    'to limit the value of the individual '
                                    'transactions.'
                                ),
                                'warning'
                            )
                        else:
                            APP.email_manager.send_template(
                                [
                                    APP.config['TREASURER_EMAIL'],
                                    APP.config['TICKETS_EMAIL']
                                ],
                                'Partial Ticket Payment',
                                'partial_payment.email',
                                transaction=self,
                                ewayresponse=response
                            )
                            flask.flash(
                                (
                                    'Your card payment was only approved for '
                                    'a partial amount. An email has been '
                                    'sent to Keble Ball staff, and the '
                                    'partial payment will be reversed. After '
                                    'this, you will be contacted via email, '
                                    'and you should then reattempt payment. '
                                    'Please check that you have enough '
                                    'available funds in your account to '
                                    'complete payment for the full amount, '
                                    'and that you have no transaction '
                                    'limits. If in doubt, please pay for '
                                    'your tickets one-by-one.'
                                ),
                                'warning'
                            )
                    else:
                        for ticket in self.tickets:
                            ticket.mark_as_paid(
                                'Card',
                                'Card Transaction {0}'.format(
                                    self.object_id
                                ),
                                transaction=self
                            )

                        DB.session.commit()

                        APP.log_manager.log_event(
                            'Completed Card Payment',
                            self.tickets,
                            self.user_id,
                            self
                        )

                        flask.flash(
                            'Your payment has completed successfully',
                            'success'
                        )
                else:
                    flask.flash(
                        'The card payment failed. You have not been charged.',
                        'error'
                    )

                return status[0]
            else:
                flask.flash(
                    (
                        'There is a problem with our payment provider, '
                        'please contact <a href="{0}">the treasurer</a> '
                        'giving reference "Trans{1:05d}" to confirm that '
                        'payment has not been taken before trying again'
                    ).format(
                        APP.config['TREASURER_EMAIL_LINK'],
                        self.object_id
                    ),
                    'error'
                )
                return None

    def cancel_eway_payment(self):
        """Mark the payment as cancelled."""
        self.completed = datetime.datetime.utcnow()
        self.result_code = 'CX'

        flask.flash(
            'Your payment has been cancelled; you have not been charged.',
            'info'
        )

        DB.session.commit()

        APP.log_manager.log_event(
            'Cancelled Card Payment',
            self.tickets,
            self.user_id,
            self
        )

    def process_refund(self, amount):
        """Refund some amount of money to the customer.

        Sends a request to the eWay API requesting that the given amount is
        refunded back to the customers card.

        Args:
            amount: (int) amount to refund in pence

        Returns:
            (bool) whether the refund was successful
        """
        data = {
            'Refund': {
                'TotalAmount': amount,
                'TransactionID': self.eway_id
            }
        }

        (success, response) = self._send_request(
            'DirectRefund',
            data
        )

        if success and response['TransactionStatus']:
            refunded_amount = response['Refund']['TotalAmount']

            self.refunded = self.refunded + refunded_amount
            DB.session.commit()

            APP.log_manager.log_event(
                'Refunded £{0:.02f}'.format(
                    refunded_amount / 100.0
                ),
                [],
                login.current_user,
                self
            )

            if refunded_amount != amount:
                APP.email_manager.send_template(
                    [
                        APP.config['TREASURER_EMAIL'],
                        APP.config['TICKETS_EMAIL']
                    ],
                    'Partial Refund',
                    'partial_refund.email',
                    transaction=self,
                    ewayresponse=response
                )
                flask.flash(
                    (
                        'Your card refund was only approved for '
                        'a partial amount. An email has been '
                        'sent to Keble Ball staff, and the '
                        'refund will be manually completed.'
                    ),
                    'warning'
                )

            return True
        else:
            APP.log_manager.log_purchase('warning', str(response))
            return False

    @staticmethod
    def get_by_id(object_id):
        """Get a card transaction object by its database ID."""
        transaction = CardTransaction.query.filter(
            CardTransaction.object_id == int(object_id)).first()

        if not transaction:
            return None

        return transaction
