# coding: utf-8
'''
email_manager.py

Contains Emailer class to aid with sending emails from templates
'''

import smtplib
from jinja2 import Environment, PackageLoader
import atexit
from email.mime.text import MIMEText

class EmailManager:
    def __init__(self, app):
        self.app = app

        app.emailer = self

        self.log = app.log_manager.log_email

        self.smtp = None

        self.jinjaenv = None

        atexit.register(self.shutdown)

    def smtp_connect(self):
        if self.app.config['SMTP_SSL']:
            self.smtp = smtplib.SMTP_SSL(self.app.config['SMTP_HOST'],
                                         self.app.config['SMTP_PORT'])
        else:
            self.smtp = smtplib.SMTP(self.app.config['SMTP_HOST'],
                                     self.app.config['SMTP_PORT'])

        if self.app.config['SMTP_LOGIN']:

            try:
                self.smtp.login(self.app.config['SMTP_USER'],
                                self.app.config['SMTP_PASSWORD'])
            except smtplib.SMTPHeloError as e:
                self.log(
                    'error',
                    (
                        'SMTP server at {0} did not reply properly to HELO at '
                        'login'
                    ).format(
                        self.app.config['SMTP_HOST']
                    )
                )
            except smtplib.SMTPAuthenticationError as e:
                self.log(
                    'error',
                    (
                        'SMTP server at {0} did accept the username/password.'
                    ).format(
                        self.app.config['SMTP_HOST']
                    )
                )
            except smtplib.SMTPException as e:
                self.log(
                    'error',
                    (
                        'No suitable authentication method found for SMTP '
                        'server at {0}'
                    ).format(
                        self.app.config['SMTP_HOST']
                    )
                )

    def smtp_open(self):
        try:
            status = self.smtp.noop()[0]
        except:  # smtplib.SMTPServerDisconnected
            status = -1
        return True if status == 250 else False

    def get_template(self, template):
        if self.jinjaenv is None:
            self.jinjaenv = Environment(
                loader=PackageLoader(
                    'kebleball',
                    'templates/emails'
                )
            )

        return self.jinjaenv.get_template(template)

    def sendTemplate(self, to, subject, template, **kwargs):
        template = self.get_template(template)

        try:
            msgfrom = kwargs['email_from']
        except KeyError:
            msgfrom = self.app.config['EMAIL_FROM']

        self.sendText(
            to,
            subject,
            template.render(**kwargs),
            msgfrom
        )

    def sendText(self, to, subject, text, msgfrom=None):
        if msgfrom is None:
            msgfrom = self.app.config['EMAIL_FROM']

        msg = MIMEText(
            text,
            'plain',
            'utf-8'
        )

        msg['Subject'] = ("[Keble Ball] - " + subject)
        msg['From'] = msgfrom
        if isinstance(to, list):
            for email in to:
                msg['To'] = email
        else:
            msg['To'] = to

        self.sendMsg(msg)

    def sendMsg(self, msg):
        if not self.app.config['SEND_EMAILS']:
            self.log(
                'info',
                'Email not sent per application policy'
            )
            return

        if self.smtp is None or not self.smtp_open():
            self.smtp_connect()

        try:
            self.smtp.sendmail(msg['From'], msg.get_all('To'), msg.as_string())
        except smtplib.SMTPRecipientsRefused as e:
            self.log(
                'error',
                (
                    'SMTP server at {0} refused recipients {1} refused for '
                    'message with subject {2}'
                ).format(
                    self.app.config['SMTP_HOST'],
                    e.recipients,
                    msg['Subject']
                )
            )
        except smtplib.SMTPHeloError as e:
            self.log(
                'error',
                (
                    'SMTP server at {0} did not reply properly to HELO for '
                    'message with subject {1}'
                ).format(
                    self.app.config['SMTP_HOST'],
                    msg['Subject']
                )
            )
        except smtplib.SMTPSenderRefused as e:
            self.log(
                'error',
                (
                    'SMTP server at {0} did not allow sender {1} for '
                    'message with subject {2}'
                ).format(
                    self.app.config['SMTP_HOST'],
                    msg['From'],
                    msg['Subject']
                )
            )
        except smtplib.SMTPDataError as e:
            self.log(
                'error',
                (
                    'SMTP server at {0} responded with unexpected error code '
                    '{1} with error message {2} for message with subject {3}'
                ).format(
                    self.app.config['SMTP_HOST'],
                    e.smtp_code,
                    e.smtp_error,
                    msg['Subject']
                )
            )

    def shutdown(self):
        if self.smtp is not None and self.smtp_open():
            self.smtp.quit()
