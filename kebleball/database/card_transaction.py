# coding: utf-8
"""
card-transaction.py

Contains CardTransaction class
Used to store data about card payments
"""

from kebleball.database import db
from kebleball.database.user import User
from datetime import datetime
from kebleball.app import app
from kebleball.helpers import generate_key
from flask import url_for, flash
from flask.ext.login import current_user

import re
import json
import requests

class CardTransaction(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    commenced = db.Column(db.DateTime(), nullable=False)
    completed = db.Column(db.DateTime(), nullable=True)
    accesscode = db.Column(db.String(200), nullable=True)
    resultcode = db.Column(db.String(2), nullable=True)
    ewayid = db.Column(db.Integer(), nullable=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )
    user = db.relationship(
        'User',
        backref=db.backref(
            'transactions',
            lazy='dynamic'
        )
    )

    def __init__(self, user, tickets):
        if hasattr(user, 'id'):
            self.user_id = user.id
        else:
            self.user_id = user

        self.tickets = tickets
        self.commenced = datetime.utcnow()

    def __repr__():
        status = self.getStatus()
        if status[0] is None:
            statusStr = 'Uncompleted'
        else:
            statusStr = 'Successful' if status[0] else 'Failed'

        return '<{0} CardTransaction: {1}, {2}'.format(
            statusStr,
            self.id,
            status[1]
        )

    def getValue(self):
        return sum([ticket.price for ticket in self.tickets])

    def getStatus(self):
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
            }[self.resultcode]
        except KeyError as e:
            return (False, 'Unknown response: {0}'.format(e.args[0]))

    def sendRequest(self, endpoint, data=None):
        url = app.config['EWAY_API_BASE'] + endpoint + '.json'
        payload = json.dumps(data)
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic {0}".format(
                app.config['EWAY_API_PASSCODE']
            )
        }

        r = requests.post(url, data=payload, headers=headers)

        if r.status_code == 200:
            return (True, r.json())
        else:
            app.log_manager.log_event(
                (
                    'Failed request to eWay endpoint {0} returning status {1}'
                ).format(
                    endpoint,
                    r.status_code
                ),
                None,
                None,
                self
            )
            return (False, None)

    def getEwayURL(self):
        data = {
            "Customer": {
              "Reference": "U{0:05d}".format(self.user.id),
              "FirstName": self.user.firstname,
              "LastName": self.user.surname
            },
            "Payment": {
              "TotalAmount": self.getValue(),
              "InvoiceReference": "Trans{0:05d}".format(self.id),
              "CurrencyCode": "GBP"
            },
            "RedirectUrl": url_for("purchase.ewaySuccess", id=self.id, _external=True),
            "CancelUrl": url_for("purchase.ewayCancel", id=self.id, _external=True),
            "Method": "ProcessPayment",
            "TransactionType": "Purchase",
            "LogoUrl": "https://www.kebleball.com/tickets/static/ewayhead.jpg",
            "HeaderText": "Keble Ball {0}".format(
                app.config['START_TIME'].strftime('%Y')
            ),
            "Language": "EN",
            "CustomerReadOnly": True
        }

        (success, response) = self.sendRequest('CreateAccessCodeShared', data)

        if success:
            self.accesscode = response['AccessCode']
            db.session.commit()

            app.log_manager.log_event(
                'Started Card Payment',
                self.tickets,
                current_user,
                self
            )

            return response['SharedPaymentUrl']
        else:
            flash(
                (
                    u'There is a problem with our payment provider, please '
                    u'try again later'
                ),
                'error'
            )
            return None

    def processEwayPayment(self):
        if self.accesscode is not None:
            data = {'AccessCode': self.accesscode}

            (success, response) = self.sendRequest('GetAccessCodeResult', data)

            if success:
                self.completed = datetime.utcnow()
                self.resultcode = response['ResponseCode']
                self.ewayid = response['TransactionID']
                db.session.commit()

                status = self.getStatus()

                if status[0]:
                    if self.resultcode == '10':
                        app.log_manager.log_event(
                            (
                                'Partial eWay payment for transaction {0} '
                                'with value {1}'
                            ).format(
                                self.id,
                                response['TotalAmount']
                            ),
                            self.tickets,
                            current_user,
                            self
                        )

                        data = {
                            "Refund": {
                                "TotalAmount": response['TotalAmount'],
                                "TransactionID": response['TransactionID']
                            }
                        }

                        (refundSuccess, refundResponse) = self.sendRequest(
                            'DirectRefund',
                            data
                        )

                        if refundSuccess:
                            self.refunded = response['TotalAmount']
                            db.session.commit()

                            flash(
                                (
                                    u'Your card payment was only authorised '
                                    u'for a partial amount, and has '
                                    u'subsequently been automatically '
                                    u'reversed. Please check that you have '
                                    u'enough available funds in your account, '
                                    u'and then attempt payment again. If in '
                                    u'doubt, pay for your tickets one-by-one '
                                    u'to limit the value of the individual '
                                    u'transactions.'
                                ),
                                'warning'
                            )
                        else:
                            app.email_manager.sendTemplate(
                                [
                                    app.config['TREASURER_EMAIL'],
                                    app.config['TICKETS_EMAIL']
                                ],
                                "Partial Ticket Payment",
                                "partialPayment.email",
                                transaction=self,
                                ewayresponse=response
                            )
                            flash(
                                (
                                    u'Your card payment was only approved for '
                                    u'a partial amount. An email has been '
                                    u'sent to Keble Ball staff, and the '
                                    u'partial payment will be reversed. After '
                                    u'this, you will be contacted via email, '
                                    u'and you should then reattempt payment. '
                                    u'Please check that you have enough '
                                    u'available funds in your account to '
                                    u'complete payment for the full amount, '
                                    u'and that you have no transaction '
                                    u'limits. If in doubt, please pay for '
                                    u'your tickets one-by-one.'
                                ),
                                'warning'
                            )
                    else:
                        for ticket in self.tickets:
                            ticket.markAsPaid(
                                'Card',
                                'Card Transaction {0}'.format(
                                    self.id
                                ),
                                transaction=self
                            )

                        db.session.commit()

                        app.log_manager.log_event(
                            'Completed Card Payment',
                            self.tickets,
                            current_user,
                            self
                        )

                        flash(
                            'Your payment has completed successfully',
                            'success'
                        )
                else:
                    flash(
                        'The card payment failed. You have not been charged.',
                        'error'
                    )

                return status[0]
            else:
                flash(
                    (
                        u'There is a problem with our payment provider, '
                        u'please contact <a href="{0}">the treasurer</a> '
                        u'giving reference "Trans{1:05d}" to confirm that '
                        u'payment has not been taken before trying again'
                    ).format(
                        app.config['TREASURER_EMAIL_LINK'],
                        self.id
                    ),
                    'error'
                )
                return None

    def cancelEwayPayment(self):
        self.completed = datetime.utcnow()
        self.resultcode = 'CX'

        flash(
            'Your payment has been cancelled; you have not been charged.',
            'info'
        )

        db.session.commit()

        app.log_manager.log_event(
            'Cancelled Card Payment',
            self.tickets,
            current_user,
            self
        )

    def processRefund(self, amount):
        data = {
            "Refund": {
                "TotalAmount": amount,
                "TransactionID": self.ewayid
            }
        }

        (success, response) = self.sendRequest(
            'DirectRefund',
            data
        )

        if success:
            self.refunded = amount
            db.session.commit()

            app.log_manager.log_event(
                'Refunded £{0:.02f}'.format(
                    amount / 100.0
                ),
                [],
                current_user,
                self
            )

            return True
        else:
            return False

    @staticmethod
    def get_by_id(id):
        return CardTransaction.query.filter(CardTransaction.id == id).first()