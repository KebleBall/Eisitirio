# coding: utf-8
"""Logic for interacting with Realex."""

from __future__ import unicode_literals

import datetime
import json
import hashlib

from flask.ext import login
import flask
import requests

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models

APP = app.APP
DB = db.DB

class SHA1CheckError(Exception):
    """Risen on SHA1hashes mismatch """

    def __str__(self):
        return "SHA1 for response does not match %s" % self.args[0]


class PostDictKeyError(Exception):
    """Risen when required key is missing from post data"""

    def __str__(self):
        return "PostDictKeyError: %s must be present in POST_DATA" % \
            self.args[0]

class RealexForm(object):
    """Should be overwritten with values required by realex api."""

    def __init__(self, transaction, currency='GBP', data=None, form_attr=None,
                 fields_attr=None, order_id=None, **kw):
        """Creates an instance of form with data for payment request.
        - currency and amount are requires parameters if you want to create the
          form and attach it in the html.
        - data is required if you want to do a validation of realex response


        :param str currency: One of currencies supported by realex. For
                             full list see
        :param amount: Exact amount to be billed to the user
        :type amount: string, float, decimal, int
        :param dict data: POST data for validation (returned by from Realex)
        :param dict form_attr: Extra attributes to be attached to the form,
                               example:
                                   form_attr = {"class": "fancy_form graybg"}
        :param dict fields_attr: Extra attributes to be attached to fields,
                                 example:
                                    fields = {
                                        "merchant_id": {
                                            "class": "nice_merchant id",
                                            "id": "merchantid"}
                                        "currency": {
                                            "class": "currency_sign",
                                            "style": "color:red;"}
                                        }
        :param str order_id: Optional order id to be used for the payment,
                             if not specified, will be generated using
                             following format:
                                order_id = "<current datetime>-<last four
                                            characters of uuid4 hex>"
        :param kw: Any other values that should be sent with the request to
                   Realex
        """
        if data:
            self.data = data
            return

        amount = '%i' % (transaction.value)

        self.form_attr = form_attr
        self.fields_attr = fields_attr

        # setting values required by Realex
        assert all([currency, amount])
        self.fields = dict()
        self.fields['currency'] = currency
        self.fields['amount'] = amount
        #self.fields['account'] = 'internet'
        self.fields['timestamp'] = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        uid = "%i" % (transaction.user_id)
        self.fields['order_id'] = "%i-%s-%s" % (transaction.object_id, self.fields['timestamp'], uid)
        # hash fields
        self.sha1hash = hashlib.sha1(".".join([self.fields['timestamp'],
                                               APP.config['REALEX_MERCHANT_ID'],
                                               self.fields['order_id'],
                                               self.fields['amount'],
                                               self.fields['currency']]))
        # sign fields hash with secret and create new hash
        self.fields['sha1hash'] = hashlib.sha1(".".join([
            self.sha1hash.hexdigest(), APP.config['REALEX_SECRET']])).hexdigest()
        self.fields['auto_settle_flag'] = 1

        # setting additional values that will be returned to you
        for k, v in kw.items():
            if k not in self.fields:
                self.fields[k] = v

    def as_form(self):
        """Renders the form along with all of it's values."""
        form_attr = self.form_attr or dict()
        form_init = {"action": APP.config['REALEX_ENDPOINT_URL'], "method": "POST"}
        form_attr.update(form_init)
        form_str = "<form %s >\n" % (" ".join(["%s='%s'" % (k, v)
                                               for k, v in form_attr.items()]))
        form_str = "%s %s \n" \
                   "<input type='submit' value='Proceed to secure server' class='button large expanded'/>" \
                   "</form>" % (form_str, self.as_fields())
        return (self.fields['order_id'], form_str)

    def as_fields(self):
        """Renders only the fields without the enclosing form tag."""
        fields_str = ""
        fields = self.fields_attr or dict()
        all_fields = {
            'merchant_id': APP.config['REALEX_MERCHANT_ID']
        }
        all_fields['merchant_response_url'] = APP.config['REALEX_RESPONSE_URL']
        all_fields.update(self.fields)
        for k, v in all_fields.items():
            field_init = {"name": k.upper(), "value": v, "type": "hidden"}
            field_data = fields.get(k, {})
            field_data.update(field_init)
            fields_str = "%s<input " % fields_str
            prepare_extras = " ".join(["%s='%s'" % (x, z)
                                       for x, z in field_data.items()])
            fields_str = "%s %s />\n" % (fields_str, prepare_extras)
        return fields_str

    def is_valid(self):
        """Validates the response from realex. Raises an exception if
        validation fails. If validation is successful it will set the
        cleaned_data attr on self.

        :raises SHA1CheckError: in case if sha1 generated for the response
                                doesn't match the sha1 returned by realex
        :raises PostDictKeyError: for any missing key that is required in the
                                  post response from realex
        """
        required_in_post = ["TIMESTAMP", "MERCHANT_ID", "ORDER_ID", "RESULT",
                            "MESSAGE", "PASREF", "AUTHCODE", "SHA1HASH"]

        for item in required_in_post:
            if item not in self.data.keys():
                raise PostDictKeyError(item)

        required_in_post.remove("SHA1HASH")

        sha1hash = hashlib.sha1(".".join([self.data[x]
                                          for x in required_in_post]))
        sha1hash = hashlib.sha1("%s.%s" % (sha1hash.hexdigest(),
                                           APP.config['REALEX_SECRET']))

        if sha1hash.hexdigest() != self.data["SHA1HASH"]:
            raise SHA1CheckError("%s != %s" % (sha1hash.hexdigest(),
                                               self.data["SHA1HASH"]))

        data = dict((k.lower(), v) for k, v in self.data.items())
        setattr(self, 'cleaned_data', data)


