# coding: utf-8
"""Database model for an announcement sent to registered users."""

from __future__ import unicode_literals

from kebleball import app
from kebleball.database import db
from kebleball.database import user
import datetime

APP = app.APP
DB = db.DB

USER_ANNOUNCE_LINK = DB.Table(
    'user_announce_link',
    DB.Model.metadata,
    DB.Column(
        'user_id',
        DB.Integer,
        DB.ForeignKey('user.object_id')
    ),
    DB.Column(
        'announcement_id',
        DB.Integer,
        DB.ForeignKey('announcement.object_id')
    )
)

EMAIL_ANNOUNCE_LINK = DB.Table(
    'email_announce_link',
    DB.Model.metadata,
    DB.Column(
        'user_id',
        DB.Integer,
        DB.ForeignKey('user.object_id')
    ),
    DB.Column(
        'announcement_id',
        DB.Integer,
        DB.ForeignKey('announcement.object_id')
    )
)

class Announcement(DB.Model):
    """Model for an announcement sent to registered users."""
    object_id = DB.Column(
        DB.Integer,
        primary_key=True,
        nullable=False
    )
    timestamp = DB.Column(
        DB.DateTime(),
        nullable=False
    )
    content = DB.Column(
        DB.UnicodeText(65536),
        nullable=False
    )
    subject = DB.Column(
        DB.UnicodeText(256),
        nullable=False
    )
    send_email = DB.Column(
        DB.Boolean,
        default=True,
        nullable=False
    )
    email_sent = DB.Column(
        DB.Boolean,
        default=False,
        nullable=False
    )

    sender_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable=False
    )
    sender = DB.relationship(
        'User',
        backref=DB.backref(
            'announcements-sent',
            lazy='dynamic'
        )
    )

    college_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('college.object_id'),
        nullable=True
    )
    college = DB.relationship(
        'College',
        backref=DB.backref(
            'announcements',
            lazy='dynamic'
        )
    )

    affiliation_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('affiliation.object_id'),
        nullable=True
    )
    affiliation = DB.relationship(
        'Affiliation',
        backref=DB.backref(
            'announcements-received',
            lazy='dynamic'
        )
    )

    is_waiting = DB.Column(
        DB.Boolean,
        nullable=True
    )
    has_tickets = DB.Column(
        DB.Boolean,
        nullable=True
    )
    has_collected = DB.Column(
        DB.Boolean,
        nullable=True
    )
    has_uncollected = DB.Column(
        DB.Boolean,
        nullable=True
    )

    users = DB.relationship(
        'User',
        secondary=USER_ANNOUNCE_LINK,
        backref='announcements'
    )

    emails = DB.relationship(
        'User',
        secondary=EMAIL_ANNOUNCE_LINK,
        lazy='dynamic'
    )

    def __init__(self,
                 subject,
                 content,
                 sender_id,
                 send_email,
                 college_id=None,
                 affiliation_id=None,
                 has_tickets=None,
                 is_waiting=None,
                 has_collected=None,
                 has_uncollected=None):
        self.timestamp = datetime.datetime.utcnow()
        self.subject = subject
        self.content = content
        self.sender_id = sender_id
        self.send_email = send_email
        self.college_id = college_id
        self.affiliation_id = affiliation_id
        self.has_tickets = has_tickets
        self.is_waiting = is_waiting
        self.has_collected = has_collected
        self.has_uncollected = has_uncollected

        recipient_query = user.User.query

        if self.college_id is not None:
            recipient_query = recipient_query.filter(
                user.User.college_id == self.college_id
            )

        if self.affiliation_id is not None:
            recipient_query = recipient_query.filter(
                user.User.affiliation_id == self.affiliation_id
            )

        for recipient in recipient_query.all():
            if (
                    (
                        self.has_tickets is None or
                        recipient.has_tickets() == self.has_tickets
                    ) and
                    (
                        self.is_waiting is None or
                        recipient.is_waiting() == self.is_waiting
                    ) and
                    (
                        self.has_collected is None or
                        recipient.has_collected_tickets() == self.has_collected
                    ) and
                    (
                        self.has_uncollected is None or (
                            recipient.has_uncollected_tickets() ==
                            self.has_uncollected
                        )
                    )
            ):
                self.users.append(recipient)
                if send_email:
                    self.emails.append(recipient)

    def __repr__(self):
        return '<Announcement {0}: {1}>'.format(self.object_id, self.subject)

    def send_emails(self, count):
        """Send the announcement as an email to a limited number of recipients.

        Used for batch sending, renders the text of the announcement into an
        email and sends it to users who match the criteria.

        Args:
            count: (int) Maximum number of emails to send

        Returns:
            (int) How much of the original limit is remaining (i.e. |count|
            minus the nuber of emails sent)
        """
        try:
            for recipient in self.emails:
                if count <= 0:
                    break

                APP.email_manager.send_text(recipient.email, self.subject,
                                            self.content, self.sender.email)

                self.emails.remove(recipient)
                count = count - 1
        finally:
            self.email_sent = (self.emails.count() == 0)
            DB.session.commit()

        return count

    @staticmethod
    def get_by_id(object_id):
        """Get an Announcement object by its database ID."""
        announcement = Announcement.query.filter(
            Announcement.object_id == int(object_id)
        ).first()

        if not announcement:
            return None

        return announcement
