# coding: utf-8
"""
announcement.py

Contains Announcement class
Used to store announcements displayed on site and emailed
"""

from kebleball import app
from kebleball.database import db
from kebleball.database import user
from email.mime.text import MIMEText
from datetime import datetime

APP = app.APP
DB = db.DB
User = user.User

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
        DB.Text(65536),
        nullable=False
    )
    subject = DB.Column(
        DB.Text(256),
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
                 sender,
                 send_email,
                 college=None,
                 affiliation=None,
                 has_tickets=None,
                 is_waiting=None,
                 has_collected=None,
                 has_uncollected=None):
        self.timestamp = datetime.utcnow()
        self.subject = subject
        self.content = content
        self.send_email = send_email
        self.has_tickets = has_tickets
        self.is_waiting = is_waiting
        self.has_collected = has_collected
        self.has_uncollected = has_uncollected

        if hasattr(sender, 'object_id'):
            self.sender_id = sender.object_id
        else:
            self.sender_id = sender

        if hasattr(college, 'object_id'):
            self.college_id = college.object_id
        else:
            self.college_id = college

        if hasattr(affiliation, 'object_id'):
            self.affiliation_id = affiliation.object_id
        else:
            self.affiliation_id = affiliation

        query = User.query

        if self.college_id is not None:
            query = query.filter(User.college_id == self.college_id)

        if self.affiliation_id is not None:
            query = query.filter(User.affiliation_id == self.affiliation_id)

        for user in query.all():
            if (
                    (
                        self.has_tickets is None or
                        user.has_tickets() == self.has_tickets
                    ) and
                    (
                        self.is_waiting is None or
                        user.is_waiting() == self.is_waiting
                    ) and
                    (
                        self.has_collected is None or
                        user.has_collected_tickets() == self.has_collected
                    ) and
                    (
                        self.has_uncollected is None or
                        user.has_uncollected_tickets() == self.has_uncollected
                    )
            ):
                self.users.append(user)
                if send_email:
                    self.emails.append(user)

    def __repr__(self):
        return "<Announcement {0}: {1}>".format(self.object_id, self.subject)

    def send_emails(self, count):
        try:
            msg = MIMEText(self.content)
            msg['Subject'] = self.subject
            msg['From'] = self.sender.email

            for user in self.emails:
                if count <= 0:
                    break
                try:
                    msg.replace_header('To', user.email)
                except KeyError:
                    msg['To'] = user.email
                APP.email_manager.sendMsg(msg)
                self.emails.remove(user)
                count = count - 1
        finally:
            DB.session.commit()
            self.email_sent = (self.emails.count() == 0)
            DB.session.commit()

        return count

    @staticmethod
    def get_by_id(object_id):
        announcement = Announcement.query.filter(
            Announcement.object_id == int(object_id)
        ).first()

        if not announcement:
            return None

        return announcement
