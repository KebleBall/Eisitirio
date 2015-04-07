# coding: utf-8
"""Helper to aid with sending emails."""

from __future__ import unicode_literals

from email.mime import text
import atexit
import smtplib

import jinja2

class EmailManager(object):
    """Helper for sending emails.

    Handles connecting to the SMTP server, formatting emails, rendering emails
    from templates and sending emails.
    """
    def __init__(self, app):
        self.default_email_from = app.config['EMAIL_FROM']
        self.smtp_host = app.config['SMTP_HOST']
        self.send_emails = app.config['SEND_EMAILS']

        app.email_manager = self

        self.log = app.log_manager.log_email

        self.smtp = None

        self.jinjaenv = None

        atexit.register(self.shutdown)

    def smtp_open(self):
        """Check if the cached connection to the SMTP server is valid."""
        try:
            status = self.smtp.noop()[0]
        except smtplib.SMTPServerDisconnected:
            status = -1
        return True if status == 250 else False

    def get_template(self, template):
        """Load a jinja template object.

        The template object is created by jinja loading a file, and is used for
        rendering the body of emails.

        Args:
            template: (str) the filename of a template located in the
                templates/emails folder
        """
        if self.jinjaenv is None:
            self.jinjaenv = jinja2.Environment(
                loader=jinja2.PackageLoader(
                    'kebleball',
                    'templates/emails'
                )
            )

        return self.jinjaenv.get_template(template)

    def send_template(self, to, subject, template, **kwargs):
        """Send an email based on a template.

        Args:
            to: (str) the email address of the recipient
            subject: (str) the subject line of the email to be sent
            template: (str) the filename of a template located in the
                templates/emails folder, to be rendered as the email body
            kwargs: if this contains an element under the |email_from| key, this
                is used as the sender of the email. Otherwise, all elements are
                passed to the template rendering as tempalte parameters.
        """
        template = self.get_template(template)

        try:
            email_from = kwargs['email_from']
        except KeyError:
            email_from = self.default_email_from

        self.send_text(
            to,
            subject,
            template.render(**kwargs),
            email_from
        )

    def send_text(self, to, subject, message_text, email_from=None):
        """Send an text email.

        Composes the email into a text.MIMEText object and passes it to the
        email sending routine.

        Args:
            to: (str) the email address of the recipient
            subject: (str) the subject line of the email to be sent
            text: (str) the body of the email
            email_from: (str or None) the reported sender of the email. If this
                is none, the default value from the application configuration is
                used.
        """
        if email_from is None:
            email_from = self.default_email_from

        message = text.MIMEText(
            message_text,
            'plain',
            'utf-8'
        )

        message['Subject'] = ('[Keble Ball] - ' + subject)
        message['From'] = email_from
        if isinstance(to, list):
            for email in to:
                message['To'] = email
        else:
            message['To'] = to

        self.send_message(message)

    def send_message(self, message):
        """Send a marked up email via SMTP.

        Takes a correctly formatted email object and sends it to the SMTP
        server. Handles sending failures and if email sending is disabled.

        Args:
            message: (text.MIMEText) A formatted email message.
        """
        if not self.send_emails:
            self.log(
                'info',
                'Email not sent per application policy'
            )
            return

        if self.smtp is None or not self.smtp_open():
            self.smtp = smtplib.SMTP(self.smtp_host)

        try:
            self.smtp.sendmail(message['From'],
                               message.get_all('To'),
                               message.as_string())
        except smtplib.SMTPRecipientsRefused as error:
            self.log(
                'error',
                (
                    'SMTP server at {0} refused recipients {1} refused for '
                    'message with subject {2}'
                ).format(
                    self.smtp_host,
                    error.recipients,
                    message['Subject']
                )
            )
        except smtplib.SMTPHeloError as _:
            self.log(
                'error',
                (
                    'SMTP server at {0} did not reply properly to HELO for '
                    'message with subject {1}'
                ).format(
                    self.smtp_host,
                    message['Subject']
                )
            )
        except smtplib.SMTPSenderRefused as _:
            self.log(
                'error',
                (
                    'SMTP server at {0} did not allow sender {1} for '
                    'message with subject {2}'
                ).format(
                    self.smtp_host,
                    message['From'],
                    message['Subject']
                )
            )
        except smtplib.SMTPDataError as error:
            self.log(
                'error',
                (
                    'SMTP server at {0} responded with unexpected error code '
                    '{1} with error message {2} for message with subject {3}'
                ).format(
                    self.smtp_host,
                    error.smtp_code,
                    error.smtp_error,
                    message['Subject']
                )
            )

    def shutdown(self):
        if self.smtp is not None and self.smtp_open():
            self.smtp.quit()
