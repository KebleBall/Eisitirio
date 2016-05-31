# coding: utf-8
"""Utility class to send SMS messages via SendLocal."""

from __future__ import unicode_literals

import logging

import requests
import jinja2

from eisitirio import app

APP = app.APP

LOG = logging.getLogger(__name__)

class SmsManager(object):
    """Utility class for sending SMS messages."""

    def __init__(self):
        self.jinjaenv = jinja2.Environment(
            loader=jinja2.PackageLoader(
                'eisitirio',
                'templates/sms'
            )
        )

    def send_template(self, recipient, template, **kwargs):
        """Send an SMS based on a template."""

        try:
            sender = kwargs['sender']
        except KeyError:
            sender = APP.config['SMS_SENDER']

        kwargs['template_config'] = {
            key: APP.config[key]
            for key in APP.config['TEMPLATE_CONFIG_KEYS']
        }

        return self.send_text(
            recipient,
            self.jinjaenv.get_template(template).render(**kwargs),
            sender
        )

    @staticmethod
    def send_text(recipient, content, sender):
        """Send an SMS."""

        post_data = {
            'apiKey': APP.config['SMS_API_KEY'],
            'sender': sender,
            'numbers': recipient.phone,
            'message': content,
        }

        response = requests.post(
            'http://api.txtlocal.com/send/',
            data=post_data
        )

        if response.status_code == requests.codes.ok:
            result = response.json()

            if 'errors' in result:
                for error in result['errors']:
                    LOG.error(
                        'SMS gateway error %s (%s) sending to %s (%s)',
                        error['code'],
                        error['message'],
                        recipient.phone,
                        recipient.identifier,
                    )
            elif 'warnings' in result:
                for warning in result['warnings']:
                    LOG.warning(
                        'SMS gateway warning %s (%s) sending to %s (%s)',
                        warning['code'],
                        warning['message'],
                        recipient.phone,
                        recipient.identifier,
                    )
            else:
                LOG.debug(
                    'Sent SMS to %s (%s)',
                    recipient.phone,
                    recipient.identifier,
                )
        else:
            LOG.error(
                'Failed sending SMS, request returned response %s',
                response.status_code
            )