def generate_payment_form(transaction):
    form = RealexForm(transaction=transaction)

    (order_id, form_str) = form.as_form()

    transaction.eway_transaction = models.EwayTransaction(
        order_id,
        transaction.value
    )

    DB.session.commit()

    APP.log_manager.log_event(
        'Started Card Payment',
        tickets=transaction.tickets,
        user=login.current_user,
        transaction=transaction
    )

    return form_str

def get_transaction_id(str):
    return int(str.split('-')[0])

def process_payment(request):

    if 'ORDER_ID' not in request.form:
        flask.flash(
            (
                'There was a problem with our payment provider, '
                'please contact <a href="{0}">the treasurer</a> '
                'to confirm that payment has not been taken before trying again'
            ).format(
                APP.config['TREASURER_EMAIL_LINK'],
            ),
            'warning'
        )
        APP.log_manager.log_event(
            'Error processing payment: ORDER_ID not in POST request.'
        )
        return None

    transaction = models.Transaction.get_by_id(
        get_transaction_id(request.form['ORDER_ID'])
    )

    if transaction is None:
        flask.flash(
            (
                'There was a problem with our payment provider, '
                'please contact <a href="{0}">the treasurer</a> '
                'to confirm that payment has not been taken before trying again'
            ).format(
                APP.config['TREASURER_EMAIL_LINK'],
            ),
            'warning'
        )
        APP.log_manager.log_event(
            (
                'Error processing payment: unable to find transaction in database.'
                ' ORDER_ID was {0}'
            ).format(
                request.form['ORDER_ID']
            )
        )

        return None

    form = RealexForm(transaction=transaction, data=request.form)

    # Path 1: SHA1HASH check does not match
    try:
        form.is_valid()
    except SHA1CheckError as exc:
        APP.log_manager.log_event(
            'Suspicious Response from Realex: SHA1HASH does not match.',
            transaction=transaction
        )

        flask.flash(
            (
                'There is a possible problem with our payment provider, '
                'please contact <a href="{0}">the treasurer</a> '
                'to confirm that payment has not been taken before trying again'
            ).format(
                APP.config['TREASURER_EMAIL_LINK'],
            ),
            'warning'
        )
        return None

    realex_transaction = transaction.eway_transaction
    realex_transaction.completed = datetime.datetime.utcnow()
    # Stored result codes are only of length two
    realex_transaction.result_code = request.form['RESULT'][:2]
    realex_transaction.charged = int(request.form['AMOUNT'])
    realex_transaction.eway_id = request.form['PASREF']

    DB.session.commit()

    # Good payment
    if realex_transaction.status[0]:

        transaction.mark_as_paid()

        APP.log_manager.log_event(
            'Completed Card Payment',
            tickets=transaction.tickets,
            user=transaction.user,
            transaction=transaction,
            in_app=True
        )
        return realex_transaction
    else: # Invalid Realex payment
        APP.log_manager.log_event(
            'Failed Card Payment',
            tickets=transaction.tickets,
            user=transaction.user,
            transaction=transaction,
            in_app=True
        )

        flask.flash(
            (
                'The card payment failed. You have not been charged. Please make '
                'sure you have enough money in your account, or try a different card.'
            ),
            'error'
        )
        return None

## def _send_request(endpoint, data, transaction):
##     """Helper to send requests to the eWay API.
##
##     Formats the data payload, sets up authorisation headers, and sends the
##     request to the eWay API.
##
##     Args:
##         endpoint: (str) the API endpoint to send the request to
##         data: (dict or None) a dictionary of data to serialise and send to
##             eWay
##
##     Returns:
##         (bool, dict) whether the request was successful, and any data
##         returned by the API
##     """
##     url = APP.config['REALEX_ENDPOINT_URL']
##     payload = json.dumps(data)
##     headers = { 'Content-Type': 'application/json' }
##
##     try:
##         request = requests.post(url, data=payload, headers=headers)
##     except requests.ConnectionError as exc:
##         APP.log_manager.log_event(
##             'Failed request to Realex endpoint {0} with error {1}'.format(
##                 endpoint,
##                 exc
##             ),
##             transaction=transaction
##         )
##         return (False, None)
##
##     if request.status_code == 200 or request.status_code == 302:
##         return (True, request.json())
##     else:
##         APP.log_manager.log_event(
##             (
##                 'Failed request to Realex endpoint {0} returning status {1}'
##             ).format(
##                 endpoint,
##                 request.status_code
##             ),
##             transaction=transaction
##         )
##         return (False, None)
##
## def get_payment_url(transaction):
##     """Get a URL for the payment gateway.
##
##     Sends a request to eWay with the users information and transaction
##     amount, and returns the URL generated by eWay that the user should be
##     redirected to to carry out payment.
##
##     Returns:
##         (str) What URL the user should be redirected to to carry out payment
##     """
##     timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
##     order_id = '%s-%s' %(timestamp, transaction.user.object_id)
##     first_data_hash = hashlib.sha1(".".join([timestamp, APP.config['REALEX_MERCHANT_ID'],
##                                              order_id, transaction.value, currency]))
##
##     final_sha1_hash = hashlib.sha1(".".join([
##         first_data_hash.hexdigest(), config['REALEX_SECRET']])).hexdigest()
##
##
##     data = {
##         'TIMESTAMP' : timestamp,
##         'MERCHANT_ID' : APP.config['REALEX_MERCHANT_ID'],
##         'ORDER_ID' : order_id,
##         'AMOUNT' : transaction.value,
##         'CURRENCY' : 'GBP',
##         'SHA1HASH' : final_sha1_hash,
##         'AUTO_SETTLE_FLAG' : 1,
##         'RESPONSE_URL' : APP.config['REALEX_RESPONSE_URL']
##     }
##
##     (success, response) = _send_request(None, data, transaction)
##
##     #############
##
##     if success and response['Errors'] is None:
##         transaction.eway_transaction = models.EwayTransaction(
##             response['AccessCode'],
##             transaction.value
##         )
##         DB.session.commit()
##
##         APP.log_manager.log_event(
##             'Started Card Payment',
##             tickets=transaction.tickets,
##             user=login.current_user,
##             transaction=transaction
##         )
##
##         return response['Location']
##     else:
##         flask.flash(
##             (
##                 'There is a problem with our payment provider, please '
##                 'try again later'
##             ),
##             'error'
##         )
##         return None
##
## def process_payment(transaction, in_app=True, success_only=False):
##     """Check if the transaction has been completed, and update the database.
##
##     Intended to be called by the eWay callback, queries the eWay API for the
##     result of the transaction (whether payment was completed) and updates
##     the persisted state of this transaction object and related ticket
##     objects.
##
##     Can also be called interactively or scripted, to allow checking if
##     transactions have been completed. In this case, |in_app| should be false (to
##     prevent trying to use flask.flash outside of the request context), and
##     |success_only| should be True - the function will only commit to the
##     database if the transaction is considered successful (to deal with eWay
##     returning a 05 Transaction Failure code for incomplete transactions).
##     """
##     if in_app:
##         flash = flask.flash
##     else:
##         def flash(*_, **unused):
##             """Use a dummy flash function to avoid using the request context."""
##             pass
##
##     eway = transaction.eway_transaction
##
##     data = {'AccessCode': eway.access_code}
##
##     (success, response) = _send_request('GetAccessCodeResult', data,
##                                         transaction)
##
##     if success:
##         eway.completed = datetime.datetime.utcnow()
##         eway.result_code = response['ResponseCode']
##         eway.eway_id = response['TransactionID']
##         eway.charged = response['TotalAmount']
##
##         if success_only and not eway.status[0]:
##             DB.session.rollback()
##             return None
##         else:
##             DB.session.commit()
##
##         if eway.status[0]:
##             if eway.result_code == '10':
##                 APP.log_manager.log_event(
##                     (
##                         'Partial eWay payment for transaction {0} '
##                         'with value {1}'
##                     ).format(
##                         transaction.object_id,
##                         response['TotalAmount']
##                     ),
##                     tickets=transaction.tickets,
##                     user=transaction.user,
##                     transaction=transaction,
##                     in_app=in_app
##                 )
##
##                 refund_success = process_refund(transaction,
##                                                 response['TotalAmount'],
##                                                 in_app)
##
##                 if refund_success:
##                     flash(
##                         (
##                             'Your card payment was only authorised '
##                             'for a partial amount, and has '
##                             'subsequently been automatically '
##                             'reversed. Please check that you have '
##                             'enough available funds in your account, '
##                             'and then attempt payment again. If in '
##                             'doubt, pay for your tickets one-by-one '
##                             'to limit the value of the individual '
##                             'transactions.'
##                         ),
##                         'warning'
##                     )
##                 else:
##                     APP.email_manager.send_template(
##                         [
##                             APP.config['TREASURER_EMAIL'],
##                             APP.config['TICKETS_EMAIL']
##                         ],
##                         'Partial Ticket Payment',
##                         'partial_payment.email',
##                         transaction=transaction,
##                         ewayresponse=response
##                     )
##                     flash(
##                         (
##                             'Your card payment was only approved for '
##                             'a partial amount. An email has been '
##                             'sent to {0} staff, and the '
##                             'partial payment will be reversed. After '
##                             'this, you will be contacted via email, '
##                             'and you should then reattempt payment. '
##                             'Please check that you have enough '
##                             'available funds in your account to '
##                             'complete payment for the full amount, '
##                             'and that you have no transaction '
##                             'limits. If in doubt, please pay for '
##                             'your tickets one-by-one.'
##                         ).format(
##                             APP.config['BALL_NAME']
##                         ),
##                         'warning'
##                     )
##             else:
##                 transaction.mark_as_paid()
##
##                 DB.session.commit()
##
##                 APP.log_manager.log_event(
##                     'Completed Card Payment',
##                     tickets=transaction.tickets,
##                     user=transaction.user,
##                     transaction=transaction,
##                     in_app=in_app
##                 )
##
##                 flash(
##                     'Your payment has completed successfully',
##                     'success'
##                 )
##         else:
##             flash(
##                 'The card payment failed. You have not been charged.',
##                 'error'
##             )
##
##         return eway.status[0]
##     else:
##         flash(
##             (
##                 'There is a problem with our payment provider, '
##                 'please contact <a href="{0}">the treasurer</a> '
##                 'giving reference "Trans{1:05d}" to confirm that '
##                 'payment has not been taken before trying again'
##             ).format(
##                 APP.config['TREASURER_EMAIL_LINK'],
##                 transaction.object_id
##             ),
##             'error'
##         )
##         return None
##
## def cancel_payment(transaction):
##     """Mark the payment as cancelled."""
##     transaction.eway_transaction.completed = datetime.datetime.utcnow()
##     transaction.eway_transaction.result_code = 'CX'
##
##     flask.flash(
##         'Your payment has been cancelled; you have not been charged.',
##         'info'
##     )
##
##     DB.session.commit()
##
##     APP.log_manager.log_event(
##         'Cancelled Card Payment',
##         tickets=transaction.tickets,
##         user=transaction.user,
##         transaction=transaction
##     )
##
## def process_refund(transaction, amount, in_app=True):
##     """Refund some amount of money to the customer.
##
##     Sends a request to the eWay API requesting that the given amount is
##     refunded back to the customers card.
##
##     Args:
##         amount: (int) amount to refund in pence
##
##     Returns:
##         (bool) whether the refund was successful
##     """
##     eway = transaction.eway_transaction
##
##     data = {
##         'Refund': {
##             'TotalAmount': amount,
##             'TransactionID': eway.eway_id
##         }
##     }
##
##     (success, response) = _send_request('DirectRefund', data, transaction)
##
##     if success and response['TransactionStatus']:
##         refunded_amount = response['Refund']['TotalAmount']
##
##         eway.refunded += refunded_amount
##         DB.session.commit()
##
##         APP.log_manager.log_event(
##             'Refunded £{0:.02f}'.format(
##                 refunded_amount / 100.0
##             ),
##             user=login.current_user,
##             transaction=transaction,
##             in_app=in_app
##         )
##
##         if refunded_amount != amount:
##             APP.email_manager.send_template(
##                 [
##                     APP.config['TREASURER_EMAIL'],
##                     APP.config['TICKETS_EMAIL']
##                 ],
##                 'Partial Refund',
##                 'partial_refund.email',
##                 transaction=transaction,
##                 ewayresponse=response
##             )
##
##             if in_app:
##                 flask.flash(
##                     (
##                         'Your card refund was only approved for a partial '
##                         'amount. An email has been sent to {0} staff, and the '
##                         'refund will be manually completed.'
##                     ).format(
##                         APP.config['BALL_NAME']
##                     ),
##                     'warning'
##                 )
##
##         return True
##     else:
##         APP.log_manager.log_purchase('warning', str(response))
##         return False
